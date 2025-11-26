"""
Setup verification script - checks if everything is configured correctly
Run this before starting the application
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("[OK] Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("[FAIL] Python version too old. Need 3.9+, have:", f"{version.major}.{version.minor}.{version.micro}")
        return False

def check_env_file():
    """Check if .env file exists"""
    if Path(".env").exists():
        print("[OK] .env file found")
        return True
    else:
        print("[FAIL] .env file not found. Copy .env.example to .env and configure it")
        return False

def check_env_variables():
    """Check required environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    }
    
    all_set = True
    for key, value in required.items():
        if value:
            print(f"[OK] {key} is set")
        else:
            print(f"[FAIL] {key} is not set in .env")
            all_set = False
    
    # Check at least one LLM provider
    llm_providers = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL"),
    }
    
    has_llm = any(llm_providers.values())
    if has_llm:
        print("[OK] At least one LLM provider configured")
    else:
        print("[FAIL] No LLM provider configured. Set at least one:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - OLLAMA_BASE_URL")
        all_set = False
    
    return all_set

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import flet
        print("[OK] Flet is installed")
    except ImportError:
        print("[FAIL] Flet not installed. Run: pip install -r requirements.txt")
        return False
    
    try:
        import mysql.connector
        print("[OK] MySQL connector is installed")
    except ImportError:
        print("[FAIL] MySQL connector not installed. Run: pip install -r requirements.txt")
        return False
    
    return True

def check_database():
    """Check database connection"""
    try:
        from database import DatabaseManager
        if DatabaseManager.test_connection():
            print("[OK] Database connection successful")
            return True
        else:
            print("[FAIL] Database connection failed. Run: python database/create_db.py")
            return False
    except Exception as e:
        print(f"[FAIL] Database check failed: {e}")
        print("  Run: python database/create_db.py")
        return False

def check_directories():
    """Check if data directories exist"""
    from config.settings import Settings
    Settings.ensure_directories()
    print("[OK] Data directories created/verified")
    return True

def main():
    """Run all checks"""
    print("=" * 60)
    print("Interview Prep AI - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("Dependencies", check_dependencies),
        ("Data Directories", check_directories),
        ("Database Connection", check_database),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Error during check: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    
    if all(results):
        print("[SUCCESS] All checks passed! You're ready to run the application.")
        print("\nTo start the app, run:")
        print("  python main.py")
    else:
        print("[ERROR] Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  1. Copy .env.example to .env and configure it")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Setup database: python database/create_db.py")
    
    print("=" * 60)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

