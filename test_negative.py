
import mysql.connector
from mysql.connector import errorcode

config = {
  'user': 'root',
  'password': 'root',
  'host': '127.0.0.1',
  'database': 'jingjiabushou',
  'raise_on_warnings': True
}

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    # Insert a dummy record with negative bidding_percent
    sql = """
    INSERT INTO call_auction_data 
    (date, time, code, name, sector, bidding_percent, bidding_amount, asking_amount)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    val = ('2099-01-01', '09:25:00', 'TEST001', 'Test Stock', 'Test Sector', -5.55, 10000.00, 20000.00)
    
    cursor.execute(sql, val)
    cnx.commit()
    print("Inserted successfully.")
    
    # Read it back
    cursor.execute("SELECT * FROM call_auction_data WHERE code='TEST001'")
    result = cursor.fetchone()
    print(f"Read back: {result}")
    
    # Clean up
    cursor.execute("DELETE FROM call_auction_data WHERE code='TEST001'")
    cnx.commit()
    print("Deleted successfully.")

    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
