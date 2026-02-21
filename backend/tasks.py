import logging
import datetime
from services.sync_service import SyncService
from services.jiuyan_service import JiuyanService

# ...

def fetch_jiuyan_data(date_str=None):
    """Fetch limit up data from Jiuyan Gongshe."""
    
    # If date not provided, calculate based on time
    if not date_str:
        now = datetime.datetime.now()
        # If after 15:30, use today, else use yesterday
        if now.hour >= 16 or (now.hour == 15 and now.minute >= 30):
            date_str = now.strftime('%Y-%m-%d')
        else:
            yesterday = now - datetime.timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')

    logger.info(f"Task started: fetch_jiuyan_data (date={date_str})")
    try:
        success, msg = JiuyanService.sync_data(date_str)
        if success:
            logger.info(f"Task completed: fetch_jiuyan_data. {msg}")
        else:
            logger.error(f"Task failed: fetch_jiuyan_data. Error: {msg}")
        return success
    except Exception as e:
        logger.error(f"Task failed: fetch_jiuyan_data. Error: {e}")
        return False


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_all_stock_codes():
    """Fetch all A-share stock codes using SyncService."""
    logger.info("Task started: get_all_stock_codes")
    try:
        result = SyncService.get_all_stock_codes()
        logger.info(f"Task completed: get_all_stock_codes. Retrieved {len(result) if result else 0} stocks.")
        return result
    except Exception as e:
        logger.error(f"Task failed: get_all_stock_codes. Error: {e}")
        return []

def fetch_call_auction_data(stock_list_data=None):
    """Fetch call auction data using SyncService."""
    logger.info("Task started: fetch_call_auction_data")
    try:
        result = SyncService.fetch_call_auction_data(stock_list_data)
        logger.info("Task completed: fetch_call_auction_data")
        return result
    except Exception as e:
        logger.error(f"Task failed: fetch_call_auction_data. Error: {e}")
        return None

def fetch_yesterday_limit_up():
    """Fetch yesterday's limit up stocks using SyncService."""
    logger.info("Task started: fetch_yesterday_limit_up")
    try:
        result = SyncService.fetch_yesterday_limit_up()
        logger.info("Task completed: fetch_yesterday_limit_up")
        return result
    except Exception as e:
        logger.error(f"Task failed: fetch_yesterday_limit_up. Error: {e}")
        return None

if __name__ == "__main__":
    # Test run
    # get_all_stock_codes()
    # fetch_call_auction_data()
    # fetch_yesterday_limit_up()
    pass
