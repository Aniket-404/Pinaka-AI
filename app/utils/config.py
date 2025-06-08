from app.utils.settings_storage import SettingsStorage
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration settings for the object detection system."""
    
    def __init__(self):
        # Initialize settings storage
        self.settings_storage = SettingsStorage()
        
        # Default configuration
        self.default_config = {
            "monitored_objects": [
                "person", "bicycle", "car", "motorcycle", "bus", "truck",
                "dog", "cat", "chair", "bottle", "laptop", "cell phone", 
                "Movement" , "stone", "gas_cylinder"
            ],
            "notification_threshold": 0.7,  # Default confidence threshold
            "notification_cooldown": 10,  # Seconds between notifications for the same object
            
            # SMS notification settings
            "sms_enabled": False,  # Whether SMS notifications are enabled
            "sms_cooldown": 60,  # Seconds between SMS notifications (longer than regular notifications)
            "sms_objects": ["person", "car", "stone", "gas_cylinder"]  # Objects that trigger SMS
        }
        
        # Load saved settings or use defaults
        self.load_settings()
        
        # Track notification times (not persisted)
        self.last_notification_time = {}  # Track last notification time for each object type
    
    def load_settings(self):
        """Load settings from storage or use defaults"""
        saved_settings = self.settings_storage.load_settings(self.default_config)
        
        # Apply saved settings to object properties
        self.monitored_objects = saved_settings.get("monitored_objects", self.default_config["monitored_objects"])
        self.notification_threshold = saved_settings.get("notification_threshold", self.default_config["notification_threshold"])
        self.notification_cooldown = saved_settings.get("notification_cooldown", self.default_config["notification_cooldown"])
        
        # SMS settings
        self.sms_enabled = saved_settings.get("sms_enabled", self.default_config["sms_enabled"])
        self.sms_cooldown = saved_settings.get("sms_cooldown", self.default_config["sms_cooldown"])
        self.sms_objects = saved_settings.get("sms_objects", self.default_config["sms_objects"])
        
        logger.info(f"Loaded settings: SMS enabled = {self.sms_enabled}")
    
    def save_settings(self):
        """Save current settings to storage"""
        settings_dict = {
            "monitored_objects": self.monitored_objects,
            "notification_threshold": self.notification_threshold,
            "notification_cooldown": self.notification_cooldown,
            
            # SMS settings
            "sms_enabled": self.sms_enabled,
            "sms_cooldown": self.sms_cooldown,
            "sms_objects": self.sms_objects
        }
        
        success = self.settings_storage.save_settings(settings_dict)
        if success:
            logger.info("Settings saved successfully")
        else:
            logger.warning("Failed to save settings")