"""
SMS Notification Module for Pinaka-AI

This module handles sending SMS notifications when objects are detected.
It uses the Twilio API for sending SMS messages.
"""

import os
from twilio.rest import Client
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSNotifier:
    def __init__(self):
        """Initialize the SMS notifier with Twilio credentials"""
        # Get credentials from environment variables
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_FROM_NUMBER')
        self.to_number = os.environ.get('TWILIO_TO_NUMBER')
        
        # Check if credentials are set
        self.is_configured = all([
            self.account_sid, 
            self.auth_token, 
            self.from_number, 
            self.to_number
        ])
        
        if self.is_configured:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("SMS notifier initialized with Twilio credentials")
        else:
            logger.warning("SMS notifier not configured. Missing Twilio credentials.")
            
        # Track the last notification time for cooldown
        self.last_notification_time = {}
        
    def send_detection_alert(self, object_name, confidence, image_url=None, coordinates=None):
        """
        Send an SMS notification for a detected object
        
        Args:
            object_name (str): Name of the detected object
            confidence (float): Detection confidence score
            image_url (str, optional): URL to the image with the detection
            coordinates (tuple, optional): Bounding box coordinates (x1, y1, x2, y2)
        
        Returns:
            bool: True if SMS was sent, False otherwise
        """
        if not self.is_configured:
            logger.warning("Cannot send SMS: Twilio not configured")
            return False
            
        try:
            # Format the message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create the message body
            message_body = f"⚠️ ALERT: {object_name} detected!\n"
            message_body += f"Time: {timestamp}\n"
            message_body += f"Confidence: {confidence:.2f}\n"
            
            # Add coordinates if available
            if coordinates:
                x1, y1, x2, y2 = coordinates
                message_body += f"Location: ({x1},{y1}) to ({x2},{y2})\n"
                
            # Add image URL if available
            if image_url:
                message_body += f"\nImage: {image_url}"
            
            # Send the SMS
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(f"SMS sent: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
    
    def should_send_notification(self, object_name, current_time, cooldown_seconds=60):
        """
        Check if we should send a notification based on cooldown period
        
        Args:
            object_name (str): The object type detected
            current_time (float): Current timestamp
            cooldown_seconds (int): Minimum seconds between notifications
            
        Returns:
            bool: True if notification should be sent, False otherwise
        """
        # If this object has been notified before
        if object_name in self.last_notification_time:
            # Check if cooldown period has passed
            time_elapsed = current_time - self.last_notification_time[object_name]
            if time_elapsed < cooldown_seconds:
                return False
        
        # Update the last notification time
        self.last_notification_time[object_name] = current_time
        return True
