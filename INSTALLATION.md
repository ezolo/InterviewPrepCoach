# 📦 Installation Guide - Interview Prep AI

Complete step-by-step guide to install and run Interview Prep AI on your local machine.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required
- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)
- **MySQL 8.0 or higher** - [Download MySQL](https://dev.mysql.com/downloads/mysql/)
- **Git** (optional, for cloning) - [Download Git](https://git-scm.com/downloads)

### Optional (for advanced features)
- **Ollama** (for local LLM) - [Download Ollama](https://ollama.ai/)
- **API Keys** for one or more LLM providers:
  - OpenAI API key
  - Anthropic API key
  - AWS Bedrock credentials
  - JSearch API key (for job search)

## 🚀 Installation Steps

### Step 1: Clone or Download the Project

**Option A: Clone from GitHub (if available)**
```bash
git clone https://github.com/yourusername/interview_prep_ai.git
cd interview_prep_ai
```

**Option B: Download ZIP**
1. Download the project ZIP file
2. Extract to your desired location
3. Open terminal/command prompt in the extracted folder

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages:
- Flet (UI framework)
- mysql-connector-python (Database)
- PyPDF2, python-docx, pdfplumber (Document parsing)
- openai, anthropic, boto3 (LLM providers)
- cryptography (Encryption)
- And other dependencies

**Optional: Install Audio/Video Dependencies**
For audio and video recording features:
```bash
pip install sounddevice soundfile opencv-python openai-whisper numpy
```

### Step 4: Setup MySQL Database

1. **Start MySQL Server**
   - Windows: Start MySQL service from Services
   - macOS: `brew services start mysql` or use MySQL Workbench
   - Linux: `sudo systemctl start mysql`

2. **Create Database User (if needed)**
   ```sql
   CREATE USER 'interview_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON interview_prep_ai.* TO 'interview_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

   Or use your existing MySQL root user.

### Step 5: Configure Environment Variables

1. **Create `.env` file** in the project root directory

2. **Copy the template below** and fill in your values:

```env
# ============================================
# Database Configuration (REQUIRED)
# ============================================
DB_HOST=localhost
DB_PORT=3306
DB_NAME=interview_prep_ai
DB_USER=root
DB_PASSWORD=your_mysql_password

# ============================================
# LLM Provider Configuration
# At least ONE provider is required
# ============================================

# OpenAI (Recommended for best quality)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# AWS Bedrock
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Ollama (Local LLM - Free)
OLLAMA_BASE_URL=http://localhost:11434

# ============================================
# Optional: Job Search API
# ============================================
JSEARCH_API_KEY=your_jsearch_rapidapi_key

# ============================================
# Application Configuration
# ============================================
APP_SECRET_KEY=change_this_to_a_random_secret_key_in_production
DEBUG_MODE=True
DEFAULT_USER_ID=1
```

**Important Notes:**
- Replace `your_mysql_password` with your actual MySQL password
- You need at least ONE LLM provider API key (OpenAI, Anthropic, or Ollama)
- For Ollama, make sure it's installed and running (`ollama serve`)
- `APP_SECRET_KEY` should be a random string for production use

### Step 6: Initialize Database

Run the database setup script:

```bash
python database/create_db.py
```

**Expected Output:**
```
==================================================
Interview Prep AI - Database Setup
==================================================

Creating database...
[OK] Database created

Creating tables...
[OK] Created table 1/21
[OK] Created table 2/21
...
[OK] Created table 21/21

Inserting default user...
[OK] Default user created

[OK] Database setup completed successfully!
```

**If you see errors:**
- Check MySQL is running
- Verify database credentials in `.env`
- Ensure MySQL user has CREATE DATABASE privileges

### Step 7: Apply Additional Migrations (if needed)

If you need the mock interview tables:

**Windows PowerShell:**
```powershell
python -c "import mysql.connector, os; from dotenv import load_dotenv; load_dotenv(); conn=mysql.connector.connect(host=os.getenv('DB_HOST','localhost'), port=int(os.getenv('DB_PORT',3306)), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','interview_prep_ai')); cursor=conn.cursor(); sql=open('database/migrations/004_add_mock_interview_tables.sql','r',encoding='utf-8').read(); statements=[s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]; [cursor.execute(stmt) for stmt in statements]; conn.commit(); cursor.close(); conn.close(); print('Migration applied')"
```

**macOS/Linux:**
```bash
python3 -c "import mysql.connector, os; from dotenv import load_dotenv; load_dotenv(); conn=mysql.connector.connect(host=os.getenv('DB_HOST','localhost'), port=int(os.getenv('DB_PORT',3306)), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','interview_prep_ai')); cursor=conn.cursor(); sql=open('database/migrations/004_add_mock_interview_tables.sql','r',encoding='utf-8').read(); statements=[s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]; [cursor.execute(stmt) for stmt in statements]; conn.commit(); cursor.close(); conn.close(); print('Migration applied')"
```

### Step 8: Run the Application

```bash
python main.py
```

The application will:
1. Initialize database connection
2. Load configuration
3. Open in a new window (desktop mode) or browser (web mode)

**First Launch:**
- The app will open with the Home dashboard
- Navigate to **Settings** to configure your LLM provider
- Test the connection before using other features

## 🔧 Post-Installation Configuration

### Configure LLM Provider

1. Click **Settings** in the left navigation
2. Select your LLM provider:
   - **OpenAI**: Enter API key, select model (GPT-4, GPT-3.5)
   - **Anthropic**: Enter API key, select model (Claude 3 Opus, Sonnet, Haiku)
   - **AWS Bedrock**: Configure AWS credentials, select model
   - **Ollama**: Enter endpoint URL (default: `http://localhost:11434`), select model
3. Adjust temperature and max tokens if needed
4. Click **Test Connection** to verify
5. Click **Save Settings**

### Setup Ollama (Optional - Free Local LLM)

If you want to use Ollama instead of paid APIs:

1. **Install Ollama:**
   - Download from https://ollama.ai/
   - Install and start the service

2. **Pull a model:**
   ```bash
   ollama pull llama3.2
   # or
   ollama pull mistral
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```

4. **Configure in Settings:**
   - Provider: Ollama
   - Endpoint: `http://localhost:11434`
   - Model: `llama3.2:latest` (or your chosen model)

### Setup JSearch API (Optional - for Job Search)

1. **Sign up at RapidAPI:**
   - Go to https://rapidapi.com/
   - Create an account

2. **Subscribe to JSearch API:**
   - Search for "JSearch" in RapidAPI
   - Subscribe to the free tier (100 requests/month)

3. **Get API Key:**
   - Copy your RapidAPI key
   - Add to `.env`: `JSEARCH_API_KEY=your_key`

## ✅ Verification

### Test Database Connection

```bash
python -c "from database.connection import DatabaseManager; DatabaseManager.test_connection(); print('Database connection successful!')"
```

### Test Application Setup

```bash
python check_setup.py
```

This will verify:
- Python version
- Required packages
- Database connection
- Environment variables
- File permissions

### Test LLM Connection

1. Open the application
2. Go to **Settings**
3. Configure your LLM provider
4. Click **Test Connection**
5. You should see a success message

## 🐛 Troubleshooting

### Database Connection Failed

**Error:** `Can't connect to MySQL server`

**Solutions:**
1. Verify MySQL is running:
   - Windows: Check Services (services.msc)
   - macOS: `brew services list`
   - Linux: `sudo systemctl status mysql`

2. Check credentials in `.env`:
   ```env
   DB_USER=root
   DB_PASSWORD=your_actual_password
   ```

3. Test connection manually:
   ```bash
   mysql -u root -p
   ```

4. Check MySQL port (default 3306):
   ```bash
   netstat -an | grep 3306  # Linux/macOS
   netstat -an | findstr 3306  # Windows
   ```

### LLM Connection Failed

**Error:** `API key invalid` or `Connection timeout`

**Solutions:**
1. **OpenAI/Anthropic:**
   - Verify API key is correct (no extra spaces)
   - Check account has credits/quota
   - Verify network connection

2. **Ollama:**
   - Ensure `ollama serve` is running
   - Check endpoint URL: `http://localhost:11434`
   - Verify model is pulled: `ollama list`
   - Test manually: `curl http://localhost:11434/api/tags`

3. **AWS Bedrock:**
   - Verify AWS credentials are correct
   - Check IAM permissions for Bedrock
   - Verify region is correct

### File Upload Not Working

**Error:** `File picker not showing files` or `Permission denied`

**Solutions:**
1. **Desktop Mode:**
   - Grant file system permissions
   - Check file size (<10MB recommended)
   - Verify file format (PDF, DOCX, TXT)

2. **File Permissions:**
   ```bash
   # Ensure data directory is writable
   chmod -R 755 data/  # Linux/macOS
   ```

3. **File Path Issues:**
   - Use absolute paths if relative paths fail
   - Check `data/` directory exists

### Import Errors

**Error:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
1. Ensure virtual environment is activated:
   ```bash
   # You should see (venv) in prompt
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. Check Python path:
   ```bash
   which python  # Should point to venv/bin/python
   ```

### Audio/Video Recording Not Working

**Error:** `sounddevice not available` or `opencv-python not available`

**Solutions:**
1. Install optional dependencies:
   ```bash
   pip install sounddevice soundfile opencv-python openai-whisper numpy
   ```

2. **Audio Issues:**
   - Check microphone permissions
   - Verify audio drivers are installed
   - Test with: `python -c "import sounddevice; print(sounddevice.query_devices())"`

3. **Video Issues:**
   - Check camera permissions
   - Verify camera is not in use by another app
   - Test with: `python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"`

### Mock Interview Tables Missing

**Error:** `Table 'mock_interview_sessions' doesn't exist`

**Solution:**
Apply the migration (see Step 7 above) or manually run:
```bash
mysql -u root -p interview_prep_ai < database/migrations/004_add_mock_interview_tables.sql
```

## 📚 Next Steps

After successful installation:

1. **Upload Your Resume:**
   - Go to Profile Analysis
   - Upload your resume (PDF, DOCX, or TXT)

2. **Try Profile Analysis:**
   - Paste a job description
   - Click Analyze Compatibility
   - View your compatibility score

3. **Explore Features:**
   - Generate interview questions
   - Practice with mock interviews
   - Search for jobs
   - Chat with career coach

4. **Read the README:**
   - See `README.md` for detailed feature documentation
   - Learn about all available features

## 🔐 Security Notes

- **Never commit `.env` file** to version control
- **Change `APP_SECRET_KEY`** in production
- **Use strong MySQL passwords**
- **Keep API keys secure** - they're encrypted in the database
- **Review file permissions** on `data/` directory

## 📞 Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review error messages in the terminal
3. Verify all prerequisites are installed
4. Check the main `README.md` for feature documentation
5. Review code comments for implementation details

## 🎉 You're All Set!

Your Interview Prep AI installation is complete. Start the application with `python main.py` and begin your interview preparation journey!

---

**Need API Keys?**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Ollama: https://ollama.ai/ (Free, local)
- JSearch: https://rapidapi.com/ (Free tier available)

