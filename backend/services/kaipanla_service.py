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
    def save_index_data():
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

            data_list = []
            
            # 1. Check for nested structure: data -> StockList (from user example)
            if isinstance(parsed, dict) and 'data' in parsed and isinstance(parsed['data'], dict) and 'StockList' in parsed['data']:
                data_list = parsed['data']['StockList']
            # 2. Check for simple list wrapper: data -> list
            elif isinstance(parsed, dict) and 'data' in parsed and isinstance(parsed['data'], list):
                data_list = parsed['data']
            # 3. Check for direct list
            elif isinstance(parsed, list):
                data_list = parsed
            # 4. Check for 'list' key
            elif isinstance(parsed, dict) and 'list' in parsed and isinstance(parsed['list'], list):
                data_list = parsed['list']
            # 5. Fallback: treat whole object as item if dict
            elif isinstance(parsed, dict):
                data_list = [parsed]

            if not data_list:
                logger.warning("No index data found in response.")
                return False, "No data found"

            current_time = datetime.datetime.now()
            date_str = current_time.strftime('%Y-%m-%d')
            time_str = current_time.strftime('%H:%M:%S')

            values_to_insert = []
            for item in data_list:
                # Flexible key extraction
                # Priority: User provided keys (StockID, prod_name) -> Standard keys
                code = item.get('StockID') or item.get('IndexCode') or item.get('code') or item.get('Code') or item.get('symbol') or item.get('Symbol')
                name = item.get('prod_name') or item.get('IndexName') or item.get('name') or item.get('Name')
                
                if not code or not name:
                    # Skip items without code/name
                    continue
                
                # Price: last_px, CurrentPrice, price
                price = item.get('last_px') or item.get('CurrentPrice') or item.get('price') or item.get('current') or 0
                
                # Rate: increase_rate, ChangeRate, rate (handle %)
                rate_raw = item.get('increase_rate') or item.get('ChangeRate') or item.get('rate') or item.get('zf') or 0
                if isinstance(rate_raw, str) and '%' in rate_raw:
                    try:
                        rate = float(rate_raw.replace('%', ''))
                    except:
                        rate = 0
                else:
                    try:
                        rate = float(rate_raw)
                    except:
                        rate = 0
                
                # Volume: Volume, volume, vol
                # Note: In user example, 'turnover' is likely amount, not volume (shares). 
                # If volume is not provided, default to 0.
                vol = item.get('Volume') or item.get('volume') or item.get('vol') or 0
                
                # Amount: turnover, Amount, amount
                amt_raw = item.get('turnover') or item.get('Amount') or item.get('amount') or item.get('amt') or 0
                try:
                    amt = float(amt_raw)
                except:
                    amt = 0
                
                # Raw JSON for debugging/future use
                raw_json = json.dumps(item, ensure_ascii=False)
                
                values_to_insert.append((
                    date_str, time_str, str(code), str(name), 
                    price, rate, vol, amt, raw_json
                ))

            if not values_to_insert:
                logger.warning("No valid index items found (missing code/name).")
                return False, "No valid items found"

            insert_sql = """
            INSERT INTO index_data 
            (date, time, index_code, index_name, current_price, change_rate, volume, amount, raw_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            count = DatabaseManager.execute_update(insert_sql, values_to_insert, many=True)
            logger.info(f"Saved {count} index records.")
            return True, f"Saved {count} records"

        except Exception as e:
            logger.error(f"Error saving index data: {e}")
            return False, str(e)
