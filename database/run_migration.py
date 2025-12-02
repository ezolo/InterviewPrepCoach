"""
Run database migration script
"""
import mysql.connector
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_migration(migration_file):
    """Run a SQL migration file"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'interview_prep_ai')
        )
        
        cursor = connection.cursor()
        
        print(f"Running migration: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute each statement
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    connection.commit()
                except mysql.connector.Error as e:
                    # Ignore errors about columns already existing
                    if "Duplicate column name" not in str(e) and "already exists" not in str(e):
                        print(f"Warning: {e}")
        
        cursor.close()
        connection.close()
        
        print(f"[OK] Migration completed: {migration_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    if not os.path.exists(migration_file):
        print(f"[ERROR] Migration file not found: {migration_file}")
        sys.exit(1)
    
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)

