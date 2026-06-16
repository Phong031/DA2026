"""
Company Cost Data extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
import numpy as np
import re

logger = logging.getLogger(__name__)


class CompanyCostExtractor:
    """Extract and validate company cost data from CSV files"""
    
    def __init__(self):
        """Initialize company cost extractor"""
        pass
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract company cost data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted company cost data
        """
        try:
            # Load the CSV file - read all columns as strings to preserve original format
            logger.info(f"Loading company cost data from: {file_path}")
            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting company cost data from {file_path}: {e}")
            raise
    
    def preserve_text_value(self, value):
        """
        Preserve text value as is (no conversion)
        
        Args:
            value: Input value
            
        Returns:
            Original value as string or empty string if null
        """
        try:
            if pd.isna(value):
                return ''
            
            # Convert to string and strip
            str_value = str(value).strip()
            
            # Handle hyphens or empty values
            if str_value in ['-', '--', '---', ' - ', '  -  ', 'N/A', 'n/a', '']:
                return ''
            
            return str_value
            
        except Exception as e:
            logger.debug(f"Error preserving text value: {e}")
            return ''
    
    def prepare_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare company cost data for Supabase upload (APPEND mode)
        
        This method:
        1. Preserves ALL columns as text (no numeric conversion)
        2. Fills all empty cells with empty strings
        3. Preserves original values including numbers as text
        4. Replaces NaN with None for Supabase
        
        Args:
            df: Raw company cost DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            df_processed = df.copy()
            
            # Process each column - keep everything as text
            for col in df_processed.columns:
                df_processed[col] = df_processed[col].apply(self.preserve_text_value)
                logger.debug(f"Preserved column '{col}' as text")
            
            # Fill any remaining empty values
            for col in df_processed.columns:
                df_processed[col] = df_processed[col].fillna('')
            
            # Replace any remaining NaN with None for Supabase
            df_processed = df_processed.where(pd.notnull(df_processed), None)
            
            # Check for missing values summary
            missing_summary = df_processed.isna().sum()
            if missing_summary.sum() > 0:
                logger.info(f"Missing values found: {missing_summary[missing_summary > 0].to_dict()}")
            else:
                logger.info("No missing values found")
            
            logger.info(f"Prepared {len(df_processed)} rows for upload with {len(df_processed.columns)} columns")
            
            # Log sample values for verification
            if len(df_processed) > 0:
                for col in df_processed.columns[:3]:
                    sample_val = df_processed[col].iloc[0]
                    if sample_val:
                        logger.debug(f"Sample value for '{col}': {str(sample_val)[:50]}")
            
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
                        df[col] = df[col].dt.strftime('%d/%m/%Y')
                        logger.debug(f"Converted datetime64 column '{col}' to string")
                    
                    # Check for object dtype that might contain datetime objects
                    elif df[col].dtype == 'object':
                        sample = df[col].dropna().head(3)
                        if not sample.empty:
                            sample_val = sample.iloc[0]
                            if isinstance(sample_val, (pd.Timestamp, datetime)):
                                df[col] = df[col].apply(
                                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
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