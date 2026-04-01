"""
Test script for job data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.job_data_extractor import JobDataExtractor

# Define required columns
required_columns = [
    'Address', 'City', 'Estimator', 'Estimator Email', 'First Received Date',
    'Foreman', 'Foreman Email', 'Foreman Phone', 'Job Area', 'Job Description',
    'Job Name', 'Job Number', 'Job Value', 'Main Contractor', 'Onsite Finish',
    'Onsite Start', 'Suburb', 'Successful Date', 'Supervisor', 'Supervisor Email',
    'Supervisor Phone', 'unique id'
]

# Test file path
test_file = project_root / "data" / "raw" / "5 Jobs Data.xlsx"

if test_file.exists():
    print(f"✅ Testing with: {test_file}")
    
    extractor = JobDataExtractor(required_columns)
    
    # Extract
    df = extractor.extract_from_file(test_file)
    print(f"\n✅ Extracted {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
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
    print("Please place '5 Jobs Data.xlsx' in data/raw/ directory")