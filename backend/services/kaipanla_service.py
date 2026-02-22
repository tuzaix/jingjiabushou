import logging
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
