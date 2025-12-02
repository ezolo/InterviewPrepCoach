"""
Migration 007: Add duration columns to mock_interview_responses table
"""
import mysql.connector
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Add missing duration columns"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'interview_prep_ai')
        )
        
        cursor = connection.cursor()
        
        print("Running migration 007: Add duration columns to mock_interview_responses")
        
        # Check which columns exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'mock_interview_responses'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add duration_seconds if it doesn't exist
        if 'duration_seconds' not in existing_columns:
            print("Adding duration_seconds column...")
            cursor.execute("""
                ALTER TABLE mock_interview_responses 
                ADD COLUMN duration_seconds INT DEFAULT 0 AFTER is_skipped
            """)
            connection.commit()
            print("[OK] Added duration_seconds column")
        else:
            print("[INFO] duration_seconds column already exists")
        
        # Add prep_time_seconds if it doesn't exist
        if 'prep_time_seconds' not in existing_columns:
            print("Adding prep_time_seconds column...")
            cursor.execute("""
                ALTER TABLE mock_interview_responses 
                ADD COLUMN prep_time_seconds INT DEFAULT 0 AFTER duration_seconds
            """)
            connection.commit()
            print("[OK] Added prep_time_seconds column")
        else:
            print("[INFO] prep_time_seconds column already exists")
        
        # Add response_time_seconds if it doesn't exist
        if 'response_time_seconds' not in existing_columns:
            print("Adding response_time_seconds column...")
            cursor.execute("""
                ALTER TABLE mock_interview_responses 
                ADD COLUMN response_time_seconds INT DEFAULT 0 AFTER prep_time_seconds
            """)
            connection.commit()
            print("[OK] Added response_time_seconds column")
        else:
            print("[INFO] response_time_seconds column already exists")
        
        # Migrate data from time_taken_seconds if it exists
        if 'time_taken_seconds' in existing_columns:
            print("Migrating data from time_taken_seconds to duration_seconds...")
            cursor.execute("""
                UPDATE mock_interview_responses 
                SET duration_seconds = time_taken_seconds 
                WHERE duration_seconds = 0 AND time_taken_seconds IS NOT NULL
            """)
            connection.commit()
            print(f"[OK] Migrated {cursor.rowcount} rows")
            
            # Optionally drop the old column (commented out for safety)
            # print("Dropping time_taken_seconds column...")
            # cursor.execute("ALTER TABLE mock_interview_responses DROP COLUMN time_taken_seconds")
            # connection.commit()
            # print("[OK] Dropped time_taken_seconds column")
        
        cursor.close()
        connection.close()
        
        print("\n[OK] Migration 007 completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

