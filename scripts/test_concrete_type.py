"""
Test script for concrete type data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.concrete_type_extractor import ConcreteTypeExtractor

# Define required columns
required_columns = [
    'Product Code',
    'Product Description',
    'Product Type'
]

# Test file path
test_file = project_root / "data" / "raw" / "concrete type.csv"

if test_file.exists():
    print(f"✅ Testing with: {test_file}")
    
    extractor = ConcreteTypeExtractor(required_columns)
    
    # Extract
    df = extractor.extract_from_file(test_file)
    print(f"\n✅ Extracted {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\n📋 Sample Product Codes:")
    if 'Product Code' in df.columns:
        for code in df['Product Code'].head(10):
            print(f"   {code}")
    
    # Show sample of product descriptions
    print("\n📋 Sample Product Descriptions:")
    if 'Product Description' in df.columns:
        for desc in df['Product Description'].head(5):
            print(f"   {desc[:50]}..." if len(desc) > 50 else f"   {desc}")
    
    # Prepare for upload
    df_prepared = extractor.prepare_for_upload(df)
    print(f"\n✅ Prepared {len(df_prepared)} rows for upload")
    
    # Show first row
    print("\nSample of prepared data (first row):")
    print(df_prepared.head(1).to_dict('records')[0])
    
    # Check for missing values
    missing = df_prepared.isna().sum()
    if missing.sum() > 0:
        print(f"\n⚠️ Missing values found:")
        print(missing[missing > 0])
    else:
        print("\n✅ No missing values found")
        
else:
    print(f"❌ Test file not found: {test_file}")
    print("Please place 'concrete_type.csv' in data/raw/ directory")