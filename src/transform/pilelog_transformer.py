"""
Transform pilelog data
"""
import pandas as pd
import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PileLogTransformer:
    """Transform raw pilelog data"""
    
    def convert_calc_conc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Calc Conc to float with 2 decimals"""
        if 'Calc Conc' in df.columns:
            df['Calc Conc'] = pd.to_numeric(df['Calc Conc'], errors='coerce').round(2)
        return df
    
    def format_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format date column to dd/mm/yyyy"""
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%d/%m/%Y')
        return df
    
    def extract_sleeve_values(self, sleeve_value) -> Tuple[Optional[float], Optional[float]]:
        """Extract temporary and permanent sleeve lengths"""
        if pd.isna(sleeve_value) or sleeve_value == 0:
            return None, None
        
        sleeve = str(sleeve_value).lower()
        temp_sleeve, perm_sleeve = None, None
        
        # Just a number
        if re.fullmatch(r"[\d.]+", sleeve):
            temp_sleeve = float(sleeve)
        
        # Extract temp sleeve
        if 'temp' in sleeve:
            match = re.search(r'temp\s*([\d.]+)\s*m', sleeve)
            if match:
                temp_sleeve = float(match.group(1))
        
        # Extract perm sleeve
        if 'perm' in sleeve:
            match = re.search(r'perm\s*([\d.]+)\s*m', sleeve)
            if match:
                perm_sleeve = float(match.group(1))
        
        # Handle jensen (adds to perm)
        if 'jensen' in sleeve and '+' in sleeve:
            match = re.search(r'\+\s*([\d.]+)', sleeve)
            if match:
                jensen = float(match.group(1))
                perm_sleeve = (perm_sleeve or 0) + jensen
        
        return temp_sleeve, perm_sleeve
    
    def add_sleeve_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporary and permanent sleeve columns"""
        df[['Temporary Sleeve', 'Permanent Sleeve']] = df['Sleeve'].apply(
            lambda x: pd.Series(self.extract_sleeve_values(x))
        )
        return df
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all transformations"""
        df = self.convert_calc_conc(df)
        df = self.format_dates(df)
        df = self.add_sleeve_columns(df)
        logger.info(f"Transformed {len(df)} rows")
        return df