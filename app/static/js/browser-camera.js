/**
 * Browser-based camera access and object detection for Pinaka AI
 * This file handles:
 * 1. Browser camera access
 * 2. Frame capture and sending to server
 * 3. Visualization of detection results
 */

// Configuration settings
const config = {
    captureInterval: 200, // milliseconds between frame captures
    detectionThreshold: 0.4, // minimum confidence score for displaying detections
    colors: { // colors for bounding boxes by class (with fallback)
        person: '#FF5733',
        car: '#33A1FF',
        dog: '#33FF57',
        cat: '#D033FF',
        stone: '#FFD700',
        gas_cylinder: '#FF4500',
        default: '#00FFFF' // fallback color
    }
};

// Store references to HTML elements
let elements = {
    video: null,
    canvas: null,
    ctx: null,
    startButton: null,
    stopButton: null,
    statusMessage: null
};

// Track application state
let state = {
    streaming: false,
    captureInterval: null,
    socket: null,
    lastDetections: []
};

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    setupElements();
    setupEventListeners();
    setupSocketConnection();
    
    // Check SMS notification status on page load
    checkSmsStatus();
    
    // Set up interval to periodically check SMS status
    setInterval(checkSmsStatus, 60000); // Check every minute
});

/**
 * Set up references to DOM elements
 */
function setupElements() {
    // Create video element if it doesn't exist
    if (!document.getElementById('camera-feed')) {
        const videoContainer = document.querySelector('.video-container');
        if (videoContainer) {
            // Remove existing image feed if any
            const existingFeed = videoContainer.querySelector('.video-feed');
            if (existingFeed) {
                existingFeed.remove();
            }
            
            // Create and add video element
            const video = document.createElement('video');
            video.id = 'camera-feed';
            video.className = 'video-feed';
            video.setAttribute('autoplay', '');
            video.setAttribute('playsinline', '');
            
            // Create and add canvas for drawing detections
            const canvas = document.createElement('canvas');
            canvas.id = 'detection-canvas';
            canvas.className = 'video-feed';
            canvas.style.position = 'absolute';
            canvas.style.top = '0';
            canvas.style.left = '0';
            
            // Create controls
            const controls = document.createElement('div');
            controls.className = 'video-controls';
            controls.style.position = 'absolute';
            controls.style.bottom = '60px';
            controls.style.left = '0';
            controls.style.right = '0';
            controls.style.display = 'flex';
            controls.style.justifyContent = 'center';
            controls.style.gap = '10px';
            controls.style.zIndex = '10';
            
            const startButton = document.createElement('button');
            startButton.id = 'start-camera';
            startButton.className = 'btn btn-primary';
            startButton.textContent = 'Start Camera';
            
            const stopButton = document.createElement('button');
            stopButton.id = 'stop-camera';
            stopButton.className = 'btn btn-danger';
            stopButton.textContent = 'Stop Camera';
            stopButton.style.display = 'none';
            
            const statusMessage = document.createElement('div');
            statusMessage.id = 'camera-status';
            statusMessage.className = 'video-status';
            statusMessage.style.textAlign = 'center';
            statusMessage.style.padding = '10px';
            statusMessage.style.backgroundColor = 'rgba(0,0,0,0.6)';
            statusMessage.style.color = 'white';
            statusMessage.style.borderRadius = '5px';
            statusMessage.style.marginTop = '10px';
            statusMessage.textContent = 'Click "Start Camera" to begin detection';
            
            controls.appendChild(startButton);
            controls.appendChild(stopButton);
            
            videoContainer.appendChild(video);
            videoContainer.appendChild(canvas);
            videoContainer.appendChild(controls);
            videoContainer.appendChild(statusMessage);
        }
    }
    
    // Store element references
    elements.video = document.getElementById('camera-feed');
    elements.canvas = document.getElementById('detection-canvas');
    elements.ctx = elements.canvas ? elements.canvas.getContext('2d') : null;
    elements.startButton = document.getElementById('start-camera');
    elements.stopButton = document.getElementById('stop-camera');
    elements.statusMessage = document.getElementById('camera-status');
}

/**
 * Set up event listeners for buttons and video
 */
function setupEventListeners() {
    if (elements.startButton) {
        elements.startButton.addEventListener('click', startCamera);
    }
    
    if (elements.stopButton) {
        elements.stopButton.addEventListener('click', stopCamera);
    }
    
    if (elements.video) {
        elements.video.addEventListener('loadedmetadata', function() {
            // Set canvas dimensions to match video
            if (elements.canvas) {
                elements.canvas.width = elements.video.videoWidth;
                elements.canvas.height = elements.video.videoHeight;
            }
        });
    }
}

/**
 * Start accessing the camera and capturing frames
 */
function startCamera() {
    if (state.streaming) return;
    
    // Update UI
    if (elements.startButton) elements.startButton.style.display = 'none';
    if (elements.stopButton) elements.stopButton.style.display = 'inline-block';
    if (elements.statusMessage) elements.statusMessage.textContent = 'Accessing camera...';
    
    // Check for browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        updateStatus('Error: Your browser does not support camera access');
        return;
    }
    
    // Request camera access
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(function(stream) {
            // Connect stream to video element
            elements.video.srcObject = stream;
            state.streaming = true;
            updateStatus('Camera active - detecting objects');
            
            // Start capture loop
            startFrameCapture();
        })
        .catch(function(err) {
            console.error('Error accessing camera:', err);
            updateStatus('Error accessing camera. Please check permissions.');
            resetButtons();
        });
}

/**
 * Stop camera and frame capture
 */
function stopCamera() {
    if (!state.streaming) return;
    
    // Stop capture interval
    if (state.captureInterval) {
        clearInterval(state.captureInterval);
        state.captureInterval = null;
    }
    
    // Stop video stream
    if (elements.video && elements.video.srcObject) {
        const stream = elements.video.srcObject;
        const tracks = stream.getTracks();
        
        tracks.forEach(function(track) {
            track.stop();
        });
        
        elements.video.srcObject = null;
    }
    
    // Clear canvas
    if (elements.ctx) {
        elements.ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
    }
    
    // Update state and UI
    state.streaming = false;
    updateStatus('Camera stopped');
    resetButtons();
}

/**
 * Reset button visibility
 */
function resetButtons() {
    if (elements.startButton) elements.startButton.style.display = 'inline-block';
    if (elements.stopButton) elements.stopButton.style.display = 'none';
}

/**
 * Update status message
 */
function updateStatus(message) {
    if (elements.statusMessage) {
        elements.statusMessage.textContent = message;
    }
}

/**
 * Start capturing frames at the specified interval
 */
function startFrameCapture() {
    state.captureInterval = setInterval(captureAndSendFrame, config.captureInterval);
}

/**
 * Capture a frame from the video and send to server for processing
 */
function captureAndSendFrame() {
    if (!state.streaming || !elements.video || !elements.canvas || !elements.ctx) return;
    
    // Ensure video is playing and has valid dimensions
    if (elements.video.readyState !== elements.video.HAVE_ENOUGH_DATA || 
        elements.video.videoWidth === 0 || 
        elements.video.videoHeight === 0) {
        return;
    }
    
    // Set canvas dimensions to match video
    elements.canvas.width = elements.video.videoWidth;
    elements.canvas.height = elements.video.videoHeight;
    
    // Draw video frame to canvas
    elements.ctx.drawImage(elements.video, 0, 0, elements.canvas.width, elements.canvas.height);
    
    // Get base64 image data
    const imageData = elements.canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
    
    // Send to server for detection
    fetch('/detect_frame', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image: imageData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Detection error:', data.error);
            updateStatus('Detection error: ' + data.error);
            return;
        }
        
        // Log the detection data for debugging (only first few to avoid console spam)
        if (data.detections && data.detections.length > 0) {
            console.log(`Received ${data.detections.length} detections:`, 
                       data.detections.slice(0, 3));
            
            // Update status
            if (data.detections.length > 0) {
                updateStatus(`Active detection: ${data.detections.length} objects found`);
            } else {
                updateStatus('Camera active - no objects detected');
            }
        }
        
        // Process and display detection results
        processDetections(data.detections);
    })
    .catch(error => {
        console.error('Error sending frame to server:', error);
        updateStatus('Connection error - check console');
    });
}

/**
 * Process detection results and visualize on canvas
 */
function processDetections(detections) {
    if (!elements.ctx || !elements.canvas) return;
    state.lastDetections = detections;
    elements.ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
    // Sort and limit to top 5 detections by confidence
    const significantDetections = detections
        .filter(d => d.confidence >= config.detectionThreshold)
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 5);
    significantDetections.forEach(detection => {
        if (detection.confidence >= 0.5 && state.socket) {
            const snapshotCanvas = document.createElement('canvas');
            snapshotCanvas.width = elements.canvas.width;
            snapshotCanvas.height = elements.canvas.height;
            const snapshotCtx = snapshotCanvas.getContext('2d');
            snapshotCtx.drawImage(elements.video, 0, 0, snapshotCanvas.width, snapshotCanvas.height);
            const snapshotData = snapshotCanvas.toDataURL('image/jpeg', 0.7).split(',')[1];
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            state.socket.emit('detection_alert', {
                object: detection.label,
                confidence: detection.confidence,
                time: timeString,
                image: snapshotData
            });
        }
    });
    drawBoxes(significantDetections);
}

function drawBoxes(detections) {
    if (!elements.ctx || !elements.canvas) return;
    elements.ctx.drawImage(elements.video, 0, 0, elements.canvas.width, elements.canvas.height);
    detections.forEach(detection => {
        let x, y, width, height;
        if (detection.x1 !== undefined && detection.y1 !== undefined && detection.x2 !== undefined && detection.y2 !== undefined) {
            x = detection.x1;
            y = detection.y1;
            width = detection.x2 - detection.x1;
            height = detection.y2 - detection.y1;
        } else if (detection.width !== undefined && detection.height !== undefined) {
            x = detection.x1 || 0;
            y = detection.y1 || 0;
            width = detection.width;
            height = detection.height;
        } else {
            width = elements.canvas.width * 0.3;
            height = elements.canvas.height * 0.3;
            x = (elements.canvas.width - width) / 2;
            y = (elements.canvas.height - height) / 2;
        }
        let color = config.colors.default;
        if (detection.model === 'custom') {
            color = config.colors[detection.label] || '#FF9900';
        } else if (detection.model === 'coco') {
            color = config.colors[detection.label] || '#3366FF';
        } else {
            color = config.colors[detection.label] || config.colors.default;
        }
        // Draw smooth rounded rectangle
        elements.ctx.save();
        elements.ctx.strokeStyle = color;
        elements.ctx.lineWidth = 3;
        roundRect(elements.ctx, x, y, width, height, 12);
        elements.ctx.stroke();
        elements.ctx.restore();
        // Label background with shadow for clarity
        const modelInfo = detection.model ? ` (${detection.model})` : '';
        const text = `${detection.label}${modelInfo}: ${Math.round(detection.confidence * 100)}%`;
        elements.ctx.font = 'bold 16px Arial';
        const textWidth = elements.ctx.measureText(text).width;
        elements.ctx.save();
        elements.ctx.globalAlpha = 0.7;
        elements.ctx.fillStyle = color;
        elements.ctx.shadowColor = '#222';
        elements.ctx.shadowBlur = 6;
        elements.ctx.fillRect(x, y - 30, textWidth + 16, 28);
        elements.ctx.restore();
        elements.ctx.save();
        elements.ctx.fillStyle = '#fff';
        elements.ctx.font = 'bold 16px Arial';
        elements.ctx.fillText(text, x + 8, y - 10);
        elements.ctx.restore();
    });
}

// Draws a rounded rectangle
function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

// --- Camera persistence across navigation ---
// Use sessionStorage to remember if camera should be running
window.addEventListener('beforeunload', function() {
    sessionStorage.setItem('cameraShouldRun', state.streaming ? '1' : '0');
});
document.addEventListener('DOMContentLoaded', function() {
    // Auto-restart camera if it was running before navigation
    if (sessionStorage.getItem('cameraShouldRun') === '1' && elements.startButton) {
        elements.startButton.click();
    }
});

/**
 * Set up Socket.IO connection
 */
function setupSocketConnection() {
    if (typeof io !== 'undefined') {
        state.socket = io();
        
        state.socket.on('connect', function() {
            console.log('Connected to Socket.IO server');
        });
        
        state.socket.on('disconnect', function() {
            console.log('Disconnected from Socket.IO server');
        });
    }
}

/**
 * Check SMS notification status
 */
function checkSmsStatus() {
    fetch('/api/sms_status')
        .then(response => response.json())
        .then(data => {
            const smsStatusElement = document.getElementById('sms-status');
            if (smsStatusElement) {
                if (data.sms_enabled) {
                    smsStatusElement.style.display = 'block';
                } else {
                    smsStatusElement.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error checking SMS status:', error);
        });
}