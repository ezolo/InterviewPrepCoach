"""Application settings and configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Project root
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'interview_prep_ai')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # API Keys
    JSEARCH_API_KEY = os.getenv('JSEARCH_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', '')
    
    # App Configuration
    APP_SECRET_KEY = os.getenv('APP_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
    DEFAULT_USER_ID = int(os.getenv('DEFAULT_USER_ID', 1))
    
    # Data directories
    DATA_DIR = PROJECT_ROOT / 'data'
    RESUMES_DIR = DATA_DIR / 'resumes'
    RECORDINGS_DIR = DATA_DIR / 'recordings'
    AUDIO_DIR = RECORDINGS_DIR / 'audio'
    VIDEO_DIR = RECORDINGS_DIR / 'video'
    JD_DIR = DATA_DIR / 'job_descriptions'
    DOCUMENTS_DIR = DATA_DIR / 'documents'
    LOGS_DIR = DATA_DIR / 'logs'
    
    # Create directories if they don't exist
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        for dir_path in [cls.RESUMES_DIR, cls.AUDIO_DIR, cls.VIDEO_DIR, 
                         cls.JD_DIR, cls.DOCUMENTS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # JSearch API
    JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com"
    JSEARCH_HEADERS = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

# Initialize directories
Settings.ensure_directories()

