"""
Script to extract, transform, and upload plant and equipment data to Supabase
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

from src.extract.plant_equipment_extractor import PlantEquipmentExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def delete_all_records(supabase_client, table_name: str, column_name: str = "Asset Code") -> None:
    """Delete all records from plant_equipment table"""
    logger.info(f"Deleting all records from {table_name}")
    
    try:
        # Delete using Asset Code column (known to exist)
        supabase_client.table(table_name).delete().neq(column_name, "NO_MATCH").execute()
        logger.info("✅ Existing data deleted successfully.")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise


def main():
    """Main execution function for plant equipment pipeline"""
    try:
        logger.info("="*60)
        logger.info("Starting Plant & Equipment ETL Pipeline")
        logger.info("="*60)
        
        # Define required columns
        required_columns = [
            'Asset Code',
            'Asset Serial',
            'Asset Type',
            'Display Name',
            'Fuel Type',
            'Groups/Fleets',
            'Machine Type',
            'Make',
            'Model',
            'Registration Plate',
            'VIN',
            'Weight Type',
            'Year'
        ]
        
        # Define file path (using data/raw directory)
        plant_equipment_path = project_root / "data" / "raw" / "plant and equipment list.csv"
        
        # Check if file exists
        if not plant_equipment_path.exists():
            logger.error(f"Plant equipment file not found: {plant_equipment_path}")
            logger.info("Please place 'plant_and_equipment_list.csv' in the data/raw/ directory")
            return {'error': 'File not found', 'uploaded': 0}
        
        # Step 1: Extract
        logger.info("Step 1: Extracting plant equipment data...")
        extractor = PlantEquipmentExtractor(required_columns)
        df_raw = extractor.extract_from_file(plant_equipment_path)
        logger.info(f"Extracted {len(df_raw)} rows")
        
        # Step 2: Prepare for upload
        logger.info("Step 2: Preparing data for upload...")
        df_upload = extractor.prepare_for_upload(df_raw)
        
        # Show sample of Asset Codes
        if 'Asset Code' in df_upload.columns:
            logger.info("\n📋 Sample Asset Codes from your data:")
            for code in df_upload['Asset Code'].head(5):
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
        TABLE_NAME = "plant_and_equipment_list"
        BATCH_SIZE = 20
        
        # Delete existing data
        try:
            delete_all_records(supabase, TABLE_NAME, "Asset Code")
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
                    first_asset = batch[0].get('Asset Code', 'N/A')
                    logger.error(f"   First Asset Code in failed batch: {first_asset}")
                failed_rows.extend(batch)
                if batch_num == 1:
                    logger.error("First batch failed - stopping upload")
                    break
            
            time.sleep(0.05)  # Rate limiting
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("Plant & Equipment Pipeline Complete!")
        logger.info("="*50)
        logger.info(f"Records processed: {len(rows)}")
        logger.info(f"Records uploaded: {successful}")
        logger.info(f"Records failed: {len(failed_rows)}")
        logger.info("="*50)
        
        # Show sample of uploaded data
        if successful > 0:
            logger.info("\n📊 Sample of uploaded data (first 3 rows):")
            print(df_upload.head(3).to_string())
        
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