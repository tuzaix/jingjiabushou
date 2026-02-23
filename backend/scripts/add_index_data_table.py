import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager

def create_index_data_table():
    print("Creating index_data table...")
    
    # Drop old table if exists
    drop_sql = "DROP TABLE IF EXISTS `kaipanla_index_data`;"
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `index_data` (
      `id` int NOT NULL AUTO_INCREMENT,
      `date` date NOT NULL,
      `time` time NOT NULL,
      `index_code` varchar(20) NOT NULL,
      `index_name` varchar(50) NOT NULL,
      `current_price` decimal(10, 2),
      `change_rate` decimal(10, 2),
      `volume` bigint,
      `amount` decimal(20, 2),
      `raw_json` text,
      `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      INDEX `idx_date_time` (`date`, `time`),
      INDEX `idx_index_code` (`index_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with DatabaseManager.get_cursor(commit=True) as cursor:
            cursor.execute(drop_sql)
            print("Dropped old table kaipanla_index_data if it existed.")
            cursor.execute(create_table_sql)
            print("Table index_data created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_index_data_table()
