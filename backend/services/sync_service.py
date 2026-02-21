import requests
import time
import datetime
import akshare as ak
import pandas as pd
import logging
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-type': 'application/json',
    'Origin': 'https://vipmoney.eastmoney.com',
    'Referer': 'https://vipmoney.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

class SyncService:
    @staticmethod
    def get_all_stock_codes():
        try:
            stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            codes = stock_zh_a_spot_em_df['代码'].tolist()
            names = stock_zh_a_spot_em_df['名称'].tolist()
            
            DatabaseManager.execute_update("TRUNCATE TABLE stock_list")
            
            insert_query = "INSERT INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
            data = []
            for code, name in zip(codes, names):
                market = 1 if code.startswith('6') else 0 
                data.append((code, name, market))
                
            count = DatabaseManager.execute_update(insert_query, data, many=True)
            logger.info(f"Updated stock list with {count} stocks.")
            return data
        except Exception as e:
            logger.error(f"Error fetching stock list: {e}")
            return []

    @staticmethod
    def fetch_call_auction_data(stock_list_data=None):
        if not stock_list_data:
            try:
                stock_list_data = DatabaseManager.execute_query("SELECT code, name, market FROM stock_list", dictionary=False)
            except Exception as e:
                logger.error(f"Error loading stock list: {e}")
                return

        if not stock_list_data:
            logger.warning("No stocks found to fetch data for.")
            return

        logger.info(f"Total {len(stock_list_data)} stocks to fetch data for.")

        secids = []
        for row in stock_list_data:
            # If dictionary=False, row is tuple (code, name, market)
            if isinstance(row, (list, tuple)):
                code, name, market = row
            else:
                code = row['code']
                name = row['name']
                market = row['market']

            secid = f"{market}.{code}"
            secids.append(secid)

        if not secids:
            logger.warning("No secids generated.")
            return

        url = 'https://push2dycalc.eastmoney.com/api/qt/ulist.np/post'
        fields = "f2,f3,f4,f5,f6,f10,f12,f13,f14,f100,f265,f608,f615,f616,f617,f618,f619,f620,f629,f630,f637,f638,f639,f641"
        
        logger.info(f"Fetching data for {len(secids)} stocks in a single request.")

        payload = {
            "fltt": 2,
            "secids": secids,
            "fields": fields,
            "fid": "f615",
            "po": 1,
            "pn": 1,
            "pz": 200,
            "ut": "c92c50e6b0fab2c17cd5e276e9a79c42"
        }
        
        try:
            # Increase timeout for large payload
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                # logger.info(f"Response keys: {res_json.keys() if res_json else 'None'}")
                if res_json and 'data' in res_json and res_json['data']:
                    data_obj = res_json['data']
                    # Some endpoints return 'diff', others might return 'full' or other keys
                    data_list = data_obj.get('diff', data_obj.get('full', []))
                    
                    logger.info(f"Received {len(data_list) if data_list else 0} records from API.")
                    if data_list:
                        SyncService.save_call_auction_data(data_list)
                    else:
                        logger.warning(f"Data list is empty. Data keys: {data_obj.keys()}")
                else:
                    logger.warning(f"No data found in response. Keys: {res_json.keys() if res_json else 'None'}. Data: {str(res_json)[:200]}...")
            else:
                logger.error(f"Failed to fetch data: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching data: {e}")

    @staticmethod
    def save_call_auction_data(data):
        try:
            current_date = datetime.date.today()
            current_time = datetime.datetime.now().time()
            
            insert_query = """
            INSERT INTO call_auction_data 
            (date, time, code, name, price, change_percent, volume, amount, bid1_vol, ask1_vol, `rank`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            def get_val(item, key, default=0):
                val = item.get(key, default)
                if val == '-': return default
                return val

            data.sort(key=lambda x: float(get_val(x, 'f6', 0)), reverse=True)
            
            db_data = []
            for idx, item in enumerate(data):
                code = item.get('f12', '')
                name = item.get('f14', '')
                price = get_val(item, 'f2', 0)
                change_percent = get_val(item, 'f3', 0)
                volume = get_val(item, 'f5', 0)
                amount = get_val(item, 'f6', 0)
                bid1_vol = 0
                ask1_vol = 0
                rank = idx + 1
                
                db_data.append((current_date, current_time, code, name, price, change_percent, volume, amount, bid1_vol, ask1_vol, rank))
                
            count = DatabaseManager.execute_update(insert_query, db_data, many=True)
            logger.info(f"Saved {count} call auction records.")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    @staticmethod
    def fetch_yesterday_limit_up():
        try:
            today = datetime.date.today()
            df = ak.stock_zt_pool_previous_em(date=today.strftime("%Y%m%d"))
            
            DatabaseManager.execute_update("DELETE FROM yesterday_limit_up WHERE date = %s", (today,))
            
            insert_query = "INSERT INTO yesterday_limit_up (date, code, name, limit_up_type) VALUES (%s, %s, %s, %s)"
            data = []
            for _, row in df.iterrows():
                code = row['代码']
                name = row['名称']
                reason = row['涨停原因类别'] if '涨停原因类别' in row else ''
                data.append((today, code, name, reason))
                
            count = DatabaseManager.execute_update(insert_query, data, many=True)
            logger.info(f"Saved {count} yesterday limit up stocks.")
            
        except Exception as e:
            logger.error(f"Error fetching yesterday limit up: {e}")

    @staticmethod
    def import_yesterday_limit_up_excel(file_path, date_str=None):
        """
        Import yesterday limit up data from Excel file.
        Updates existing records for the same date and code, specifically updating consecutive_boards.
        """
        try:
            if not date_str:
                date_str = datetime.date.today().strftime('%Y-%m-%d')
            
            logger.info(f"Importing Excel: {file_path} for date {date_str}")
            df = pd.read_excel(file_path)
            
            # Identify columns dynamically
            code_col = None
            consecutive_days_col = None
            
            for col in df.columns:
                col_str = str(col)
                if '股票代码' in col_str:
                    code_col = col
                elif '连续涨停天数' in col_str:
                    consecutive_days_col = col
            
            if not code_col or not consecutive_days_col:
                logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
                return 0
            
            # Prepare update query
            update_query = """
                UPDATE yesterday_limit_up 
                SET consecutive_boards = %s
                WHERE date = %s AND code = %s
            """
            
            update_data = []
            
            for _, row in df.iterrows():
                raw_code = str(row[code_col])
                
                # Skip invalid rows (e.g., footer)
                if not raw_code or not raw_code[0].isdigit():
                    continue
                
                # Remove suffix like .SH or .SZ
                code = raw_code.split('.')[0]
                
                consecutive_boards = 0
                val = row[consecutive_days_col]
                if pd.notna(val):
                    try:
                        consecutive_boards = int(val)
                    except:
                        pass
                
                # Only update if we have valid data
                if code:
                    update_data.append((consecutive_boards, date_str, code))
            
            if update_data:
                count = DatabaseManager.execute_update(update_query, update_data, many=True)
                logger.info(f"Updated {count} yesterday limit up stocks with consecutive_boards from Excel for date {date_str}.")
                return count
            else:
                logger.warning("No valid data found to update.")
                return 0
            
        except Exception as e:
            logger.error(f"Error importing Excel: {e}")
            raise e
