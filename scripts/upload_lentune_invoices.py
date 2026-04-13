"""
Script to extract, transform, and upload lentune invoices data to Supabase (APPEND mode)
"""
import sys
from pathlib import Path
from typing import List  # Add this import

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from dotenv import load_dotenv # type: ignore
import os
import logging
import time
from supabase import create_client
from datetime import datetime
import numpy as np

from src.extract.lentune_extractor import LentuneExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """
    Convert non-JSON-serializable objects to JSON-serializable formats
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable object
    """
    try:
        if pd.isna(obj):
            return "0"
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return str(int(obj))
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return str(float(obj)) if not np.isnan(obj) else "0"
        elif isinstance(obj, (list, dict)):
            return str(obj)
        else:
            return str(obj) if obj is not None else "0"
    except Exception as e:
        logger.debug(f"Error converting object: {e}")
        return "0"


def get_supabase_columns(supabase_client, table_name: str, expected_columns: List[str]) -> List[str]:
    """
    Get actual columns from Supabase table
    
    Args:
        supabase_client: Supabase client
        table_name: Name of the table
        expected_columns: Expected columns if table is empty
        
    Returns:
        List of column names in Supabase table
    """
    try:
        response = supabase_client.table(table_name).select("*").limit(1).execute()
        if response.data:
            columns = list(response.data[0].keys())
            logger.info(f"Found Supabase columns: {columns}")
            return columns
        else:
            logger.warning(f"Table {table_name} is empty, using expected columns")
            return expected_columns
    except Exception as e:
        logger.warning(f"Could not fetch columns: {e}, using expected columns")
        return expected_columns


def main():
    """Main execution function for lentune invoices pipeline (APPEND mode)"""
    try:
        logger.info("="*60)
        logger.info("Starting Lentune Invoices ETL Pipeline (APPEND Mode)")
        logger.info("="*60)
        
        # Define required columns
        required_columns = [
            'Categories',
            'Checked Date',
            'First Approved Date',
            'Invoice Number',
            'Line Cost Code',
            'Line Description',
            'Line Excluding',
            'Line Including',
            'Line Price',
            'Line Project',
            'Line Quantity',
            'Line Tax',
            'Processed Date',
            'Second Approved Date',
            'Status',
            'Supplier Description',
            'Transaction Date'
        ]
        
        # Define file path (using data/raw directory)
        lentune_path = project_root / "data" / "raw" / "Lentune_Invoice_Data - adding month.csv"
        
        # Check if file exists
        if not lentune_path.exists():
            logger.error(f"Lentune invoices file not found: {lentune_path}")
            logger.info("Please place 'Lentune_Invoice_Data - adding month.csv' in the data/raw/ directory")
            return {'error': 'File not found', 'uploaded': 0}
        
        # Step 1: Extract
        logger.info("Step 1: Extracting lentune invoices data...")
        extractor = LentuneExtractor(required_columns)
        df_raw = extractor.extract_from_file(lentune_path)
        logger.info(f"Extracted {len(df_raw)} rows")
        
        # Step 2: Prepare for upload
        logger.info("Step 2: Preparing data for upload...")
        df_prepared = extractor.prepare_for_upload(df_raw)
        
        # Show sample of data
        logger.info("\n📋 Sample of prepared data (first row):")
        if len(df_prepared) > 0:
            sample = df_prepared.head(1).to_dict('records')[0]
            for key, value in list(sample.items())[:5]:
                logger.info(f"   {key}: {value}")
        
        # Step 3: Load to Supabase
        logger.info("\nStep 3: Loading to Supabase (APPEND mode)...")
        
        # Load environment variables
        env_path = project_root / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("Loaded environment variables")
        else:
            logger.error(f".env file not found at {env_path}")
            return {'error': '.env file not found', 'uploaded': 0}
        
        # Initialize Supabase client
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        logger.info("Supabase client initialized")
        
        # Configuration
        TABLE_NAME = "lentune_invoices_data"
        BATCH_SIZE = 500
        
        # Get Supabase table columns
        supabase_columns = get_supabase_columns(supabase, TABLE_NAME, required_columns)
        
        # Filter DataFrame to match Supabase columns
        df_upload = extractor.filter_columns_for_supabase(df_prepared, supabase_columns)
        
        # Remove 'Batch Code' if it exists (explicitly)
        if 'Batch Code' in df_upload.columns:
            logger.warning("Explicitly removing 'Batch Code' column")
            df_upload = df_upload.drop(columns=['Batch Code'])
        
        # Show data summary
        logger.info(f"\n📊 Data to upload:")
        logger.info(f"   Total records: {len(df_upload)}")
        logger.info(f"   Columns: {list(df_upload.columns)}")
        
        # Prepare rows with JSON serializable values
        rows = df_upload.to_dict(orient='records')
        
        # Ensure all values are JSON serializable
        for row in rows:
            for key, value in list(row.items()):
                row[key] = make_json_serializable(value)
        
        logger.info(f"\n📤 Starting APPEND upload in batches of {BATCH_SIZE}...")
        
        # Upload in batches (APPEND mode - no delete)
        successful_batches = 0
        failed_rows = []
        total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            try:
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                
                # Check if successful
                if hasattr(response, "data") and response.data is not None:
                    successful_batches += 1
                    logger.info(f"✅ Batch {batch_num}/{total_batches}: Appended {len(batch)} records")
                else:
                    logger.warning(f"⚠️ Batch {batch_num}/{total_batches}: No response data")
                    failed_rows.extend(batch)
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Batch {batch_num}/{total_batches}: Failed - {error_msg[:200]}")
                failed_rows.extend(batch)
                
                # If first batch fails, show detailed error
                if batch_num == 1:
                    logger.error("\n🔍 First batch error details:")
                    if 'Batch Code' in error_msg:
                        logger.error("   The 'Batch Code' column is still present.")
                        logger.error(f"   Current columns: {list(df_upload.columns)}")
                    break
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("LENTUNE INVOICES UPLOAD SUMMARY")
        logger.info("="*50)
        
        if failed_rows:
            logger.warning(f"⚠️ Failed rows: {len(failed_rows)}")
            logger.info(f"✅ Successfully appended: {len(rows) - len(failed_rows)} records")
        else:
            logger.info(f"✅ All {len(rows)} records appended successfully to {TABLE_NAME}!")
        
        logger.info("="*50)
        
        # Verify total records after append
        try:
            response = supabase.table(TABLE_NAME).select("*", count="exact").execute()
            if hasattr(response, 'count'):
                logger.info(f"\n📊 Total records now in {TABLE_NAME}: {response.count}")
            else:
                logger.info(f"\n📊 Total records now in {TABLE_NAME}: {len(response.data)}")
        except Exception as e:
            logger.warning(f"Could not verify total records: {e}")
        
        # Show sample of uploaded data
        if successful_batches > 0:
            logger.info("\n📊 Sample of uploaded data (first 3 rows):")
            display_cols = ['Invoice Number', 'Line Description', 'Line Price', 'Status']
            available_cols = [col for col in display_cols if col in df_upload.columns]
            if available_cols:
                print(df_upload[available_cols].head(3).to_string())
        
        return {
            'total': len(rows),
            'uploaded': len(rows) - len(failed_rows),
            'failed': len(failed_rows),
            'batches_successful': successful_batches
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {'error': str(e), 'uploaded': 0}


if __name__ == "__main__":
    main()