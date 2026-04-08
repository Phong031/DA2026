"""
Test script for claim data extraction
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract.claim_extractor import ClaimExtractor
from src.utils.config_loader import ConfigLoader

# Load configuration
config_loader = ConfigLoader(project_root / "config")
claim_config = config_loader.get_claim_config()

# Get file paths
file_paths = [Path(path) for path in claim_config['file_paths']]

print(f"Testing with {len(file_paths)} claim files\n")
print("File paths:")
for path in file_paths:
    exists = "✅" if path.exists() else "❌"
    print(f"  {exists} {path.name}")

# Extract and combine
extractor = ClaimExtractor()
df = extractor.combine_files(file_paths)

if not df.empty:
    print(f"\n✅ Extracted {len(df)} total rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\n📋 Sample data (first 3 rows):")
    display_cols = ['Contract No', 'Description', 'Type', 'Total Amount']
    available_cols = [col for col in display_cols if col in df.columns]
    print(df[available_cols].head(3).to_string())
    
    # Prepare for upload
    df_prepared = extractor.prepare_for_upload(df)
    print(f"\n✅ Prepared {len(df_prepared)} rows for upload")
    
    # Show sleeve columns summary
    sleeve_cols = ['Permanent Sleeve Claimed', 'Temporary Sleeve Claimed']
    print("\n📊 Sleeve Claims:")
    for col in sleeve_cols:
        if col in df_prepared.columns:
            non_null = df_prepared[col].notna().sum()
            if non_null > 0:
                print(f"   {col}: {non_null} records")
            else:
                print(f"   {col}: No records found")
    
    # Show Type distribution
    if 'Type' in df_prepared.columns:
        print("\n📊 Claim Types Distribution:")
        print(df_prepared['Type'].value_counts())
    
else:
    print("❌ No data extracted")