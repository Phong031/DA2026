"""
Main script to extract, transform, and upload pilelog data
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd  # Add this import
from dotenv import load_dotenv # type: ignore
import os
import logging

from src.utils.config_loader import ConfigLoader
from src.extract.excel_loader import ExcelLoader
from src.extract.pilelog_extractor import PileLogExtractor
from src.transform.pilelog_transformer import PileLogTransformer
from src.load.supabase_client import SupabaseClient
from src.load.uploader import SupabaseUploader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    try:
        # Load configuration
        config_loader = ConfigLoader(project_root / "config")
        pilelog_config = config_loader.get_pilelog_config()
        
        logger.info("="*60)
        logger.info("Starting Pilelog ETL Pipeline")
        logger.info("="*60)
        
        # Step 1: Extract
        logger.info("Step 1: Extracting data...")
        extractor = PileLogExtractor(pilelog_config['required_columns'])
        
        all_data = []
        for file_path_str in pilelog_config['file_paths']:
            file_path = Path(file_path_str)
            if file_path.exists():
                logger.info(f"Processing: {file_path.name}")
                data = extractor.extract_from_file(file_path)
                all_data.extend(data)
                logger.info(f"  Extracted {len(data)} sheets from {file_path.name}")
            else:
                logger.warning(f"File not found: {file_path}")
        
        if not all_data:
            logger.error("No data extracted from any files")
            return {'error': 'No data extracted', 'uploaded': 0}
        
        # Combine all data
        df_raw = pd.concat(all_data, ignore_index=True)
        logger.info(f"Total extracted rows: {len(df_raw)}")
        
        # Save raw data
        output_path = project_root / pilelog_config['output_path']
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_raw.to_csv(output_path, index=False)
        logger.info(f"Saved raw data to {output_path}")
        
        # Step 2: Transform
        logger.info("Step 2: Transforming data...")
        transformer = PileLogTransformer()
        df_transformed = transformer.transform(df_raw)
        
        # Select final columns
        final_columns = [
            'Pile Number', 'Date', 'Auger', 'Drill Depth', 'Rock Depth',
            'SED/Beam', 'SED/Beam Length', 'Concrete Pump', 'Sleeve',
            'Actual Rock', 'Calc Conc', 'Job Number', 'Wall Name',
            'Temporary Sleeve', 'Permanent Sleeve'
        ]
        # Only keep columns that exist
        existing_columns = [col for col in final_columns if col in df_transformed.columns]
        df_upload = df_transformed[existing_columns]
        logger.info(f"Prepared {len(df_upload)} rows for upload with {len(existing_columns)} columns")
        
        # Step 3: Load
        logger.info("Step 3: Loading to Supabase...")
        
        # Load environment variables
        env_path = project_root / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("Loaded environment variables")
        else:
            logger.error(f".env file not found at {env_path}")
            return {'error': '.env file not found', 'uploaded': 0}
        
        # Initialize Supabase
        supabase_client = SupabaseClient()
        supabase_client.initialize(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY')
        )
        
        # Upload data
        uploader = SupabaseUploader(supabase_client)
        stats = uploader.upload(
            df=df_upload,
            table_name=pilelog_config['table_name'],
            mode=pilelog_config['upload_mode'],
            batch_size=500
        )
        
        # Summary
        logger.info("="*60)
        logger.info("Pipeline Complete!")
        logger.info(f"Records processed: {stats['total']}")
        logger.info(f"Records uploaded: {stats['uploaded']}")
        logger.info(f"Records failed: {stats['failed']}")
        logger.info("="*60)
        
        return stats
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {'error': str(e), 'uploaded': 0}


if __name__ == "__main__":
    main()