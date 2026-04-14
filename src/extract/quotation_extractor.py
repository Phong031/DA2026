"""
Combined Quotation Data extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class QuotationExtractor:
    """Extract and validate combined quotation data from CSV files"""
    
    def __init__(self):
        """Initialize quotation extractor"""
        pass
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract quotation data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted quotation data
        """
        try:
            # Load the CSV file
            logger.info(f"Loading quotation data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting quotation data from {file_path}: {e}")
            raise
    
    def prepare_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare quotation data for Supabase upload (APPEND mode)
        
        This method:
        1. Fills all empty cells with appropriate values
        2. Converts datetime columns to strings
        3. Replaces NaN with None for Supabase
        4. Ensures all values are JSON serializable
        
        Args:
            df: Raw quotation DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            df_processed = df.copy()
            
            # Fill empty cells - numeric with 0, text with empty string
            for col in df_processed.columns:
                if pd.api.types.is_numeric_dtype(df_processed[col]):
                    df_processed[col] = df_processed[col].fillna(0)
                else:
                    df_processed[col] = df_processed[col].fillna('')
            
            # Convert datetime columns to string format
            for col in df_processed.columns:
                if pd.api.types.is_datetime64_any_dtype(df_processed[col]):
                    df_processed[col] = pd.to_datetime(df_processed[col]).dt.strftime('%Y-%m-%d')
                    logger.debug(f"Converted datetime column '{col}' to string")
            
            # Replace NaN with None for Supabase (safety check)
            df_processed = df_processed.where(pd.notnull(df_processed), None)
            
            # Check for missing values summary
            missing_summary = df_processed.isna().sum()
            if missing_summary.sum() > 0:
                logger.info(f"Missing values found: {missing_summary[missing_summary > 0].to_dict()}")
            else:
                logger.info("No missing values found")
            
            logger.info(f"Prepared {len(df_processed)} rows for upload with {len(df_processed.columns)} columns")
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error preparing data for upload: {e}")
            raise
    
    def convert_to_json_serializable(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert all non-JSON-serializable types to JSON-serializable formats
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with all values JSON serializable
        """
        try:
            for col in df.columns:
                try:
                    # Check if column contains datetime64 values
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.strftime('%Y-%m-%d')
                        logger.debug(f"Converted datetime64 column '{col}' to string")
                    
                    # Check for object dtype that might contain datetime objects
                    elif df[col].dtype == 'object':
                        # Sample a few non-null values
                        sample = df[col].dropna().head(3)
                        if not sample.empty:
                            sample_val = sample.iloc[0]
                            if isinstance(sample_val, (pd.Timestamp, datetime)):
                                df[col] = df[col].apply(
                                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
                                )
                                logger.debug(f"Converted datetime objects in column '{col}' to string")
                    
                    # Convert numpy integers to Python ints
                    elif pd.api.types.is_integer_dtype(df[col]):
                        df[col] = df[col].where(pd.notna(df[col]), None)
                        
                    # Convert numpy floats to Python floats
                    elif pd.api.types.is_float_dtype(df[col]):
                        df[col] = df[col].where(pd.notna(df[col]), None)
                        
                except Exception as e:
                    logger.debug(f"Error processing column {col}: {e}")
                    continue
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting to JSON serializable: {e}")
            return df