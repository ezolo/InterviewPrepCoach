@echo off
echo ========================================
echo Interview Prep AI - Startup Script
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if database exists, if not create it
echo Checking database...
python -c "from database import DatabaseManager; DatabaseManager.test_connection()" 2>nul
if errorlevel 1 (
    echo.
    echo [INFO] Database not found. Creating database...
    python database\create_db.py
    if errorlevel 1 (
        echo.
        echo [ERROR] Database creation failed. Please check your MySQL settings in .env
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting Interview Prep AI...
echo.
python main.py

pause

