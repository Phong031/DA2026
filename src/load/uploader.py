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
    
    def __init__(self, client: SupabaseClient):
        self.client = client.client
    
    def delete_all(self, table_name: str) -> None:
        """Delete all records from table"""
        logger.info(f"Deleting all records from {table_name}")
        try:
            self.client.table(table_name).delete().neq("Wall Name", "NO_MATCH").execute()
            logger.info("Delete successful")
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
        
        # Convert to records
        rows = df_processed.to_dict(orient='records')
        
        # Overwrite mode
        if mode == 'overwrite':
            self.delete_all(table_name)
        
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