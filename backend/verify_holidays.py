import akshare as ak
import datetime

def check_holidays():
    try:
        print("Fetching trading days...")
        df = ak.tool_trade_date_hist_sina()
        
        # Convert to set of strings
        trading_days = set(d.strftime('%Y-%m-%d') for d in df['trade_date'])
        
        # Check specific holidays (Non-trading days) for 2024
        check_dates = [
            '2024-02-09', # CNY Eve 2024 (Fri) - Trading?
            '2024-02-12', # CNY 2024 (Mon) - Holiday
            '2024-05-01', # Labor Day 2024 (Wed) - Holiday
            '2024-10-01', # National Day 2024 (Tue) - Holiday
            '2024-10-07', # National Day 2024 (Mon) - Holiday
            '2024-10-08', # Post-Holiday (Tue) - Trading
        ]
        
        print("\nChecking dates:")
        for date_str in check_dates:
            is_trading = date_str in trading_days
            print(f"{date_str}: {'Trading Day' if is_trading else 'Holiday/Weekend'}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_holidays()
