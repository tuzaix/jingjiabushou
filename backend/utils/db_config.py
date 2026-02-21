import mysql.connector
from mysql.connector import pooling

config = {
  'user': 'root',
  'password': 'root',
  'host': '127.0.0.1',
  'database': 'jingjiabushou',
  'raise_on_warnings': False
}

# Create a connection pool
cnx_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool",
                                                       pool_size=10,
                                                       **config)

def get_connection():
    return cnx_pool.get_connection()
