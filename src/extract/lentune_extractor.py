"""
Lentune Invoices extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class LentuneExtractor:
    """Extract and validate lentune invoices data from CSV files"""
    
    def __init__(self, required_columns: List[str]):
        """
        Initialize lentune invoices extractor
        
        Args:
            required_columns: List of columns that must exist in the file
        """
        self.required_columns = required_columns
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract lentune invoices data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted and validated invoices data
        """
        try:
            # Load the CSV file
            logger.info(f"Loading lentune invoices data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            # Validate required columns
            self.validate_columns(df, file_path.name)
            
            # Filter to required columns
            df_filtered = df[self.required_columns]
            logger.info(f"Filtered to {len(df_filtered.columns)} columns")
            
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error extracting lentune invoices data from {file_path}: {e}")
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
        Prepare lentune invoices data for Supabase upload
        
        This method:
        1. Fills empty cells with 0
        2. Converts datetime columns to strings
        3. Ensures all values are JSON serializable
        
        Args:
            df: Raw invoices DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            df_processed = df.copy()
            
            # Fill empty cells with 0
            df_processed = df_processed.fillna(0)
            
            # Replace any remaining None or null values with 0
            df_processed = df_processed.replace([None, 'None', 'null', ''], 0)
            
            # Convert datetime columns to strings
            date_columns = [
                'Checked Date',
                'First Approved Date',
                'Processed Date',
                'Second Approved Date',
                'Transaction Date'
            ]
            
            for col in date_columns:
                if col in df_processed.columns:
                    df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
                    df_processed[col] = df_processed[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df_processed[col] = df_processed[col].fillna('0')
                    logger.debug(f"Formatted {col} to string")
            
            # Convert all columns to string to avoid type issues
            for col in df_processed.columns:
                try:
                    df_processed[col] = df_processed[col].astype(str).replace('0.0', '0').replace('nan', '0').replace('None', '0')
                except Exception as e:
                    logger.debug(f"Error converting column {col}: {e}")
                    df_processed[col] = '0'
            
            # Verify no empty cells remain
            missing_values = df_processed.isnull().sum()
            if missing_values.sum() > 0:
                logger.warning(f"Still have {missing_values.sum()} empty cells after filling")
                # Fill any remaining NaN with '0'
                df_processed = df_processed.fillna('0')
            else:
                logger.info("All empty cells have been filled")
            
            logger.info(f"Prepared {len(df_processed)} rows for upload with {len(df_processed.columns)} columns")
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error preparing data for upload: {e}")
            raise
    
    def filter_columns_for_supabase(self, df: pd.DataFrame, supabase_columns: List[str]) -> pd.DataFrame:
        """
        Filter DataFrame to match Supabase table columns
        
        Args:
            df: Input DataFrame
            supabase_columns: Columns that exist in Supabase
            
        Returns:
            Filtered DataFrame
        """
        try:
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