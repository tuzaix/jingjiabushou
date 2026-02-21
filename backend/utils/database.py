import logging
from contextlib import contextmanager
from utils.db_config import get_connection

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database Manager to handle connections and execute queries.
    """
    
    @staticmethod
    @contextmanager
    def get_cursor(commit=False, dictionary=False):
        """
        Context manager for database cursor.
        Handles connection acquisition, commit/rollback, and closing.
        """
        cnx = None
        cursor = None
        try:
            cnx = get_connection()
            cursor = cnx.cursor(dictionary=dictionary)
            yield cursor
            if commit:
                cnx.commit()
        except Exception as e:
            if cnx and commit:
                try:
                    cnx.rollback()
                except Exception:
                    pass
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    @staticmethod
    def execute_query(query, params=None, dictionary=True, fetch_one=False):
        """
        Execute a SELECT query and return results.
        """
        with DatabaseManager.get_cursor(commit=False, dictionary=dictionary) as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()

    @staticmethod
    def execute_update(query, params=None, many=False):
        """
        Execute an INSERT/UPDATE/DELETE query.
        Returns the number of affected rows.
        """
        with DatabaseManager.get_cursor(commit=True) as cursor:
            if many:
                cursor.executemany(query, params or [])
            else:
                cursor.execute(query, params or ())
            return cursor.rowcount
