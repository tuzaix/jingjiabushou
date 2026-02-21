
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
    cursor.execute("DESCRIBE call_auction_data")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print(err)
