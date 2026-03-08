import mysql.connector
import logging
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_config import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database():
    """
    Migrate database tables to the correct schemas and add optimized indexes.
    """
    cnx = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        
        # 1. Migrate call_auction_data
        logger.info("Checking call_auction_data schema...")
        cursor.execute("SHOW COLUMNS FROM call_auction_data")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Check for missing columns and add them
        needed_columns = {
            'sector': "varchar(50) DEFAULT '' AFTER name",
            'bidding_percent': "decimal(10, 2) DEFAULT 0.00 AFTER price",
            'bidding_amount': "decimal(20, 2) DEFAULT 0.00 AFTER bidding_percent",
            'asking_amount': "decimal(20, 2) DEFAULT 0.00 AFTER bidding_amount",
            'non_asking_amount': "decimal(20, 2) DEFAULT 0.00 AFTER asking_amount",
            'non_asking_volume': "bigint DEFAULT 0 AFTER non_asking_amount",
            'yidongleixing': "varchar(255) DEFAULT '' AFTER non_asking_volume"
        }
        
        for col, definition in needed_columns.items():
            if col not in columns:
                logger.info(f"Adding column {col} to call_auction_data...")
                cursor.execute(f"ALTER TABLE call_auction_data ADD COLUMN {col} {definition}")
        
        # 2. Migrate yesterday_limit_up
        logger.info("Checking yesterday_limit_up schema...")
        cursor.execute("SHOW COLUMNS FROM yesterday_limit_up")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        needed_columns_lu = {
            'edition': "int DEFAULT 0 AFTER consecutive_days",
            'consecutive_boards': "int DEFAULT 0 AFTER edition",
            'expound': "text AFTER open_count"
        }
        
        for col, definition in needed_columns_lu.items():
            if col not in columns:
                logger.info(f"Adding column {col} to yesterday_limit_up...")
                cursor.execute(f"ALTER TABLE yesterday_limit_up ADD COLUMN {col} {definition}")

        # 3. Add optimized indexes
        logger.info("Adding optimized indexes...")
        
        # Indexes for call_auction_data
        try:
            cursor.execute("CREATE INDEX idx_date_code ON call_auction_data (date, code)")
            logger.info("Added idx_date_code to call_auction_data")
        except mysql.connector.Error as err:
            if err.errno != 1061: raise err # Skip if exists
            
        try:
            cursor.execute("CREATE INDEX idx_date_time_code ON call_auction_data (date, time, code)")
            logger.info("Added idx_date_time_code to call_auction_data")
        except mysql.connector.Error as err:
            if err.errno != 1061: raise err

        # Indexes for yesterday_limit_up
        try:
            cursor.execute("CREATE INDEX idx_date_code ON yesterday_limit_up (date, code)")
            logger.info("Added idx_date_code to yesterday_limit_up")
        except mysql.connector.Error as err:
            if err.errno != 1061: raise err

        # Ensure other tables exist
        from init_db import TABLES
        for table_name in ['index_data', 'market_sentiment_stats', 'market_capacity']:
            try:
                cursor.execute(TABLES[table_name])
                logger.info(f"Created table {table_name}")
            except mysql.connector.Error as err:
                if err.errno == 1050: # Table already exists
                    pass
                else:
                    raise err

        cnx.commit()
        cursor.close()
        logger.info("Database migration and optimization complete.")
        
    except mysql.connector.Error as err:
        logger.error(f"Database error during migration: {err}")
    finally:
        if cnx:
            cnx.close()

if __name__ == "__main__":
    migrate_database()
