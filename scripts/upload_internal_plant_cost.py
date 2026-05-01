"""
Script to extract, transform, and upload internal plant cost data to Supabase (APPEND mode)
"""
import sys
from pathlib import Path
from typing import List

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

from src.extract.internal_plant_cost_extractor import InternalPlantCostExtractor

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
            return None
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj) if not np.isnan(obj) else None
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (list, dict)):
            return obj
        else:
            return obj
    except Exception as e:
        logger.debug(f"Error converting object: {e}")
        return str(obj) if obj is not None else None


def get_supabase_columns(supabase_client, table_name: str) -> List[str]:
    """
    Get actual columns from Supabase table
    
    Args:
        supabase_client: Supabase client
        table_name: Name of the table
        
    Returns:
        List of column names in Supabase table
    """
    try:
        response = supabase_client.table(table_name).select("*").limit(1).execute()
        if response.data:
            columns = list(response.data[0].keys())
            logger.info(f"Found Supabase columns: {columns[:10]}...")  # Show first 10
            return columns
        else:
            logger.warning(f"Table {table_name} is empty")
            return []
    except Exception as e:
        logger.warning(f"Could not fetch columns: {e}")
        return []


def filter_columns_for_supabase(df: pd.DataFrame, supabase_columns: List[str]) -> pd.DataFrame:
    """
    Filter DataFrame to match Supabase table columns
    
    Args:
        df: Input DataFrame
        supabase_columns: Columns that exist in Supabase
        
    Returns:
        Filtered DataFrame
    """
    try:
        if not supabase_columns:
            logger.warning("No Supabase columns provided, keeping all columns")
            return df
        
        # Find columns that exist in both dataframe and Supabase
        columns_to_keep = [col for col in supabase_columns if col in df.columns]
        columns_to_remove = [col for col in df.columns if col not in supabase_columns]
        
        if columns_to_remove:
            logger.info(f"Removing {len(columns_to_remove)} columns not in Supabase table")
            for col in columns_to_remove[:5]:  # Show first 5
                logger.debug(f"  Removing column: {col}")
        
        # Remove columns not in Supabase
        df_filtered = df[columns_to_keep]
        logger.info(f"Keeping {len(df_filtered.columns)} columns for upload")
        
        return df_filtered
        
    except Exception as e:
        logger.error(f"Error filtering columns: {e}")
        return df


def main():
    """Main execution function for internal plant cost pipeline (APPEND mode)"""
    try:
        logger.info("="*60)
        logger.info("Starting Internal Plant Cost ETL Pipeline (APPEND Mode)")
        logger.info("="*60)
        
        # Define file path (using data/raw directory)
        plant_cost_path = project_root / "data" / "raw" / "Internal_Plant_Cost - adding month.csv"
        
        # Check if file exists
        if not plant_cost_path.exists():
            logger.error(f"Internal plant cost file not found: {plant_cost_path}")
            logger.info("Please place 'Internal_Plant_Cost - adding month.csv' in the data/raw/ directory")
            return {'error': 'File not found', 'uploaded': 0}
        
        # Step 1: Extract
        logger.info("Step 1: Extracting internal plant cost data...")
        extractor = InternalPlantCostExtractor()
        df_raw = extractor.extract_from_file(plant_cost_path)
        logger.info(f"Extracted {len(df_raw)} rows with {len(df_raw.columns)} columns")
        
        # Show column list
        logger.info(f"\n📋 Available columns: {list(df_raw.columns)[:10]}...")
        if len(df_raw.columns) > 10:
            logger.info(f"   ... and {len(df_raw.columns) - 10} more columns")
        
        # Step 2: Prepare for upload (fill empty cells, convert dates)
        logger.info("\nStep 2: Preparing data for upload...")
        df_prepared = extractor.prepare_for_upload(df_raw)
        
        # Convert to JSON serializable
        df_prepared = extractor.convert_to_json_serializable(df_prepared)
        
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
        TABLE_NAME = "internal_plant_cost"
        BATCH_SIZE = 100  # Standard batch size for plant cost data
        
        # Get Supabase table columns (optional - for filtering)
        supabase_columns = get_supabase_columns(supabase, TABLE_NAME)
        
        # Filter DataFrame to match Supabase columns (if needed)
        if supabase_columns:
            df_upload = filter_columns_for_supabase(df_prepared, supabase_columns)
        else:
            df_upload = df_prepared
            logger.info("Using all columns for upload")
        
        # Show data summary
        logger.info(f"\n📊 Data to upload:")
        logger.info(f"   Total records: {len(df_upload)}")
        logger.info(f"   Columns: {list(df_upload.columns)[:10]}...")
        
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
                    logger.error(f"   Error: {error_msg}")
                    if batch:
                        logger.error(f"   First record keys: {list(batch[0].keys())[:5]}...")
                    break
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("INTERNAL PLANT COST DATA UPLOAD SUMMARY")
        logger.info("="*50)
        
        if failed_rows:
            logger.warning(f"⚠️ Failed rows: {len(failed_rows)}")
            logger.info(f"✅ Successfully appended: {len(rows) - len(failed_rows)} records")
        else:
            logger.info(f"✅ All {len(rows)} records appended successfully to {TABLE_NAME}!")
        
        logger.info("="*50)
        
        # Verify total records after append
        try:
            response = supabase.table(TABLE_NAME).select("*", count="exact").limit(1).execute()
            if hasattr(response, 'count'):
                logger.info(f"\n📊 Total records now in {TABLE_NAME}: {response.count}")
            else:
                logger.info(f"\n📊 Total records now in {TABLE_NAME}: Table has data")
        except Exception as e:
            logger.warning(f"Could not verify total records: {e}")
        
        # Show sample of uploaded data
        if successful_batches > 0 and len(df_upload) > 0:
            logger.info("\n📊 Sample of uploaded data (first 3 rows):")
            # Show first 3 rows with first 5 columns
            display_cols = list(df_upload.columns)[:5]
            print(df_upload[display_cols].head(3).to_string())
        
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