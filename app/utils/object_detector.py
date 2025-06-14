import cv2
import time
import base64
import os
import sys
import urllib.request
import numpy as np
import shutil
import random
from app.utils.sms_notifier import SMSNotifier

# Check if we're in production mode
IS_PRODUCTION = os.environ.get('RENDER', False)

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt", socketio=None, use_fallback=False):
        self.model_loaded = False
        self.socketio = socketio
        self.demo_mode = False  # Changed: don't default to demo mode even in production
        self.last_notification_time = {}  # For tracking notification cooldowns
        self.yolo_available = False
        self.last_detections = []  # Store detailed detection info
        
        # Initialize SMS notifier
        self.sms_notifier = SMSNotifier()
        
        # Generate demo frame with some sample detections
        self._create_demo_frame()
        
        # Skip actual model loading if using fallback
        if use_fallback:
            print("Using fallback detection mode")
            return
            
        try:
            # Try importing YOLO if not already imported
            try:
                import torch
                from ultralytics import YOLO
                self.yolo_available = True
                print("YOLO import successful in ObjectDetector")
            except Exception as e:
                print(f"Error importing YOLO: {e}")
                self.yolo_available = False
              # Model loading (only in development mode)
            model_locations = [
                model_path,  # Original path (should be absolute)
                os.path.join('models', os.path.basename(model_path)),  # models directory relative
            ]
            
            model_found = False
            for location in model_locations:
                if os.path.exists(location):
                    print(f"Found model at: {location}")
                    model_path = location
                    model_found = True
                    break
            
            if not model_found:
                print(f"Could not find model: {model_path}")
                print("Will use demo mode with placeholder detection")
                self.demo_mode = True
                return
            
            if not self.yolo_available:
                print("YOLO is not available, cannot load model")
                raise ImportError("YOLO is not available in the current environment")
              # Load the model
            print(f"Loading model from: {model_path}")
            try:
                # First try standard loading method
                self.model = YOLO(model_path)
                self.model_loaded = True
                print("Model loaded successfully using standard method")
            except Exception as e:
                print(f"Error in standard model loading: {e}")
                
                # If we get "invalid load key, 'v'" error, try an alternative approach
                if "invalid load key" in str(e):
                    print("Detected 'invalid load key' error, trying alternative loading method...")
                    try:
                        # Try loading with explicit task parameter
                        self.model = YOLO(model_path, task='detect')
                        self.model_loaded = True
                        print("Model loaded successfully using alternative method")
                    except Exception as alt_e:
                        print(f"Alternative loading also failed: {alt_e}")
                        self.model_loaded = False
                        self.demo_mode = True
                else:
                    # For other errors, just fall back to demo mode
                    self.model_loaded = False
                    self.demo_mode = True
            
            # Print available classes for this model
            if hasattr(self.model, 'names'):
                print(f"Model loaded with classes: {list(self.model.names.values())}")
                
                # Update demo frame with success message
                self._create_demo_frame(f"Model loaded: {os.path.basename(model_path)}", True)
            else:
                print("Model loaded but class names not available")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            print("Will fall back to a simplified detection method")
            self.model_loaded = False
            
            # Update demo frame with error message
            self._create_demo_frame(f"Error: {str(e)[:50]}", False)

    def _create_demo_frame(self, message="Demo Mode - Browser Camera", success=True):
        """Create a demo frame with simulated detections for deployment"""
        # Create a base frame (black background)
        self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw some sample shapes to make it more interesting
        colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0)]
        
        # Add the message at the top
        color = (0, 255, 0) if success else (0, 0, 255)
        cv2.putText(self.demo_frame, message, (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add timestamp to show it's updating
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(self.demo_frame, timestamp, (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add info about deployment
        cv2.putText(self.demo_frame, "Pinaka-AI running on Render", (20, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Draw some random objects with bounding boxes to simulate detections
        objects = ["person", "car", "stone", "gas_cylinder"]
        for i in range(3):            # Randomize the position and size of the "detected" object
            x = random.randint(50, 500)
            y = random.randint(100, 350)
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            # Randomly select an object and color
            obj = random.choice(objects)
            color = random.choice(colors)
            # Draw the bounding box and label
            cv2.rectangle(self.demo_frame, (x, y), (x+w, y+h), color, 2)
            conf = random.uniform(0.5, 0.95)
            cv2.putText(self.demo_frame, f"{obj} {conf:.2f}", 
                       (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def _process_frame(self, frame, config):
        """Process a single frame with detection"""
        detected_objects = []
        self.last_detections = []  # Reset detection info
        current_time = time.time()
        
        # Use simulated detections in demo mode
        if self.demo_mode:
            # Update the demo frame
            if hasattr(self, 'frame_counter'):
                self.frame_counter += 1
            else:
                self.frame_counter = 0
                
            # Every 10 frames, update the demo frame to simulate motion
            if self.frame_counter % 10 == 0:
                self._create_demo_frame()
                
            # Add simulated detections
            objects = []
            for obj in config.monitored_objects:
                if random.random() > 0.7:  # 30% chance to "detect" each monitored object
                    confidence = random.uniform(0.6, 0.95)
                    
                    # Create random bounding box
                    x1 = random.randint(50, frame.shape[1] - 150)
                    y1 = random.randint(50, frame.shape[0] - 150)
                    width = random.randint(50, 150)
                    height = random.randint(50, 150)
                    x2 = x1 + width
                    y2 = y1 + height
                    
                    # Store detection with coordinates
                    detected_object = (obj, confidence, x1, y1, x2, y2)
                    objects.append((obj, confidence))
                    self.last_detections.append(detected_object)
                    
                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{obj} {confidence:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Randomly create a notification
                    if confidence > config.notification_threshold and random.random() > 0.9:
                        self._send_notification(frame, obj, confidence, current_time, config, x1, y1, x2, y2)
            
            return frame, objects
        
        # Regular model-based detection
        if self.model_loaded:
            # Perform object detection with YOLO
            results = self.model(frame)
            
            # Process detection results
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    confidence = box.conf[0].item()  # Confidence score
                    class_id = int(box.cls[0])
                    label = result.names[class_id]  # Class name
                    
                    # Store full detection information
                    self.last_detections.append((label, confidence, x1, y1, x2, y2))
                    
                    # Always add the detection to the list, but only draw/notify if it meets the threshold
                    detected_objects.append((label, confidence))
                    
                    # Check if object should be monitored
                    if label in config.monitored_objects and confidence >= config.notification_threshold:
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                          # Send notification if cooldown period has passed
                        self._send_notification(frame, label, confidence, current_time, config, x1, y1, x2, y2)
        else:        # Simple detection using motion detection as a fallback
            self._add_simulated_detections(frame, config, detected_objects, current_time)
                
        return frame, detected_objects
    
    def _add_simulated_detections(self, frame, config, detected_objects, current_time):
        """Add simulated detections when real model is not available"""        # Add a message to the frame
        cv2.putText(frame, "Using motion detection fallback", 
                   (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Use motion detection as a fallback
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Store the first frame for comparison
        if not hasattr(self, 'first_frame') or self.first_frame is None:
            self.first_frame = gray
            return
        
        # Compute absolute difference between current frame and first frame
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate the thresholded image to fill in holes
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours on thresholded image
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Minimum contour area to be considered significant motion
        min_area = 500
        
        for c in contours:
            if cv2.contourArea(c) < min_area:
                continue
                
            # Compute the bounding box for the contour
            (x, y, w, h) = cv2.boundingRect(c)
            
            # Add "Movement" detection with coordinates
            label = "Movement"
            confidence = 0.7  # Fake confidence
            
            # Store full detection information
            self.last_detections.append((label, confidence, x, y, x + w, y + h))
            detected_objects.append((label, confidence))
            
            # Draw a rectangle around the contour
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Check if this object should be monitored
            if label in config.monitored_objects and confidence >= config.notification_threshold:
                cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Send notification if cooldown period has passed
                self._send_notification(frame, label, confidence, current_time, config, x, y, x + w, y + h)
                
        # Periodically update the first frame to adapt to lighting changes
        if time.time() % 10 < 0.1:  # Update roughly every 10 seconds
            self.first_frame = gray
    def _send_notification(self, frame, label, confidence, current_time, config, x1=0, y1=0, x2=0, y2=0):
        """Send a notification via SocketIO and SMS if configured"""
        # Check if socketio is available
        if not self.socketio:
            return
            
        # Check cooldown period (don't spam notifications)
        cooldown = 5  # seconds between notifications for same object
        if label in self.last_notification_time:
            time_since_last = current_time - self.last_notification_time[label]
            if time_since_last < cooldown:
                return
                
        # Update the last notification time
        self.last_notification_time[label] = current_time
        
        # Encode a small portion of the frame for the notification
        try:
            # If we have valid coordinates, crop to the object
            if x1 > 0 and y1 > 0 and x2 > x1 and y2 > y1:
                # Add some padding
                padding = 20
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(frame.shape[1], x2 + padding)
                y2 = min(frame.shape[0], y2 + padding)
                
                # Crop the frame
                cropped = frame[y1:y2, x1:x2]
            else:
                # Use the whole frame
                cropped = frame
                
            # Resize for smaller image
            cropped = cv2.resize(cropped, (320, 240))
            
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', cropped, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                return
                
            # Convert to base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
              # Format timestamp as readable time
            import datetime
            readable_time = datetime.datetime.fromtimestamp(current_time).strftime('%H:%M:%S')
            
            # Send the notification
            self.socketio.emit('detection_alert', {
                'object': label,
                'confidence': float(confidence),
                'time': readable_time,
                'timestamp': current_time,
                'coordinates': {'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2)},
                'image': jpg_as_text
            })
              # Send SMS notification if enabled and object is in the SMS list
            if hasattr(config, 'sms_enabled') and config.sms_enabled:
                if label in config.sms_objects:
                    # Check SMS-specific cooldown
                    if self.sms_notifier.should_send_notification(label, current_time, config.sms_cooldown):
                        # Send SMS with detection details
                        self.sms_notifier.send_detection_alert(
                            object_name=label,
                            confidence=confidence,
                            coordinates=(x1, y1, x2, y2)
                        )
                        print(f"SMS notification sent for {label}")
                        
        except Exception as e:
            print(f"Error sending notification: {e}")