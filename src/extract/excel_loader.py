"""
Basic Excel file loader
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ExcelLoader:
    """Load and read Excel files"""
    
    def load(self, file_path: Path, sheet_name: str = 0, header: Optional[int] = 0) -> pd.DataFrame:
        """Load an Excel sheet"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header)
            logger.info(f"Loaded {file_path.name}: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise
    
    def get_sheet_names(self, file_path: Path) -> List[str]:
        """Get all sheet names from Excel file"""
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Failed to get sheet names from {file_path}: {e}")
            raise