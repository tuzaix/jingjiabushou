import os
import sys
import json
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_stock_list():
    """
    Read stock codes from 股票集合.md, deduplicate them, and write to stock_list table.
    """
    # Define the path to the MD file
    # Based on the user's input: d:\develop\jingjiabushou\文档\股票集合.md
    # Current script is in backend/scripts, so we go up two levels to get to root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    md_file_path = os.path.join(base_dir, '文档', '股票集合.md')
    
    if not os.path.exists(md_file_path):
        logger.error(f"MD file not found at: {md_file_path}")
        return

    try:
        all_codes = set()
        with open(md_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
               
                try:
                    codes = json.loads(line)
                    
                    for code_str in codes:
                        market, code = [x.strip() for x in code_str.split('.')]
                        all_codes.add((code, market))
                except Exception as line_err:
                    logger.warning(f"Error parsing line: {line[:50]}... Error: {line_err}")
        
        logger.info(f"Total unique stock codes found: {len(all_codes)}")
        
        if not all_codes:
            logger.warning("No valid stock codes found in the file.")
            return

        print(len(all_codes))
        # Prepare data for batch insertion
        # We use REPLACE INTO to handle duplicates in the table
        insert_query = "REPLACE INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
        values = [(code, code, market) for code, market in all_codes] 
        
        # Execute batch insertion
        try:
            # Check if DatabaseManager has execute_batch
            if hasattr(DatabaseManager, 'execute_batch'):
                DatabaseManager.execute_batch(insert_query, values)
            else:
                # Fallback to execute_update with many=True if execute_batch is not yet available
                DatabaseManager.execute_update(insert_query, values, many=True)
                
            logger.info(f"Successfully imported {len(values)} stock codes into stock_list table.")
        except Exception as db_err:
            logger.error(f"Database error during import: {db_err}")
            
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import_stock_list()
