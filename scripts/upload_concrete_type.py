"""
Script to extract, transform, and upload concrete type data to Supabase
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

from src.extract.concrete_type_extractor import ConcreteTypeExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def delete_all_records(supabase_client, table_name: str, column_name: str = "Product Code") -> None:
    """Delete all records from concrete_type table"""
    logger.info(f"Deleting all records from {table_name}")
    
    try:
        # Delete using Product Code column (known to exist)
        supabase_client.table(table_name).delete().neq(column_name, "NO_MATCH").execute()
        logger.info("✅ Existing data deleted successfully.")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise


def main():
    """Main execution function for concrete type pipeline"""
    try:
        logger.info("="*60)
        logger.info("Starting Concrete Type ETL Pipeline")
        logger.info("="*60)
        
        # Define required columns
        required_columns = [
            'Product Code',
            'Product Description',
            'Product Type'
        ]
        
        # Define file path (using data/raw directory)
        concrete_type_path = project_root / "data" / "raw" / "concrete type.csv"
        
        # Check if file exists
        if not concrete_type_path.exists():
            logger.error(f"Concrete type file not found: {concrete_type_path}")
            logger.info("Please place 'concrete_type.csv' in the data/raw/ directory")
            return {'error': 'File not found', 'uploaded': 0}
        
        # Step 1: Extract
        logger.info("Step 1: Extracting concrete type data...")
        extractor = ConcreteTypeExtractor(required_columns)
        df_raw = extractor.extract_from_file(concrete_type_path)
        logger.info(f"Extracted {len(df_raw)} rows")
        
        # Step 2: Prepare for upload
        logger.info("Step 2: Preparing data for upload...")
        df_upload = extractor.prepare_for_upload(df_raw)
        
        # Show sample of Product Codes
        if 'Product Code' in df_upload.columns:
            logger.info("\n📋 Sample Product Codes from your data:")
            for code in df_upload['Product Code'].head(5):
                logger.info(f"   {code}")
        
        # Show missing values summary
        missing_summary = df_upload.isna().sum()
        if missing_summary.sum() > 0:
            logger.info("\nMissing values summary:")
            for col, count in missing_summary[missing_summary > 0].items():
                logger.info(f"  {col}: {count} missing values")
        else:
            logger.info("\nNo missing values found")
        
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
        TABLE_NAME = "concrete_type"
        BATCH_SIZE = 50  # Larger batch size for concrete type (smaller dataset)
        
        # Delete existing data
        try:
            delete_all_records(supabase, TABLE_NAME, "Product Code")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return {'error': f'Delete failed: {e}', 'uploaded': 0}
        
        # Prepare data for upload
        df = df_upload.copy()
        
        # Convert to records
        rows = df.to_dict(orient='records')
        
        logger.info(f"\n📊 Uploading {len(rows)} records...")
        
        # Upload in batches
        successful = 0
        failed_rows = []
        total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            try:
                supabase.table(TABLE_NAME).insert(batch).execute()
                successful += len(batch)
                logger.info(f"✅ Batch {batch_num}/{total_batches}: Uploaded {len(batch)} records")
            except Exception as e:
                logger.error(f"❌ Batch {batch_num}/{total_batches}: Failed - {e}")
                if batch:
                    first_code = batch[0].get('Product Code', 'N/A')
                    logger.error(f"   First Product Code in failed batch: {first_code}")
                failed_rows.extend(batch)
                if batch_num == 1:
                    logger.error("First batch failed - stopping upload")
                    break
            
            time.sleep(0.05)  # Rate limiting
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("Concrete Type Pipeline Complete!")
        logger.info("="*50)
        logger.info(f"Records processed: {len(rows)}")
        logger.info(f"Records uploaded: {successful}")
        logger.info(f"Records failed: {len(failed_rows)}")
        logger.info("="*50)
        
        # Show sample of uploaded data
        if successful > 0:
            logger.info("\n📊 Sample of uploaded data (first 5 rows):")
            print(df_upload.head(5).to_string())
        
        return {
            'total': len(rows),
            'uploaded': successful,
            'failed': len(failed_rows)
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {'error': str(e), 'uploaded': 0}


if __name__ == "__main__":
    main()