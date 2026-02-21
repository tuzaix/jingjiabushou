import json
import requests
import re
import datetime
import logging
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

class JiuyanService:
    @staticmethod
    def parse_curl_command(curl_command):
        """
        Parses a curl command to extract URL, headers, and data.
        """
        # Clean up newlines and backslashes
        curl_command = curl_command.replace('\\\n', ' ').replace('\\', '')
        
        # Extract URL
        url_match = re.search(r"curl\s+'([^']+)'", curl_command) or re.search(r'curl\s+"([^"]+)"', curl_command)
        url = url_match.group(1) if url_match else None
        
        if not url:
            # Try without quotes
            url_match = re.search(r"curl\s+(\S+)", curl_command)
            url = url_match.group(1) if url_match else None

        if not url:
            raise ValueError("Could not extract URL from curl command")

        # Extract headers
        headers = {}
        header_matches = re.findall(r"-H\s+'([^']+)'", curl_command) or re.findall(r'-H\s+"([^"]+)"', curl_command)
        for header in header_matches:
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()

        # Extract cookies
        cookie_match = re.search(r"-b\s+'([^']+)'", curl_command) or re.search(r'-b\s+"([^"]+)"', curl_command)
        if not cookie_match:
            cookie_match = re.search(r"--cookie\s+'([^']+)'", curl_command) or re.search(r'--cookie\s+"([^"]+)"', curl_command)
        
        if cookie_match:
            headers['Cookie'] = cookie_match.group(1)

        # Extract data
        data_match = re.search(r"--data-raw\s+'([^']+)'", curl_command) or re.search(r'--data-raw\s+"([^"]+)"', curl_command)
        data_str = data_match.group(1) if data_match else None
        
        try:
            data = json.loads(data_str) if data_str else {}
        except json.JSONDecodeError:
            data = {} 

        return {
            "url": url,
            "headers": headers,
            "body": data,
            "method": "POST"
        }

    @staticmethod
    def update_config(curl_command):
        try:
            parsed = JiuyanService.parse_curl_command(curl_command)
            
            # Save to DB
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
                json.dumps(parsed['body'])
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
                    row['headers'] = json.loads(row['headers'])
                if isinstance(row['body'], str):
                    row['body'] = json.loads(row['body'])
                
                # Reconstruct curl command
                row['curl'] = JiuyanService.generate_curl_command(row)
                return row
            return None
        except Exception as e:
            logger.error(f"Error getting Jiuyan config: {e}")
            return None

    @staticmethod
    def fetch_data(date_str=None):
        config = JiuyanService.get_config()
        if not config:
            return False, "未找到配置"
            
        if not date_str:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
            
        body = config['body']
        if isinstance(body, dict):
            body['date'] = date_str
        
        try:
            response = requests.request(
                method=config['method'],
                url=config['url'],
                headers=config['headers'],
                json=body,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                return False, f"HTTP Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            logger.error(f"Error fetching Jiuyan data: {e}")
            return False, str(e)
    
    @staticmethod
    def sync_data(date_str=None):
        success, result = JiuyanService.fetch_data(date_str)
        if not success:
            return False, result
            
        data_list = result.get('data', [])
        if not data_list:
             return True, "No data found"

        # Determine date
        if not date_str:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
            
        try:
            # Delete existing data for the date
            DatabaseManager.execute_update("DELETE FROM yesterday_limit_up WHERE date = %s", (date_str,))
            
            insert_query = """
                INSERT INTO yesterday_limit_up 
                (date, code, name, limit_up_type, consecutive_days, days_boards, limit_up_form, first_limit_up_time, last_limit_up_time, open_count, expound, consecutive_boards) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            stock_map = {}
            
            for item in data_list:
                category = item.get('name', '')
                stock_list = item.get('list', [])
                
                for stock in stock_list:
                    code_raw = stock.get('code', '')
                    # Strip prefix (e.g., sz001896 -> 001896)
                    code = re.sub(r'^\D+', '', code_raw)
                    if not code: continue
                    
                    if code not in stock_map:
                        name = stock.get('name', '')
                        article = stock.get('article', {}) or {}
                        action_info = article.get('action_info', {}) or {}
                        
                        # 解析连续天数和板数
                        num_str = action_info.get('num', '') # "3天3板"
                        # 解析涨停时间
                        limit_up_time = action_info.get('time', '') # "09:25:00"
                        
                        # 解析连续天数
                        try:
                            consecutive_days = int(action_info.get('day', 1))
                        except:
                            consecutive_days = 1
                        # 解析连续板数
                        try:
                            consecutive_boards = int(action_info.get('edition', 1))
                        except:
                            consecutive_boards = 1
                        # 几天几板
                        days_boards = num_str if num_str else '首板'

                        # 解析扩展信息
                        expound = action_info.get('expound', '')
                        
                        stock_map[code] = {
                            'date': date_str,
                            'code': code,
                            'name': name,
                            'categories': [category],
                            'consecutive_days': consecutive_days,
                            'days_boards': days_boards,
                            'limit_up_form': '',
                            'first_time': limit_up_time,
                            'last_time': limit_up_time,
                            'open_count': 0,
                            'expound': expound,
                            'consecutive_boards': consecutive_boards
                        }
                    else:
                        if category not in stock_map[code]['categories']:
                            stock_map[code]['categories'].append(category)
            
            final_data = []
            for code, info in stock_map.items():
                limit_up_type = '+'.join(info['categories'])
                # Truncate to 50 chars to fit DB column
                if len(limit_up_type) > 50:
                    limit_up_type = limit_up_type[:47] + "..."
                    
                final_data.append((
                    info['date'],
                    info['code'],
                    info['name'],
                    limit_up_type,
                    info['consecutive_days'],
                    info['days_boards'],
                    info['limit_up_form'],
                    info['first_time'],
                    info['last_time'],
                    info['open_count'],
                    info['expound'],
                    info['consecutive_boards']
                ))
                
            count = DatabaseManager.execute_update(insert_query, final_data, many=True)
            return True, f"Synced {count} records for date {date_str}"
            
        except Exception as e:
            logger.error(f"Error syncing Jiuyan data: {e}")
            return False, str(e)
