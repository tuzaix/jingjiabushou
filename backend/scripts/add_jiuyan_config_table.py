
import sys
import os
import mysql.connector
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_config import config as DB_CONFIG

def add_jiuyan_config_table():
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
        
        table_sql = """
        CREATE TABLE IF NOT EXISTS `api_configs` (
          `id` int NOT NULL AUTO_INCREMENT,
          `name` varchar(50) NOT NULL UNIQUE,
          `url` varchar(255) NOT NULL,
          `method` varchar(10) NOT NULL DEFAULT 'POST',
          `headers` TEXT,
          `body` TEXT,
          `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB
        """
        
        cursor.execute(table_sql)
        print("Table api_configs created successfully")
        
        # Insert default record if not exists
        check_sql = "SELECT id FROM api_configs WHERE name = 'jiuyan_limit_up'"
        cursor.execute(check_sql)
        result = cursor.fetchone()
        
        if not result:
            insert_sql = """
            INSERT INTO api_configs (name, url, method, headers, body)
            VALUES (%s, %s, %s, %s, %s)
            """
            default_url = "https://app.jiuyangongshe.com/jystock-app/api/v1/action/field"
            default_headers = '{}' # Empty JSON
            default_body = '{"date": "", "pc": 1}'
            cursor.execute(insert_sql, ('jiuyan_limit_up', default_url, 'POST', default_headers, default_body))
            print("Default config inserted")
            
        cnx.commit()
        cursor.close()
        cnx.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    add_jiuyan_config_table()
