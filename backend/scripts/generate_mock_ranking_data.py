import sys
import os
import random
from decimal import Decimal

# Add backend directory to sys.path to allow imports from utils
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from utils.database import DatabaseManager
except ImportError:
    # Fallback for running from different directories
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from utils.database import DatabaseManager

def generate_mock_data():
    date_str = '2026-02-13'
    base_time = '09:25:00'
    
    print(f"Fetching data for {date_str} {base_time}...")
    
    # Select original data
    query = """
    SELECT date, time, code, name, sector, bidding_percent, bidding_amount, asking_amount
    FROM call_auction_data 
    WHERE date = %s AND time = %s
    """
    
    data = DatabaseManager.execute_query(query, (date_str, base_time), dictionary=True)
    
    if not data:
        print("No data found!")
        return

    print(f"Found {len(data)} records. Generating mock data...")
    
    new_records = []
    
    for row in data:
        # Generate 09:20:00 data
        # Amount: 80% - 95% of 09:25 amount
        amount_920 = row['asking_amount'] * Decimal(random.uniform(0.8, 0.95))
        # Percent: +/- 10% variation
        percent_920 = row['bidding_percent'] * Decimal(random.uniform(0.9, 1.1))
        
        new_records.append((
            row['date'],
            '09:20:00',
            row['code'],
            row['name'],
            row['sector'],
            percent_920,
            row['bidding_amount'], # Keep bidding amount similar or vary if needed, but asking_amount is key for ranking
            amount_920
        ))
        
        # Generate 09:15:00 data
        # Amount: 60% - 80% of 09:25 amount
        amount_915 = row['asking_amount'] * Decimal(random.uniform(0.6, 0.8))
        # Percent: +/- 20% variation
        percent_915 = row['bidding_percent'] * Decimal(random.uniform(0.8, 1.2))
        
        new_records.append((
            row['date'],
            '09:15:00',
            row['code'],
            row['name'],
            row['sector'],
            percent_915,
            row['bidding_amount'],
            amount_915
        ))
    
    print(f"Generated {len(new_records)} new records. Inserting into database...")
    
    insert_sql = """
    REPLACE INTO call_auction_data 
    (date, time, code, name, sector, bidding_percent, bidding_amount, asking_amount) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        # Batch insert
        DatabaseManager.execute_update(insert_sql, new_records, many=True)
        print("Successfully inserted mock data!")
    except Exception as e:
        print(f"Error inserting data: {e}")

    # Now verify the data
    print("\nVerifying data insertion:")
    verify_query = """
    SELECT time, COUNT(*) as count 
    FROM call_auction_data 
    WHERE date = %s AND time IN ('09:25:00', '09:20:00', '09:15:00')
    GROUP BY time
    """
    results = DatabaseManager.execute_query(verify_query, (date_str,), dictionary=True)
    for row in results:
        print(f"Time: {row['time']}, Count: {row['count']}")

if __name__ == "__main__":
    generate_mock_data()
