"""
Test script for plant and equipment data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.plant_equipment_extractor import PlantEquipmentExtractor

# Define required columns
required_columns = [
    'Asset Code', 'Asset Serial', 'Asset Type', 'Display Name',
    'Fuel Type', 'Groups/Fleets', 'Machine Type', 'Make', 'Model',
    'Registration Plate', 'VIN', 'Weight Type', 'Year'
]

# Test file path
test_file = project_root / "data" / "raw" / "plant and equipment list.csv"

if test_file.exists():
    print(f"✅ Testing with: {test_file}")
    
    extractor = PlantEquipmentExtractor(required_columns)
    
    # Extract
    df = extractor.extract_from_file(test_file)
    print(f"\n✅ Extracted {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\n📋 Sample Asset Codes:")
    if 'Asset Code' in df.columns:
        for code in df['Asset Code'].head(10):
            print(f"   {code}")
    
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
    print("Please place 'plant_and_equipment_list.csv' in data/raw/ directory")