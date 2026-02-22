import json
import requests
import re
import datetime
import logging
import shlex
from utils.database import DatabaseManager

from .base_curl_service import BaseCurlService

logger = logging.getLogger(__name__)

class JiuyanService(BaseCurlService):
    @staticmethod
    def update_config(curl_command):
        success, msg, _ = BaseCurlService._update_config_base(curl_command, 'jiuyan_limit_up')
        return success, msg

    @staticmethod
    def get_config():
        return BaseCurlService._get_config_base('jiuyan_limit_up')

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
                if not first_limit_up_time:
                    continue
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