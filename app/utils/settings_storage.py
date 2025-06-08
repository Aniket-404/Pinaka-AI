"""
Settings Storage Module for Pinaka-AI

This module provides functionality to save and load user settings
to make them persistent across application restarts.
"""

import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SettingsStorage:
    def __init__(self, storage_dir=None):
        """Initialize the settings storage with a directory path
        
        Args:
            storage_dir (str, optional): Directory to store settings files.
                                       If None, uses the app directory.
        """
        if storage_dir is None:
            # Use the 'data' directory in the same folder as this file
            base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            app_dir = base_dir.parent.parent  # Go up to the app root
            storage_dir = os.path.join(app_dir, 'data')
            
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        self.storage_dir = storage_dir
        self.settings_file = os.path.join(storage_dir, 'user_settings.json')
        logger.info(f"Settings will be stored in: {self.settings_file}")
    
    def save_settings(self, settings_dict):
        """Save settings to the JSON file
        
        Args:
            settings_dict (dict): Dictionary of settings to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings_dict, f, indent=4)
            logger.info(f"Settings saved successfully to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def load_settings(self, default_settings=None):
        """Load settings from the JSON file
        
        Args:
            default_settings (dict, optional): Default settings to use if file doesn't exist
            
        Returns:
            dict: Dictionary of settings, or default_settings if file doesn't exist
        """
        if default_settings is None:
            default_settings = {}
            
        if not os.path.exists(self.settings_file):
            logger.info(f"Settings file not found, using defaults")
            return default_settings
            
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            logger.info(f"Settings loaded successfully from {self.settings_file}")
            return settings
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return default_settings
