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
        try:
            config = JiuyanService.get_config()
            if not config:
                return False, "未找到配置信息，请先配置 cURL"

            url = config['url']
            method = config['method']
            headers = config['headers'].copy() if config['headers'] else {}
            body = config['body']
            
            if date_str:
                body['date'] = date_str
            
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
                'timeout': 30
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
    def test_config_fetch_data():
        """
        测试配置文件是否能正常抓取数据，主要用于后台管理页面的测试按钮
        """
        return JiuyanService.fetch_data()

    @staticmethod
    def fetch_limit_up_data(date_str=None):
        '''
        获取指定日期的涨停数据
        '''
        return JiuyanService.fetch_data(date_str)

    @staticmethod
    def process_limit_up_data(data, date_str):
        '''
        处理返回的数据与数据库表字段对应关系
        '''
        processed_data = []
        for row in data.get("data", []):
            # 排除掉简图的部分
            if not row.get("action_field_id"): 
                continue
            
            # 板块概念
            limit_up_type = row.get("name", "")

            if limit_up_type.startswith("ST"): # 过滤掉ST股票
                continue 
            # 板块内的股票列表
            stocks = row.get("list", [])
            for stock in stocks:
                # code只获取数字部分
                tmp_code = stock.get("code", "")
                code = re.sub(r'\D', '', tmp_code)

                name = stock.get("name", "")
                if not code or not name:
                    continue
                action_info = stock.get("article", {}).get("action_info", {})

                try:
                    consecutive_days = int(action_info.get("day", 0))
                except:
                    consecutive_days = 1
                try:
                    edition = int(action_info.get("edition", 0))
                except:
                    edition = 1
                consecutive_boards = edition
                days_boards = action_info.get("num", "")
                if not days_boards:
                    days_boards = "首板"
                first_limit_up_time = action_info.get("time", "")
                last_limit_up_time = first_limit_up_time
                expound = action_info.get("expound", "")
            
                processed_data.append((
                    date_str, code, name, limit_up_type, consecutive_days, edition, consecutive_boards, days_boards, first_limit_up_time, last_limit_up_time, expound
                ))
        import pprint
        pprint.pprint(processed_data)
        return processed_data

    @staticmethod
    def save_limit_up_data(data, date_str=None):
        '''
        保存涨停数据到表中
        '''
        if not date_str:
            return 
        # 清理{date_str}的旧数据
        DatabaseManager.execute_update("DELETE FROM yesterday_limit_up WHERE date = %s", (date_str,))
        
        # Insert with extended fields
        insert_query = """
            INSERT INTO yesterday_limit_up 
            (date, code, name, limit_up_type, consecutive_days, edition, consecutive_boards, days_boards, first_limit_up_time, last_limit_up_time, expound) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        count = DatabaseManager.execute_update(insert_query, data, many=True)
        logger.info(f"Saved {count} yesterday limit up stocks from Jiuyan for date {date_str}.")