"""
Test configuration loading
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_yaml_files():
    """Test loading YAML files directly"""
    print("="*60)
    print("Testing YAML Files")
    print("="*60)
    
    # Test config.yaml
    config_path = project_root / "config" / "config.yaml"
    print(f"\n1. Loading {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"   ✅ Loaded successfully")
        print(f"   Keys: {list(config.keys())}")
        
        # Check data_sources
        if 'data_sources' in config:
            print(f"   data_sources found")
            if 'pilelog' in config['data_sources']:
                print(f"   pilelog config found")
                print(f"   Required columns: {len(config['data_sources']['pilelog']['required_columns'])} columns")
            else:
                print(f"   ❌ pilelog not found in data_sources")
        else:
            print(f"   ❌ data_sources not found")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test pilelog_files.yaml
    files_path = project_root / "config" / "pilelog_files.yaml"
    print(f"\n2. Loading {files_path}")
    try:
        with open(files_path, 'r', encoding='utf-8') as f:
            files_config = yaml.safe_load(f)
        
        if files_config is None:
            print(f"   ❌ File is empty or has invalid YAML")
        else:
            print(f"   ✅ Loaded successfully")
            print(f"   Keys: {list(files_config.keys())}")
            
            if 'pilelog_files' in files_config:
                file_count = len(files_config['pilelog_files'])
                print(f"   Found {file_count} file paths")
                if file_count > 0:
                    print(f"   First file: {files_config['pilelog_files'][0]}")
            else:
                print(f"   ❌ 'pilelog_files' key not found")
                
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "="*60)

def test_config_loader():
    """Test ConfigLoader class"""
    print("\n" + "="*60)
    print("Testing ConfigLoader")
    print("="*60)
    
    try:
        from src.utils.config_loader import ConfigLoader
        
        config_loader = ConfigLoader(project_root / "config")
        print("✅ ConfigLoader created")
        
        # Test load_yaml
        print("\nTesting load_yaml for config.yaml...")
        main_config = config_loader.load_yaml("config.yaml")
        print(f"✅ Loaded config.yaml with keys: {list(main_config.keys())}")
        
        print("\nTesting load_yaml for pilelog_files.yaml...")
        files_config = config_loader.load_yaml("pilelog_files.yaml")
        if files_config is None:
            print("❌ files_config is None")
        else:
            print(f"✅ Loaded pilelog_files.yaml with keys: {list(files_config.keys())}")
            
        # Test get_pilelog_config
        print("\nTesting get_pilelog_config...")
        pilelog_config = config_loader.get_pilelog_config()
        print(f"✅ Got pilelog config")
        print(f"   Table name: {pilelog_config.get('table_name')}")
        print(f"   Upload mode: {pilelog_config.get('upload_mode')}")
        print(f"   File paths count: {len(pilelog_config.get('file_paths', []))}")
        
    except Exception as e:
        print(f"❌ ConfigLoader test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_yaml_files()
    test_config_loader()