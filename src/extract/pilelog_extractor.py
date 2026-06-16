"""
Pilelog-specific extraction logic
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging

from .excel_loader import ExcelLoader

logger = logging.getLogger(__name__)


class PileLogExtractor:
    """Extract data from pilelog Excel files with dynamic header detection"""
    
    def __init__(self, required_columns: List[str]):
        self.required_columns = required_columns
        self.excel_loader = ExcelLoader()
    
    def _find_header_row(self, sheet_data: pd.DataFrame) -> Optional[int]:
        """Find row containing all required columns"""
        for idx, row in sheet_data.iterrows():
            row_values = [str(val).strip() for val in row.values]
            if all(col in row_values for col in self.required_columns):
                return idx
        return None
              
    def _extract_job_number(self, sheet_data: pd.DataFrame) -> str:
        """Extract job number from first row, second column"""
        try:
            first_row_text = str(sheet_data.iloc[0, 1])
            # Extract all leading digits by iterating
            job_number = ''
            for char in first_row_text.strip():
                if char.isdigit():
                    job_number += char
                else:
                    break
            return job_number if job_number else "0000"
        except:
            return "0000"
    
    def extract_from_file(self, file_path: Path) -> List[pd.DataFrame]:
        """Extract data from all sheets in a pilelog file"""
        extracted_data = []
        
        try:
            sheet_names = self.excel_loader.get_sheet_names(file_path)
            logger.debug(f"Found {len(sheet_names)} sheets in {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to get sheet names from {file_path}: {e}")
            return extracted_data
        
        for sheet_name in sheet_names:
            try:
                # Load sheet without headers
                sheet_data = self.excel_loader.load(file_path, sheet_name=sheet_name, header=None)
                
                # Find header row
                header_row = self._find_header_row(sheet_data)
                if header_row is None:
                    logger.debug(f"No header row found in {file_path.name} - {sheet_name}")
                    continue
                
                # Extract data
                job_number = self._extract_job_number(sheet_data)
                
                # Set headers and remove header row
                sheet_data.columns = sheet_data.iloc[header_row]
                sheet_data = sheet_data.drop(range(header_row + 1))
                
                # Keep only required columns that exist
                available_columns = [col for col in self.required_columns if col in sheet_data.columns]
                if not available_columns:
                    logger.warning(f"None of the required columns found in {sheet_name}")
                    continue
                
                sheet_data = sheet_data[available_columns]
                
                # Add metadata columns
                sheet_data["Job Number"] = job_number
                sheet_data["Wall Name"] = sheet_name
                
                extracted_data.append(sheet_data)
                logger.debug(f"Extracted {len(sheet_data)} rows from {sheet_name}")
                
            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name} in {file_path.name}: {e}")
                continue
        
        return extracted_data