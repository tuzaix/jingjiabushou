import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.jiuyan_service import JiuyanService

class TestJiuyanService(unittest.TestCase):
    
    def test_parse_curl_command_simple(self):
        curl = "curl 'http://example.com' -H 'Content-Type: application/json' --data-raw '{\"foo\":\"bar\"}'"
        parsed = JiuyanService.parse_curl_command(curl)
        self.assertEqual(parsed['url'], 'http://example.com')
        self.assertEqual(parsed['method'], 'POST')
        self.assertEqual(parsed['headers']['Content-Type'], 'application/json')
        self.assertEqual(parsed['body'], {'foo': 'bar'})

    def test_parse_curl_command_multiline(self):
        curl = """curl 'http://example.com' \
  -H 'Accept: */*' \
  --data-raw '{"date":"2024-05-20"}'"""
        parsed = JiuyanService.parse_curl_command(curl)
        self.assertEqual(parsed['url'], 'http://example.com')
        self.assertEqual(parsed['body'], {'date': '2024-05-20'})

    def test_parse_curl_command_no_quotes(self):
        curl = "curl http://example.com"
        parsed = JiuyanService.parse_curl_command(curl)
        self.assertEqual(parsed['url'], 'http://example.com')
        self.assertEqual(parsed['method'], 'GET')

    @patch('services.jiuyan_service.DatabaseManager')
    @patch('services.jiuyan_service.requests')
    def test_fetch_data_test_mode(self, mock_requests, mock_db):
        # Mock DB config
        mock_db.execute_query.return_value = [{
            'url': 'http://api.jiuyan.com/list',
            'method': 'POST',
            'headers': '{"Content-Type": "application/json"}',
            'body': '{"date": "2024-05-20", "type": 1}'
        }]
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.request.return_value = mock_response
        
        # Test fetch_data without date (Test Mode)
        success, result = JiuyanService.fetch_data(date_str=None)
        
        self.assertTrue(success)
        
        # Verify request called with config body (no override)
        args, kwargs = mock_requests.request.call_args
        self.assertEqual(kwargs['json'], {"date": "2024-05-20", "type": 1})

    @patch('services.jiuyan_service.DatabaseManager')
    @patch('services.jiuyan_service.requests')
    def test_fetch_data_scheduler_mode(self, mock_requests, mock_db):
        # Mock DB config
        mock_db.execute_query.return_value = [{
            'url': 'http://api.jiuyan.com/list',
            'method': 'POST',
            'headers': '{"Content-Type": "application/json"}',
            'body': '{"date": "2024-05-20", "type": 1}'
        }]
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_requests.request.return_value = mock_response
        
        # Test fetch_data with date (Scheduler Mode)
        target_date = "2025-01-01"
        success, result = JiuyanService.fetch_data(date_str=target_date)
        
        self.assertTrue(success)
        
        # Verify request called with OVERRIDDEN date
        args, kwargs = mock_requests.request.call_args
        self.assertEqual(kwargs['json']['date'], target_date)
        self.assertEqual(kwargs['json']['type'], 1)

if __name__ == '__main__':
    unittest.main()
