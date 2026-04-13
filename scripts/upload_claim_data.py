"""
Script to extract, transform, and upload claim data to Supabase
"""
import sys
from pathlib import Path

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

from src.extract.claim_extractor import ClaimExtractor
from src.utils.config_loader import ConfigLoader

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
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj) if not np.isnan(obj) else None
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, (list, dict)):
            return obj
        else:
            return obj
    except Exception as e:
        logger.debug(f"Error converting object: {e}")
        return str(obj) if obj is not None else None


def delete_all_records(supabase_client, table_name: str) -> None:
    """Delete all records from claim table"""
    logger.info(f"Deleting all records from {table_name}")
    
    try:
        # Try to delete using Contract No column
        supabase_client.table(table_name).delete().gte('Contract No', 0).execute()
        logger.info("✅ Existing data deleted successfully.")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise


def main():
    """Main execution function for claim data pipeline"""
    try:
        logger.info("="*60)
        logger.info("Starting Claim Data ETL Pipeline")
        logger.info("="*60)
        
        # Load configuration
        config_loader = ConfigLoader(project_root / "config")
        claim_config = config_loader.get_claim_config()
        
        # Get file paths
        file_paths = [Path(path) for path in claim_config['file_paths']]
        
        # Step 1: Extract and Combine
        logger.info("Step 1: Extracting and combining claim data...")
        extractor = ClaimExtractor()
        df_raw = extractor.combine_files(file_paths)
        
        if df_raw.empty:
            logger.error("No data extracted from claim files")
            return {'error': 'No data extracted', 'uploaded': 0}
        
        logger.info(f"Extracted {len(df_raw)} total rows from {len(file_paths)} files")
        
        # Show sample of Contract Numbers
        if 'Contract No' in df_raw.columns:
            logger.info("\n📋 Sample Contract Numbers from your data:")
            for contract in df_raw['Contract No'].dropna().unique()[:5]:
                logger.info(f"   {contract}")
        
        # Step 2: Prepare for upload (add sleeve columns and clean)
        logger.info("\nStep 2: Preparing data for upload...")
        df_upload = extractor.prepare_for_upload(df_raw)
        
        # Final safety check - ensure all values are JSON serializable
        logger.info("\nFinal JSON serialization check...")
        for col in df_upload.columns:
            try:
                # Test first few values
                sample = df_upload[col].dropna().head(3)
                for val in sample:
                    make_json_serializable(val)
                logger.debug(f"Column '{col}' passed JSON check")
            except Exception as e:
                logger.warning(f"Column '{col}' had issues: {e}, converting to string")
                df_upload[col] = df_upload[col].astype(str)
        
        # Show missing values summary
        missing_summary = df_upload.isna().sum()
        if missing_summary.sum() > 0:
            logger.info("\nMissing values summary:")
            for col, count in missing_summary[missing_summary > 0].items():
                if count < len(df_upload) * 0.5:  # Only show if less than 50% missing
                    logger.info(f"  {col}: {count} missing values")
        else:
            logger.info("\nNo missing values found")
        
        # Show sleeve columns summary
        sleeve_cols = ['Permanent Sleeve Claimed', 'Temporary Sleeve Claimed', 
                      'Permanent Sleeve Metre Claimed', 'Temporary Sleeve Metre Claimed']
        logger.info("\n📊 Sleeve Claims Summary:")
        for col in sleeve_cols:
            if col in df_upload.columns:
                non_null = df_upload[col].notna().sum()
                if non_null > 0:
                    logger.info(f"   {col}: {non_null} records")
        
        # Step 3: Load to Supabase
        logger.info("\nStep 3: Loading to Supabase...")
        
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
        TABLE_NAME = claim_config['table_name']
        BATCH_SIZE = claim_config.get('batch_size', 100)
        
        # Delete existing data
        try:
            delete_all_records(supabase, TABLE_NAME)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return {'error': f'Delete failed: {e}', 'uploaded': 0}
        
        # Prepare data for upload - convert to records with JSON serializable values
        rows = df_upload.to_dict(orient='records')
        
        # Ensure all values in rows are JSON serializable
        for row in rows:
            for key, value in list(row.items()):
                row[key] = make_json_serializable(value)
        
        logger.info(f"\n📊 Uploading {len(rows)} records...")
        
        # Upload in batches
        successful = 0
        failed_rows = []
        total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            try:
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                successful += len(batch)
                logger.info(f"✅ Batch {batch_num}/{total_batches}: Uploaded {len(batch)} records")
            except Exception as e:
                logger.error(f"❌ Batch {batch_num}/{total_batches}: Failed - {e}")
                if batch and batch_num == 1:
                    first_contract = batch[0].get('Contract No', 'N/A')
                    logger.error(f"   First Contract No in failed batch: {first_contract}")
                failed_rows.extend(batch)
                if batch_num == 1:
                    logger.error("First batch failed - stopping upload")
                    break
            
            time.sleep(0.05)  # Rate limiting
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("Claim Data Pipeline Complete!")
        logger.info("="*50)
        logger.info(f"Files processed: {len(file_paths)}")
        logger.info(f"Records processed: {len(rows)}")
        logger.info(f"Records uploaded: {successful}")
        logger.info(f"Records failed: {len(failed_rows)}")
        logger.info("="*50)
        
        # Show sample of uploaded data
        if successful > 0:
            logger.info("\n📊 Sample of uploaded data (first 3 rows):")
            display_cols = ['Contract No', 'Description', 'Type', 'Total Amount', 
                           'Permanent Sleeve Claimed', 'Temporary Sleeve Claimed']
            available_cols = [col for col in display_cols if col in df_upload.columns]
            if available_cols:
                print(df_upload[available_cols].head(3).to_string())
        
        return {
            'files_processed': len(file_paths),
            'total': len(rows),
            'uploaded': successful,
            'failed': len(failed_rows)
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {'error': str(e), 'uploaded': 0}


if __name__ == "__main__":
    main()