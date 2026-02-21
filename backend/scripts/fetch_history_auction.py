import sys
import os
import requests
import datetime
import time
import logging
from decimal import Decimal

# Add backend directory to sys.path to allow imports from utils
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from utils.database import DatabaseManager
except ImportError:
    # Fallback for running from different directories
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(current_dir, 'fetch_history_auction.log'))
    ]
)
logger = logging.getLogger(__name__)

URL = "https://apphis.longhuvip.com/w1/api/index.php"
HEADERS = {
    "Host": "apphis.longhuvip.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Accept": "*/*",
    "User-Agent": "lhb/5.21.1 (com.kaipanla.www; build:1; iOS 17.6.1) Alamofire/4.9.1",
    "Accept-Language": "zh-Hans-US;q=1.0, en-US;q=0.9, zh-Hant-US;q=0.8"
}

# Configuration for 6 pages based on curl commands
# Index: st value
PAGE_CONFIGS = [
    {"index": 0, "st": 20},
    {"index": 9, "st": 31},
    {"index": 29, "st": 31},
    {"index": 50, "st": 30},
    {"index": 69, "st": 31},
    {"index": 89, "st": 31}
]

def fetch_page(date_str, page_config):
    """
    Fetch a single page of data for a given date.
    """
    data = {
        "Day": date_str,
        "Filter": "0",
        "FilterGem": "0",
        "FilterMotherboard": "0",
        "FilterTIB": "0",
        "Index": str(page_config["index"]),
        "Is_st": "1",
        "Order": "1",
        "PhoneOSNew": "2",
        "PidType": "8",
        "Type": "18",
        "VerSion": "5.21.0.1",
        "a": "HisDaBanList",
        "apiv": "w42",
        "c": "HisHomeDingPan",
        "st": str(page_config["st"])
    }
    
    try:
        response = requests.post(URL, headers=HEADERS, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch page {page_config['index']} for {date_str}: Status {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Exception fetching page {page_config['index']} for {date_str}: {e}")
        return None

def process_and_save_data(date_str, items):
    """
    Process list items and save to database.
    """
    if not items:
        return 0
        
    insert_sql = """
    REPLACE INTO call_auction_data 
    (date, time, code, name, sector, bidding_percent, bidding_amount, asking_amount) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = []
    for i, item in enumerate(items):
        try:
            code = item[0]
            name = item[1]

            sector = item[11]

            # Index 18 seems to be asking amount (large number)
            asking_amount = float(item[18]) if item[18] else 0.0

            # Use index 19 for change percent (observed in test_fetch.py)
            bidding_percent = float(item[19]) if item[19] else 0.0
 
            # Using index 22 as Amount based on observation (21M for ZhangYue matches auction amount)
            bidding_amount = float(item[22]) if item[22] else 0.0
            
            # logger.info(f"Sql: {insert_sql}")
            # logger.info(f"Processing item {i}: {code} {name} {bidding_percent} {bidding_amount} {asking_amount} {sector}, {bidding_amount} {asking_amount}, {asking_amount}")

            values.append((
                date_str,
                '09:25:00',
                code,
                name,
                sector,
                bidding_percent,
                bidding_amount,
                asking_amount
            ))
        except Exception as e:
            logger.warning(f"Error processing item {item}: {e}")
            continue
            
    if values:
        try:
            # We use DatabaseManager directly
            # Note: DatabaseManager usually handles connection, here we use execute_update with many=True
            # But we might want to check for duplicates first? 
            # The calling function handles date-level duplication check.
            # Here we just insert.
            count = DatabaseManager.execute_update(insert_sql, values, many=True)
            return count
        except Exception as e:
            logger.error(f"Database error inserting data for {date_str}: {e}")
            return 0
    return 0

def main():
    # Calculate date range: last 3 months
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=120)
    
    logger.info(f"Starting fetch for range: {start_date} to {end_date}")
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Check if weekend
        if current_date.weekday() >= 5: # 5=Saturday, 6=Sunday
            logger.info(f"Skipping weekend: {date_str}")
            current_date += datetime.timedelta(days=1)
            continue
            
        # Check if data already exists
        try:
            # We need a context manager for fetch_one
            check_sql = "SELECT COUNT(*) as count FROM call_auction_data WHERE date = %s"
            result = DatabaseManager.execute_query(check_sql, (date_str,), dictionary=True, fetch_one=True)
            if result and result['count'] > 0:
                logger.info(f"Data already exists for {date_str}, skipping.")
                current_date += datetime.timedelta(days=1)
                continue
        except Exception as e:
            logger.error(f"Error checking existing data for {date_str}: {e}")
            # Continue to try fetching if check fails? Or skip?
            # Safer to continue and maybe fail on insert if unique constraint exists (but no unique constraint on date+time+code in schema provided earlier, just PK id and index)
            pass

        logger.info(f"Fetching data for {date_str}...")
        
        total_inserted = 0
        has_data = False
        
        for config in PAGE_CONFIGS:
            page_data = fetch_page(date_str, config)
            if page_data and 'list' in page_data and len(page_data['list']) > 0:
                items = page_data['list']
                inserted = process_and_save_data(date_str, items)
                total_inserted += inserted
                has_data = True
                logger.info(f"  Page {config['index']}: Inserted {inserted} records.")
            else:
                logger.info(f"  Page {config['index']}: No data.")
            
            # Rate limiting between pages
            time.sleep(1)
            
        if not has_data:
            logger.info(f"No data found for {date_str} (possibly holiday).")
        else:
            logger.info(f"Completed {date_str}: Total {total_inserted} records.")
            
        # Rate limiting between days
        time.sleep(2)
        current_date += datetime.timedelta(days=1)

if __name__ == "__main__":
    main()
