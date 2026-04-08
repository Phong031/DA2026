"""
Claim data extractor for combining multiple Excel files with complex business logic
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extract and combine claim data from multiple Excel files"""
    
    def __init__(self):
        """Initialize claim extractor"""
        self.variation_flag = False
    
    def extract_contract_no(self, df: pd.DataFrame, start_row_index: int) -> List[str]:
        """
        Extract Contract No from rows above the start row
        
        Args:
            df: DataFrame with raw data
            start_row_index: Index where data starts
            
        Returns:
            List of numbers found in Contract No row
        """
        try:
            for index, row in df.iloc[:start_row_index].iterrows():
                row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
                if "Contract No" in row_str:
                    numbers = re.findall(r'\d+', row_str)
                    if numbers:
                        return numbers
            return []
        except Exception as e:
            logger.debug(f"Error extracting contract number: {e}")
            return []
    
    def find_start_row(self, df: pd.DataFrame) -> int:
        """
        Find row index where data starts (contains "Description")
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            Row index of start row
        """
        try:
            for index, row in df.iterrows():
                row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
                if "Description" in row_str:
                    return index
            return 0
        except Exception as e:
            logger.debug(f"Error finding start row: {e}")
            return 0
    
    def find_end_row(self, df: pd.DataFrame) -> int:
        """
        Find row index where data ends (contains "TOTAL CLAIM")
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            Row index of end row
        """
        try:
            for index, row in df.iterrows():
                row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
                if "TOTAL CLAIM" in row_str:
                    return index
            return len(df)
        except Exception as e:
            logger.debug(f"Error finding end row: {e}")
            return len(df)
    
    def safe_get_header_row(self, df: pd.DataFrame, row_index: int) -> List[str]:
        """
        Safely extract and clean header row
        
        Args:
            df: DataFrame with raw data
            row_index: Index of header row
            
        Returns:
            List of cleaned header names
        """
        try:
            header_values = df.iloc[row_index].values
            cleaned_headers = []
            
            for i, val in enumerate(header_values):
                if pd.isna(val):
                    cleaned_headers.append(f"Column_{i}")
                else:
                    cleaned_val = str(val).strip()
                    if cleaned_val == "":
                        cleaned_headers.append(f"Column_{i}")
                    else:
                        cleaned_headers.append(cleaned_val)
            
            return cleaned_headers
        except Exception as e:
            logger.error(f"Error getting header row: {e}")
            return []
    
    def label_type(self, description) -> str:
        """
        Label claim type based on description
        
        Args:
            description: Claim description text
            
        Returns:
            Type label: "Vari", "Est", or "Work"
        """
        try:
            if pd.isna(description):
                return "Unknown"
            
            desc_str = str(description)
            
            # Check for variation
            if self.variation_flag:
                return "Vari"
            elif "Variation" in desc_str or "VARIATION" in desc_str:
                self.variation_flag = True
                return "Vari"
            elif "Establishment" in desc_str or "establishment" in desc_str:
                return "Est"
            else:
                return "Work"
        except Exception as e:
            logger.debug(f"Error labeling type: {e}")
            return "Unknown"
    
    def allowable_type(self, description) -> float:
        """
        Determine allowable factor based on description
        
        Args:
            description: Claim description text
            
        Returns:
            Allowable factor (1.0 for establishment, 0.8221 for others)
        """
        try:
            if pd.isna(description):
                return 0.8221
            
            desc_str = str(description)
            if "Establishment" in desc_str or "establishment" in desc_str:
                return 1.0
            else:
                return 0.8221
        except Exception as e:
            logger.debug(f"Error calculating allowable: {e}")
            return 0.8221
    
    def process_sleeve_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add sleeve claim columns based on description and rate
        
        Args:
            df: DataFrame with claim data
            
        Returns:
            DataFrame with added sleeve columns
        """
        try:
            # Initialize columns with NaN
            df['Permanent Sleeve Claimed'] = np.nan
            df['Temporary Sleeve Claimed'] = np.nan
            df['Permanent Sleeve Metre Claimed'] = np.nan
            df['Temporary Sleeve Metre Claimed'] = np.nan
            
            # Check if required columns exist
            if 'Description' not in df.columns:
                logger.warning("Cannot add sleeve columns: 'Description' column missing")
                return df
            
            # Define conditions for sleeve detection
            description_series = df['Description'].fillna('').astype(str)
            sleeve_condition = description_series.str.contains(r'sleeve|casing', case=False, na=False)
            
            # Permanent sleeve condition
            permanent_condition = sleeve_condition & description_series.str.contains(r'thin|perm|spira', case=False, na=False)
            if 'Rate' in df.columns:
                rate_condition = pd.to_numeric(df['Rate'], errors='coerce') < 900
                permanent_condition = permanent_condition & rate_condition.fillna(False)
            
            # Temporary sleeve condition
            temporary_condition = sleeve_condition & description_series.str.contains(r'temp', case=False, na=False)
            if 'Rate' in df.columns:
                temporary_condition = temporary_condition & rate_condition.fillna(False)
            
            # Add sleeve amount columns
            if 'To Date Amount' in df.columns:
                df.loc[permanent_condition, 'Permanent Sleeve Claimed'] = df.loc[permanent_condition, 'To Date Amount']
                df.loc[temporary_condition, 'Temporary Sleeve Claimed'] = df.loc[temporary_condition, 'To Date Amount']
            
            # Add sleeve metre columns
            if 'To Date' in df.columns:
                df.loc[permanent_condition, 'Permanent Sleeve Metre Claimed'] = df.loc[permanent_condition, 'To Date']
                df.loc[temporary_condition, 'Temporary Sleeve Metre Claimed'] = df.loc[temporary_condition, 'To Date']
            
            permanent_count = permanent_condition.sum()
            temporary_count = temporary_condition.sum()
            logger.debug(f"Added sleeve columns: {permanent_count} permanent, {temporary_count} temporary")
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing sleeve columns: {e}")
            return df
    
    def safe_convert_to_numeric(self, df: pd.DataFrame, column_name: str) -> pd.Series:
        """
        Safely convert a column to numeric
        
        Args:
            df: Input DataFrame
            column_name: Name of column to convert
            
        Returns:
            Series with numeric values
        """
        try:
            if column_name not in df.columns:
                return pd.Series([np.nan] * len(df), index=df.index)
            
            return pd.to_numeric(df[column_name], errors='coerce')
        except Exception as e:
            logger.debug(f"Error converting {column_name} to numeric: {e}")
            return pd.Series([np.nan] * len(df), index=df.index)
    
    def process_quantity_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process Original Schedule Quantity column (replace "RATE ONLY" with 1)
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with processed quantity column
        """
        try:
            if 'Original Schedule Quantity' not in df.columns:
                return df
            
            def process_qty(x):
                try:
                    if pd.isna(x):
                        return 1
                    x_str = str(x).strip().upper()
                    if x_str in ["RATE ONLY", "RATE RANGE", "RATE"]:
                        return 1
                    return x
                except Exception:
                    return 1
            
            df['Original Schedule Quantity'] = df['Original Schedule Quantity'].apply(process_qty)
            df['Original Schedule Quantity'] = pd.to_numeric(df['Original Schedule Quantity'], errors='coerce').fillna(1)
            
            return df
        except Exception as e:
            logger.error(f"Error processing quantity column: {e}")
            return df
    
    def clean_columns_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove placeholder columns and clean up column names for upload
        
        This method removes:
        - Columns starting with 'Column_' (placeholders from header detection)
        - Columns starting with 'Unnamed' (empty columns from Excel)
        - Any non-string column names
        - Duplicate columns
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with only valid columns for upload
        """
        try:
            if df.empty:
                return df
            
            original_col_count = len(df.columns)
            columns_to_keep = []
            
            for col in df.columns:
                # Skip if column name is not a string
                if not isinstance(col, str):
                    logger.debug(f"Skipping non-string column: {col}")
                    continue
                
                # Skip placeholder columns
                if col.startswith('Column_'):
                    logger.debug(f"Skipping placeholder column: {col}")
                    continue
                
                # Skip unnamed columns
                if col.startswith('Unnamed'):
                    logger.debug(f"Skipping unnamed column: {col}")
                    continue
                
                # Skip empty column names
                if col == "" or col.isspace():
                    logger.debug(f"Skipping empty column name")
                    continue
                
                # Keep all other columns
                columns_to_keep.append(col)
            
            # Remove duplicate columns (keep first occurrence)
            seen = set()
            unique_columns = []
            for col in columns_to_keep:
                if col not in seen:
                    seen.add(col)
                    unique_columns.append(col)
            
            # Filter to only keep valid columns
            df_cleaned = df[unique_columns]
            
            removed_count = original_col_count - len(unique_columns)
            if removed_count > 0:
                logger.info(f"Cleaned columns: removed {removed_count} placeholder/duplicate columns, kept {len(unique_columns)} columns")
                logger.debug(f"Columns kept for upload: {unique_columns}")
            
            return df_cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning columns: {e}")
            return df
    
    def convert_to_json_serializable(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert all non-JSON-serializable types to JSON-serializable formats
        
        This handles:
        - datetime objects -> strings
        - Timestamp objects -> strings
        - NaN/Inf -> None
        - numpy types -> Python native types
        
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
                        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                        logger.debug(f"Converted datetime64 column '{col}' to string")
                    
                    # Check for object dtype that might contain datetime objects
                    elif df[col].dtype == 'object':
                        # Sample a few non-null values
                        sample = df[col].dropna().head(3)
                        if not sample.empty:
                            # Check if first sample is a datetime object
                            sample_val = sample.iloc[0]
                            if isinstance(sample_val, (pd.Timestamp, datetime)):
                                df[col] = df[col].apply(
                                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) and isinstance(x, (pd.Timestamp, datetime)) else x
                                )
                                logger.debug(f"Converted datetime objects in column '{col}' to string")
                            # Convert any other non-string objects to string
                            elif not isinstance(sample_val, (str, int, float, bool, type(None))):
                                df[col] = df[col].astype(str)
                                logger.debug(f"Converted object column '{col}' to string for JSON compatibility")
                    
                    # Convert numpy integers to Python ints
                    elif pd.api.types.is_integer_dtype(df[col]):
                        df[col] = df[col].where(pd.notna(df[col]), None)
                        if not df[col].isna().all():
                            df[col] = df[col].astype(object)
                            logger.debug(f"Converted integer column '{col}' to Python int")
                    
                    # Convert numpy floats to Python floats
                    elif pd.api.types.is_float_dtype(df[col]):
                        df[col] = df[col].where(pd.notna(df[col]), None)
                        logger.debug(f"Float column '{col}' prepared for JSON")
                        
                except Exception as e:
                    logger.debug(f"Error processing column {col}: {e}")
                    # Fallback: convert entire column to string
                    try:
                        df[col] = df[col].astype(str)
                        logger.debug(f"Fallback: Converted column '{col}' to string")
                    except Exception as e2:
                        logger.warning(f"Could not convert column {col}: {e2}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting to JSON serializable: {e}")
            return df
    
    def extract_from_file(self, file_path: Path) -> pd.DataFrame:
        """
        Extract claim data from a single Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            DataFrame with extracted claim data
        """
        try:
            # Reset variation flag for each file
            self.variation_flag = False
            
            # Check if file exists
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return pd.DataFrame()
            
            # Read the Excel file
            logger.info(f"Processing file: {file_path.name}")
            xls = pd.ExcelFile(file_path)
            
            # Get the first sheet
            sheet_names = xls.sheet_names
            if not sheet_names:
                logger.warning(f"No sheets found in {file_path.name}")
                return pd.DataFrame()
            
            first_tab = sheet_names[0]
            logger.debug(f"First sheet: {first_tab}")
            
            # Read the entire first tab WITHOUT headers
            df_full = pd.read_excel(xls, first_tab, header=None)
            logger.debug(f"Full sheet shape: {df_full.shape}")
            
            if df_full.empty:
                logger.warning(f"Empty sheet in {file_path.name}")
                return pd.DataFrame()
            
            # Find start and end rows
            start_row_index = self.find_start_row(df_full)
            end_row_index = self.find_end_row(df_full)
            logger.debug(f"Start row: {start_row_index}, End row: {end_row_index}")
            
            # Extract Contract No
            contract_no = self.extract_contract_no(df_full, start_row_index)
            logger.debug(f"Contract No: {contract_no}")
            
            # Calculate data rows
            data_start_row = start_row_index + 1
            data_rows = end_row_index - start_row_index - 1
            
            if data_rows <= 0:
                logger.warning(f"No data rows found in {file_path.name}")
                return pd.DataFrame()
            
            # Get header row
            header_row = self.safe_get_header_row(df_full, start_row_index)
            if not header_row:
                logger.warning(f"Could not extract header row from {file_path.name}")
                return pd.DataFrame()
            
            # Read data rows
            try:
                df = pd.read_excel(
                    xls, first_tab,
                    skiprows=data_start_row,
                    nrows=data_rows,
                    header=None
                )
            except Exception as e:
                logger.error(f"Error reading data rows: {e}")
                return pd.DataFrame()
            
            if df.empty:
                logger.warning(f"No data read from {file_path.name}")
                return pd.DataFrame()
            
            # Ensure column count matches
            if len(header_row) != len(df.columns):
                logger.debug(f"Header length ({len(header_row)}) vs data columns ({len(df.columns)})")
                if len(header_row) < len(df.columns):
                    # Pad header row
                    for i in range(len(header_row), len(df.columns)):
                        header_row.append(f"Column_{i}")
                else:
                    # Truncate header row
                    header_row = header_row[:len(df.columns)]
            
            # Assign column names
            df.columns = header_row
            
            # Remove completely empty columns
            try:
                empty_cols = [col for col in df.columns if df[col].isna().all()]
                if empty_cols:
                    df = df.drop(columns=empty_cols)
                    logger.debug(f"Removed {len(empty_cols)} empty columns")
            except Exception as e:
                logger.debug(f"Error removing empty columns: {e}")
            
            # Clean column names
            try:
                df.columns = [str(col).strip() for col in df.columns]
            except Exception as e:
                logger.debug(f"Error cleaning column names: {e}")
            
            # Add Contract No column
            if contract_no:
                df.insert(0, "Contract No", contract_no[0])
                logger.debug(f"Added Contract No: {contract_no[0]}")
            
            # Check if required columns exist
            if 'Description' not in df.columns:
                logger.error(f"'Description' column not found in {file_path.name}")
                logger.debug(f"Available columns: {list(df.columns)[:20]}")
                return pd.DataFrame()
            
            # Apply business logic
            try:
                df["Type"] = df["Description"].apply(self.label_type)
                df["Allowable"] = df["Description"].apply(self.allowable_type)
            except Exception as e:
                logger.error(f"Error applying type/allowable logic: {e}")
            
            # Process quantity column
            df = self.process_quantity_column(df)
            
            # Convert numeric columns
            numeric_columns = [
                "Original Schedule Quantity", "Rate", "Original Schedule Amount",
                "CERTIFIED Previous", "CLAIMED Period", "To Date",
                "Previous CERTIFIED Amount", "CLAIMED Period Amount", "To Date Amount"
            ]
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = self.safe_convert_to_numeric(df, col)
            
            # Calculate Total Amount
            if 'Original Schedule Quantity' in df.columns and 'Rate' in df.columns:
                try:
                    df["Total Amount"] = df["Original Schedule Quantity"] * df["Rate"]
                    logger.debug("Added Total Amount column")
                except Exception as e:
                    logger.debug(f"Error calculating Total Amount: {e}")
            
            logger.info(f"Successfully extracted {len(df)} rows from {file_path.name}")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def combine_files(self, file_paths: List[Path]) -> pd.DataFrame:
        """
        Combine claim data from multiple Excel files
        
        Args:
            file_paths: List of Excel file paths
            
        Returns:
            Combined DataFrame with all claim data
        """
        all_data = []
        successful_files = 0
        
        for file_path in file_paths:
            try:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                df = self.extract_from_file(file_path)
                if not df.empty:
                    all_data.append(df)
                    successful_files += 1
                    logger.info(f"Successfully processed: {file_path.name}")
                else:
                    logger.warning(f"No data extracted from: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
                continue
        
        if not all_data:
            logger.error("No data extracted from any file")
            return pd.DataFrame()
        
        # Combine all data
        try:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Combined {successful_files} files into {len(combined_df)} rows")
            return combined_df
        except Exception as e:
            logger.error(f"Error combining dataframes: {e}")
            return pd.DataFrame()
    
    def prepare_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare claim data for Supabase upload
        
        This method:
        1. Adds sleeve claim columns
        2. Cleans up placeholder columns (Column_*, Unnamed*)
        3. Removes duplicate columns
        4. Converts all values to JSON serializable format
        5. Converts NaN to None for Supabase
        
        Args:
            df: Raw claim DataFrame
            
        Returns:
            Prepared DataFrame ready for upload
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame, nothing to prepare")
                return df
            
            df_processed = df.copy()
            
            # Add sleeve columns
            df_processed = self.process_sleeve_columns(df_processed)
            
            # Clean columns - remove placeholder columns (Column_*, Unnamed*)
            df_processed = self.clean_columns_for_upload(df_processed)
            
            # Convert all values to JSON serializable format
            df_processed = self.convert_to_json_serializable(df_processed)
            
            # Replace NaN with None for Supabase
            df_processed = df_processed.replace({np.nan: None, pd.NA: None})
            
            logger.info(f"Prepared {len(df_processed)} rows for upload with {len(df_processed.columns)} columns")
            logger.debug(f"Columns being uploaded: {list(df_processed.columns)}")
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error preparing data for upload: {e}")
            return df