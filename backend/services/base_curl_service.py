import json
import logging
import shlex
import requests
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class BaseCurlService:
    """
    Base service for handling cURL command parsing, configuration management, 
    and generic data fetching.
    """

    @staticmethod
    def parse_curl_command(curl_command):
        """
        Parses a curl command to extract URL, headers, and data.
        Handles both single and double quotes, and various curl formats.
        """
        try:
            # Basic cleanup: remove newlines and trailing backslashes
            # Handle both \n and \r\n, and line continuation backslashes
            clean_cmd = curl_command.replace('\\\n', ' ').replace('\\\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
            
            # Use shlex to split the command properly handling quotes
            try:
                tokens = shlex.split(clean_cmd)
            except ValueError as e:
                # Fallback for simple splitting if shlex fails (e.g. unclosed quotes)
                logger.warning(f"shlex split failed: {e}, falling back to basic split")
                tokens = clean_cmd.split()

            if not tokens or tokens[0] != 'curl':
                # Sometimes user might paste starting with 'curl ' or just the args if they are careless,
                # but we strictly expect 'curl' as first token for now.
                # However, if the first token is a URL, it might be a valid curl command without 'curl' in some contexts?
                # No, standard is `curl url`.
                if tokens[0].startswith('http'):
                     # Be lenient if they forgot 'curl'
                     tokens.insert(0, 'curl')
                elif tokens[0] != 'curl':
                     raise ValueError("Not a valid curl command")

            url = None
            method = 'GET' # Default to GET
            headers = {}
            data = None
            
            i = 1
            while i < len(tokens):
                token = tokens[i]
                
                if token.startswith('http') and not url:
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
                # Handle standalone URL that might appear later
                elif not url and not token.startswith('-'):
                    url = token
                
                i += 1

            if not url:
                raise ValueError("Could not find URL in curl command")

            # Parse JSON data if possible
            parsed_data = None
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
    def generate_curl_command(config):
        """
        Reconstructs a cURL command string from the configuration dictionary.
        """
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
    def _update_config_base(curl_command, config_name):
        """
        Generic method to update config by name in the database.
        """
        try:
            # Parse the command
            config = BaseCurlService.parse_curl_command(curl_command)
            
            # Serialize headers and body
            headers_json = json.dumps(config['headers'])
            body_json = json.dumps(config['body']) if isinstance(config['body'], (dict, list)) else config['body']
            
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
            
            return True, "配置更新成功", config
        except Exception as e:
            logger.error(f"Error updating config ({config_name}): {e}")
            return False, f"配置更新失败: {str(e)}", None

    @staticmethod
    def _get_config_base(config_name):
        """
        Generic method to retrieve config by name from the database.
        """
        try:
            query = "SELECT url, method, headers, body FROM api_configs WHERE name = %s"
            result = DatabaseManager.execute_query(query, (config_name,), dictionary=True)
            
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
                    logger.warning(f"Error parsing stored JSON config ({config_name}): {e}")

                # Reconstruct curl command
                row['curl'] = BaseCurlService.generate_curl_command(row)
                return row
            
            return None

        except Exception as e:
            logger.error(f"Error getting config ({config_name}): {e}")
            return None

    @staticmethod
    def _fetch_data_base(config_name, timeout=10):
        """
        Generic method to fetch data using stored config.
        """
        try:
            config = BaseCurlService._get_config_base(config_name)
            if not config:
                return False, "未找到配置信息，请先配置 cURL"

            url = config['url']
            method = config['method']
            headers = config['headers']
            body = config['body']
            
            # Prepare request arguments
            kwargs = {
                'headers': headers,
                'timeout': timeout
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
                    return True, data
                except json.JSONDecodeError:
                    return False, f"响应不是有效的 JSON: {response.text[:100]}"
            else:
                return False, f"请求失败，状态码: {response.status_code}, 内容: {response.text[:100]}"

        except Exception as e:
            logger.error(f"Error fetching data ({config_name}): {e}")
            return False, f"抓取异常: {str(e)}"
