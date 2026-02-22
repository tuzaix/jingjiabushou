import json
import requests
import re
import datetime
import logging
import shlex
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class JiuyanService:
    @staticmethod
    def parse_curl_command(curl_command):
        """
        Parses a curl command to extract URL, headers, and data using shlex for better shell tokenization.
        """
        try:
            # Clean up line continuations just in case, though shlex handles them if they are proper
            # But users might paste with newlines that shlex might complain about if not escaped
            # So let's join lines first if they end with \
            cleaned_command = curl_command.replace('\\\n', ' ').replace('\\\r\n', ' ')
            # Also remove newlines that are not escaped? No, shlex.split handles strings with newlines if quoted.
            # But if the user pasted a multiline command without backslashes, shlex might fail or treat them as separate commands.
            # Let's just replace all newlines with spaces to be safe, assuming it's one command.
            cleaned_command = cleaned_command.replace('\n', ' ').replace('\r', ' ')
            
            tokens = shlex.split(cleaned_command)
        except Exception as e:
            logger.error(f"Failed to parse curl command with shlex: {e}")
            # Fallback to regex or just fail
            raise ValueError(f"Invalid curl command format: {e}")

        url = None
        method = "GET"
        headers = {}
        data_str = None
        
        # Iterate tokens
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token == 'curl':
                i += 1
                continue
                
            if token.startswith('http'):
                url = token
                i += 1
                continue
                
            if token in ('-X', '--request'):
                if i + 1 < len(tokens):
                    method = tokens[i+1]
                    i += 2
                else:
                    i += 1
                continue
                
            if token in ('-H', '--header'):
                if i + 1 < len(tokens):
                    header_str = tokens[i+1]
                    if ':' in header_str:
                        key, value = header_str.split(':', 1)
                        headers[key.strip()] = value.strip()
                    i += 2
                else:
                    i += 1
                continue
                
            if token in ('-b', '--cookie'):
                if i + 1 < len(tokens):
                    cookie_str = tokens[i+1]
                    # If Cookie header already exists, append to it (though usually -b is preferred or they are separate)
                    # But requests usually takes a dict for cookies or we can put it in headers['Cookie']
                    # Let's put it in headers['Cookie'] for simplicity as that's what curl does effectively
                    if 'Cookie' in headers:
                         headers['Cookie'] += f"; {cookie_str}"
                    else:
                         headers['Cookie'] = cookie_str
                    i += 2
                else:
                    i += 1
                continue
                
            if token in ('-d', '--data', '--data-raw', '--data-binary', '--data-ascii'):
                if i + 1 < len(tokens):
                    data_str = tokens[i+1]
                    method = "POST" # Implied POST
                    i += 2
                else:
                    i += 1
                continue
                
            if token in ('--compressed',):
                # headers['Accept-Encoding'] = 'gzip, deflate, br' # requests handles this automatically usually
                i += 1
                continue
                
            # Skip unknown flags
            if token.startswith('-'):
                i += 1
                if i < len(tokens) and not tokens[i].startswith('-'):
                    i += 1
                continue
                
            # If we found a standalone string and don't have a URL yet, it might be the URL
            if not url and not token.startswith('-'):
                url = token
                i += 1
                continue
                
            i += 1

        if not url:
            raise ValueError("Could not extract URL from curl command")

        # Parse body if present
        body = None
        if data_str:
            try:
                body = json.loads(data_str)
            except json.JSONDecodeError:
                body = data_str

        return {
            "url": url,
            "headers": headers,
            "body": body,
            "method": method
        }

    @staticmethod
    def update_config(curl_command):
        try:
            parsed = JiuyanService.parse_curl_command(curl_command)
            
            # Save to DB
            # We store body as JSON string if it's a dict, or raw string otherwise
            body_to_store = json.dumps(parsed['body']) if isinstance(parsed['body'], (dict, list)) else parsed['body']
            
            query = """
                INSERT INTO api_configs (name, url, method, headers, body) 
                VALUES (%s, %s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE 
                url = new.url, 
                method = new.method, 
                headers = new.headers, 
                body = new.body
            """
            DatabaseManager.execute_update(query, (
                'jiuyan_limit_up', 
                parsed['url'], 
                parsed['method'], 
                json.dumps(parsed['headers']), 
                body_to_store
            ))
            return True, "配置更新成功"
        except Exception as e:
            logger.error(f"Error updating Jiuyan config: {e}")
            return False, str(e)

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
        try:
            result = DatabaseManager.execute_query(
                "SELECT url, method, headers, body FROM api_configs WHERE name = 'jiuyan_limit_up'", 
                dictionary=True
            )
            if result:
                row = result[0]
                if isinstance(row['headers'], str):
                    try:
                        row['headers'] = json.loads(row['headers'])
                    except:
                        row['headers'] = {}
                
                # Body might be a JSON string representing a dict, or just a string
                # If it was stored as JSON string of a dict, we load it.
                if row['body']:
                    try:
                        # Try to parse it as JSON
                        row['body'] = json.loads(row['body'])
                    except:
                        # If fail, keep as is
                        pass
                
                # Reconstruct curl command for display
                row['curl'] = JiuyanService.generate_curl_command(row)
                return row
            return None
        except Exception as e:
            logger.error(f"Error getting Jiuyan config: {e}")
            return None

    @staticmethod
    def fetch_data(date_str=None):
        """
        Fetch data from Jiuyan.
        If date_str is provided, it attempts to inject it into the request body (if body is a dict).
        If date_str is None (e.g. testing), it uses the body as configured.
        """
        config = JiuyanService.get_config()
        print(config)
        if not config:
            return False, "未找到配置"
            
        body = config['body']
        
        if date_str:
            # If date is provided (Scheduler mode), override it
            if isinstance(body, dict):
                body['date'] = date_str
            else:
                logger.warning("date_str provided but body is not a dict, cannot inject date.")
        
        # Remove Content-Length header as requests will recalculate it
        if 'Content-Length' in config['headers']:
            del config['headers']['Content-Length']
            
        # Also remove Host header as it might cause issues if IP changed
        if 'Host' in config['headers']:
             del config['headers']['Host']

        try:
            logger.info(f"Fetching Jiuyan data. URL: {config['url']}, Method: {config['method']}")
            
            response = requests.request(
                method=config['method'],
                url=config['url'],
                headers=config['headers'],
                json=body if isinstance(body, (dict, list)) else None,
                data=body if not isinstance(body, (dict, list)) else None,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, data
                except json.JSONDecodeError:
                    return False, f"Invalid JSON response: {response.text[:200]}"
            else:
                return False, f"HTTP Error: {response.status_code} - {response.text[:200]}"
                
        except Exception as e:
            logger.error(f"Error fetching Jiuyan data: {e}")
            return False, str(e)
    
    @staticmethod
    def sync_data(date_str=None):
        """
        Fetch and sync data to DB.
        """
        # Determine date if not provided (for sync logic, we need to know what date we are syncing)
        target_date_str = date_str
        if not target_date_str:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            target_date_str = yesterday.strftime('%Y-%m-%d')
            
        # Call fetch_data with the determined date (so it gets injected)
        success, result = JiuyanService.fetch_data(target_date_str)
        
        print(result)

        if not success:
            return False, result
            
        data_list = result.get('data', [])
        if not data_list:
             return True, "No data found"

        try:
            # Delete existing data for the date
            DatabaseManager.execute_update(
                "DELETE FROM yesterday_limit_up WHERE date = %s", 
                (target_date_str,)
            )
            
            # Insert new data
            count = 0
            query = """
                INSERT INTO yesterday_limit_up 
                (date, code, name, limit_up_type, consecutive_days, edition, consecutive_boards, days_boards, first_limit_up_time, expound)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = []
            for item in data_list:
                # Adjust field names based on actual API response structure
                # This is a guess based on common structures, might need adjustment
                print(item)
                code = item.get('code')
                name = item.get('name')
                reason_type = item.get('reason_type', '') # e.g. 首板, 2连板
                reason_info = item.get('reason_info', '') # e.g. 华为概念
                limit_up_type = item.get('limit_up_type', '') # e.g. 自然涨停
                consecutive_days = item.get('consecutive_days', 0)
                edition = item.get('edition', '')
                consecutive_boards = item.get('consecutive_boards', 0)
                days_boards = item.get('days_boards', 0)
                first_limit_up_time = item.get('first_limit_up_time', '')
                expound = item.get('expound', '')
                
                if code:
                    params.append((target_date_str, code, name, limit_up_type, consecutive_days, edition, consecutive_boards, days_boards, first_limit_up_time, expound))
                    count += 1
            
            if params:
                DatabaseManager.execute_batch(query, params)
                
            return True, f"Successfully synced {count} records for {target_date_str}"
            
        except Exception as e:
            logger.error(f"Error syncing Jiuyan data: {e}")
            return False, str(e)

    @staticmethod
    def test_config_fetch_data():
        """
        测试配置文件是否能正常抓取数据，主要用于后台管理页面的测试按钮
        """
        try:
            config = JiuyanService.get_config()
            from pprint import pprint
            pprint(config)
            if not config:
                return False, "未找到配置信息，请先配置 cURL"

            url = config['url']
            method = config['method']
            headers = config['headers'].copy() if config['headers'] else {}
            
            # Clean header values: remove newlines/carriage returns that might have been preserved by shlex
            # and ensure they are single lines as required by HTTP/1.1
            for key, value in headers.items():
                if isinstance(value, str):
                    headers[key] = value.replace('\n', ' ').replace('\r', ' ').strip()
            
            # Remove Content-Length as requests will recalculate it
            if 'Content-Length' in headers:
                del headers['Content-Length']

            # Prepare request arguments
            kwargs = {
                'headers': headers,
                'timeout': 10
            }
            
            body = config['body']
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
                    # If response is not JSON, return text but mark as potentially successful if that's expected?
                    # Usually APIs return JSON. If not, maybe return text preview.
                    # But for now, let's assume JSON is required.
                    # Actually, some APIs might return text.
                    return False, f"响应不是有效的 JSON: {response.text[:100]}"
            else:
                return False, f"请求失败，状态码: {response.status_code}, 内容: {response.text[:100]}"

        except Exception as e:
            logger.error(f"Error fetching Jiuyan data: {e}")
            return False, f"抓取异常: {str(e)}"

    @staticmethod
    def fetch_limit_up_data(secids):
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
    def process_limit_up_data(raw_data_list):
        pass

    @staticmethod
    def save_limit_up_data(data, date_str=None):
        pass
