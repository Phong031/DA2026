"""
Configuration loader for YAML files
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage configuration from YAML files"""
    
    def __init__(self, config_dir: Path):
        """Initialize with config directory path"""
        self.config_dir = Path(config_dir)
        logger.info(f"ConfigLoader initialized with: {self.config_dir}")
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file"""
        file_path = self.config_dir / filename
        logger.info(f"Loading config from: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                logger.error(f"Config file is empty: {filename}")
                raise ValueError(f"Config file is empty: {filename}")
            
            logger.info(f"Successfully loaded config from {filename}")
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise
    
    def get_pilelog_config(self) -> Dict[str, Any]:
        """Get complete pilelog configuration including file paths"""
        try:
            # Load main config
            logger.info("Loading main configuration...")
            main_config = self.load_yaml("config.yaml")
            
            # Check if data_sources exists
            if 'data_sources' not in main_config:
                raise KeyError("'data_sources' not found in config.yaml")
            
            if 'pilelog' not in main_config['data_sources']:
                raise KeyError("'pilelog' not found in data_sources")
            
            # Copy pilelog config
            pilelog_config = main_config['data_sources']['pilelog'].copy()
            logger.info(f"Loaded pilelog config with required columns: {len(pilelog_config.get('required_columns', []))}")
            
            # Load file paths from separate file
            logger.info("Loading pilelog file paths...")
            files_config = self.load_yaml("pilelog_files.yaml")
            
            # Check if pilelog_files exists
            if 'pilelog_files' not in files_config:
                raise KeyError("'pilelog_files' not found in pilelog_files.yaml")
            
            # Add file paths to config
            pilelog_config['file_paths'] = files_config['pilelog_files']
            logger.info(f"Added {len(pilelog_config['file_paths'])} file paths to config")
            
            return pilelog_config
            
        except Exception as e:
            logger.error(f"Failed to get pilelog config: {e}")
            raise

    def get_claim_config(self) -> Dict[str, Any]:
        """
        Load claim configuration and file paths from separate YAML
    
        Returns:
            Dictionary with claim config including file list
        """
        # Load main config
        main_config = self.load_yaml("config.yaml")
        claim_config = main_config['data_sources']['claim'].copy()
    
        # Load file list from separate YAML
        files_config_file = claim_config.get('files_config')
    
        if files_config_file:
            files_data = self.load_yaml(files_config_file)
        
            if 'claim_files' in files_data:
                file_paths = files_data['claim_files']
                claim_config['file_paths'] = file_paths
                logger.info(f"Loaded {len(file_paths)} claim file paths from {files_config_file}")
    
        return claim_config