import logging
import datetime
from services.sync_service import SyncService
from services.jiuyan_service import JiuyanService
from services.eastmoney_service import EastmoneyService
from utils.database import DatabaseManager

def fetch_eastmoney_call_auction(dry_run=True, date_str=None):
    """
    Fetch real-time call auction data from Eastmoney.
    dry_run: If True, only fetch and log data, do not save to DB.
    date_str: Optional date string 'YYYY-MM-DD'. If provided, used for logging/saving.
              If not provided, uses current date.
    """
    logger.info(f"Task started: fetch_eastmoney_call_auction (dry_run={dry_run}, date={date_str})")
    try:
        success, result = EastmoneyService.fetch_data()
        if not success:
            logger.error(f"Failed to fetch Eastmoney data: {result}")
            return False

        # Parse data
        data_list = []
        if isinstance(result, dict):
            inner_data = result.get('data')
            if isinstance(inner_data, dict):
                if 'diff' in inner_data:
                    data_list = inner_data['diff']
                    if isinstance(data_list, dict):
                        data_list = list(data_list.values())
                elif 'list' in inner_data:
                    data_list = inner_data['list']
                elif 'full' in inner_data:
                    data_list = inner_data['full']
                else:
                    data_list = list(inner_data.values())

        if not data_list:
            logger.warning("No data found in Eastmoney response.")
            return False

        logger.info(f"Fetched {len(data_list)} records from Eastmoney.")

        # Determine time
        now = datetime.datetime.now()
        current_time_str = now.strftime('%H:%M:%S')
        
        if not date_str:
            date_str = now.strftime('%Y-%m-%d')
        
        # Logic: 9:15 - 9:25 -> use actual time, else -> 9:25:00
        if '09:15:00' <= current_time_str <= '09:25:00':
            record_time = current_time_str
        else:
            record_time = '09:25:00'

        if dry_run:
            logger.info(f"Dry run mode. Date: {date_str}, Time: {record_time}. Sample first record: {data_list[0] if data_list else 'None'}")
            # Print table to log for verification
            log_msg = "\n" + "-" * 90 + "\n"
            log_msg += f"{'Code':<10} {'Name':<15} {'Price':<10} {'Change%':<10} {'Amount':<15} {'Time'} {'Date'}\n"
            log_msg += "-" * 90 + "\n"
            count = 0
            for item in data_list:
                if count >= 20: break
                if not isinstance(item, dict): continue
                code = str(item.get('f12', 'N/A'))
                name = item.get('f14', 'N/A')
                price = item.get('f2', 0)
                change = item.get('f3', 0)
                amount = item.get('f6', 0)
                log_msg += f"{code:<10} {name:<15} {price:<10} {change:<10} {amount:<15} {record_time} {date_str}\n"
                count += 1
            log_msg += "-" * 90
            logger.info(log_msg)
            return True

        # TODO: Implement DB insertion logic here when ready
        # ...
        
        return True

    except Exception as e:
        logger.error(f"Task failed: fetch_eastmoney_call_auction. Error: {e}")
        return False


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

def fetch_call_auction_data(stock_list_data=None, date_str=None):
    """Fetch call auction data using SyncService."""
    logger.info(f"Task started: fetch_call_auction_data (date={date_str})")
    try:
        result = SyncService.fetch_call_auction_data(stock_list_data, date_str)
        logger.info("Task completed: fetch_call_auction_data")
        return result
    except Exception as e:
        logger.error(f"Task failed: fetch_call_auction_data. Error: {e}")
        return None

def fetch_yesterday_limit_up(date_str=None):
    """Fetch yesterday's limit up stocks using SyncService."""
    logger.info(f"Task started: fetch_yesterday_limit_up (date={date_str})")
    try:
        result = SyncService.fetch_yesterday_limit_up(date_str)
        logger.info(f"Task completed: fetch_yesterday_limit_up for date {date_str}")
        return result
    except Exception as e:
        logger.error(f"Task failed: fetch_yesterday_limit_up. Error: {e}")
        return None

if __name__ == "__main__":
    # Test run
    # get_all_stock_codes()
    fetch_call_auction_data()
    # fetch_yesterday_limit_up()
    pass
