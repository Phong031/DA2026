"""
Job Data extractor for Excel files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class JobDataExtractor:
    """Extract and validate job data from Excel files"""
    
    def __init__(self, required_columns: List[str]):
        """
        Initialize job data extractor
        
        Args:
            required_columns: List of columns that must exist in the file
        """
        self.required_columns = required_columns
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract job data from Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            DataFrame with extracted and validated job data
        """
        try:
            # Load the Excel file
            logger.info(f"Loading job data from: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            # Validate required columns
            self.validate_columns(df, file_path.name)
            
            # Filter to required columns
            df_filtered = df[self.required_columns]
            logger.info(f"Filtered to {len(df_filtered.columns)} columns")
            
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error extracting job data from {file_path}: {e}")
            raise
    
    def validate_columns(self, df: pd.DataFrame, filename: str) -> None:
        """
        Validate that all required columns exist in the DataFrame
        
        Args:
            df: DataFrame to validate
            filename: Source filename for error messages
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            error_msg = f"Missing required columns in {filename}: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"All {len(self.required_columns)} required columns present")
    
    def prepare_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare job data for Supabase upload
        
        Args:
            df: Raw job data DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        df_processed = df.copy()
        
        # Fill missing unique id with "UNKNOWN"
        if "unique id" in df_processed.columns:
            df_processed["unique id"] = df_processed["unique id"].fillna("UNKNOWN")
            logger.debug("Filled missing 'unique id' with 'UNKNOWN'")
        
        # Convert datetime columns to string format
        date_columns = [
            'First Received Date',
            'Onsite Finish',
            'Onsite Start',
            'Successful Date'
        ]
        
        for col in date_columns:
            if col in df_processed.columns:
                # Convert to datetime, then to string
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
                df_processed[col] = df_processed[col].dt.strftime('%Y-%m-%d')
                logger.debug(f"Formatted {col} to YYYY-MM-DD")
        
        # Replace NaN with None for Supabase
        df_processed = df_processed.where(pd.notnull(df_processed), None)
        
        logger.info(f"Prepared {len(df_processed)} rows for upload")
        return df_processed