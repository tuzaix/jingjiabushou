from flask import Flask
from flask_cors import CORS
import logging
from routes import api_bp
# from scheduler import init_scheduler  <-- Removed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes
    
    # Register Blueprints
    app.register_blueprint(api_bp)
    
    # Init Scheduler
    # Scheduler is now a separate service. Run scheduler.py independently.
    # init_scheduler()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False) 
    # use_reloader=False to avoid scheduler running twice
