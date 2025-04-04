import cv2
import torch
import time
import base64
import os
import sys
import urllib.request
from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt", camera_id=0, socketio=None, use_fallback=False):
        self.model_loaded = False
        self.socketio = socketio
        self.camera_id = camera_id
        self.cap = None
        
        if use_fallback:
            print("Using fallback motion detection mode")
            return
            
        try:
            # Check if model exists, if not and it's yolov8n.pt, download it manually
            if model_path == "yolov8n.pt" and not os.path.exists(model_path):
                print(f"Model {model_path} not found. Attempting to download manually...")
                try:
                    # Manual download with urllib
                    url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
                    print(f"Downloading from {url}...")
                    urllib.request.urlretrieve(url, model_path)
                    print(f"Successfully downloaded {model_path}")
                except Exception as e:
                    print(f"Failed to download model: {e}")
                    print("Please download YOLOv8n model manually from:")
                    print("https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
                    return
            
            # Load the model
            self.model = YOLO(model_path)
            self.model_loaded = True
            
            # Print available classes for this model
            if hasattr(self.model, 'names'):
                print(f"Model loaded with classes: {list(self.model.names.values())}")
            else:
                print("Model loaded but class names not available")
                
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            print("Will fall back to a simplified detection method")
    
    def _ensure_camera_open(self):
        """Ensure the camera is open, attempt to reopen if closed"""
        if self.cap is None or not self.cap.isOpened():
            # Try DroidCam first (usually device 1 or 2)
            for device_id in [1, 2, 0]:  # Try DroidCam devices first, then fallback to default
                self.cap = cv2.VideoCapture(device_id)
                if self.cap.isOpened():
                    print(f"Successfully opened camera device {device_id}")
                    break
                self.cap.release()
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open any camera device. Please ensure DroidCam is running and connected.")
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
                
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            
    def release(self):
        """Release camera resources"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release() 