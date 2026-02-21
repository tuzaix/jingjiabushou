
import requests
import json
import sys
import os
import logging
from datetime import datetime, timedelta
import time

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_table_if_not_exists():
    """Create the market_sentiment_stats table if it doesn't exist."""
    # Drop table first to ensure schema update (since we are renaming columns)
    # drop_query = "DROP TABLE IF EXISTS market_sentiment_stats"
    # try:
    #     DatabaseManager.execute_update(drop_query)
    #     logger.info("Dropped old 'market_sentiment_stats' table to apply new schema.")
    # except Exception as e:
    #     logger.warning(f"Failed to drop old table: {e}")

    query = """
    CREATE TABLE IF NOT EXISTS market_sentiment_stats (
        date DATE NOT NULL COMMENT '日期',
        time TIME NOT NULL COMMENT '时间',
        limit_up_count INT DEFAULT 0 COMMENT '涨停总家数(ZT)',
        limit_down_count INT DEFAULT 0 COMMENT '跌停总家数(DT)',
        non_st_limit_up_count INT DEFAULT 0 COMMENT '非ST涨停家数(SJZT)',
        non_st_limit_down_count INT DEFAULT 0 COMMENT '非ST跌停家数(SJDT)',
        st_limit_up_count INT DEFAULT 0 COMMENT 'ST涨停家数(STZT)',
        st_limit_down_count INT DEFAULT 0 COMMENT 'ST跌停家数(STDT)',
        rise_count INT DEFAULT 0 COMMENT '上涨家数',
        fall_count INT DEFAULT 0 COMMENT '下跌家数',
        flat_count INT DEFAULT 0 COMMENT '平盘家数',
        market_sentiment VARCHAR(255) COMMENT '市场人气',
        shanghai_turnover BIGINT DEFAULT 0 COMMENT '上海成交额',
        total_turnover BIGINT DEFAULT 0 COMMENT '全市场成交额',
        rise_fall_distribution TEXT COMMENT '涨跌分布',
        raw_response_json JSON COMMENT '原始响应JSON',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (date, time)
    )
    """
    try:
        DatabaseManager.execute_update(query)
        logger.info("Table 'market_sentiment_stats' check/creation successful.")
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise

def save_market_stats(date_str, data):
    """Save market stats to database."""
    info = data.get('info', {})
    if not info:
        logger.warning(f"No 'info' field in data for {date_str}, skipping save.")
        return

    # Extract fields
    time_str = '15:00:00' 
    
    limit_up_count = int(info.get('ZT', 0))
    limit_down_count = int(info.get('DT', 0))
    non_st_limit_up_count = int(info.get('SJZT', 0))
    non_st_limit_down_count = int(info.get('SJDT', 0))
    st_limit_up_count = int(info.get('STZT', 0))
    st_limit_down_count = int(info.get('STDT', 0))
    rise_count = int(info.get('SZJS', 0))
    fall_count = int(info.get('XDJS', 0))
    flat_count = int(info.get('0', 0))
    market_sentiment = info.get('sign', '')
    shanghai_turnover = int(info.get('szln', 0))
    total_turnover = int(info.get('qscln', 0))
    rise_fall_distribution = info.get('ZSZDFB', '')
    
    # Prepare query
    query = """
    INSERT INTO market_sentiment_stats 
    (date, time, limit_up_count, limit_down_count, non_st_limit_up_count, non_st_limit_down_count, 
     st_limit_up_count, st_limit_down_count, rise_count, fall_count, flat_count, 
     market_sentiment, shanghai_turnover, total_turnover, rise_fall_distribution, raw_response_json)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    limit_up_count=VALUES(limit_up_count), limit_down_count=VALUES(limit_down_count), 
    non_st_limit_up_count=VALUES(non_st_limit_up_count), non_st_limit_down_count=VALUES(non_st_limit_down_count),
    st_limit_up_count=VALUES(st_limit_up_count), st_limit_down_count=VALUES(st_limit_down_count),
    rise_count=VALUES(rise_count), fall_count=VALUES(fall_count), flat_count=VALUES(flat_count),
    market_sentiment=VALUES(market_sentiment), shanghai_turnover=VALUES(shanghai_turnover), 
    total_turnover=VALUES(total_turnover), rise_fall_distribution=VALUES(rise_fall_distribution), 
    raw_response_json=VALUES(raw_response_json)
    """
    
    params = (
        date_str, time_str, limit_up_count, limit_down_count, non_st_limit_up_count, non_st_limit_down_count,
        st_limit_up_count, st_limit_down_count, rise_count, fall_count, flat_count, 
        market_sentiment, shanghai_turnover, total_turnover, rise_fall_distribution, json.dumps(data)
    )
    
    try:
        DatabaseManager.execute_update(query, params)
        logger.info(f"Successfully saved market stats for date: {date_str} time: {time_str}")
    except Exception as e:
        logger.error(f"Failed to save market stats: {e}")
        raise

def fetch_limit_up_stats(day):
    url = "https://apphis.longhuvip.com/w1/api/index.php"

    headers = {
        "Host": "apphis.longhuvip.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Accept": "*/*",
        "User-Agent": "lhb/5.21.1 (com.kaipanla.www; build:1; iOS 17.6.1) Alamofire/4.9.1",
        "Accept-Language": "zh-Hans-US;q=1.0, en-US;q=0.9, zh-Hant-US;q=0.8"
    }

    data = {
        "Day": day,
        "PhoneOSNew": "2",
        "VerSion": "5.21.0.1",
        "a": "HisZhangFuDetail",
        "apiv": "w42",
        "c": "HisHomeDingPan"
    }

    print(f"Fetching data for date: {day}...")
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        try:
            json_data = response.json()
            # Save to database
            save_market_stats(day, json_data)
            
        except json.JSONDecodeError:
            print(f"\nResponse Text for {day} (Not JSON):")
            print(response.text)

    except Exception as e:
        print(f"Error occurred for {day}: {e}")

def batch_fetch_stats(start_date_str, end_date_str):
    """Fetch stats for a date range."""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    current_date = start_date
    while current_date <= end_date:
        day_str = current_date.strftime("%Y-%m-%d")
        
        # Skip weekends? (Optional: Market is closed on weekends, but API might return empty or error)
        # For now, let's just fetch everything and handle empty responses.
        if current_date.weekday() < 5: # 0-4 are Mon-Fri
             fetch_limit_up_stats(day_str)
             time.sleep(0.5) # Be nice to the API
        else:
             logger.info(f"Skipping weekend: {day_str}")

        current_date += timedelta(days=1)

if __name__ == "__main__":
    # Ensure table exists
    create_table_if_not_exists()

    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        print(f"Starting batch fetch from {start_date} to {end_date}...")
        batch_fetch_stats(start_date, end_date)
    elif len(sys.argv) == 2:
        target_date = sys.argv[1]
        fetch_limit_up_stats(target_date)
    else:
        print("Usage: python fetch_limit_up_stats.py <start_date> [end_date]")
        print("Example: python fetch_limit_up_stats.py 2026-02-01 2026-02-13")
        # Default run for today if no args
        today = datetime.now().strftime('%Y-%m-%d')
        fetch_limit_up_stats(today)
