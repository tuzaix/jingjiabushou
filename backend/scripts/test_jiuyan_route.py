
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from services.jiuyan_service import JiuyanService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_jiuyan_test_endpoint():
    app = create_app()
    
    # Mock config first
    # Using example.com
    curl_cmd = "curl 'http://example.com' -H 'Content-Type: application/json' --data-raw '{\"date\": \"2023-01-01\"}'"
    JiuyanService.update_config(curl_cmd)
    
    with app.test_client() as client:
        logger.info("Calling /api/admin/jiuyan/test ...")
        response = client.post('/api/admin/jiuyan/test')
        
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            logger.error("Endpoint not found (404)!")
        elif response.status_code == 500:
            # 500 is expected because example.com returns HTML not JSON
            logger.info("Endpoint reachable (500 expected due to mock data parsing error).")
            # Log error details if available
            try:
                logger.info(f"Response: {response.get_json()}")
            except:
                logger.info(f"Response text: {response.data}")
        elif response.status_code == 200:
            logger.info("Endpoint reachable (200 OK).")
            logger.info(f"Response: {response.get_json()}")

if __name__ == "__main__":
    test_jiuyan_test_endpoint()
