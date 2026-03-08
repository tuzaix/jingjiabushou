import mysql.connector
import logging
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_config import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_indexes():
    """
    Update database indexes for performance optimization.
    """
    cnx = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        
        # 1. Update call_auction_data
        logger.info("Updating indexes for call_auction_data...")
        try:
            cursor.execute("CREATE INDEX idx_date_code ON call_auction_data (date, code)")
            logger.info("Added idx_date_code to call_auction_data.")
        except mysql.connector.Error as err:
            if err.errno == 1061: # Duplicate key name
                logger.info("idx_date_code already exists on call_auction_data.")
            else:
                logger.error(f"Error adding idx_date_code to call_auction_data: {err}")
        
        try:
            cursor.execute("CREATE INDEX idx_date_time_code ON call_auction_data (date, time, code)")
            logger.info("Added idx_date_time_code to call_auction_data.")
        except mysql.connector.Error as err:
            if err.errno == 1061:
                logger.info("idx_date_time_code already exists on call_auction_data.")
            else:
                logger.error(f"Error adding idx_date_time_code to call_auction_data: {err}")

        # 2. Update yesterday_limit_up
        logger.info("Updating indexes for yesterday_limit_up...")
        try:
            cursor.execute("CREATE INDEX idx_date_code ON yesterday_limit_up (date, code)")
            logger.info("Added idx_date_code to yesterday_limit_up.")
        except mysql.connector.Error as err:
            if err.errno == 1061:
                logger.info("idx_date_code already exists on yesterday_limit_up.")
            else:
                logger.error(f"Error adding idx_date_code to yesterday_limit_up: {err}")
        
        cnx.commit()
        cursor.close()
        logger.info("Database indexes updated successfully.")
        
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
    finally:
        if cnx:
            cnx.close()

if __name__ == "__main__":
    update_indexes()
