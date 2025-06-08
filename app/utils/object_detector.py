import cv2
import time
import base64
import os
import sys
import urllib.request
import numpy as np
import shutil
import random

# Check if we're in production mode
IS_PRODUCTION = os.environ.get('RENDER', False)

# Only import YOLO/torch in development mode or if explicitly requested
if not IS_PRODUCTION:
    try:
        import torch
        from ultralytics import YOLO
        YOLO_AVAILABLE = True
    except Exception as e:
        print(f"Error importing YOLO: {e}")
        YOLO_AVAILABLE = False
else:
    # In production, don't even try to import unless explicitly needed
    YOLO_AVAILABLE = False
    print("Running in production mode - YOLO imports disabled by default")

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt", camera_id=0, socketio=None, use_fallback=False):
        self.model_loaded = False
        self.socketio = socketio
        self.camera_id = camera_id
        self.cap = None
        self.demo_mode = IS_PRODUCTION
        self.last_notification_time = {}  # For tracking notification cooldowns
        
        # Generate demo frame with some sample detections
        self._create_demo_frame()
        
        # In production, we'll use the demo mode by default
        if IS_PRODUCTION:
            print("Running in production environment, using demo mode")
            return
            
        # Skip actual model loading if using fallback or YOLO not available
        if use_fallback or not YOLO_AVAILABLE:
            print("Using fallback detection mode")
            return
            
        try:
            # Model loading (only in development mode)
            model_locations = [
                model_path,  # Original path
                os.path.join('models', os.path.basename(model_path)),  # models directory
                os.path.join('/tmp/models', os.path.basename(model_path))  # tmp models directory
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
            
            # Import YOLO here if we're actually going to use it
            if IS_PRODUCTION and not 'YOLO' in globals():
                try:
                    import torch
                    from ultralytics import YOLO
                except Exception as e:
                    print(f"Error importing YOLO in production: {e}")
                    self.demo_mode = True
                    return
            
            # Load the model
            print(f"Loading model from: {model_path}")
            self.model = YOLO(model_path)
            self.model_loaded = True
            
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
            
            # Update demo frame with error message
            self._create_demo_frame(f"Error: {str(e)[:50]}", False)
    
    def _create_demo_frame(self, message="Demo Mode - No Camera", success=True):
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
        for i in range(3):
            # Randomize the position and size of the "detected" object
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
    
    def _ensure_camera_open(self):
        """Ensure the camera is open, or use demo mode if in production"""
        # In production, always use demo mode
        if IS_PRODUCTION:
            self.demo_mode = True
            # Update the demo frame to simulate changing video
            self._create_demo_frame()
            return
            
        # If cap is None or not opened, try to open it
        if self.cap is None or not self.cap.isOpened():
            # In development, try to access camera
            for device_id in [1, 2, 0]:  # Try different camera devices
                self.cap = cv2.VideoCapture(device_id)
                if self.cap.isOpened():
                    print(f"Successfully opened camera device {device_id}")
                    self.demo_mode = False
                    break
                self.cap.release()
            
            if not self.cap.isOpened():
                print("Could not open any camera device. Using demo mode.")
                self.cap = cv2.VideoCapture()
                self.demo_mode = True
                self._create_demo_frame("Camera not available")
                
            time.sleep(0.5)  # Give camera time to initialize
    
    def _process_frame(self, frame, config):
        """Process a single frame with detection"""
        detected_objects = []
        current_time = time.time()
        
        # In demo mode or production, use simulated detections
        if IS_PRODUCTION or self.demo_mode:
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
                    objects.append((obj, confidence))
                    
                    # Randomly create a notification
                    if confidence > config.notification_threshold and random.random() > 0.9:
                        self._send_notification(self.demo_frame, obj, confidence, current_time, config)
            
            return self.demo_frame, objects
        
        # Regular model-based detection (only in development)
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
                    
                    # Check if object should be monitored
                    if label in config.monitored_objects and confidence >= config.notification_threshold:
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        detected_objects.append((label, confidence))
                        
                        # Send notification if cooldown period has passed
                        self._send_notification(frame, label, confidence, current_time, config, x1, y1, x2, y2)
        else:
            # Simple detection - just add a message to the frame
            cv2.putText(frame, "Model not loaded - using simplified detection", 
                       (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Draw some fake detections
            self._add_simulated_detections(frame, config, detected_objects, current_time)
                
        return frame, detected_objects
    
    def _add_simulated_detections(self, frame, config, detected_objects, current_time):
        """Add simulated detections when real model is not available"""
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
            
            # Draw a rectangle around the contour
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add "Movement" detection
            label = "Movement"
            confidence = 0.7  # Fake confidence
            
            # Check if this object should be monitored
            if label in config.monitored_objects and confidence >= config.notification_threshold:
                cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                detected_objects.append((label, confidence))
                
                # Send notification if cooldown period has passed
                self._send_notification(frame, label, confidence, current_time, config, x, y, x + w, y + h)
                
        # Periodically update the first frame to adapt to lighting changes
        if time.time() % 10 < 0.1:  # Update roughly every 10 seconds
            self.first_frame = gray
    
    def _send_notification(self, frame, label, confidence, current_time, config, x1=0, y1=0, x2=0, y2=0):
        """Send a notification via SocketIO"""
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
            
            # Send the notification
            self.socketio.emit('detection_alert', {
                'object': label,
                'confidence': float(confidence),
                'timestamp': current_time,
                'image': jpg_as_text
            })
    
    def _ensure_camera_open(self):
        """Ensure the camera is open, attempt to reopen if closed"""
        if self.cap is None or not self.cap.isOpened():
            # Check if we're in a production environment (like Render)
            is_production = os.environ.get('RENDER', False)
            
            if is_production:
                # In production, use a demo video or image instead of camera
                print("Running in production environment, using demo mode")
                # Create a black image as fallback
                self.cap = cv2.VideoCapture()
                self.demo_mode = True
                self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(self.demo_frame, "Camera not available in web deployment", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(self.demo_frame, "Please run locally for camera access", (70, 280), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                return
            else:
                # In local development, try to access camera
                # Try DroidCam first (usually device 1 or 2)
                for device_id in [1, 2, 0]:  # Try DroidCam devices first, then fallback to default
                    self.cap = cv2.VideoCapture(device_id)
                    if self.cap.isOpened():
                        print(f"Successfully opened camera device {device_id}")
                        self.demo_mode = False
                        break
                    self.cap.release()
                
                if not self.cap.isOpened():
                    print("Could not open any camera device. Using demo mode.")
                    self.cap = cv2.VideoCapture()
                    self.demo_mode = True
                    self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(self.demo_frame, "Camera not available", (180, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    return
                    
            time.sleep(1)  # Give camera time to initialize
    
    def _process_frame(self, frame, config):
        """Process a single frame with YOLO detection"""
        detected_objects = []
        current_time = time.time()
        
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
                    
                    # Check if object should be monitored
                    if label in config.monitored_objects and confidence >= config.notification_threshold:
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        detected_objects.append((label, confidence))
                        
                        # Send notification if cooldown period has passed
                        self._send_notification(frame, label, confidence, current_time, config, x1, y1, x2, y2)
        else:
            # Simplified detection for demo (just detect movement)
            if hasattr(self, 'prev_frame') and self.prev_frame is not None:
                # Convert to grayscale
                gray1 = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate absolute difference
                diff = cv2.absdiff(gray1, gray2)
                
                # Apply threshold
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Process significant contours
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:  # Minimum area to consider
                        x, y, w, h = cv2.boundingRect(contour)
                        label = "Movement"
                        confidence = min(area / 10000, 0.99)  # Scale confidence based on area
                        
                        # Draw bounding box
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        
                        detected_objects.append((label, confidence))
                        
                        # Send notification if cooldown period has passed
                        if label in config.monitored_objects or "Movement" in config.monitored_objects:
                            self._send_notification(frame, label, confidence, current_time, config, x, y, x+w, y+h)
            
            # Store current frame for next comparison
            self.prev_frame = frame.copy()
        
        return frame, detected_objects
    
    def _send_notification(self, frame, label, confidence, current_time, config, x1, y1, x2, y2):
        """Send notification via Socket.IO if conditions are met"""
        # Double-check that this object is in the monitored objects list
        if label not in config.monitored_objects:
            print(f"Skipping notification for {label} - not in monitored objects: {config.monitored_objects}")
            return
            
        # Check if we're past the cooldown period
        last_notification = config.last_notification_time.get(label, 0)
        if current_time - last_notification > config.notification_cooldown:
            if self.socketio:
                # Crop the detection area
                detection_area = frame[max(0, y1-10):min(frame.shape[0], y2+10), 
                                    max(0, x1-10):min(frame.shape[1], x2+10)]
                if detection_area.size > 0:  # Make sure it's not empty
                    # Encode the detection image to base64 for sending to browser
                    ret, buffer = cv2.imencode('.jpg', detection_area)
                    if ret:
                        img_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send notification to all connected clients
                        self.socketio.emit('detection_alert', {
                            'object': label,
                            'confidence': float(confidence),
                            'time': time.strftime("%H:%M:%S"),
                            'image': img_base64
                        })
                        config.last_notification_time[label] = current_time
                        print(f"Browser notification sent for {label} detection")
    
    def generate_frames(self, config):
        """Generator function to yield processed frames for streaming"""
        try:
            self._ensure_camera_open()
            
            while True:
                # Check if we're in demo mode
                if hasattr(self, 'demo_mode') and self.demo_mode:
                    # Use the demo frame instead of reading from camera
                    frame = self.demo_frame.copy()
                    success = True
                else:
                    # Normal camera operation
                    success, frame = self.cap.read()
                    if not success:
                        self._ensure_camera_open()
                        continue
                
                # Process the frame
                processed_frame, _ = self._process_frame(frame, config)
                
                # Encode the frame for web streaming
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                if not ret:
                    continue
                    
                # Yield the frame in the format expected by Flask
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                
                # If in demo mode, add a small delay to simulate video
                if hasattr(self, 'demo_mode') and self.demo_mode:
                    time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            
    def release(self):
        """Release camera resources"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()