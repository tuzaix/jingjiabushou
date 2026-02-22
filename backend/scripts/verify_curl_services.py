import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add backend and project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock mysql.connector and DatabaseManager before importing services
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = MagicMock()

# Also mock utils.database if it fails to import due to mysql
mock_db_manager = MagicMock()
sys.modules['utils.database'] = MagicMock()
sys.modules['utils.database'].DatabaseManager = mock_db_manager

# Now import services
# Note: we need to reload or import carefully if they were already imported (not the case here)
from services.base_curl_service import BaseCurlService
from services.jiuyan_service import JiuyanService
from services.kaipanla_service import KaipanlaService
from services.eastmoney_service import EastmoneyService

class TestBaseCurlService(unittest.TestCase):
    def test_parse_curl_command_basic(self):
        cmd = "curl 'http://example.com'"
        result = BaseCurlService.parse_curl_command(cmd)
        self.assertEqual(result['url'], 'http://example.com')
        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['headers'], {})

    def test_parse_curl_command_complex(self):
        cmd = """curl 'http://api.example.com/v1/data' \
  -H 'User-Agent: Mozilla/5.0' \
  -H 'Content-Type: application/json' \
  --data-raw '{"key": "value"}' \
  --compressed"""
        result = BaseCurlService.parse_curl_command(cmd)
        self.assertEqual(result['url'], 'http://api.example.com/v1/data')
        self.assertEqual(result['method'], 'POST')
        self.assertEqual(result['headers']['User-Agent'], 'Mozilla/5.0')
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        # Check partial match or exact match depending on implementation
        # The implementation sets Accept-Encoding for --compressed
        self.assertIn('gzip', result['headers']['Accept-Encoding'])
        self.assertEqual(result['body'], {'key': 'value'})

    def test_parse_curl_cookies(self):
        cmd = "curl 'http://example.com' -b 'name=value' --cookie 'auth=123'"
        result = BaseCurlService.parse_curl_command(cmd)
        self.assertIn('name=value', result['headers']['Cookie'])
        self.assertIn('auth=123', result['headers']['Cookie'])

    def test_generate_curl_command(self):
        config = {
            'url': 'http://example.com',
            'method': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'body': {'foo': 'bar'}
        }
        cmd = BaseCurlService.generate_curl_command(config)
        self.assertIn("curl 'http://example.com'", cmd)
        self.assertIn("-X POST", cmd)
        self.assertIn("-H 'Content-Type: application/json'", cmd)
        self.assertIn("--data-raw '{\"foo\": \"bar\"}'", cmd)

class TestServices(unittest.TestCase):
    def setUp(self):
        # Reset mock calls
        mock_db_manager.execute_update.reset_mock()

    def test_jiuyan_update_config(self):
        cmd = "curl 'http://jiuyan.com'"
        # We need to ensure BaseCurlService uses the mocked DatabaseManager
        # Since we mocked sys.modules['utils.database'], it should work.
        # But BaseCurlService imports DatabaseManager from utils.database.
        # Let's verify if the import worked as expected.
        
        success, msg = JiuyanService.update_config(cmd)
        self.assertTrue(success)
        mock_db_manager.execute_update.assert_called()
        args = mock_db_manager.execute_update.call_args[0]
        self.assertIn('jiuyan_limit_up', args[1])

    def test_kaipanla_update_config(self):
        cmd = "curl 'http://kaipanla.com'"
        success, msg = KaipanlaService.update_config(cmd)
        self.assertTrue(success)
        args = mock_db_manager.execute_update.call_args[0]
        self.assertIn('kaipanla_call_auction', args[1])

        success, msg = KaipanlaService.update_volume_config(cmd)
        self.assertTrue(success)
        args = mock_db_manager.execute_update.call_args[0]
        self.assertIn('kaipanla_volume', args[1])

    @patch('services.eastmoney_service.EastmoneyService.update_stock_list_from_secids')
    def test_eastmoney_update_config(self, mock_update_stock):
        cmd = "curl 'http://eastmoney.com' --data-raw 'secids=1.600000'"
        success, msg = EastmoneyService.update_config(cmd)
        self.assertTrue(success)
        mock_update_stock.assert_called_with('1.600000')

if __name__ == '__main__':
    unittest.main()
