"""
Upload data to Supabase
"""
import pandas as pd
import time
from typing import Dict, List, Literal
import logging

from .supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class SupabaseUploader:
    """Handle batch uploads to Supabase"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client.client
    
    def get_available_columns(self, table_name: str) -> List[str]:
        """Get list of columns available in the table"""
        try:
            response = self.client.table(table_name).select("*").limit(1).execute()
            if response.data:
                columns = list(response.data[0].keys())
                logger.debug(f"Available columns in {table_name}: {columns}")
                return columns
            else:
                logger.warning(f"Table {table_name} is empty, cannot get columns")
                return []
        except Exception as e:
            logger.error(f"Failed to get columns: {e}")
            return []
    
    def delete_all(self, table_name: str) -> None:
        """Delete all records from table using available columns"""
        logger.info(f"Deleting all records from {table_name}")
        
        try:
            # Get available columns
            columns = self.get_available_columns(table_name)
            
            if not columns:
                logger.warning("Cannot determine columns, skipping delete")
                return
            
            # Use the first available column for delete condition
            # Try common column names first
            preferred_columns = ["unique id", "id", "Job Number", "Wall Name", "Asset Code"]
            delete_column = None
            
            for col in preferred_columns:
                if col in columns:
                    delete_column = col
                    break
            
            # If none of the preferred columns found, use first column
            if not delete_column and columns:
                delete_column = columns[0]
            
            if delete_column:
                logger.info(f"Using column '{delete_column}' for delete condition")
                # Delete all records where the column is not null
                self.client.table(table_name).delete().not_.is_(delete_column, "null").execute()
                logger.info("Delete successful")
            else:
                logger.warning("No suitable column found for delete, skipping")
                
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    def upload_batch(self, table_name: str, batch: List[Dict], 
                     batch_num: int, total: int) -> bool:
        """Upload a single batch"""
        try:
            self.client.table(table_name).insert(batch).execute()
            logger.info(f"Batch {batch_num}/{total}: Uploaded {len(batch)} records")
            return True
        except Exception as e:
            logger.error(f"Batch {batch_num}/{total} failed: {e}")
            return False
    
    def upload(self, df: pd.DataFrame, table_name: str,
              mode: Literal['overwrite', 'append'] = 'append',
              batch_size: int = 500) -> Dict[str, int]:
        """Upload DataFrame to Supabase"""
        stats = {
            'total': len(df),
            'uploaded': 0,
            'failed': 0
        }
        
        if len(df) == 0:
            logger.warning("No data to upload")
            return stats
        
        # Prepare data
        df_processed = df.fillna(0)
        # Convert datetime columns to string to avoid issues
        for col in df_processed.columns:
            if pd.api.types.is_datetime64_any_dtype(df_processed[col]):
                df_processed[col] = df_processed[col].dt.strftime('%Y-%m-%d')
        
        # Convert to records
        rows = df_processed.to_dict(orient='records')
        
        # Overwrite mode - delete all existing data
        if mode == 'overwrite':
            try:
                self.delete_all(table_name)
            except Exception as e:
                logger.error(f"Delete failed: {e}")
                logger.warning("Continuing with upload anyway...")
        
        # Upload in batches
        total_batches = (len(rows) + batch_size - 1) // batch_size
        logger.info(f"Uploading {len(rows)} records in {total_batches} batches")
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if self.upload_batch(table_name, batch, batch_num, total_batches):
                stats['uploaded'] += len(batch)
            else:
                stats['failed'] += len(batch)
                if batch_num == 1:
                    logger.error("First batch failed - stopping upload")
                    break
            
            time.sleep(0.05)  # Rate limiting
        
        logger.info(f"Upload complete: {stats['uploaded']}/{stats['total']}")
        return stats