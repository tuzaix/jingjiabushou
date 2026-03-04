import requests
import datetime
from utils.locks import akshare_lock
# import akshare as ak  <-- Moved inside method to avoid crash
import pandas as pd
import logging
from utils.database import DatabaseManager
from .eastmoney_service import EastmoneyService
from .jiuyan_service import JiuyanService
import re

logger = logging.getLogger(__name__)

class SyncService:
    @staticmethod
    def update_all_stock_codes():
        """
        根据管理后台配置中的“东方财富实时竞价”配置，解析 body 字段中的 secids 列表来更新股票列表。
        """
        try:
            config = EastmoneyService.get_config()
            if not config:
                logger.error("No Eastmoney configuration found.")
                return []
            
            body_obj = config.get('body')
            secids = None
            
            if isinstance(body_obj, dict):
                secids = body_obj.get('secids')
            elif isinstance(body_obj, str):
                if 'secids=' in body_obj:
                    from urllib.parse import parse_qs
                    parsed = parse_qs(body_obj)
                    if 'secids' in parsed:
                        secids = parsed['secids'][0]
                elif ',' in body_obj:
                    # Possibly just a comma-separated list
                    secids = body_obj
            
            if not secids:
                logger.error("No secids found in Eastmoney configuration body.")
                return []
                
            if isinstance(secids, str):
                secids = secids.split(',')
            
            # Prepare data for stock_list
            data = []
            seen_codes = set()
            for secid in secids:
                # secid format: "0.000001" or "1.600000"
                parts = secid.strip().split('.')
                if len(parts) == 2:
                    _, stock_code = parts
                    if stock_code not in seen_codes:
                        # market = 1 if code starts with 6 (Shanghai), else 0
                        market = 1 if stock_code.startswith('6') else 0
                        # 使用 stock_code 作为 name (忽略股票名字)
                        data.append((stock_code, stock_code, market))
                        seen_codes.add(stock_code)
            
            if not data:
                logger.error("No valid stock codes parsed from secids.")
                return []
            
            # Update database
            DatabaseManager.execute_update("TRUNCATE TABLE stock_list")
            insert_query = "INSERT INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
            count = DatabaseManager.execute_update(insert_query, data, many=True)
            
            logger.info(f"Updated stock list with {count} stocks from configuration secids.")
            return data
            
        except Exception as e:
            logger.error(f"Error updating stock codes from configuration: {e}")
            return []

    @staticmethod
    def sync_call_auction_data(stock_list_data=None, date_str=None):
        '''
        同步东方财富的竞价数据到数据库
        '''
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

        # Fetch using EastmoneyService
        raw_data = EastmoneyService.fetch_call_auction_data(secids)
        
        if raw_data:
            # Process/Normalize data
            processed_data = EastmoneyService.process_call_auction_data(raw_data)
            # Save data
            EastmoneyService.save_call_auction_data(processed_data, date_str)
        else:
            logger.warning("No data fetched from EastmoneyService.")

    @staticmethod
    def sync_yesterday_limit_up(date_str=None):
        '''
        同步昨天的涨停数据到数据库
        '''
        try:
            if not date_str:
                date_str = datetime.date.today().strftime('%Y-%m-%d')
            
            logger.info(f"Starting sync_yesterday_limit_up for {date_str} using JiuyanService...")
            success, jiuyan_data = JiuyanService.fetch_limit_up_data(date_str)

            # 获取数据状态验证
            if not success:
                logger.error(f"Failed to fetch limit up data for {date_str} from JiuyanService")
                return
            
            # Process data
            processed_data = JiuyanService.process_limit_up_data(jiuyan_data, date_str)
            
            # Save processed data
            JiuyanService.save_limit_up_data(processed_data, date_str)
            
            logger.info(f"Successfully synced yesterday limit up data for {date_str}")
            
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
                elif '首次涨停时间' in col_str:
                    first_limit_up_time_col = col
                elif "最终涨停时间" in col_str:
                    last_limit_up_time_col = col
            
            if not code_col or not consecutive_days_col or not first_limit_up_time_col or not last_limit_up_time_col:
                logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
                return 0
            
            # Prepare update query
            update_query = """
                UPDATE yesterday_limit_up 
                SET consecutive_boards = %s,
                first_limit_up_time = %s,
                last_limit_up_time = %s
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
                first_limit_up_time = ""
                val = row[first_limit_up_time_col]
                if pd.notna(val):
                    first_limit_up_time = val
                
                last_limit_up_time = ""
                val = row[last_limit_up_time_col]
                if pd.notna(val):
                    last_limit_up_time = val
                
                # Only update if we have valid data
                if code:
                    update_data.append((consecutive_boards, first_limit_up_time, last_limit_up_time, date_str, code))   
            
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
