import sys
import os
import datetime
import json
import time

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.eastmoney_service import EastmoneyService

def fetch_and_print_auction_data():
    print(f"[{datetime.datetime.now()}] Starting fetch from Eastmoney...")
    
    # Fetch data
    success, result = EastmoneyService.fetch_call_auction_data()
    
    if not success:
        print(f"Error: {result}")
        return

    # Parse data
    # Eastmoney usually returns data in result['data']['diff']
    data_list = []
    if isinstance(result, dict):
        if 'data' in result and result['data']:
            inner_data = result['data']
            if isinstance(inner_data, dict):
                if 'diff' in inner_data:
                    data_list = inner_data['diff']
                    # Check if diff is list or dict (sometimes dict with index keys)
                    if isinstance(data_list, dict):
                        data_list = list(data_list.values())
                elif 'list' in inner_data:
                    data_list = inner_data['list']
                elif 'full' in inner_data:
                    data_list = inner_data['full']
                else:
                    # Fallback: maybe the dict itself is the list of values
                    data_list = list(inner_data.values()) if isinstance(inner_data, dict) else []
    
    if not data_list:
        print("No data found in response or unknown format.")
        return

    print(f"Fetched {len(data_list)} records.")
    
    # Determine time to use
    now = datetime.datetime.now()
    current_time_str = now.strftime('%H:%M:%S')
    current_date_str = now.strftime('%Y-%m-%d')
    
    # Logic: 9:15 - 9:25 -> use actual time, else -> 9:25:00
    if '09:15:00' <= current_time_str <= '09:25:00':
        record_time = current_time_str
        print(f"Current time {current_time_str} is within 09:15-09:25. Using actual time.")
    else:
        record_time = '09:25:00'
        print(f"Current time {current_time_str} is outside 09:15-09:25. Using default time: {record_time}")
        
    # Process and Print
    # Mapping Eastmoney fields (standard assumption):
    # f12: code, f14: name, f2: price, f3: change_pct, f6: amount, f5: volume
    
    print("-" * 80)
    print(f"{'Code':<10} {'Name':<15} {'Price':<10} {'Change%':<10} {'Amount':<15} {'Time'}")
    print("-" * 80)
    
    count = 0
    for item in data_list:
        if not isinstance(item, dict):
            continue
            
        code = str(item.get('f12', 'N/A'))
        name = item.get('f14', 'N/A')
        
        # Handle numeric values safely
        try:
            price = float(item.get('f2', 0))
            change_pct = float(item.get('f3', 0))
            amount = float(item.get('f6', 0))
        except (ValueError, TypeError):
            price = 0
            change_pct = 0
            amount = 0
            
        # Filter: Only print if we have valid code (optional)
        if code == 'N/A':
            continue
            
        # Print first 20 records
        if count < 20:
            print(f"{code:<10} {name:<15} {price:<10.2f} {change_pct:<10.2f} {amount:<15.2f} {record_time}")
            count += 1
        
    print("-" * 80)
    print(f"Total processed: {len(data_list)}")
    print("Test run completed. Data NOT saved to DB.")

if __name__ == "__main__":
    fetch_and_print_auction_data()
