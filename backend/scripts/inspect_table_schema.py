
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_table():
    try:
        # Use DESCRIBE or SHOW COLUMNS to get schema
        query = "DESCRIBE call_auction_data"
        columns = DatabaseManager.execute_query(query, dictionary=True)
        
        logger.info("Table Schema for call_auction_data:")
        for col in columns:
            logger.info(f"Field: {col['Field']}, Type: {col['Type']}")
            
    except Exception as e:
        logger.error(f"Error inspecting table: {e}")

if __name__ == "__main__":
    inspect_table()
