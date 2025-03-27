class Config:
    """Configuration settings for the object detection system."""
    
    def __init__(self):
        # Common COCO classes that YOLOv8 detects
        self.monitored_objects = [
            "person", "bicycle", "car", "motorcycle", "bus", "truck",
            "dog", "cat", "chair", "bottle", "laptop", "cell phone", 
            "Movement"
        ]
        self.notification_threshold = 0.7  # Default confidence threshold
        self.notification_cooldown = 10  # Seconds between notifications for the same object
        self.last_notification_time = {}  # Track last notification time for each object type 