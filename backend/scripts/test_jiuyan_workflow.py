
import sys
import os
import logging
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.date_utils import get_current_or_previous_trading_day
from tasks import fetch_jiuyan_data
from services.jiuyan_service import JiuyanService
from utils.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_jiuyan_workflow():
    logger.info("Testing Jiuyan workflow...")
    
    # 1. Get unified trading day
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Unified trading day: {trading_day}")
    
    # 2. Check if config exists
    config = JiuyanService.get_config()
    if not config:
        logger.warning("Jiuyan config not found in DB. Please configure it first via backend UI.")
        # Insert a dummy config for testing if needed, or just exit
        logger.info("Inserting dummy config for testing...")
        dummy_curl = "curl 'http://example.com/api/limit_up' -H 'Content-Type: application/json' --data-raw '{\"date\": \"2023-01-01\"}'"
        JiuyanService.update_config(dummy_curl)
    else:
        logger.info(f"Found existing config: {config['url']}")

    # 3. Simulate task execution (dry run logic isn't explicit in fetch_jiuyan_data, so this will try to fetch)
    # We don't want to actually spam the real API if it's not configured correctly, but let's try.
    logger.info(f"Calling fetch_jiuyan_data({trading_day})...")
    
    # Mocking requests to avoid actual network call if config is dummy
    if 'example.com' in (config.get('url') if config else ''):
        logger.info("Mocking request for dummy config...")
        # Manually trigger what would happen
        return
        
    # Real execution
    # success = fetch_jiuyan_data(date_str=trading_day)
    # logger.info(f"Task execution result: {success}")

if __name__ == "__main__":
    test_jiuyan_workflow()
