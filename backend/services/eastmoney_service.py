import json
import requests
import logging
import shlex
import datetime
from utils.database import DatabaseManager
from utils.locks import akshare_lock

from .base_curl_service import BaseCurlService

# Use a specific logger for this service
logger = logging.getLogger('eastmoney_service')

class EastmoneyService(BaseCurlService):
    @staticmethod
    def update_config(curl_command):
        """
        Parses the curl command and saves the configuration to the database.
        """
        success, msg, config = BaseCurlService._update_config_base(curl_command, 'eastmoney_call_auction')
        
        if success and config:
            # Auto-update stock_list from secids in the configuration
            try:
                secids = None
                body_obj = config.get('body')
                
                if isinstance(body_obj, dict):
                    secids = body_obj.get('secids')
                elif isinstance(body_obj, str):
                    # Check if it contains secids parameter
                    if 'secids=' in body_obj:
                        from urllib.parse import parse_qs
                        # parse_qs handles url decoding
                        parsed = parse_qs(body_obj)
                        if 'secids' in parsed:
                            secids = parsed['secids'][0]
                
                if secids:
                    logger.info("Found secids in configuration, updating stock_list...")
                    EastmoneyService.update_stock_list_from_secids(secids)
                    
            except Exception as e:
                logger.error(f"Error auto-updating stock_list from secids: {e}")
        
        return success, msg

    @staticmethod
    def update_stock_list_from_secids(secids):
        """
        Updates stock_list table based on the provided secids list.
        secids format: ["1.600000", "0.000001"] or "1.600000,0.000001"
        """
        try:
            if not secids:
                return 0
                
            if isinstance(secids, str):
                secids = secids.split(',')
                
            target_codes = set()
            for secid in secids:
                # Format is market.code
                parts = secid.split('.')
                if len(parts) == 2:
                    target_codes.add(parts[1])
            
            if not target_codes:
                logger.warning("No valid codes found in secids.")
                return 0
            
            logger.info(f"Updating stock_list with {len(target_codes)} codes from secids...")
            
            # Fetch all stock info to get names
            with akshare_lock:
                import akshare as ak
                stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            
            # Filter by target codes first
            df_subset = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['代码'].isin(target_codes)]
            
            # Apply exclusion filters (ST, Delisted, New Third Board/Beijing)
            mask_valid_name = ~df_subset['名称'].str.contains('ST|退')
            mask_valid_code = df_subset['代码'].str.match('^(00|30|60|68)')
            
            filtered_df = df_subset[mask_valid_name & mask_valid_code]
            
            # Log dropped count
            dropped_count = len(df_subset) - len(filtered_df)
            if dropped_count > 0:
                logger.info(f"Filtered out {dropped_count} stocks (ST/Delisted/New Third Board).")
            
            # Prepare data
            codes = filtered_df['代码'].tolist()
            names = filtered_df['名称'].tolist()
            
            # Handle codes that might not be in the fetched list (e.g. indices or new stocks)
            # Note: If they were filtered out by name/code logic above, we shouldn't add them back as 'Unknown'
            # We only add back 'Unknown' if they were VALID codes but just not found in akshare data (rare)
            
            found_codes = set(codes)
            # Only consider missing codes that WOULD have been valid
            potential_missing = target_codes - set(df_subset['代码'].tolist()) # Codes not in akshare at all
            
            valid_missing_codes = []
            for code in potential_missing:
                # Check if it looks like a valid code
                if code.startswith(('00', '30', '60', '68')):
                    valid_missing_codes.append(code)
            
            if valid_missing_codes:
                logger.warning(f"Could not find names for {len(valid_missing_codes)} valid codes: {valid_missing_codes[:10]}...")
                for code in valid_missing_codes:
                    codes.append(code)
                    names.append('Unknown') # Placeholder name

            DatabaseManager.execute_update("TRUNCATE TABLE stock_list")
            
            insert_query = "INSERT INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
            data = []
            for code, name in zip(codes, names):
                market = 1 if code.startswith('6') else 0 
                data.append((code, name, market))
                
            count = DatabaseManager.execute_update(insert_query, data, many=True)
            logger.info(f"Successfully updated stock list with {count} stocks.")
            return count
            
        except Exception as e:
            logger.error(f"Error updating stock list from secids: {e}")
            return 0


    @staticmethod
    def get_config():
        """
        Retrieves the current configuration from the database.
        """
        return BaseCurlService._get_config_base('eastmoney_call_auction')

    @staticmethod
    def test_config_fetch_data():
        """
        测试配置文件是否能正常抓取数据，主要用于后台管理页面的测试按钮
        """
        return BaseCurlService._fetch_data_base('eastmoney_call_auction')

    @staticmethod
    def fetch_call_auction_data(secids):
        """
        Fetches raw call auction data from Eastmoney for the given secids.
        """
        try:
            config = EastmoneyService.get_config()
            if not config:
                logger.error("No Eastmoney configuration found.")
                return []

            url = config.get('url')
            if not url:
                logger.error("Configuration URL is missing.")
                return []

            headers = config.get('headers', {})
            payload = config.get('body', {})
            
            if not isinstance(payload, dict):
                logger.error(f"Configuration body must be a JSON object, got {type(payload)}.")
                return []

            # Update payload
            # Create a copy to avoid modifying the cached config if get_config returns a reference
            payload = payload.copy()
            payload['secids'] = secids
            payload['pz'] = len(secids)
            payload['pn'] = 1
            
            logger.info(f"Fetching data using configured URL: {url}")
            logger.info(f"Payload overrides: pz={payload['pz']}, secids count={len(secids)}")

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json and 'data' in res_json and res_json['data']:
                    data_obj = res_json['data']
                    data_list = data_obj.get('diff', data_obj.get('full', []))
                    logger.info(f"Received {len(data_list) if data_list else 0} records from API.")
                    return data_list
                else:
                    logger.warning(f"No data found in response. Keys: {res_json.keys() if res_json else 'None'}.")
                    return []
            else:
                logger.error(f"Failed to fetch data: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching call auction data: {e}")
            return []

    @staticmethod
    def process_call_auction_data(raw_data_list):
        """
        Processes raw data list into standardized dictionaries.
        """
        processed_list = []
        if not raw_data_list:
            return processed_list
            
        def get_val(item, key, default=0):
            val = item.get(key, default)
            if val == '-': return default
            return val
            
        for item in raw_data_list:
            # f616: Auction Amount (bidding_amount)
            bidding_amount = get_val(item, 'f616', 0)
            # f618: Unmatched Amount (asking_amount)
            # Note: f618 is "Bid Unmatched Amount" (Limit Up Bid Amount)
            # We map it to asking_amount as per table schema availability: asking_amount = f618 + f616
            asking_amount = get_val(item, 'f618', 0) + bidding_amount

            processed = {
                'code': item.get('f12', ''),
                'name': item.get('f14', ''),
                'sector': item.get('f100', ''),
                'price': get_val(item, 'f2', 0),
                'bidding_percent': get_val(item, 'f615', 0),
                'bidding_amount': bidding_amount,
                'yidongleixing': get_val(item, 'f265', ''),
                'asking_amount': asking_amount
            }
            processed_list.append(processed)
            
        return processed_list

    @staticmethod
    def save_call_auction_data(data, date_str=None):
        try:
            if date_str:
                current_date = date_str
            else:
                current_date = datetime.date.today()
                
            now = datetime.datetime.now()
            current_time = now.time()
            current_time_str = now.strftime('%H:%M:%S')
            
            # Logic: 9:15 - 9:25 -> use actual time, else -> 9:25:00
            if '09:15:00' <= current_time_str <= '09:25:00':
                record_time = current_time_str
            else:
                # If we are strictly within market hours logic, we should probably stick to actual time
                # But if we are running catch-up or testing, we might want 09:25:00
                # Let's use 09:25:00 if outside the window, similar to fetch_eastmoney_call_auction logic
                record_time = '09:25:00'
            
            insert_query = """
            REPLACE INTO call_auction_data 
            (date, time, code, name, sector, price, bidding_percent, bidding_amount, asking_amount, yidongleixing)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Sort by bidding_amount
            data.sort(key=lambda x: float(x.get('bidding_amount', 0)), reverse=True)
            
            db_data = []
            
            for item in data:
                code = item.get('code', '')
                name = item.get('name', '')
                
                # Filter out ST, Delisted
                if name.startswith('ST') or name.startswith('*') or name.endswith('退'):
                    continue
                    
                sector = item.get('sector', '')
                price = item.get('price', 0)
                bidding_amount = item.get('bidding_amount', 0)
                
                if price == 0 and bidding_amount == 0:
                    continue
                
                bidding_percent = item.get('bidding_percent', 0)
                yidongleixing = item.get('yidongleixing', '')
                asking_amount = item.get('asking_amount', 0)
                
                db_data.append((current_date, record_time, code, name, sector, price, bidding_percent, bidding_amount, asking_amount, yidongleixing))

            # Sort by asking_amount (index -2) and take top 200
            db_data.sort(key=lambda x: x[-2], reverse=True)
            db_data = db_data[:200]
              
            count = DatabaseManager.execute_update(insert_query, db_data, many=True)
            logger.info(f"Saved {count} call auction records for date {current_date} time {record_time}.")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
