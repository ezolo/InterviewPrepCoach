# Interview Prep AI 🎯

An AI-powered desktop/web application for comprehensive interview preparation, built with **Flet** UI framework and **MySQL** database. Features include resume analysis, AI career coaching, interview question generation, mock interview practice, document writing, and job search integration.

> 📦 **New to the project?** Start with the [Installation Guide](INSTALLATION.md) for step-by-step setup instructions.

## ✨ Features

### 📄 Profile Analysis
- Upload resume (PDF, DOCX, TXT) with automatic parsing
- Paste or upload job descriptions
- AI-powered compatibility analysis (0-100% score)
- **Robust LLM Response Normalization** - Works consistently across all LLM providers (OpenAI, Anthropic, Bedrock, Ollama)
- Matched and missing skills identification (color-coded chips)
- Strengths and improvement suggestions
- **Previous Analyses** - View and reload past compatibility analyses
- Resume naming and job description metadata (company, job title)
- Compact two-column layout with persistent results
- Intelligent text truncation for long resumes/JDs while preserving analysis quality

### 🎯 Mock Interview Hub (NEW!)
- **Comprehensive Practice Hub** - Full interview simulation experience
- **Multiple Interview Formats:**
  - Traditional Interview
  - Technical Interview
  - Behavioral Interview (STAR method)
  - Case Study Interview
- **Session Setup Wizard:**
  - Choose interview format
  - Select question source (auto-generate, question set, or custom)
  - Configure number of questions, difficulty, timing
  - Set feedback mode (real-time, per-question, or post-session)
- **Live Interview Flow:**
  - One question at a time with progress tracking
  - Notes area for keywords and preparation
  - Flag questions for review
  - Skip option (with limits)
  - Pause/resume functionality
- **Response Modes:**
  - Written responses (text input)
  - Audio recording (with transcription)
  - Video recording (with analysis)
- **AI-Powered Evaluation:**
  - Content scoring (relevance, depth, specificity)
  - STAR method analysis for behavioral questions
  - Delivery metrics (pace, tone, clarity)
  - Strengths and weaknesses identification
  - Actionable improvement suggestions
- **Practice Library:**
  - Searchable session history
  - View transcripts, audio, and video recordings
  - Track progress over time
  - Export session reports

### 🎤 Practice Sessions
- **Three Response Modes:**
  - 📝 **Written** - Type your answers
  - 🎤 **Audio** - Record and transcribe responses
  - 🎥 **Video** - Record video with analysis
- **Question Set Selection** - Choose from generated question sets
- **AI Evaluation:**
  - Score (0-100) with color-coded feedback
  - STAR method breakdown
  - Strengths and areas for improvement
  - Specific suggestions for enhancement
- **Session History** - View and review past practice sessions
- **Timer Tracking** - Monitor response time

### ❓ Questions Generator
- Generate personalized interview questions based on:
  - Your resume
  - Selected job description
  - Question types (technical, behavioral, situational, company-specific)
- Customizable question count (3-15 questions)
- Save question sets for practice
- View previous question sets
- Export questions for offline review

### 💼 Job Opportunities (JSearch Integration)
- Real-time job search from multiple sources
- Automatic compatibility ranking with your resume
- Remote job filtering
- Save jobs for later
- View detailed job descriptions
- Add saved jobs to application planner
- Search history tracking

### 🧠 AI Career Coach
- **Chat Interface** - Conversational AI coach with full message history
- **Quick Advice Buttons** - Instant advice on:
  - Resume improvement tips
  - Interview preparation strategies
  - Job search strategies
  - Skills development plans
  - Salary negotiation guidance
- **Session Management** - Start/end sessions, view previous conversations
- **Previous Sessions** - Browse and reload past chat sessions
- **File Attachments** - Upload resumes and job descriptions during chat
- **Context-Aware** - Coach knows your resume, skills, and job interests
- **Markdown Support** - Rich text formatting (bold, lists) in responses
- **Persistent State** - Chat history persists across tab switches

### ✍️ Document Writer
- **Resume Generator** - AI-powered resume creation and enhancement
- **Cover Letter Generator** - Personalized cover letters based on:
  - Your resume details
  - Target job description
- **Cold Email Generator** - Professional outreach emails
- Resume selection/upload for context-aware generation
- Export to TXT and DOCX formats

### 📅 Application Planner
- Track job applications with status pipeline
- Add applications manually or from job search
- Status tracking: Saved, Applied, Screening, Interview, Offer, Rejected
- Date tracking (applied date, interview date)
- Salary expectations and notes
- Statistics dashboard
- Filter by status
- Convert saved jobs from job search to tracked applications
- Edit, update status, and delete applications
- View job URLs and application details

### 🎯 Settings & LLM Configuration
- Support for multiple LLM providers:
  - **OpenAI** (GPT-4, GPT-3.5)
  - **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
  - **AWS Bedrock** (Claude, Titan, etc.)
  - **Ollama** (Local LLMs: Llama 3.2, Mistral, Phi-3, TinyLlama)
- **Advanced LLM Integration:**
  - System/user prompt separation for better instruction adherence
  - Intelligent prompt truncation (preserves format instructions)
  - Robust JSON parsing and repair (handles malformed LLM responses)
  - Response normalizer for consistent output across providers
  - Memory-aware error handling for Ollama (suggests smaller models)
- Configurable temperature and max tokens
- API key encryption for security
- Test connection functionality with detailed feedback (modal dialogs)
- Settings persistence with confirmation feedback
- Model selection per provider

## 🚀 Quick Start

For detailed installation instructions, see **[INSTALLATION.md](INSTALLATION.md)**.

### Quick Installation (5 minutes)

```bash
# 1. Clone/download the project
cd interview_prep_ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (see INSTALLATION.md for template)
# Configure database and API keys

# 5. Setup database
python database/create_db.py

# 6. Run application
python main.py
```

**For complete step-by-step guide with troubleshooting, see [INSTALLATION.md](INSTALLATION.md)**

## 📁 Project Structure

```
interview_prep_ai/
├── main.py                          # Flet app entry point
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
├── .env.example                    # Example environment file
│
├── config/
│   ├── settings.py                 # App settings
│   └── prompts.py                  # LLM prompts library
│
├── database/
│   ├── connection.py               # Database connection pool
│   ├── create_db.py                # Auto database setup script
│   ├── schema.py                   # Database schema definitions
│   └── migrations/
│       ├── 001_initial_schema.sql  # Initial database schema
│       ├── 002_add_indexes.sql     # Performance indexes
│       ├── 003_add_jsearch_history.sql  # JSearch history table
│       └── 004_add_mock_interview_tables.sql  # Mock interview tables
│
├── core/
│   ├── document_parser.py          # PDF/DOCX/TXT parsing
│   ├── text_extractor.py           # Text extraction utilities
│   ├── encryption.py               # API key encryption
│   ├── auth.py                     # Authentication (simple)
│   ├── validators.py               # Input validation
│   ├── recording_service.py        # Audio/video recording
│   └── response_normalizer.py     # LLM response normalization (NEW)
│
├── ai/
│   ├── agents/
│   │   └── career_coach.py         # Career coach agent
│   └── providers/
│       ├── base_provider.py        # Abstract LLM provider
│       ├── openai_provider.py      # OpenAI implementation
│       ├── anthropic_provider.py  # Anthropic implementation
│       ├── bedrock_provider.py    # AWS Bedrock implementation
│       └── ollama_provider.py      # Ollama implementation
│
├── services/
│   ├── llm_service.py              # LLM provider management
│   ├── resume_service.py           # Resume operations
│   ├── jd_service.py               # Job description operations
│   ├── compatibility_service.py    # Compatibility analysis with normalizer
│   ├── question_service.py         # Question generation
│   ├── practice_service.py         # Practice sessions
│   ├── mock_interview_service.py   # Mock interview sessions
│   ├── jsearch_service.py          # JSearch API integration
│   ├── document_service.py         # Document generation
│   ├── coach_service.py            # AI Career Coach
│   └── application_service.py      # Application tracking
│
├── ui/
│   ├── components/
│   │   ├── navigation.py           # Navigation rail
│   │   ├── file_uploader.py        # File upload component
│   │   ├── score_card.py           # Score display
│   │   └── job_card.py             # Job listing card
│   ├── views/
│   │   ├── home_view.py            # Dashboard
│   │   ├── profile_analysis_view.py # Resume analysis
│   │   ├── opportunities_view.py    # Job search
│   │   ├── questions_view.py       # Questions generator
│   │   ├── practice_view.py        # Practice sessions
│   │   ├── mock_interview_view.py  # Mock interview hub (NEW)
│   │   ├── writer_view.py          # Document writer
│   │   ├── planner_view.py         # Application planner
│   │   ├── coach_view.py           # AI Career Coach
│   │   └── settings_view.py        # Settings
│   └── styles/
│       ├── theme.py                # Color schemes
│       └── constants.py            # UI constants
│
└── data/                           # File storage
    ├── resumes/
    ├── job_descriptions/
    ├── documents/
    ├── recordings/
    │   ├── audio/
    │   └── video/
    └── logs/
```

## 🔧 Configuration

### LLM Providers Setup

**OpenAI:**
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. Configure in Settings UI

**Anthropic (Claude):**
1. Get API key from https://console.anthropic.com/
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Configure in Settings UI

**AWS Bedrock:**
1. Configure AWS credentials
2. Enable Bedrock models in AWS Console
3. Configure in Settings UI

**Ollama (Local):**
1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama: `ollama serve`
4. Configure in Settings UI (endpoint: `http://localhost:11434`)

### JSearch API Setup

1. Sign up at RapidAPI: https://rapidapi.com/
2. Subscribe to JSearch API: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
3. Add API key to `.env`: `JSEARCH_API_KEY=your_key`

## 🎮 Usage

### 1. Profile Analysis
1. Go to **Profile Analysis**
2. Upload your resume (or use existing)
3. Choose job description input method:
   - **Option 1:** Upload JD file
   - **Option 2:** Paste JD text
4. Optionally name your resume and add company/job title
5. Click **Analyze Compatibility**
6. View compatibility score, matched/missing skills, and suggestions
7. Access **Previous Analyses** to view past results

### 2. Mock Interview Hub
1. Go to **Practice** → Click **Mock Interview Hub** button (or navigate to `/mock-interview`)
2. Click **➕ New Mock Interview**
3. **Setup Wizard:**
   - Select interview format (Traditional, Technical, Behavioral, Case)
   - Choose question source (Auto-generate, Question Set, or Custom)
   - Configure: number of questions, difficulty, timing, feedback mode
   - Enter session name
4. Click **🚀 Start Mock Interview**
5. **Live Session:**
   - Answer questions one at a time
   - Use notes area for keywords
   - Flag questions for review or skip if needed
   - Submit responses
6. **View Results:**
   - See AI evaluation with scores
   - Review strengths and weaknesses
   - Access practice library for history

### 3. Practice Sessions
1. Go to **Practice**
2. Select a question set from dropdown
3. Choose a question
4. Select response mode (Written, Audio, or Video)
5. Click **▶ Start Practice**
6. Record/type your response
7. Click **✓ Submit Response** for AI evaluation
8. View detailed feedback with scores and suggestions

### 4. AI Career Coach
1. Go to **Career Coach**
2. Click **Start New Coaching Session** (or use existing)
3. Use **Quick Advice** buttons for instant tips
4. Chat with the AI coach about career questions
5. Upload files (resume/JD) using attachment button
6. View **Previous Sessions** to reload past conversations
7. Click **End Session** when done

### 5. Questions Generator
1. Go to **Questions**
2. Select a resume from dropdown
3. Select or upload a job description
4. Choose question type and count
5. Click **✨ Generate Questions**
6. Review generated questions
7. Save question sets for practice

### 6. Document Writer
1. Go to **Writer**
2. Select tab: Resume, Cover Letter, or Cold Email
3. Select/upload a resume for context
4. Select a job description (for cover letter/email)
5. Click **Generate**
6. Review and edit generated document
7. Click **Export** to save as TXT or DOCX

### 7. Job Search
1. Go to **Opportunities**
2. Enter search keywords (e.g., "Python Developer")
3. Optionally add location
4. Check "Remote only" if desired
5. Click **Search Jobs**
6. View jobs ranked by compatibility
7. Save interesting jobs or add to planner

### 8. Application Planner
1. Go to **Planner**
2. Click **➕ New Application** (dialog will open)
3. Fill in company, position, dates, status
4. Add notes and salary expectations
5. Click **Add Application** to save
6. Track status through pipeline using **Update Status** button
7. Edit applications or convert saved jobs from job search
8. View statistics dashboard and filter by status

### 9. LLM Configuration
1. Go to **Settings**
2. Select LLM Provider
3. Choose model
4. Enter API key (if required)
5. Adjust temperature and max tokens
6. Click **Test Connection** (with feedback)
7. Click **Save Settings** (confirmation will appear)

## 📊 Database Schema

The application uses MySQL with the following main tables:

**Core Tables:**
- `users` & `user_profiles` - User information
- `resumes` - Uploaded resumes with parsed data
- `job_descriptions` - Job descriptions with metadata
- `compatibility_analyses` - Analysis results and history

**Interview Preparation:**
- `question_sets` & `questions` - Interview questions
- `practice_sessions` - Practice history (written/audio/video)
- `mock_interview_sessions` - Mock interview sessions (NEW)
- `mock_interview_responses` - Per-question responses (NEW)
- `mock_interview_feedback` - AI evaluations (NEW)
- `mock_interview_analytics` - Session analytics (NEW)

**Job Search:**
- `applications` & `application_reminders` - Application tracking
- `jsearch_jobs` - Cached job listings
- `jsearch_history` - Search history

**AI & Coaching:**
- `llm_settings` - User LLM configuration
- `coach_conversations` & `coach_messages` - Career coach chat sessions
- `generated_documents` - Generated resumes, cover letters, emails

## ⚠️ Troubleshooting

For detailed troubleshooting, see **[INSTALLATION.md](INSTALLATION.md#-troubleshooting)**.

**Common Issues:**

- **Database connection failed:** See [INSTALLATION.md - Database Connection](INSTALLATION.md#database-connection-failed)
- **LLM connection failed:** See [INSTALLATION.md - LLM Connection](INSTALLATION.md#llm-connection-failed)
- **Ollama 500 errors / Memory issues:** 
  - Try a smaller model: `ollama pull tinyllama`
  - Use CPU-only mode: `OLLAMA_NUM_GPU=0 ollama serve`
  - The app will suggest smaller models automatically
- **Compatibility analysis showing 0% or missing skills:**
  - The response normalizer handles various LLM output formats
  - If issues persist, try a different LLM provider
  - Check that resume and JD text are not empty
- **File upload not working:** See [INSTALLATION.md - File Upload](INSTALLATION.md#file-upload-not-working)
- **Audio/Video recording not working:** See [INSTALLATION.md - Audio/Video](INSTALLATION.md#audiovideo-recording-not-working)
- **Mock interview tables missing:** See [INSTALLATION.md - Migrations](INSTALLATION.md#mock-interview-tables-missing)
- **Dialogs not appearing:** Ensure you're using the latest version. Dialogs use `page.overlay` for proper rendering.
- **Planner not loading:** Check database connection and ensure `applications` table exists.
- **Dropdown errors:** Fixed in latest version - dropdowns refresh after views are built.
- **Document generation errors:** Ensure `generated_documents` table has correct schema (uses `job_description_id`, not `jd_id`).

## 🛠️ Development

### Database Management

**Reset database:**
```bash
# Drop and recreate (WARNING: Deletes all data)
python database/create_db.py
```

**Apply migrations:**
```bash
# Apply specific migration
python -c "import mysql.connector, os; from dotenv import load_dotenv; load_dotenv(); conn=mysql.connector.connect(host=os.getenv('DB_HOST','localhost'), port=int(os.getenv('DB_PORT',3306)), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), database=os.getenv('DB_NAME','interview_prep_ai')); cursor=conn.cursor(); sql=open('database/migrations/004_add_mock_interview_tables.sql','r',encoding='utf-8').read(); statements=[s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]; [cursor.execute(stmt) for stmt in statements]; conn.commit(); cursor.close(); conn.close(); print('Migration applied')"
```

**Verify database:**
```python
from database import DatabaseManager
DatabaseManager.test_connection()
```

### Adding New Features

1. Create service in `services/`
2. Create UI view in `ui/views/`
3. Add route in `main.py`
4. Add navigation item in `ui/components/navigation.py` (if needed)
5. Create database migration if new tables needed

## 📝 License

MIT License

## 🤝 Contributing

This is a personal project. Feel free to fork and customize for your needs!

## 📧 Support

For issues or questions, please check the troubleshooting section above or review the code comments.

---

**Built with ❤️ using Flet, MySQL, and AI**

## 🔄 Recent Updates

**Latest Improvements (v1.1.0):**
- ✅ **LLM Response Consistency** - Moved format instructions to system prompt, added intelligent text truncation
- ✅ **Response Normalizer** - Handles inconsistent JSON outputs from different LLM providers
- ✅ **Enhanced Error Handling** - Better Ollama memory error messages, JSON repair for malformed responses
- ✅ **UI Fixes** - Fixed dropdown refresh errors in Questions and Writer views
- ✅ **Schema Alignment** - Fixed DocumentService to use correct database columns
- ✅ **Improved Prompt Engineering** - System/user prompt separation for better LLM adherence

**Version:** 1.1.0  
**Last Updated:** November 2024
