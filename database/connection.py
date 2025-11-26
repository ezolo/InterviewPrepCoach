"""
Database configuration and connection management
"""
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'interview_prep_ai'),
}

# Connection pool
connection_pool = None

def init_pool():
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="interview_prep_pool",
            pool_size=5,
            pool_reset_session=True,
            **DB_CONFIG
        )
        print("[OK] Database connection pool initialized")
        return True
    except Exception as e:
        print(f"[ERROR] Error initializing database pool: {e}")
        return False

def get_connection():
    """Get a connection from the pool"""
    global connection_pool
    if connection_pool is None:
        init_pool()
    return connection_pool.get_connection()

class DatabaseManager:
    """Database manager class with static methods"""
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return get_connection()
    
    @staticmethod
    def get_cursor():
        """Get a cursor context manager"""
        from contextlib import contextmanager
        
        @contextmanager
        def cursor_manager():
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
                conn.close()
        
        return cursor_manager()
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """Execute a query using the execute_query function"""
        return execute_query(query, params, fetch_one, fetch_all, commit)


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction
    
    Returns:
        Query result or None
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
            return cursor.lastrowid
        elif fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        
        return None
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
