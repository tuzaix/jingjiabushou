
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.sync_service import SyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_syntax():
    logger.info("Import successful. Syntax check passed.")

if __name__ == "__main__":
    check_syntax()
