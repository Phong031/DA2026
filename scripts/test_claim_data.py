"""
Test script for claim data extraction with detailed file-by-file analysis
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.extract.claim_extractor import ClaimExtractor
from src.utils.config_loader import ConfigLoader


def analyze_file_columns(file_path: Path, required_columns: list = None):
    """
    Analyze a single claim file and report column issues
    
    Args:
        file_path: Path to Excel file
        required_columns: Optional list of required columns to check
    """
    print(f"\n{'='*60}")
    print(f"Analyzing: {file_path.name}")
    print(f"Path: {file_path}")
    print(f"{'='*60}")
    
    try:
        # Read the Excel file
        xls = pd.ExcelFile(file_path)
        first_tab = xls.sheet_names[0]
        
        # Read the entire first tab without headers
        df_full = pd.read_excel(xls, first_tab, header=None)
        
        # Find header row (where Description appears)
        extractor = ClaimExtractor()
        start_row_index = extractor.find_start_row(df_full)
        end_row_index = extractor.find_end_row(df_full)
        
        print(f"\n📋 File Structure:")
        print(f"   Header row index: {start_row_index}")
        print(f"   Data end row index: {end_row_index}")
        print(f"   Total rows in sheet: {len(df_full)}")
        
        # Get header row
        header_row = df_full.iloc[start_row_index].values
        header_row_clean = [str(col).strip() if pd.notna(col) else f"Column_{i}" for i, col in enumerate(header_row)]
        
        print(f"\n📊 Header Row Analysis:")
        print(f"   Total columns in header: {len(header_row_clean)}")
        
        # Check for duplicate column names
        seen = set()
        duplicates = []
        for col in header_row_clean:
            if col in seen:
                duplicates.append(col)
            else:
                seen.add(col)
        
        if duplicates:
            print(f"\n   ⚠️ DUPLICATE COLUMN NAMES FOUND:")
            for dup in set(duplicates):
                count = header_row_clean.count(dup)
                print(f"      - '{dup}' appears {count} times")
        else:
            print(f"   ✅ No duplicate column names found")
        
        # Check for empty column names
        empty_cols = [i for i, col in enumerate(header_row_clean) if col.startswith('Column_') or col == '']
        if empty_cols:
            print(f"\n   ⚠️ EMPTY/UNNAMED COLUMNS:")
            print(f"      Found {len(empty_cols)} columns without proper names")
            print(f"      Column indices: {empty_cols[:10]}")
        
        # Show first 20 column names
        print(f"\n   First 20 column names:")
        for i, col in enumerate(header_row_clean[:20]):
            print(f"      {i}: '{col}'")
        
        # Check for required columns if provided
        if required_columns:
            print(f"\n📋 Required Columns Check:")
            missing_cols = []
            found_cols = []
            
            for req_col in required_columns:
                if req_col in header_row_clean:
                    found_cols.append(req_col)
                else:
                    missing_cols.append(req_col)
            
            if missing_cols:
                print(f"   ❌ MISSING REQUIRED COLUMNS:")
                for col in missing_cols:
                    print(f"      - {col}")
            else:
                print(f"   ✅ All required columns found")
            
            print(f"   Found {len(found_cols)} of {len(required_columns)} required columns")
        
        # Try to extract data to see if it works
        print(f"\n📊 Testing Data Extraction:")
        try:
            data_start_row = start_row_index + 1
            data_rows = end_row_index - start_row_index - 1
            
            if data_rows <= 0:
                print(f"   ⚠️ No data rows found (data_rows = {data_rows})")
                return False
            
            df = pd.read_excel(
                xls, first_tab,
                skiprows=data_start_row,
                nrows=data_rows,
                header=None
            )
            
            # Assign column names
            df.columns = header_row_clean[:len(df.columns)]
            
            print(f"   ✅ Extracted {len(df)} rows with {len(df.columns)} columns")
            
            # Check for duplicate columns after assignment
            if len(df.columns) != len(set(df.columns)):
                dup_cols = [col for col in df.columns if list(df.columns).count(col) > 1]
                print(f"   ⚠️ Duplicate columns after extraction: {set(dup_cols)}")
                return False
            
            print(f"   ✅ Data extraction successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Data extraction failed: {e}")
            return False
        
    except Exception as e:
        print(f"\n❌ Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test claim data extraction with detailed file analysis"""
    print("="*60)
    print("Testing Claim Data ETL Pipeline - File Analysis Mode")
    print("="*60)
    
    # Load configuration
    config_loader = ConfigLoader(project_root / "config")
    
    try:
        claim_config = config_loader.get_claim_config()
    except Exception as e:
        print(f"\n❌ Failed to load configuration: {e}")
        print("\nPlease check your config.yaml and claim_files.yaml")
        return
    
    # Get file paths
    file_paths = [Path(path) for path in claim_config.get('file_paths', [])]
    required_columns = claim_config.get('required_columns', [])
    
    print(f"\n📁 Found {len(file_paths)} claim files in configuration")
    print(f"📋 Required columns: {len(required_columns)} columns expected")
    
    # Check which files exist
    existing_files = []
    missing_files = []
    
    print("\n📁 File Status:")
    for file_path in file_paths:
        if file_path.exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path.name}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path.name} (not found)")
    
    if missing_files:
        print(f"\n⚠️ Missing {len(missing_files)} files. Please check paths.")
    
    if not existing_files:
        print("\n❌ No claim files found. Please check your claim_files.yaml configuration.")
        return
    
    # Analyze each existing file
    print("\n" + "="*60)
    print("ANALYZING EACH CLAIM FILE")
    print("="*60)
    
    results = {}
    for file_path in existing_files:
        success = analyze_file_columns(file_path, required_columns)
        results[file_path.name] = success
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    
    successful_files = [name for name, success in results.items() if success]
    failed_files = [name for name, success in results.items() if not success]
    
    print(f"\n✅ Successfully processed: {len(successful_files)} files")
    for name in successful_files:
        print(f"   - {name}")
    
    if failed_files:
        print(f"\n❌ Failed/Problematic files: {len(failed_files)} files")
        for name in failed_files:
            print(f"   - {name}")
        print("\n📝 Please check the problematic files above and fix their column structure.")
        print("   Common issues:")
        print("   - Duplicate column names")
        print("   - Empty/unamed columns")
        print("   - Missing header row")
        print("   - Inconsistent column count")
    else:
        print("\n✅ All files are ready for upload!")
        print("\nYou can now run the full pipeline:")
        print("   python scripts/upload_claim_data.py")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()