import datetime
from utils.database import DatabaseManager
from utils.cache import CacheManager
import logging

logger = logging.getLogger(__name__)

class MarketService:
    """
    Service for querying market data (Call Auction, Limit Up, etc.)
    """

    @staticmethod
    def get_top_n_call_auction(limit=50, date_str=None, time_str=None):
        """
        Get Top N call auction data with amounts at 9:15, 9:20, and 9:25.
        Also attempts to join with yesterday_limit_up to get consecutive days.
        """
        if not date_str:
            date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        cache_key = f"top_n:{date_str}:{time_str}:{limit}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # 1. Get Top N stocks based on 9:25 amount
            # Time window for 9:25
            query_top_n = """
            SELECT code, name, sector, 
                   bidding_percent as change_percent, 
                   asking_amount as amount, 
                   time, date
            FROM call_auction_data 
            WHERE date = %s AND time >= '09:25:00' AND time < '09:26:00'
            ORDER BY asking_amount DESC LIMIT %s
            """
            
            top_n_data = DatabaseManager.execute_query(query_top_n, (date_str, limit), dictionary=True)
            
            if not top_n_data:
                return []
                
            codes = [row['code'] for row in top_n_data]
            if not codes:
                return []
                
            # 2. Fetch data for these codes at 9:20 and 9:15
            format_strings = ','.join(['%s'] * len(codes))
            query_history = f"""
            SELECT code, time, asking_amount as amount
            FROM call_auction_data
            WHERE date = %s 
              AND code IN ({format_strings})
              AND (
                  (time >= '09:20:00' AND time < '09:21:00') OR
                  (time >= '09:15:00' AND time < '09:16:00')
              )
            """
            params_history = [date_str] + codes
            history_data = DatabaseManager.execute_query(query_history, params_history, dictionary=True)
            
            # Map history data by code and time window
            history_map = {}
            for row in history_data:
                code = row['code']
                time_val = str(row['time'])
                if code not in history_map:
                    history_map[code] = {}
                
                # Check time window
                if '09:15' in time_val:
                    history_map[code]['915'] = row['amount']
                elif '09:20' in time_val:
                    history_map[code]['920'] = row['amount']
            
            # 3. Get consecutive days from yesterday_limit_up (from previous trading day)
            # Find previous trading day
            prev_date_str = None
            trading_days = MarketService.get_trading_days()
            if trading_days and date_str in trading_days:
                idx = trading_days.index(date_str)
                if idx > 0:
                    prev_date_str = trading_days[idx - 1]
            
            limit_up_map = {}
            if prev_date_str:
                query_limit_up = f"""
                SELECT code, consecutive_days
                FROM yesterday_limit_up
                WHERE date = %s AND code IN ({format_strings})
                """
                params_limit = [prev_date_str] + codes
                limit_up_data = DatabaseManager.execute_query(query_limit_up, params_limit, dictionary=True)
                for row in limit_up_data:
                    limit_up_map[row['code']] = row['consecutive_days']
            
            # 4. Merge all data
            result = []
            for row in top_n_data:
                code = row['code']
                hist = history_map.get(code, {})
                
                # Format time
                time_val = row['time']
                if isinstance(time_val, datetime.timedelta):
                    time_val = str(time_val)
                elif isinstance(time_val, datetime.time):
                    time_val = time_val.strftime('%H:%M:%S')
                
                # Format date
                date_val = row['date']
                if isinstance(date_val, datetime.date):
                    date_val = date_val.strftime('%Y-%m-%d')
                
                item = {
                    'code': code,
                    'name': row['name'],
                    'sector': row['sector'],
                    'change_percent': row['change_percent'],
                    'amount': row['amount'], # This is 9:25 amount
                    'amount_920': hist.get('920', 0),
                    'amount_915': hist.get('915', 0),
                    'consecutive_days': limit_up_map.get(code),
                    'time': time_val,
                    'date': date_val,
                    'rank': row.get('rank', 0) # Though we didn't set rank in query
                }
                result.append(item)
                
            # Cache
            CacheManager.set(cache_key, result, ttl=5)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching top N data: {e}")
            return []

    @staticmethod
    def get_ranking_by_time_range(start_time, end_time, limit=50, date_str=None):
        """
        Get ranking of stocks based on amount within a specific time range.
        """
        if not date_str:
            date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        cache_key = f"ranking:{date_str}:{start_time}:{end_time}:{limit}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        try:
            query = """
            SELECT code, name, sector, 
                   bidding_percent as change_percent, 
                   asking_amount as amount, 
                   time
            FROM call_auction_data 
            WHERE date = %s AND time >= %s AND time < %s
            ORDER BY asking_amount DESC LIMIT %s
            """
            
            data = DatabaseManager.execute_query(query, (date_str, start_time, end_time, limit), dictionary=True)
            
            # Format results
            result = []
            for row in data:
                # Format time
                time_val = row['time']
                if isinstance(time_val, datetime.timedelta):
                    time_val = str(time_val)
                elif isinstance(time_val, datetime.time):
                    time_val = time_val.strftime('%H:%M:%S')
                
                result.append({
                    'code': row['code'],
                    'name': row['name'],
                    'sector': row['sector'],
                    'amount': row['amount'],
                    'change_percent': row['change_percent'],
                    'time': time_val
                })
            
            CacheManager.set(cache_key, result, ttl=5)
            return result
        except Exception as e:
            logger.error(f"Error fetching ranking for {start_time}-{end_time}: {e}")
            return []

    @staticmethod
    def get_yesterday_limit_up(date_str=None):
        """
        Get yesterday's limit up stocks.
        Filters:
        - consecutive_days >= 2 (2连板及以上)
        - Exclude ST stocks (name not containing 'ST')
        """
        if not date_str:
            date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        cache_key = f"yesterday_limit_up:{date_str}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        query = """
        SELECT * FROM yesterday_limit_up 
        WHERE date = %s 
          AND consecutive_days >= 2 
          AND name NOT LIKE '%%ST%%'
        """
        try:
            data = DatabaseManager.execute_query(query, (date_str,), dictionary=True)
            
            for row in data:
                if isinstance(row['date'], datetime.date):
                    row['date'] = row['date'].strftime('%Y-%m-%d')
            
            CacheManager.set(cache_key, data, ttl=60) # Cache for 1 minute
            return data
        except Exception as e:
            logger.error(f"Error fetching yesterday limit up: {e}")
            return []

    @staticmethod
    def get_yesterday_limit_up_performance(target_date_str=None):
        """
        Get stocks that were limit up on the previous trading day (relative to target_date_str),
        and join with their call auction performance at 09:25 on target_date_str.
        """
        if not target_date_str:
            target_date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        # 1. Find previous trading day
        trading_days = MarketService.get_trading_days()
        if not trading_days:
             # Fallback: simple date subtraction (not ideal but better than crash)
             # This happens if akshare fails.
             # We should probably return empty or try a simple calc
             prev_date_str = (datetime.datetime.strptime(target_date_str, '%Y-%m-%d') - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            try:
                # trading_days is a list of strings 'YYYY-MM-DD', sorted
                if target_date_str in trading_days:
                    idx = trading_days.index(target_date_str)
                    if idx > 0:
                        prev_date_str = trading_days[idx - 1]
                    else:
                        return [] # target_date is the first available day, no previous day
                else:
                    # target_date might be a weekend/holiday selected by user?
                    # or future date.
                    # Find the closest previous trading day to be the "prev_date"?
                    # No, if target_date is not a trading day, usually we don't have auction data for it.
                    # But maybe user selected a weekend and wants to see Friday's performance?
                    # The requirement says "Yesterday Limit Up Performance" on "Home Page".
                    # Usually "Home Page" shows data for "Today" (or selected date).
                    # If I select Saturday, I probably want to see Friday's data.
                    # But here we assume target_date is a valid trading day where we expect auction data.
                    # If target_date is not a trading day, return empty.
                    return []
            except ValueError:
                return []

        cache_key = f"yesterday_limit_up_perf:{target_date_str}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data

        # 2. Get limit up stocks from prev_date
        # Filter: consecutive_days >= 2, no ST
        # Also select first_limit_up_time for sorting
        query_limit_up = """
        SELECT code, name, consecutive_days, limit_up_type, first_limit_up_time 
        FROM yesterday_limit_up 
        WHERE date = %s 
          AND consecutive_days >= 2 
          AND name NOT LIKE '%%ST%%'
        """
        
        try:
            limit_up_stocks = DatabaseManager.execute_query(query_limit_up, (prev_date_str,), dictionary=True)
            if not limit_up_stocks:
                return []
                
            codes = [s['code'] for s in limit_up_stocks]
            if not codes:
                return []
            
            # 3. Get auction data for these stocks on target_date at 09:25
            # We use IN clause
            format_strings = ','.join(['%s'] * len(codes))
            # Updated to match new schema: bidding_percent, asking_amount
            # Mapping: bidding_percent -> change_percent, asking_amount -> amount
            query_auction = f"""
            SELECT code, bidding_percent as change_percent, asking_amount as amount 
            FROM call_auction_data 
            WHERE date = %s 
              AND time >= '09:25:00' AND time < '09:26:00'
              AND code IN ({format_strings})
            """
            
            params = [target_date_str] + codes
            auction_data = DatabaseManager.execute_query(query_auction, params, dictionary=True)
            
            # Create a map for easy lookup
            auction_map = {row['code']: row for row in auction_data}
            
            # 4. Merge data
            result = []
            for stock in limit_up_stocks:
                code = stock['code']
                auction = auction_map.get(code, {})
                
                # Format time string if needed
                first_time = stock.get('first_limit_up_time')
                if isinstance(first_time, datetime.timedelta):
                    first_time = str(first_time)
                elif isinstance(first_time, datetime.time):
                    first_time = first_time.strftime('%H:%M:%S')
                
                item = {
                    'code': code,
                    'name': stock['name'],
                    'consecutive_days': stock['consecutive_days'],
                    'sector': stock['limit_up_type'], # Using limit_up_type as sector
                    'first_limit_up_time': first_time,
                    'change_percent': auction.get('change_percent'),
                    'amount': auction.get('amount')
                }
                result.append(item)
            
            # Sort by consecutive_days desc, then first_limit_up_time asc
            # Note: first_limit_up_time might be None, handle that
            result.sort(key=lambda x: (
                -x['consecutive_days'], 
                x['first_limit_up_time'] if x['first_limit_up_time'] else '23:59:59'
            ))
            
            CacheManager.set(cache_key, result, ttl=10) # Short cache as auction data might update if today
            return result
            
        except Exception as e:
            logger.error(f"Error fetching yesterday limit up performance: {e}")
            return []

    @staticmethod
    def get_limit_up_at_925(date_str=None):
        """
        Get stocks with >= 9.9% change at 09:25:00.
        """
        if not date_str:
            date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        cache_key = f"limit_up_925:{date_str}"
        cached_data = CacheManager.get(cache_key)
        # if cached_data:
        #     return cached_data

        # We look for records at 09:25:xx with change_percent meeting limit up criteria
        # Main board: >= 9.8%, ChiNext/STAR (300/688): >= 19.8%, ST: >= 4.9%, BJ (8/4/9): >= 29.8%
        query = """
        SELECT code, name, sector,
               bidding_percent as change_percent, 
               asking_amount as amount, 
               0 as price, 
               time, date
        FROM call_auction_data 
        WHERE date = %s 
          AND time >= '09:25:00' AND time < '09:26:00' 
          AND (
            (name LIKE '%%ST%%' AND bidding_percent >= 4.9)
            OR
            (name NOT LIKE '%%ST%%' AND (
                ((code LIKE '30%%' OR code LIKE '688%%') AND bidding_percent >= 19.8)
                OR
                ((code LIKE '8%%' OR code LIKE '43%%' OR code LIKE '92%%') AND bidding_percent >= 29.8)
                OR
                (code NOT LIKE '30%%' AND code NOT LIKE '688%%' AND code NOT LIKE '8%%' AND code NOT LIKE '43%%' AND code NOT LIKE '92%%' AND bidding_percent >= 9.8)
            ))
          )
        ORDER BY asking_amount DESC
        """
        try:
            data = DatabaseManager.execute_query(query, (date_str,), dictionary=True)
            
            for row in data:
                if isinstance(row['date'], datetime.date):
                    row['date'] = row['date'].strftime('%Y-%m-%d')
                if isinstance(row['time'], datetime.timedelta):
                    row['time'] = str(row['time'])
                elif isinstance(row['time'], datetime.time):
                    row['time'] = row['time'].strftime('%H:%M:%S')
            
            CacheManager.set(cache_key, data, ttl=5)
            return data
        except Exception as e:
            logger.error(f"Error fetching limit up at 9:25: {e}")
            return []

    @staticmethod
    def get_trading_days(start_date=None, end_date=None):
        """
        Get list of trading days from Sina via akshare.
        """
        import akshare as ak
        
        today = datetime.date.today()
        if not start_date:
            # Default to past 3 years to cover more history
            start_date = today - datetime.timedelta(days=365 * 3)
        if not end_date:
            # Future 60 days
            end_date = today + datetime.timedelta(days=60)
            
        cache_key = f"trading_days:{start_date}:{end_date}"
        cached_data = CacheManager.get(cache_key)
        if cached_data:
            return cached_data
            
        try:
            df = ak.tool_trade_date_hist_sina()
            # Convert 'trade_date' to datetime.date if not already
            # Usually it returns a column of dates
            
            # Filter range
            mask = (df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)
            filtered = df.loc[mask]
            
            date_list = [d.strftime('%Y-%m-%d') for d in filtered['trade_date']]
            
            # Cache for 6 hours
            CacheManager.set(cache_key, date_list, ttl=21600)
            return date_list
        except Exception as e:
            logger.error(f"Error fetching trading days: {e}")
            return []
