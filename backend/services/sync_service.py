import requests
import datetime
import akshare as ak
import pandas as pd
import logging
from utils.database import DatabaseManager
from .eastmoney_service import EastmoneyService
from .jiuyan_service import JiuyanService
import re

logger = logging.getLogger(__name__)

class SyncService:
    @staticmethod
    def get_all_stock_codes():
        try:
            stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            
            # Filter out ST, Delisted, and New Third Board/Beijing stocks
            # 1. Remove ST and Delisted based on name
            mask_valid_name = ~stock_zh_a_spot_em_df['名称'].str.contains('ST|退')
            
            # 2. Keep only Main Board (00, 60), ChiNext (30), STAR Market (68)
            # Exclude Beijing (8, 4, 92) and B-shares (900, 200)
            mask_valid_code = stock_zh_a_spot_em_df['代码'].str.match('^(00|30|60|68)')
            
            filtered_df = stock_zh_a_spot_em_df[mask_valid_name & mask_valid_code]
            
            codes = filtered_df['代码'].tolist()
            names = filtered_df['名称'].tolist()
            
            DatabaseManager.execute_update("TRUNCATE TABLE stock_list")
            
            insert_query = "INSERT INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
            data = []
            for code, name in zip(codes, names):
                market = 1 if code.startswith('6') else 0 
                data.append((code, name, market))
                
            count = DatabaseManager.execute_update(insert_query, data, many=True)
            logger.info(f"Updated stock list with {count} stocks (Filtered ST, Delisted, and non-A-share).")
            return data
        except Exception as e:
            logger.error(f"Error fetching stock list: {e}")
            return []

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
    def fetch_yesterday_limit_up(date_str=None):
        try:
            if not date_str:
                date_str = datetime.date.today().strftime('%Y-%m-%d')
            
            logger.info(f"Starting fetch_yesterday_limit_up for {date_str} using JiuyanService...")
            success, msg = JiuyanService.sync_data(date_str)
            
            data_source = "jiuyan"
            
            jiuyan_data = []
            if success:
                jiuyan_data = DatabaseManager.execute_query(
                    "SELECT * FROM yesterday_limit_up WHERE date = %s", 
                    (date_str,), 
                    dictionary=True
                )
            
            if not success or not jiuyan_data:
                logger.warning(f"Jiuyan sync failed or no data ({msg}), falling back to AkShare.")
                data_source = "akshare"
            
            if data_source == "jiuyan":
                # Process Jiuyan Data
                DatabaseManager.execute_update("DELETE FROM yesterday_limit_up WHERE date = %s", (date_str,))
                
                # Insert with extended fields
                insert_query = """
                    INSERT INTO yesterday_limit_up 
                    (date, code, name, limit_up_type, consecutive_days, consecutive_boards, first_limit_up_time) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                data_to_insert = []
                for row in jiuyan_data:
                    code = row['code']
                    name = row['name']
                    reason_info = row['reason_info'] # e.g. "华为概念"
                    plate_name = row['plate_name']
                    
                    # Parse consecutive days
                    consecutive = 1
                    if reason_type == '首板':
                        consecutive = 1
                    elif reason_type and '连板' in reason_type:
                        try:
                            match = re.search(r'(\d+)', reason_type)
                            if match:
                                consecutive = int(match.group(1))
                        except:
                            pass
                    
                    # Construct limit_up_type (reason)
                    limit_up_type_val = reason_info if reason_info else ''
                    if plate_name and plate_name not in limit_up_type_val:
                         limit_up_type_val = f"{plate_name} {limit_up_type_val}".strip()
                    
                    # Jiuyan doesn't provide time, set to None
                    first_limit_up_time = None
                    
                    data_to_insert.append((
                        date_str, code, name, limit_up_type_val, consecutive, consecutive, first_limit_up_time
                    ))
                
                count = DatabaseManager.execute_update(insert_query, data_to_insert, many=True)
                logger.info(f"Saved {count} yesterday limit up stocks from Jiuyan for date {date_str}.")
                
            else:
                # AkShare Fallback
                date_param = date_str.replace('-', '')
                df = ak.stock_zt_pool_previous_em(date=date_param)
                
                DatabaseManager.execute_update("DELETE FROM yesterday_limit_up WHERE date = %s", (date_str,))
                
                insert_query = "INSERT INTO yesterday_limit_up (date, code, name, limit_up_type) VALUES (%s, %s, %s, %s)"
                data = []
                for _, row in df.iterrows():
                    code = row['代码']
                    name = row['名称']
                    reason = row['涨停原因类别'] if '涨停原因类别' in row else ''
                    data.append((date_str, code, name, reason))
                
                count = DatabaseManager.execute_update(insert_query, data, many=True)
                logger.info(f"Saved {count} yesterday limit up stocks (AkShare) for date {date_str}.")
            
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
