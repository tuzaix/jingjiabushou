
import sys
import os
import logging
import time

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.eastmoney_service import EastmoneyService
from utils.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_update_config():
    # Test cURL with secids (using real stock codes: 600000=PF Bank, 000001=Ping An)
    # Note: secids format is market.code
    curl_cmd = """
    curl 'http://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.600000,0.000001&fields=f12,f14' \
      -H 'Accept: */*' \
      --data-raw 'fltt=2&secids=1.600000,0.000001&fields=f12,f14'
    """

    logger.info("Starting update_config test...")
    
    # Run update
    try:
        success, msg = EastmoneyService.update_config(curl_cmd)
        logger.info(f"Update result: {success}, {msg}")
    except Exception as e:
        logger.error(f"Update failed with exception: {e}")
        return

    # Check database
    try:
        stocks = DatabaseManager.execute_query("SELECT * FROM stock_list", dictionary=True)
        logger.info(f"Stock list count: {len(stocks)}")
        for s in stocks:
            logger.info(f"Stock: {s['code']} - {s['name']} (Market: {s['market']})")
            
        if len(stocks) == 2:
             logger.info("Test PASSED: stock_list updated correctly.")
        else:
             logger.warning(f"Test FAILED: Expected 2 stocks, got {len(stocks)}")
             
    except Exception as e:
        logger.error(f"Database query failed: {e}")

if __name__ == "__main__":
    test_update_config()
