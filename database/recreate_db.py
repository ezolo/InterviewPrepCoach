"""
Script to drop and recreate the database
WARNING: This will delete all data!
"""
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

# Database configuration (without database name for dropping)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
}

DB_NAME = os.getenv('DB_NAME', 'interview_prep_ai')

def drop_and_recreate():
    """Drop and recreate the database"""
    try:
        # Connect without database
        print("=" * 50)
        print("Interview Prep AI - Database Recreation")
        print("=" * 50)
        print(f"\nWARNING: This will DELETE all data in '{DB_NAME}' database!")
        
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Drop database
        print(f"\nDropping database '{DB_NAME}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"[OK] Database '{DB_NAME}' dropped")
        
        cursor.close()
        connection.close()
        
        # Now run create_db.py
        print(f"\nCreating new database '{DB_NAME}'...")
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database.create_db import create_database
        create_database()
        
        print("\n" + "=" * 50)
        print("[OK] Database recreated successfully!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to recreate database: {e}")
        return False

if __name__ == "__main__":
    drop_and_recreate()

