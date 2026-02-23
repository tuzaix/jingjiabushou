import logging
import datetime
from services.sync_service import SyncService
from services.jiuyan_service import JiuyanService
from services.eastmoney_service import EastmoneyService
from services.kaipanla_service import KaipanlaService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_update_stock_list():
    """Fetch all A-share stock codes using SyncService."""
    logger.info("Task started: get_all_stock_codes")
    try:
        result = SyncService.update_all_stock_codes()
        logger.info(f"Task completed: update_all_stock_codes. Retrieved {len(result) if result else 0} stocks.")
        return result
    except Exception as e:
        logger.error(f"Task failed: update_all_stock_codes. Error: {e}")
        return []

def run_update_call_auction_data(stock_list_data=None, date_str=None):
    """Fetch call auction data using SyncService."""
    logger.info(f"Task started: run_update_call_auction_data (date={date_str})")
    try:
        result = SyncService.sync_call_auction_data(stock_list_data, date_str)
        logger.info("Task completed: run_update_call_auction_data")
        return result
    except Exception as e:
        logger.error(f"Task failed: run_update_call_auction_data. Error: {e}")
        return None

def run_update_yesterday_limit_up(date_str=None):
    """Fetch yesterday's limit up stocks using SyncService."""
    logger.info(f"Task started: run_update_yesterday_limit_up (date={date_str})")
    try:
        result = SyncService.sync_yesterday_limit_up(date_str)
        logger.info(f"Task completed: run_update_yesterday_limit_up for date {date_str}")
        return result
    except Exception as e:
        logger.error(f"Task failed: run_update_yesterday_limit_up. Error: {e}")
        return None

def run_fetch_index_data(date_str=None):
    """Fetch index data using KaipanlaService."""
    logger.info(f"Task started: run_fetch_index_data (date={date_str})")
    try:
        success, msg = KaipanlaService.save_index_data(date_str)
        logger.info(f"Task completed: run_fetch_index_data. {msg}")
        return success
    except Exception as e:
        logger.error(f"Task failed: run_fetch_index_data. Error: {e}")
        return False

if __name__ == "__main__":
    # Test run
    # get_all_stock_codes()
    # fetch_call_auction_data()
    # fetch_yesterday_limit_up()
    #JiuyanService.sync_data('2026-02-13')
    # run_update_call_auction_data(date_str='2026-02-13')
    # run_update_yesterday_limit_up(date_str='2026-02-13')
    run_fetch_index_data('2026-02-13')
    pass
