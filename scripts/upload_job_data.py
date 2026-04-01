"""
Script to extract, transform, and upload job data to Supabase
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from dotenv import load_dotenv  # type: ignore
import os
import logging

from src.extract.job_data_extractor import JobDataExtractor
from src.load.supabase_client import SupabaseClient
from src.load.uploader import SupabaseUploader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function for job data pipeline"""
    try:
        logger.info("="*60)
        logger.info("Starting Job Data ETL Pipeline")
        logger.info("="*60)
        
        # Define required columns
        required_columns = [
            'Address',
            'City',
            'Estimator',
            'Estimator Email',
            'First Received Date',
            'Foreman',
            'Foreman Email',
            'Foreman Phone',
            'Job Area',
            'Job Description',
            'Job Name',
            'Job Number',
            'Job Value',
            'Main Contractor',
            'Onsite Finish',
            'Onsite Start',
            'Suburb',
            'Successful Date',
            'Supervisor',
            'Supervisor Email',
            'Supervisor Phone',
            'unique id'
        ]
        
        # Define file path (using data/raw directory)
        job_data_path = project_root / "data" / "raw" / "5 Jobs Data.xlsx"
        
        # Check if file exists
        if not job_data_path.exists():
            logger.error(f"Job data file not found: {job_data_path}")
            logger.info("Please place '5 Jobs Data.xlsx' in the data/raw/ directory")
            return {'error': 'File not found', 'uploaded': 0}
        
        # Step 1: Extract
        logger.info("Step 1: Extracting job data...")
        extractor = JobDataExtractor(required_columns)
        df_raw = extractor.extract_from_file(job_data_path)
        logger.info(f"Extracted {len(df_raw)} rows")
        
        # Step 2: Prepare for upload
        logger.info("Step 2: Preparing data for upload...")
        df_upload = extractor.prepare_for_upload(df_raw)
        
        # Show missing values summary
        missing_summary = df_upload.isna().sum()
        if missing_summary.sum() > 0:
            logger.info("Missing values summary:")
            for col, count in missing_summary[missing_summary > 0].items():
                logger.info(f"  {col}: {count} missing values")
        else:
            logger.info("No missing values found")
        
        # Step 3: Load to Supabase
        logger.info("Step 3: Loading to Supabase...")
        
        # Load environment variables
        env_path = project_root / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("Loaded environment variables")
        else:
            logger.error(f".env file not found at {env_path}")
            return {'error': '.env file not found', 'uploaded': 0}
        
        # Initialize Supabase client
        supabase_client = SupabaseClient()
        supabase_client.initialize(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY')
        )
        
        # Upload data (overwrite mode for job data)
        uploader = SupabaseUploader(supabase_client)
        stats = uploader.upload(
            df=df_upload,
            table_name="job_data",
            mode="overwrite",  # Job data should be overwritten
            batch_size=20  # Small batch size for job data
        )
        
        # Summary
        logger.info("="*60)
        logger.info("Job Data Pipeline Complete!")
        logger.info(f"Records processed: {stats['total']}")
        logger.info(f"Records uploaded: {stats['uploaded']}")
        logger.info(f"Records failed: {stats['failed']}")
        logger.info("="*60)
        
        # Show sample of uploaded data
        if stats['uploaded'] > 0:
            logger.info("\nSample of uploaded data (first 3 rows):")
            print(df_upload.head(3).to_string())
        
        return stats
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {'error': str(e), 'uploaded': 0}


if __name__ == "__main__":
    main()