import cv2
import torch
import time
import base64
import os
import sys
import urllib.request
import numpy as np
import shutil

# Try importing YOLO, but have a fallback if it fails
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception as e:
    print(f"Error importing YOLO: {e}")
    YOLO_AVAILABLE = False

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt", camera_id=0, socketio=None, use_fallback=False):
        self.model_loaded = False
        self.socketio = socketio
        self.camera_id = camera_id
        self.cap = None
        self.demo_mode = os.environ.get('RENDER', False)
        self.demo_frame = None
        
        # Initialize demo frame
        self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(self.demo_frame, "Initializing object detection...", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if use_fallback or not YOLO_AVAILABLE:
            print("Using fallback motion detection mode")
            return
            
        try:
            # Check if model exists, if not, try multiple locations and download if needed
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
            
            if not model_found and os.path.basename(model_path) == "yolov8n.pt":
                print(f"Model not found. Attempting to download manually...")
                try:
                    # Make sure the models directory exists
                    os.makedirs('models', exist_ok=True)
                    
                    # Manual download with urllib
                    url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
                    print(f"Downloading from {url}...")
                    download_path = os.path.join('models', 'yolov8n.pt')
                    urllib.request.urlretrieve(url, download_path)
                    print(f"Successfully downloaded to {download_path}")
                    
                    # Also save a copy to tmp
                    tmp_path = os.path.join('/tmp/models', 'yolov8n.pt')
                    os.makedirs('/tmp/models', exist_ok=True)
                    shutil.copy2(download_path, tmp_path)
                    print(f"Saved a copy to {tmp_path}")
                    
                    model_path = download_path
                    model_found = True
                except Exception as e:
                    print(f"Failed to download model: {e}")
                    print("Will use demo mode with placeholder detection")
            
            if not model_found:
                print(f"Could not find or download model: {model_path}")
                print("Will use demo mode with placeholder detection")
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
                self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(self.demo_frame, "Model loaded successfully", (50, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(self.demo_frame, f"Classes: {list(self.model.names.values())[:5]}...", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(self.demo_frame, "Running in demo mode (no camera)", (50, 280), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            else:
                print("Model loaded but class names not available")
                
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            print("Will fall back to a simplified detection method")
            
            # Update demo frame with error message
            self.demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(self.demo_frame, "Error loading model", (50, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(self.demo_frame, str(e)[:50], (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(self.demo_frame, "Using simplified detection", (50, 280), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
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