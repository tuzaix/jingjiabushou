import requests
import json
import sys
import os
import time
import logging
from datetime import datetime, timedelta

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_table_if_not_exists():
    """Create the market_capacity table if it doesn't exist."""
    # DROP table to ensure schema is correct during development
    # In production, we would use ALTER or migrations
    # drop_query = "DROP TABLE IF EXISTS market_capacity"
    
    create_query = """
    CREATE TABLE IF NOT EXISTS `market_capacity` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `date` date NOT NULL COMMENT '日期',
    `call_auction_amount` int DEFAULT NULL COMMENT '竞价量能 (trends[0])万',
    `full_day_amount` int DEFAULT NULL COMMENT '收盘全天量能 (trends[-1])万',
    `trends` text COMMENT '全天量能趋势 (trends)',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """
    try:
        # Check if table exists and has correct columns, or just drop and recreate for now
        # Since this is a new feature, dropping is safe-ish if user hasn't stored critical data yet
        # But to be safe, let's just run CREATE IF NOT EXISTS. 
        # If the schema is wrong (bigint vs json), we might need to fix it.
        # Given the weird Read output, I'll force a DROP first to be sure.
        # DatabaseManager.execute_update(drop_query)
        DatabaseManager.execute_update(create_query)
        logger.info("Table 'market_capacity' created/reset successfully.")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        sys.exit(1)

def save_market_capacity(date_str, call_auction_volume, full_day_volume, trends):
    """Save market capacity data to database."""
    query = """
    INSERT INTO market_capacity (date, call_auction_amount, full_day_amount, trends)
    VALUES (%s, %s, %s, %s)
    """
    params = (
        date_str,
        call_auction_volume,
        full_day_volume,
        json.dumps(trends, ensure_ascii=False)
    )
    
    try:
        DatabaseManager.execute_update(query, params)
        logger.info(f"Successfully saved market capacity for date: {date_str}")
    except Exception as e:
        logger.error(f"Error saving data for {date_str}: {e}")

def fetch_market_capacity(date_str):
    url = "https://apphis.longhuvip.com/w1/api/index.php"

    headers = {
        "Host": "apphis.longhuvip.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Accept": "*/*",
        "User-Agent": "lhb/5.21.1 (com.kaipanla.www; build:1; iOS 17.6.1) Alamofire/4.9.1",
        "Accept-Language": "zh-Hans-US;q=1.0, en-US;q=0.9, zh-Hant-US;q=0.8"
    }

    data = {
        "Date": date_str,
        "PhoneOSNew": "2",
        "Type": "0",
        "VerSion": "5.21.0.1",
        "a": "MarketCapacity",
        "apiv": "w42",
        "c": "HisHomeDingPan"
    }

    logger.info(f"Fetching market capacity data for date: {date_str}...")
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        try:
            json_data = response.json()
            
            print(f"DEBUG: info_val: {json_data.keys()}")

            from pprint import pprint
            pprint(json_data['info'].keys())

            trends = json_data.get('info', {}).get('trends', [])

            if len(trends) > 0:

                call_auction_volume = float(trends[0][1])
                full_day_volume = float(trends[-1][3])
                
                save_market_capacity(date_str, call_auction_volume, full_day_volume, trends)
            else:
                logger.warning(f"No valid 'info' (trends) found for date: {date_str}")
                # print(f"DEBUG Response: {json.dumps(json_data, ensure_ascii=False)}")

        except json.JSONDecodeError:
            logger.error(f"Response not JSON for date: {date_str}")

    except Exception as e:
        logger.error(f"Error occurred fetching {date_str}: {e}")

def batch_fetch_capacity(start_date_str, end_date_str):
    """Fetch capacity for a date range."""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Date format error: {e}")
        return

    current_date = start_date
    while current_date <= end_date:
        day_str = current_date.strftime("%Y-%m-%d")
        
        # Skip weekends
        if current_date.weekday() < 5: # 0-4 are Mon-Fri
             fetch_market_capacity(day_str)
             time.sleep(0.5) # Be nice to the API
        else:
             logger.info(f"Skipping weekend: {day_str}")

        current_date += timedelta(days=1)

if __name__ == "__main__":
    # Ensure table exists (and reset schema)
    create_table_if_not_exists()

    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        print(f"Starting batch fetch from {start_date} to {end_date}...")
        batch_fetch_capacity(start_date, end_date)
    elif len(sys.argv) == 2:
        target_date = sys.argv[1]
        fetch_market_capacity(target_date)
    else:
        print("Usage: python fetch_market_capacity.py <start_date> [end_date]")
        print("Example: python fetch_market_capacity.py 2026-02-01 2026-02-13")
        # Default run for today if no args
        today = datetime.now().strftime('%Y-%m-%d')
        fetch_market_capacity(today)
