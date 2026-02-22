
import akshare as ak
import pandas as pd

def check_stock_data():
    print("Fetching stock data...")
    df = ak.stock_zh_a_spot_em()
    print("Columns:", df.columns)
    
    # Check for ST stocks
    st_stocks = df[df['名称'].str.contains('ST')]
    print(f"Found {len(st_stocks)} ST stocks. Examples:")
    print(st_stocks[['代码', '名称']].head())
    
    # Check for Beijing stocks (starts with 8 or 4)
    bj_stocks = df[df['代码'].str.match('^(8|4)')]
    print(f"Found {len(bj_stocks)} Beijing/NEEQ stocks. Examples:")
    print(bj_stocks[['代码', '名称']].head())
    
    # Check for delisted (contains '退')
    delisted = df[df['名称'].str.contains('退')]
    print(f"Found {len(delisted)} potentially delisted stocks. Examples:")
    print(delisted[['代码', '名称']].head())

if __name__ == "__main__":
    check_stock_data()
