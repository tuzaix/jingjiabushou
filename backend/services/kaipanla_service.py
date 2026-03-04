import logging
import json
import datetime
from utils.database import DatabaseManager
from .base_curl_service import BaseCurlService

# Use a specific logger for this service
logger = logging.getLogger('kaipanla_service')

class KaipanlaService(BaseCurlService):
    @staticmethod
    def update_config(curl_command):
        """
        Parses the curl command and saves the call auction configuration to the database.
        """
        success, msg, _ = BaseCurlService._update_config_base(curl_command, 'kaipanla_call_auction')
        return success, msg

    @staticmethod
    def update_volume_config(curl_command):
        """
        Parses the curl command and saves the volume configuration to the database.
        """
        success, msg, _ = BaseCurlService._update_config_base(curl_command, 'kaipanla_volume')
        return success, msg

    @staticmethod
    def update_index_config(curl_command):
        """
        Parses the curl command and saves the index configuration to the database.
        """
        success, msg, _ = BaseCurlService._update_config_base(curl_command, 'kaipanla_index')
        return success, msg

    @staticmethod
    def update_stat_config(curl_command):
        """
        Parses the curl command and saves the statistics configuration to the database.
        """
        success, msg, _ = BaseCurlService._update_config_base(curl_command, 'kaipanla_stat')
        return success, msg

    @staticmethod
    def get_config():
        """
        Retrieves the call auction configuration from the database.
        """
        return BaseCurlService._get_config_base('kaipanla_call_auction')

    @staticmethod
    def get_volume_config():
        """
        Retrieves the volume configuration from the database.
        """
        return BaseCurlService._get_config_base('kaipanla_volume')

    @staticmethod
    def get_index_config():
        """
        Retrieves the index configuration from the database.
        """
        return BaseCurlService._get_config_base('kaipanla_index')

    @staticmethod
    def get_stat_config():
        """
        Retrieves the statistics configuration from the database.
        """
        return BaseCurlService._get_config_base('kaipanla_stat')

    @staticmethod
    def fetch_data():
        """
        Fetches call auction data using the stored configuration.
        """
        return BaseCurlService._fetch_data_base('kaipanla_call_auction')

    @staticmethod
    def fetch_volume_data():
        """
        Fetches volume data using the stored configuration.
        """
        return BaseCurlService._fetch_data_base('kaipanla_volume')

    @staticmethod
    def get_latest_index_data(date_str=None):
        """
        Retrieves the latest index data for the specified date.
        If no date is specified, uses today's date.
        """
        if not date_str:
            date_str = datetime.date.today().strftime('%Y-%m-%d')
            
        query = """
        SELECT index_code, index_name, increase_amount, increase_rate, index_volume
        FROM index_data
        WHERE date = %s
        AND index_code != 'SZ399001'
        AND time = (
            SELECT MAX(time)
            FROM index_data
            WHERE date = %s
        )
        """
        
        try:
            results = DatabaseManager.execute_query(query, (date_str, date_str))
            return results
        except Exception as e:
            logger.error(f"Error retrieving index data: {e}")
            return []

    @staticmethod
    def fetch_index_data():
        """
        Fetches index data using the stored configuration.
        """
        return BaseCurlService._fetch_data_base('kaipanla_index')

    @staticmethod
    def fetch_stat_data():
        """
        Fetches statistics data using the stored configuration.
        """
        return BaseCurlService._fetch_data_base('kaipanla_stat')

    @staticmethod
    def save_index_data(date_str=None):
        """
        Fetches index data and saves it to the database.
        """
        success, result = KaipanlaService.fetch_index_data()
        if not success:
            logger.error(f"Failed to fetch index data: {result}")
            return False, result

        try:
            # Result could be a dict (parsed JSON) or string
            parsed = None
            if isinstance(result, (dict, list)):
                parsed = result
            else:
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse response as JSON: {result[:100]}...")
                    return False, "Invalid JSON response"

            data_list = parsed.get('StockList', [])
            
            if not data_list:
                logger.warning("No index data found in response.")
                return False, "No data found"

            current_time = datetime.datetime.now()
        
            # 如果current_time小于9:15则time_str等于09:15:00, 如果大于15点，则time_str=15:00:00，否则就是用当前时间
            if current_time < datetime.datetime.now().replace(hour=9, minute=15, second=0):
                time_str = '09:15:00'
            elif current_time > datetime.datetime.now().replace(hour=15, minute=0, second=0):
                time_str = '15:00:00'
            else:
                time_str = current_time.strftime('%H:%M:%S')

                # {
                #     "Icon": 0,
                #     "Level": 0,
                #     "StockID": "SH000001",
                #     "gang": "",
                #     "increase_amount": -51.95,
                #     "increase_rate": "-1.26%",
                #     "last_px": 4082.07,
                #     "prod_name": "上证指数",
                #     "state": "86",
                #     "turnover": "846808337462"
                # },

            values_to_insert = []
            for item in data_list:
                index_code = item.get('StockID')   
                index_name = item.get('prod_name')
                increase_amount = float(item.get('increase_amount'))
                increase_rate = float(item.get('increase_rate').strip('%'))
                index_volume = float(item.get('last_px'))
               
                values_to_insert.append((
                    date_str, time_str, str(index_code), str(index_name), 
                    increase_amount, increase_rate, index_volume
                ))

            if not values_to_insert:
                logger.warning("No valid index items found (missing code/name).")
                return False, "No valid items found"

            insert_sql = """
            REPLACE INTO index_data 
            (date, time, index_code, index_name, increase_amount, increase_rate, index_volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            DatabaseManager.execute_batch(insert_sql, values_to_insert)
            logger.info(f"Successfully saved {len(values_to_insert)} index data items for {date_str} at {time_str}")
            return True, f"Saved {len(values_to_insert)} items"

        except Exception as e:
            logger.error(f"Error saving index data: {e}")
            return False, str(e)

    @staticmethod
    def save_stat_data(date_str=None):
        """
        Fetches statistics data and saves it to the database.
        """
        success, result = KaipanlaService.fetch_stat_data()
        if not success:
            logger.error(f"Failed to fetch statistics data: {result}")
            return False, result

        try:
            # Result could be a dict (parsed JSON) or string
            data = None
            if isinstance(result, (dict, list)):
                data = result
            else:
                try:
                    data = json.loads(result)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse response as JSON: {result[:100]}...")
                    return False, "Invalid JSON response"

            info = data.get('list', {})
            if not info:
                logger.warning(f"No 'list' field in data for {date_str}, skipping save.")
                return False, "No list field"

            if not date_str:
                date_str = datetime.date.today().strftime('%Y-%m-%d')

            current_time = datetime.datetime.now()
            # 如果current_time小于9:15则time_str等于09:15:00, 如果大于15点，则time_str=15:00:00，否则就是用当前时间
            if current_time < datetime.datetime.now().replace(hour=9, minute=15, second=0):
                time_str = '09:15:00'
            elif current_time > datetime.datetime.now().replace(hour=15, minute=0, second=0):
                time_str = '15:00:00'
            else:
                time_str = current_time.strftime('%H:%M:%S')

            # Extract fields (reference from fetch_limit_up_stats.py)
            limit_up_count = int(info.get('ZT', 0))
            limit_down_count = int(info.get('DT', 0))
            non_st_limit_up_count = int(info.get('ZTJS', 0))
            non_st_limit_down_count = int(info.get('DTJS', 0))
            st_limit_up_count = int(info.get('STZT', 0))
            st_limit_down_count = int(info.get('STDT', 0))
            rise_count = int(info.get('SZJS', 0))
            fall_count = int(info.get('XDJS', 0))
            flat_count = int(info.get('0', 0))
            market_sentiment = info.get('sign', '')
            shanghai_turnover = int(info.get('szln', 0))
            total_turnover = int(info.get('qscln', 0))
            rise_fall_distribution = info.get('ZSZDFB', '')

            query = """
            REPLACE INTO market_sentiment_stats 
            (date, time, limit_up_count, limit_down_count, non_st_limit_up_count, non_st_limit_down_count, 
             st_limit_up_count, st_limit_down_count, rise_count, fall_count, flat_count, 
             market_sentiment, shanghai_turnover, total_turnover, rise_fall_distribution, raw_response_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                date_str, time_str, limit_up_count, limit_down_count, non_st_limit_up_count, non_st_limit_down_count,
                st_limit_up_count, st_limit_down_count, rise_count, fall_count, flat_count, 
                market_sentiment, shanghai_turnover, total_turnover, rise_fall_distribution, json.dumps(data)
            )
            
            DatabaseManager.execute_update(query, params)
            logger.info(f"Successfully saved market stats for date: {date_str} time: {time_str}")
            return True, f"Saved stats for {date_str} {time_str}"

        except Exception as e:
            logger.error(f"Error saving statistics data: {e}")
            return False, str(e)
