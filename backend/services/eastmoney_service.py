import json
import requests
import re
import logging
import shlex
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
    def fetch_data():
        """
        Fetches data using the stored configuration.
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
