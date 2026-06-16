"""
Workshop Cost Data extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
import numpy as np
import re

logger = logging.getLogger(__name__)


class WorkshopCostExtractor:
    """Extract and validate workshop cost data from CSV files"""
    
    def __init__(self):
        """Initialize workshop cost extractor"""
        # List of columns that should be treated as text/dates (not numeric)
        self.text_columns = [
            'Report Month', 'Date', 'Month', 'Report Date',
            'Workshop', 'Job Number', 'Cost Type', 'Description'
        ]
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract workshop cost data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted workshop cost data
        """
        try:
            # Load the CSV file
            logger.info(f"Loading workshop cost data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting workshop cost data from {file_path}: {e}")
            raise
    
    def should_keep_as_text(self, column_name: str) -> bool:
        """
        Determine if a column should be kept as text (not converted to numeric)
        
        Args:
            column_name: Name of the column
            
        Returns:
            True if column should be kept as text
        """
        column_lower = column_name.lower()
        
        # Check against text columns list
        for text_col in self.text_columns:
            if text_col.lower() in column_lower:
                return True
        
        # Also check for date-like column names
        if 'date' in column_lower or 'month' in column_lower:
            return True
        
        return False
    
    def clean_numeric_value(self, value):
        """
        Clean a value to be numeric-friendly
        
        Converts:
        - Hyphens/dashes to 0
        - Empty strings to 0
        - Non-numeric strings to 0
        - Preserves valid numbers
        
        Args:
            value: Input value
            
        Returns:
            Numeric value or 0 if not convertible
        """
        try:
            if pd.isna(value):
                return 0
            
            # Convert to string for processing
            str_value = str(value).strip()
            
            # Check if it's a dash or hyphen
            if str_value in ['-', '--', '---', ' - ', '  -  ', 'N/A', 'n/a', '']:
                return 0
            
            # Try to convert to float
            # Remove any currency symbols or commas
            cleaned = re.sub(r'[$,%]', '', str_value)
            
            # Try to convert
            numeric_value = float(cleaned)
            return numeric_value
            
        except (ValueError, TypeError):
            # If conversion fails, return 0
            return 0
    
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
        Prepare workshop cost data for Supabase upload (APPEND mode)
        
        This method:
        1. Identifies text/date columns to preserve as-is
        2. Converts numeric columns appropriately
        3. Fills all empty cells with appropriate values
        4. Preserves date columns as text (no conversion)
        5. Replaces NaN with None for Supabase
        
        Args:
            df: Raw workshop cost DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            df_processed = df.copy()
            
            # Process each column
            for col in df_processed.columns:
                if self.should_keep_as_text(col):
                    # Keep as text - preserve original format
                    df_processed[col] = df_processed[col].apply(self.preserve_text_value)
                    logger.debug(f"Preserved text column '{col}' as-is")
                else:
                    # Check if column contains numeric data
                    sample = df_processed[col].dropna().head(5)
                    if not sample.empty:
                        # Test if it looks like numeric data
                        sample_str = sample.astype(str).str.strip()
                        has_currency = sample_str.str.contains(r'[\d$€£]', regex=True).any()
                        has_hyphen = sample_str.str.contains(r'^-', regex=True).any()
                        
                        if has_currency or has_hyphen or pd.api.types.is_numeric_dtype(df_processed[col]):
                            # Treat as numeric
                            df_processed[col] = df_processed[col].apply(self.clean_numeric_value)
                            logger.debug(f"Cleaned numeric column '{col}'")
                        else:
                            # Default to text
                            df_processed[col] = df_processed[col].apply(self.preserve_text_value)
                            logger.debug(f"Treated column '{col}' as text")
            
            # Fill any remaining NaN values
            for col in df_processed.columns:
                if self.should_keep_as_text(col):
                    df_processed[col] = df_processed[col].fillna('')
                else:
                    if pd.api.types.is_numeric_dtype(df_processed[col]):
                        df_processed[col] = df_processed[col].fillna(0)
                    else:
                        df_processed[col] = df_processed[col].fillna('')
            
            # Replace NaN with None for Supabase (safety check)
            df_processed = df_processed.where(pd.notnull(df_processed), None)
            
            # Check for missing values summary
            missing_summary = df_processed.isna().sum()
            if missing_summary.sum() > 0:
                logger.info(f"Missing values found: {missing_summary[missing_summary > 0].to_dict()}")
            else:
                logger.info("No missing values found")
            
            logger.info(f"Prepared {len(df_processed)} rows for upload with {len(df_processed.columns)} columns")
            
            # Log sample of text columns for verification
            for col in df_processed.columns:
                if self.should_keep_as_text(col) and len(df_processed) > 0:
                    sample_val = df_processed[col].iloc[0]
                    logger.debug(f"Sample value for '{col}': {sample_val}")
            
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
                        # Keep as string in original format
                        df[col] = df[col].dt.strftime('%d/%m/%Y')
                        logger.debug(f"Converted datetime64 column '{col}' to string")
                    
                    # Check for object dtype that might contain datetime objects
                    elif df[col].dtype == 'object':
                        # Sample a few non-null values
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