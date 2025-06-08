import os
from flask import Flask, render_template, redirect, url_for, flash, Response, jsonify, request
from flask_socketio import SocketIO
from app.forms import NotificationForm
from app.utils.config import Config
from dotenv import load_dotenv
import cv2
import time
import traceback
import base64
import numpy as np
import requests

# Load environment variables
load_dotenv()

# Set Ultralytics config directory if not already set
if 'YOLO_CONFIG_DIR' not in os.environ:
    os.environ['YOLO_CONFIG_DIR'] = '/tmp/yolo_config'
    
# Create the directory if it doesn't exist
if not os.path.exists(os.environ['YOLO_CONFIG_DIR']):
    os.makedirs(os.environ['YOLO_CONFIG_DIR'], exist_ok=True)

# Disable Ultralytics cache downloads
os.environ['ULTRALYTICS_NO_CACHE'] = '1'

# Create Flask app with correct template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app)

# Check if we're in production environment
is_production = os.environ.get('RENDER', False)

# Only import the ObjectDetector class after setting environment variables
from app.utils.object_detector import ObjectDetector
import pathlib

# Get absolute path to the models directory
base_dir = os.path.abspath(os.path.dirname(__file__))
models_dir = os.path.join(base_dir, "models")

# Model paths (using absolute paths)
custom_model_path = os.path.join(models_dir, "custom_yolo_100epochs_best.pt")
custom_model_drive_url = "https://drive.google.com/file/d/1a5URsD5oIkujCwpmUaGUd_6HTSswdcwZ/view?usp=sharing"
coco_model_path = os.path.join(models_dir, "yolov8n.pt")

# Print model paths for debugging
print(f"Custom model path: {custom_model_path}")
print(f"COCO model path: {coco_model_path}")

# Initialize detectors
custom_detector = None
coco_detector = None

def download_file_from_google_drive(drive_url, destination):
    # Extract file ID from Google Drive share link
    import re
    file_id_match = re.search(r'/d/([\w-]+)', drive_url)
    if not file_id_match:
        print('Invalid Google Drive link')
        return False
    file_id = file_id_match.group(1)
    download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
    print(f"Downloading model from Google Drive: {download_url}")
    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(1024 * 1024):
                f.write(chunk)
        print(f"Downloaded model to {destination}")
        return True
    else:
        print(f"Failed to download model. Status code: {response.status_code}")
        return False

def initialize_model(model_path, name="model", max_retries=2, retry_delay=2):
    """Initialize a model with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempting to load {name} (attempt {attempt+1}/{max_retries+1}): {model_path}")
            detector = ObjectDetector(model_path=model_path, socketio=socketio)
            if detector.model_loaded:
                print(f"{name} loaded successfully")
                return detector
            else:
                print(f"{name} initialization returned False for model_loaded")
                if attempt < max_retries:
                    print(f"Will retry in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"Error loading {name}: {e}")
            if attempt < max_retries:
                print(f"Will retry in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    # If we get here, all attempts failed
    print(f"All attempts to load {name} failed, using fallback")
    return ObjectDetector(use_fallback=True)

# Verify that model files exist before loading
if not os.path.exists(custom_model_path):
    print(f"WARNING: Custom model not found at {custom_model_path}. Will use fallback mode.")
    custom_detector = ObjectDetector(use_fallback=True)
else:
    # Load custom model
    custom_detector = initialize_model(custom_model_path, "custom model")

if not os.path.exists(coco_model_path):
    print(f"WARNING: COCO model not found at {coco_model_path}. Will use fallback mode.")
    coco_detector = ObjectDetector(use_fallback=True)
else:
    # Load COCO model
    coco_detector = initialize_model(coco_model_path, "COCO model")

# Config for detection settings
config = Config()

# Helper to get the active detector - now returns both if available
def get_active_detectors():
    detectors = []
    
    # Always use both models if available
    if custom_detector and custom_detector.model_loaded:
        detectors.append(custom_detector)
    if coco_detector and coco_detector.model_loaded:
        detectors.append(coco_detector)
    
    # If neither is available, return whichever is initialized
    if not detectors:
        if custom_detector:
            detectors.append(custom_detector)
        if coco_detector:
            detectors.append(coco_detector)
    
    return detectors

@app.route('/health')
def health_check():
    """Enhanced health check endpoint for Render"""
    import platform
    import psutil
    
    # Memory usage stats
    memory = psutil.virtual_memory()
    
    status = {
        "status": "healthy",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "custom_model": {
            "loaded": custom_detector.model_loaded if custom_detector else False,
            "available_classes": list(custom_detector.model.names.values()) if custom_detector and custom_detector.model_loaded and hasattr(custom_detector.model, 'names') else []
        },
        "coco_model": {
            "loaded": coco_detector.model_loaded if coco_detector else False,
            "available_classes": list(coco_detector.model.names.values()) if coco_detector and coco_detector.model_loaded and hasattr(coco_detector.model, 'names') else []
        },
        "system": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
        },
        "environment": {
            "production_mode": bool(os.environ.get('RENDER', False)),
            "ultralytics_cache": os.environ.get('ULTRALYTICS_NO_CACHE', 'not set'),
            "yolo_config_dir": os.environ.get('YOLO_CONFIG_DIR', 'not set'),
        },
        "version": "1.2.0"
    }
    return jsonify(status)

@app.errorhandler(500)
def server_error(e):
    """Handle server errors gracefully"""
    error_details = traceback.format_exc()
    print(f"Server Error: {error_details}")
    return render_template('error.html', error=str(e), details=error_details), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = NotificationForm()
    
    # Create model class information for display
    available_classes = {}
    
    # Get classes from custom model
    if custom_detector and hasattr(custom_detector, 'model_loaded') and custom_detector.model_loaded:
        if hasattr(custom_detector, 'model') and hasattr(custom_detector.model, 'names'):
            custom_classes = list(custom_detector.model.names.values())
            available_classes['custom'] = sorted(custom_classes)
    
    # Get classes from COCO model
    if coco_detector and hasattr(coco_detector, 'model_loaded') and coco_detector.model_loaded:
        if hasattr(coco_detector, 'model') and hasattr(coco_detector.model, 'names'):
            coco_classes = list(coco_detector.model.names.values())
            available_classes['coco'] = sorted(coco_classes)
      # Add special classes
    special_classes = ["Movement", "stone", "gas_cylinder"]
    available_classes['special'] = special_classes
    
    # Combine all classes for the flat view
    all_classes = set()
    for class_group in available_classes.values():
        all_classes.update(class_group)
      # Fallback: if still empty, provide a default set
    if not all_classes:
        all_classes = set(["person", "car", "dog", "cat", "Movement", "stone", "gas_cylinder"])
    
    # Sort classes for display
    all_classes = sorted(all_classes)
    
    if form.validate_on_submit():
        config.monitored_objects = [c.strip() for c in form.monitored_objects.data.split(',') if c.strip()]
        config.notification_threshold = form.confidence_threshold.data
        
        # Save SMS settings
        config.sms_enabled = form.sms_enabled.data
        if form.sms_objects.data:
            config.sms_objects = [c.strip() for c in form.sms_objects.data.split(',') if c.strip()]
        config.sms_cooldown = form.sms_cooldown.data
        
        # Save the settings to make them persistent
        config.save_settings()
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('index'))
    
    if not form.is_submitted():
        form.monitored_objects.data = ','.join(config.monitored_objects)
        form.confidence_threshold.data = config.notification_threshold
        
        # Initialize SMS form fields if the config has them
        if hasattr(config, 'sms_enabled'):
            form.sms_enabled.data = config.sms_enabled
        if hasattr(config, 'sms_objects'):
            form.sms_objects.data = ','.join(config.sms_objects)
        if hasattr(config, 'sms_cooldown'):
            form.sms_cooldown.data = config.sms_cooldown
    
    return render_template('settings.html', form=form, 
                          available_classes=all_classes, 
                          model_classes=available_classes)

@app.route('/detect_frame', methods=['POST'])
def detect_frame():
    """Endpoint to receive a frame from the browser, run detection, and return results."""
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    try:
        # Decode base64 image
        img_data = base64.b64decode(data['image'])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Run both detectors regardless of selected model in settings
        results = []
        
        # Always use custom detector if available
        if custom_detector and custom_detector.model_loaded:
            # Get processed frame and detected objects
            processed_frame, detected_custom = custom_detector._process_frame(frame.copy(), config)
            
            # Extract the full detection information
            custom_results = []
            # Look for detection boxes in the processed frame or objects list
            if hasattr(custom_detector, 'last_detections') and custom_detector.last_detections:
                for det in custom_detector.last_detections:
                    if isinstance(det, tuple) and len(det) >= 6:  # Full detection with coordinates
                        label, conf, x1, y1, x2, y2 = det
                        custom_results.append({
                            'label': label,
                            'confidence': float(conf),
                            'x1': int(x1),
                            'y1': int(y1),
                            'x2': int(x2),
                            'y2': int(y2),
                            'width': int(x2 - x1),
                            'height': int(y2 - y1),
                            'model': 'custom'
                        })
                    elif isinstance(det, tuple) and len(det) == 2:  # Just label and confidence
                        label, conf = det
                        custom_results.append({
                            'label': label,
                            'confidence': float(conf),
                            'model': 'custom'
                        })
            else:
                # Fallback to just label and confidence pairs
                for label, conf in detected_custom:
                    custom_results.append({
                        'label': label,
                        'confidence': float(conf),
                        'model': 'custom'
                    })
            
            # Add to combined results
            results.extend(custom_results)
            
        # Always use COCO detector if available
        if coco_detector and coco_detector.model_loaded:
            # Get processed frame and detected objects
            processed_frame, detected_coco = coco_detector._process_frame(frame.copy(), config)
            
            # Extract the full detection information
            coco_results = []
            # Look for detection boxes in the processed frame or objects list
            if hasattr(coco_detector, 'last_detections') and coco_detector.last_detections:
                for det in coco_detector.last_detections:
                    if isinstance(det, tuple) and len(det) >= 6:  # Full detection with coordinates
                        label, conf, x1, y1, x2, y2 = det
                        coco_results.append({
                            'label': label,
                            'confidence': float(conf),
                            'x1': int(x1),
                            'y1': int(y1),
                            'x2': int(x2),
                            'y2': int(y2),
                            'width': int(x2 - x1),
                            'height': int(y2 - y1),
                            'model': 'coco'
                        })
                    elif isinstance(det, tuple) and len(det) == 2:  # Just label and confidence
                        label, conf = det
                        coco_results.append({
                            'label': label,
                            'confidence': float(conf),
                            'model': 'coco'
                        })
            else:
                # Fallback to just label and confidence pairs
                for label, conf in detected_coco:
                    coco_results.append({
                        'label': label,
                        'confidence': float(conf),
                        'model': 'coco'
                    })
            
            # Add to combined results
            results.extend(coco_results)
        
        return jsonify({'detections': results})
    except Exception as e:
        print(f"Error in detect_frame: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/api/sms_status')
def sms_status():
    """API endpoint to check SMS notification status"""
    return jsonify({
        'sms_enabled': config.sms_enabled,
        'sms_objects': config.sms_objects,
        'sms_cooldown': config.sms_cooldown
    })

@app.route('/api/toggle_sms', methods=['POST'])
def toggle_sms():
    """API endpoint to toggle SMS notifications on/off"""
    data = request.get_json()
    if data and 'enabled' in data:
        config.sms_enabled = bool(data['enabled'])
        # Save the setting
        config.save_settings()
        return jsonify({
            'success': True,
            'sms_enabled': config.sms_enabled
        })
    return jsonify({
        'success': False,
        'error': 'Invalid request'
    }), 400

if __name__ == '__main__':
    # Use this for local development
    socketio.run(app, debug=True)
    
# This is needed for Render deployment with gunicorn
# The application variable for gunicorn to use
application = app