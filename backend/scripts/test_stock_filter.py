
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.sync_service import SyncService
from utils.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stock_filter():
    # Test Codes:
    # 600000: PF Bank (Valid)
    # 000001: Ping An (Valid)
    # 603021: ST Huapeng (ST - Should be removed)
    # 833994: Hanbo Gaoxin (Beijing - Should be removed)
    # 688555: Delisted Zeda (Delisted - Should be removed)
    
    secids = "1.600000,0.000001,1.603021,0.833994,1.688555"
    
    logger.info("Starting stock filter test...")
    
    try:
        count = SyncService.update_stock_list_from_secids(secids)
        logger.info(f"Update completed. Inserted count: {count}")
        
        # Verify in DB
        stocks = DatabaseManager.execute_query("SELECT * FROM stock_list", dictionary=True)
        logger.info(f"Database contains {len(stocks)} stocks:")
        for s in stocks:
            logger.info(f" - {s['code']} {s['name']}")
            
        # Assertions
        codes = [s['code'] for s in stocks]
        if '600000' in codes and '000001' in codes:
             logger.info("Valid stocks present.")
        else:
             logger.error("Valid stocks missing!")
             
        if '603021' not in codes and '833994' not in codes and '688555' not in codes:
             logger.info("Invalid stocks (ST/BJ/Delisted) successfully filtered out.")
        else:
             logger.error(f"Invalid stocks found in DB! Codes: {codes}")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_stock_filter()
