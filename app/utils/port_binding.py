# middleware to ensure port binding is detected by Render
import os
from flask import Flask, request

# Get Render's PORT environment variable
port = int(os.environ.get("PORT", 10000))

def init_port_bindings(app):
    """Initialize port bindings for Render compatibility"""
    # Log the port we're binding to
    print(f"Binding to port {port}")
    
    # Add middleware to log requests (helps with debugging)
    @app.before_request
    def log_request_info():
        app.logger.debug('Request Headers: %s', request.headers)
        app.logger.debug('Request Body: %s', request.get_data())
        
    return port
