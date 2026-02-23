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
        if not date_str:
            logger.error("Date string is required")
            return False, "Date string is required"
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
            # 如果时间超过了15:00，则默认时间为：15:00:00
            if current_time.hour >= 15:
                time_str = '15:00:00'
            elif current_time.hour < 9: # 小于9:15:00，则默认为9:15:00
                time_str = '09:15:00'
            else:
                time_str = current_time.strftime('%H:%M:%S')

            values_to_insert = []
            for item in data_list:
                index_code = item.get('StockID')
                index_name = item.get('prod_name')
                increase_rate = float(item.get('increase_rate').strip('%'))
                index_volume = float(item.get('last_px'))
                increase_amount = float(item.get('increase_amount'))
               
                values_to_insert.append((
                    date_str, time_str, str(index_code), str(index_name), 
                    increase_rate, index_volume, increase_amount
                ))

            if not values_to_insert:
                logger.warning("No valid index items found (missing code/name).")
                return False, "No valid items found"

            insert_sql = """
            INSERT INTO index_data 
            (date, time, index_code, index_name, increase_rate, index_volume, increase_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            count = DatabaseManager.execute_update(insert_sql, values_to_insert, many=True)
            logger.info(f"Saved {count} index records.")
            return True, f"Saved {count} records"

        except Exception as e:
            logger.error(f"Error saving index data: {e}")
            return False, str(e)
