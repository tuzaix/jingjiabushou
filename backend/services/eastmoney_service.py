import json
import requests
import re
import logging
import shlex
import datetime
from urllib.parse import urlparse

# Use a specific logger for this service
logger = logging.getLogger('eastmoney_service')

class EastmoneyService:
    @staticmethod
    def parse_curl_command(curl_command):
        """
        Parses a curl command to extract URL, headers, and data.
        Handles both single and double quotes, and various curl formats.
        """
        try:
            # Basic cleanup: remove newlines and trailing backslashes
            clean_cmd = curl_command.replace('\\\n', ' ').replace('\n', ' ')
            
            # Use shlex to split the command properly handling quotes
            try:
                tokens = shlex.split(clean_cmd)
            except ValueError as e:
                # Fallback for simple splitting if shlex fails (e.g. unclosed quotes)
                logger.warning(f"shlex split failed: {e}, falling back to basic split")
                tokens = clean_cmd.split()

            if not tokens or tokens[0] != 'curl':
                raise ValueError("Not a valid curl command")

            url = None
            method = 'GET' # Default to GET
            headers = {}
            data = None
            cookies = {}

            i = 1
            while i < len(tokens):
                token = tokens[i]
                
                if token.startswith('http'):
                    url = token
                elif token in ('-H', '--header'):
                    if i + 1 < len(tokens):
                        header_str = tokens[i+1]
                        if ':' in header_str:
                            key, value = header_str.split(':', 1)
                            headers[key.strip()] = value.strip()
                        i += 1
                elif token in ('-X', '--request'):
                    if i + 1 < len(tokens):
                        method = tokens[i+1].upper()
                        i += 1
                elif token in ('-d', '--data', '--data-raw', '--data-binary', '--data-ascii'):
                    if i + 1 < len(tokens):
                        data = tokens[i+1]
                        method = 'POST' # Implies POST
                        i += 1
                elif token in ('-b', '--cookie'):
                     if i + 1 < len(tokens):
                        cookie_str = tokens[i+1]
                        # Cookie header usually handled in headers, but curl -b adds to Cookie header
                        # We can just add it to headers['Cookie']
                        if 'Cookie' in headers:
                             headers['Cookie'] += '; ' + cookie_str
                        else:
                             headers['Cookie'] = cookie_str
                        i += 1
                elif token == '--compressed':
                    headers['Accept-Encoding'] = 'gzip, deflate, br'
                
                i += 1

            if not url:
                raise ValueError("Could not find URL in curl command")

            # Parse JSON data if possible
            parsed_data = {}
            if data:
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError:
                    parsed_data = data # Keep as string if not JSON

            return {
                "url": url,
                "headers": headers,
                "body": parsed_data,
                "method": method
            }

        except Exception as e:
            logger.error(f"Error parsing curl command: {e}")
            raise ValueError(f"Failed to parse curl command: {str(e)}")

    @staticmethod
    def update_config(curl_command):
        """
        Parses the curl command and saves the configuration to the database.
        """
        try:
            # Parse the command
            config = EastmoneyService.parse_curl_command(curl_command)
            
            # Database update logic
            # Assuming we use a similar structure to JiuyanService, storing in 'api_configs' table
            # We need to import DatabaseManager here to avoid circular imports if possible, 
            # or ensure it's available.
            from utils.database import DatabaseManager
            
            # Use a specific name for Eastmoney config
            config_name = 'eastmoney_call_auction' 
            
            # Serialize headers and body
            headers_json = json.dumps(config['headers'])
            body_json = json.dumps(config['body']) if isinstance(config['body'], (dict, list)) else config['body']
            
            # Check if config exists to decide INSERT or UPDATE (or use ON DUPLICATE KEY UPDATE)
            # Assuming api_configs table has a unique key on 'name'
            
            query = """
                INSERT INTO api_configs (name, url, method, headers, body) 
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                url = VALUES(url), 
                method = VALUES(method), 
                headers = VALUES(headers), 
                body = VALUES(body)
            """
            
            params = (
                config_name,
                config['url'],
                config['method'],
                headers_json,
                body_json
            )
            
            DatabaseManager.execute_update(query, params)
            
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
                    # Local import to avoid circular dependency
                    from .sync_service import SyncService
                    SyncService.update_stock_list_from_secids(secids)
                    
            except Exception as e:
                logger.error(f"Error auto-updating stock_list from secids: {e}")
            
            return True, "配置更新成功"

        except Exception as e:
            logger.error(f"Error updating Eastmoney config: {e}")
            return False, f"配置更新失败: {str(e)}"

    @staticmethod
    def generate_curl_command(config):
        if not config:
            return ""
        
        url = config.get('url')
        method = config.get('method', 'GET')
        headers = config.get('headers', {})
        body = config.get('body')
        
        parts = [f"curl '{url}'"]
        
        if method != 'GET':
            parts.append(f"-X {method}")
            
        for key, value in headers.items():
            # Escape single quotes in header values
            safe_value = str(value).replace("'", "'\\''")
            parts.append(f"-H '{key}: {safe_value}'")
            
        if body:
            if isinstance(body, (dict, list)):
                body_str = json.dumps(body)
            else:
                body_str = str(body)
            # Escape single quotes in body
            safe_body = body_str.replace("'", "'\\''")
            parts.append(f"--data-raw '{safe_body}'")
            
        return " \\\n  ".join(parts)

    @staticmethod
    def get_config():
        """
        Retrieves the current configuration from the database.
        """
        try:
            from utils.database import DatabaseManager
            
            query = "SELECT url, method, headers, body FROM api_configs WHERE name = 'eastmoney_call_auction'"
            result = DatabaseManager.execute_query(query, dictionary=True)
            
            if result:
                row = result[0]
                
                # Parse JSON fields
                try:
                    if isinstance(row['headers'], str):
                        row['headers'] = json.loads(row['headers'])
                    if isinstance(row['body'], str):
                        try:
                            row['body'] = json.loads(row['body'])
                        except:
                            pass # Keep as string if not valid JSON
                except Exception as e:
                    logger.warning(f"Error parsing stored JSON config: {e}")

                # Reconstruct curl command
                row['curl'] = EastmoneyService.generate_curl_command(row)
                return row
            
            return None

        except Exception as e:
            logger.error(f"Error getting Eastmoney config: {e}")
            return None

    @staticmethod
    def test_config_fetch_data():
        """
        测试配置文件是否能正常抓取数据，主要用于后台管理页面的测试按钮
        """
        try:
            config = EastmoneyService.get_config()
            if not config:
                return False, "未找到配置信息，请先配置 cURL"

            url = config['url']
            method = config['method']
            headers = config['headers']
            body = config['body']
            
            # Prepare request arguments
            kwargs = {
                'headers': headers,
                'timeout': 10
            }
            
            if body:
                if isinstance(body, dict) or isinstance(body, list):
                    kwargs['json'] = body
                else:
                    kwargs['data'] = body

            # Execute request
            response = requests.request(method, url, **kwargs)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Basic validation of response structure could go here
                    return True, data
                except json.JSONDecodeError:
                    return False, f"响应不是有效的 JSON: {response.text[:100]}"
            else:
                return False, f"请求失败，状态码: {response.status_code}, 内容: {response.text[:100]}"

        except Exception as e:
            logger.error(f"Error fetching Eastmoney data: {e}")
            return False, f"抓取异常: {str(e)}"

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
            from utils.database import DatabaseManager

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
