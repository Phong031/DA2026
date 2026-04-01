"""
Concrete Type extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class ConcreteTypeExtractor:
    """Extract and validate concrete type data from CSV files"""
    
    def __init__(self, required_columns: List[str]):
        """
        Initialize concrete type extractor
        
        Args:
            required_columns: List of columns that must exist in the file
        """
        self.required_columns = required_columns
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract concrete type data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted and validated concrete type data
        """
        try:
            # Load the CSV file
            logger.info(f"Loading concrete type data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            # Validate required columns
            self.validate_columns(df, file_path.name)
            
            # Filter to required columns
            df_filtered = df[self.required_columns]
            logger.info(f"Filtered to {len(df_filtered.columns)} columns")
            
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error extracting concrete type data from {file_path}: {e}")
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
        Prepare concrete type data for Supabase upload
        
        Args:
            df: Raw concrete type DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        df_processed = df.copy()
        
        # Fill empty cells with 0 (matching your original logic)
        df_processed = df_processed.fillna(0)
        
        # Convert NaN to None for Supabase
        df_processed = df_processed.where(pd.notnull(df_processed), None)
        
        logger.info(f"Prepared {len(df_processed)} rows for upload")
        
        # Show sample of Product Codes for verification
        if 'Product Code' in df_processed.columns:
            sample_codes = df_processed['Product Code'].head(5).tolist()
            logger.debug(f"Sample Product Codes: {sample_codes}")
        
        return df_processed