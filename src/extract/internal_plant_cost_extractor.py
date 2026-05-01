"""
Internal Plant Cost Data extractor for CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime
import numpy as np
import re

logger = logging.getLogger(__name__)


class InternalPlantCostExtractor:
    """Extract and validate internal plant cost data from CSV files"""
    
    def __init__(self):
        """Initialize internal plant cost extractor"""
        pass
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract internal plant cost data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with extracted plant cost data
        """
        try:
            # Load the CSV file
            logger.info(f"Loading internal plant cost data from: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting internal plant cost data from {file_path}: {e}")
            raise
    
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
    
    def standardize_date_format(self, date_value):
        """
        Standardize date to dd/mm/yyyy format as text
        
        Args:
            date_value: Input date value (could be various formats)
            
        Returns:
            Date string in dd/mm/yyyy format
        """
        try:
            if pd.isna(date_value):
                return ''
            
            # Convert to string
            date_str = str(date_value).strip()
            
            # If it's empty or just hyphens
            if date_str in ['-', '--', '---', ' - ', '  -  ', 'N/A', 'n/a', '']:
                return ''
            
            # Try to parse the date
            # First check if it's already in dd/mm/yyyy format
            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                # Parse and reformat to ensure consistent dd/mm/yyyy
                try:
                    # Try to parse as dd/mm/yyyy
                    parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                    return parsed_date.strftime('%d/%m/%Y')
                except ValueError:
                    pass
            
            # Try other common formats
            date_formats = [
                '%Y-%m-%d',      # 2024-03-15
                '%d-%m-%Y',      # 15-03-2024
                '%m/%d/%Y',      # 03/15/2024
                '%Y/%m/%d',      # 2024/03/15
                '%d.%m.%Y',      # 15.03.2024
                '%d %b %Y',      # 15 Mar 2024
                '%d %B %Y',      # 15 March 2024
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            
            # If all parsing fails, return original
            logger.debug(f"Could not parse date: {date_str}, keeping as is")
            return date_str
            
        except Exception as e:
            logger.debug(f"Error standardizing date: {e}")
            return date_str if not pd.isna(date_value) else ''
    
    def prepare_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare internal plant cost data for Supabase upload (APPEND mode)
        
        This method:
        1. Cleans numeric columns (converts hyphens/dashes to 0)
        2. Fills all empty cells with appropriate values
        3. Preserves date format as dd/mm/yyyy (text)
        4. Replaces NaN with None for Supabase
        5. Ensures all values are JSON serializable
        
        Args:
            df: Raw plant cost DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            df_processed = df.copy()
            
            # List of numeric columns that need cleaning
            numeric_columns = ['RW Lease Rates Total', 'Internal Rates Total']
            
            # Clean numeric columns - convert hyphens/dashes to 0
            for col in numeric_columns:
                if col in df_processed.columns:
                    df_processed[col] = df_processed[col].apply(self.clean_numeric_value)
                    logger.debug(f"Cleaned numeric column '{col}'")
            
            # Process date column - preserve dd/mm/yyyy format
            if 'Date' in df_processed.columns:
                # Apply date standardization
                df_processed['Date'] = df_processed['Date'].apply(self.standardize_date_format)
                logger.debug("Processed Date column - preserved dd/mm/yyyy format")
            
            # Fill remaining empty cells - numeric with 0, text with empty string
            for col in df_processed.columns:
                if col in numeric_columns or col == 'Date':
                    # Already handled, skip
                    continue
                elif pd.api.types.is_numeric_dtype(df_processed[col]):
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
                        # Convert to string in dd/mm/yyyy format
                        df[col] = df[col].dt.strftime('%d/%m/%Y')
                        logger.debug(f"Converted datetime64 column '{col}' to dd/mm/yyyy string")
                    
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
                                logger.debug(f"Converted datetime objects in column '{col}' to dd/mm/yyyy string")
                    
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