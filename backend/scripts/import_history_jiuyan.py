import sys
import os
import logging
import datetime
import time
import random

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.jiuyan_service import JiuyanService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import argparse

# ... (imports remain the same)

def import_history_data(start_date=None, end_date=None, target_date=None):
    # 1. Update Config with the latest curl command
    # ... (curl_command remains the same)
    curl_command = r"""curl 'https://app.jiuyangongshe.com/jystock-app/api/v1/action/field' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -b 'SESSION=NzE2YWU3NWQtMTE4Ni00NzA4LTkxMTQtZTFlZWQ1N2NmODI5; Hm_lvt_58aa18061df7855800f2a1b32d6da7f4=1771507606,1771571086; Hm_lpvt_58aa18061df7855800f2a1b32d6da7f4=1771571139' \
  -H 'Origin: https://www.jiuyangongshe.com' \
  -H 'Referer: https://www.jiuyangongshe.com/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36' \
  -H 'platform: 3' \
  -H 'sec-ch-ua: "Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'timestamp: 1771571177386' \
  -H 'token: c6c97fb4d2a915a10ee8f2b5cdde1c86' \
  --data-raw '{"date":"2026-02-13","pc":1}'"""

    logger.info("Updating Jiuyan API Config...")
    success, msg = JiuyanService.update_config(curl_command)
    if not success:
        logger.error(f"Failed to update config: {msg}")
        return
    logger.info("Config updated successfully.")

    # Determine date range
    today = datetime.date.today()
    
    if target_date:
        start_date_obj = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        end_date_obj = start_date_obj
    elif start_date and end_date:
        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default: Past 90 days
        end_date_obj = today
        start_date_obj = today - datetime.timedelta(days=90)
    
    logger.info(f"Starting import from {start_date_obj} to {end_date_obj}")

    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Skip weekends (simple check, not covering holidays)
        # weekday() returns 0 for Monday, 6 for Sunday.
        if current_date.weekday() >= 5:
            logger.info(f"Skipping weekend: {date_str}")
            current_date += datetime.timedelta(days=1)
            continue

        logger.info(f"Syncing data for: {date_str} ...")
        
        try:
            success, result = JiuyanService.sync_data(date_str)
            if success:
                logger.info(f"Success: {result}")
            else:
                # Some days might not have data (holidays), log as warning but continue
                logger.warning(f"Failed/No Data for {date_str}: {result}")
        except Exception as e:
            logger.error(f"Exception for {date_str}: {e}")

        # Sleep to be nice to the API if processing multiple days
        if start_date_obj != end_date_obj:
            sleep_time = random.uniform(1.0, 3.0)
            logger.info(f"Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)
        
        current_date += datetime.timedelta(days=1)

    logger.info("Import completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import limit-up data from Jiuyan Gongshe')
    parser.add_argument('--date', type=str, help='Specific date to import (YYYY-MM-DD)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    import_history_data(start_date=args.start, end_date=args.end, target_date=args.date)
