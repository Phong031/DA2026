"""
Test script for month end data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.month_end_extractor import MonthEndExtractor

# Test file path
test_file = project_root / "data" / "raw" / "financial report table - adding month.xlsx"

if test_file.exists():
    print(f"✅ Testing with: {test_file}")
    
    extractor = MonthEndExtractor()
    
    # Extract
    df = extractor.extract_from_file(test_file)
    print(f"\n✅ Extracted {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Prepare for upload
    df_prepared = extractor.prepare_for_upload(df)
    print(f"\n✅ Prepared {len(df_prepared)} rows for upload")
    
    # Convert to JSON serializable
    df_serializable = extractor.convert_to_json_serializable(df_prepared)
    
    # Show first row
    print("\nSample of prepared data (first row):")
    sample = df_serializable.head(1).to_dict('records')[0]
    for key, value in list(sample.items())[:5]:
        print(f"   {key}: {value}")
    
    # Check for missing values
    missing = df_serializable.isna().sum()
    if missing.sum() > 0:
        print(f"\n⚠️ Missing values found:")
        print(missing[missing > 0])
    else:
        print("\n✅ No missing values found")
        
else:
    print(f"❌ Test file not found: {test_file}")
    print("Please place 'financial report table - adding month.xlsx' in data/raw/ directory")