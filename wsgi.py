# Import app directly from app.py to avoid confusion with the app package
import importlib.util
import os
import sys

# Directly load the app.py module
spec = importlib.util.spec_from_file_location("app_module", 
                                             os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Get app and socketio from the loaded module
app = app_module.app
socketio = app_module.socketio

if __name__ == '__main__':
    socketio.run(app)