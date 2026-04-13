"""
Test script for lentune invoices data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.lentune_extractor import LentuneExtractor

# Define required columns
required_columns = [
    'Categories',
    'Checked Date',
    'First Approved Date',
    'Invoice Number',
    'Line Cost Code',
    'Line Description',
    'Line Excluding',
    'Line Including',
    'Line Price',
    'Line Project',
    'Line Quantity',
    'Line Tax',
    'Processed Date',
    'Second Approved Date',
    'Status',
    'Supplier Description',
    'Transaction Date'
]

# Test file path
test_file = project_root / "data" / "raw" / "Lentune_Invoice_Data - adding month.csv"

if test_file.exists():
    print(f"✅ Testing with: {test_file}")
    
    extractor = LentuneExtractor(required_columns)
    
    # Extract
    df = extractor.extract_from_file(test_file)
    print(f"\n✅ Extracted {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\n📋 Sample Invoice Numbers:")
    if 'Invoice Number' in df.columns:
        for inv in df['Invoice Number'].head(10):
            print(f"   {inv}")
    
    # Prepare for upload
    df_prepared = extractor.prepare_for_upload(df)
    print(f"\n✅ Prepared {len(df_prepared)} rows for upload")
    
    # Show first row
    print("\nSample of prepared data (first row):")
    sample = df_prepared.head(1).to_dict('records')[0]
    for key, value in list(sample.items())[:5]:
        print(f"   {key}: {value}")
    
    # Check for missing values
    missing = df_prepared.isna().sum()
    if missing.sum() > 0:
        print(f"\n⚠️ Missing values found:")
        print(missing[missing > 0])
    else:
        print("\n✅ No missing values found")
        
else:
    print(f"❌ Test file not found: {test_file}")
    print("Please place 'Lentune_Invoice_Data - adding month.csv' in data/raw/ directory")