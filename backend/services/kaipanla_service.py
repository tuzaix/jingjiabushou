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
        SELECT index_code, index_name, current_price, change_rate, volume, amount, time
        FROM index_data
        WHERE date = %s
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
            
            count = DatabaseManager.execute_update(insert_sql, values_to_insert, many=True)
            logger.info(f"Saved {count} index records.")
            return True, f"Saved {count} records"

        except Exception as e:
            logger.error(f"Error saving index data: {e}")
            return False, str(e)
