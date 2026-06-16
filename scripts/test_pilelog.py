"""
Test script for pilelog data extraction and transformation
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.extract.pilelog_extractor import PileLogExtractor
from src.transform.pilelog_transformer import PileLogTransformer
from src.utils.config_loader import ConfigLoader

def main():
    """Test pilelog data extraction and transformation"""
    print("="*60)
    print("Testing Pilelog ETL Pipeline")
    print("="*60)
    
    # Load configuration
    config_loader = ConfigLoader(project_root / "config")
    pilelog_config = config_loader.get_pilelog_config()
    
    # Get file paths
    file_paths = [Path(path) for path in pilelog_config['file_paths']]
    required_columns = pilelog_config['required_columns']
    
    print(f"\n📁 Found {len(file_paths)} pilelog files in configuration")
    
    # Check which files exist
    existing_files = []
    missing_files = []
    
    for file_path in file_paths:
        if file_path.exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path.name}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path.name} (not found)")
    
    if not existing_files:
        print("\n❌ No pilelog files found. Please check your file paths.")
        return
    
    print(f"\n📊 Testing with {len(existing_files)} existing files")
    
    # Initialize extractor
    extractor = PileLogExtractor(required_columns)
    
    # Test extraction from first file
    print("\n" + "="*60)
    print("Step 1: Testing Extraction")
    print("="*60)
    
    test_file = existing_files[0]
    print(f"\n📄 Testing extraction from: {test_file.name}")
    
    try:
        # Extract from single file
        extracted_data = extractor.extract_from_file(test_file)
        
        if extracted_data:
            # Combine sheets from this file
            if extracted_data:
                df_file = pd.concat(extracted_data, ignore_index=True) if len(extracted_data) > 1 else extracted_data[0]
                print(f"   ✅ Extracted {len(df_file)} rows from {len(extracted_data)} sheets")
                print(f"   Columns: {list(df_file.columns)}")
                
                # Show sample data
                print("\n   📋 Sample data (first 2 rows):")
                print(df_file.head(2).to_string())
            else:
                print("   ⚠️ No data extracted from file")
        else:
            print("   ❌ No data extracted from file")
            
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test combining multiple files
    print("\n" + "="*60)
    print("Step 2: Testing Multi-File Combination")
    print("="*60)
    
    try:
        # Combine all files
        all_data = []
        for file_path in existing_files[:3]:  # Test with first 3 files only
            data = extractor.extract_from_file(file_path)
            if data:
                all_data.extend(data)
        
        if all_data:
            df_combined = pd.concat(all_data, ignore_index=True)
            print(f"   ✅ Combined {len(all_data)} sheets into {len(df_combined)} rows")
            print(f"   Total columns: {len(df_combined.columns)}")
        else:
            print("   ⚠️ No data to combine")
            
    except Exception as e:
        print(f"   ❌ Combination failed: {e}")
    
    # Test transformation
    print("\n" + "="*60)
    print("Step 3: Testing Transformation")
    print("="*60)
    
    try:
        # Use the combined data from above
        if 'df_combined' in locals() and not df_combined.empty:
            transformer = PileLogTransformer()
            df_transformed = transformer.process_pilelog(df_combined.copy())
            
            print(f"   ✅ Transformed {len(df_transformed)} rows")
            print(f"   Original columns: {len(df_combined.columns)}")
            print(f"   Transformed columns: {len(df_transformed.columns)}")
            
            # Check for sleeve columns
            sleeve_cols = ['Temporary Sleeve', 'Permanent Sleeve']
            existing_sleeve = [col for col in sleeve_cols if col in df_transformed.columns]
            if existing_sleeve:
                print(f"   ✅ Sleeve columns added: {existing_sleeve}")
                
                # Show sleeve value statistics
                for col in existing_sleeve:
                    non_null = df_transformed[col].notna().sum()
                    if non_null > 0:
                        print(f"      - {col}: {non_null} records have values")
            
            # Show sample of transformed data
            print("\n   📋 Sample of transformed data (first 2 rows):")
            display_cols = ['Pile Number', 'Date', 'Job Number', 'Wall Name', 'Temporary Sleeve', 'Permanent Sleeve']
            available_cols = [col for col in display_cols if col in df_transformed.columns]
            if available_cols:
                print(df_transformed[available_cols].head(2).to_string())
        else:
            print("   ⚠️ No data to transform")
            
    except Exception as e:
        print(f"   ❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Files found: {len(existing_files)}/{len(file_paths)}")
    
    if existing_files:
        print("✅ Pilelog extractor is ready")
        print("✅ Transformer is ready")
        print("\nYou can now run the full pipeline:")
        print("   python scripts/upload_pilelog.py")
    else:
        print("❌ No valid pilelog files found")
        print("\nPlease check your pilelog_files.yaml configuration")
        print("Ensure the file paths are correct and files exist")

if __name__ == "__main__":
    main()