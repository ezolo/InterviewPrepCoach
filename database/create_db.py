"""
Database setup script - Creates database and all tables
"""
import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import CREATE_DATABASE, CREATE_TABLES, INSERT_DEFAULT_USER

load_dotenv()

def create_database():
    """Create the database and all tables"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        cursor = connection.cursor()
        
        print("Creating database...")
        cursor.execute(CREATE_DATABASE)
        print("[OK] Database created")
        
        # Select the database
        database_name = os.getenv('DB_NAME', 'interview_prep_ai')
        cursor.execute(f"USE {database_name}")
        
        print("\nCreating tables...")
        for i, table_sql in enumerate(CREATE_TABLES, 1):
            cursor.execute(table_sql)
            print(f"[OK] Created table {i}/{len(CREATE_TABLES)}")
        
        print("\nInserting default user...")
        cursor.execute(INSERT_DEFAULT_USER)
        connection.commit()
        print("[OK] Default user created")
        
        # Sync id alias columns with id for code compatibility
        print("\nSyncing id columns...")
        try:
            cursor.execute("UPDATE job_descriptions SET jd_id = id WHERE jd_id IS NULL OR jd_id != id")
            connection.commit()
            print("[OK] Synced jd_id in job_descriptions")
        except Exception as e:
            print(f"[INFO] jd_id sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE question_sets SET set_id = id WHERE set_id IS NULL OR set_id != id")
            connection.commit()
            print("[OK] Synced set_id in question_sets")
        except Exception as e:
            print(f"[INFO] set_id sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE resumes SET resume_id = id WHERE resume_id IS NULL OR resume_id != id")
            connection.commit()
            print("[OK] Synced resume_id in resumes")
        except Exception as e:
            print(f"[INFO] resume_id sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE questions SET question_id = id, set_id = question_set_id WHERE question_id IS NULL OR question_id != id")
            connection.commit()
            print("[OK] Synced question_id and set_id in questions")
        except Exception as e:
            print(f"[INFO] question_id sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE applications SET application_id = id WHERE application_id IS NULL OR application_id != id")
            connection.commit()
            print("[OK] Synced application_id in applications")
        except Exception as e:
            print(f"[INFO] application_id sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE resumes SET resume_text = extracted_text WHERE resume_text IS NULL AND extracted_text IS NOT NULL")
            connection.commit()
            print("[OK] Synced resume_text from extracted_text in resumes")
        except Exception as e:
            print(f"[INFO] resume_text sync skipped (table may be empty): {e}")
        
        try:
            cursor.execute("UPDATE compatibility_analyses SET analysis_id = id WHERE analysis_id IS NULL OR analysis_id != id")
            connection.commit()
            print("[OK] Synced analysis_id in compatibility_analyses")
        except Exception as e:
            print(f"[INFO] analysis_id sync skipped (table may be empty): {e}")
        
        cursor.close()
        connection.close()
        
        print("\n[OK] Database setup completed successfully!")
        return True
        
    except mysql.connector.Error as err:
        print(f"\n[ERROR] {err}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("Interview Prep AI - Database Setup")
    print("="*50)
    print()
    
    success = create_database()
    
    if success:
        print("\nYou can now run the application with: python main.py")
    else:
        print("\nPlease check your database configuration in .env file")
        sys.exit(1)
