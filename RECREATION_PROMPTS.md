# Interview Prep AI – Phase-Based Recreation Prompts

These prompts are reorganized around a lean **Flet MVP first** roadmap. Each phase layers new capabilities while keeping the scope manageable. Use or remix the prompts as instructions for another AI assistant or as your own development checklist.

---

## Phase 1 – MVP Foundations (Profile Analysis, Question Generation, Settings)

Goal: launch a working Flet desktop MVP that lets a user upload a resume, compare it against a job description, generate interview questions, and configure LLM settings.

### Prompt 1.1 – Project Bootstrap
```
Initialize a Python 3.9+ project called "Interview Prep AI" optimized for a Flet desktop MVP.

Requirements:
- Use Flet for UI, MySQL for persistence, python-dotenv for configuration.
- Create folders: config/, database/, core/, ai/, services/, ui/components/, ui/views/, ui/styles/, data/(resumes|job_descriptions|documents|logs), utils/.
- Add requirements.txt with: flet, python-dotenv, mysql-connector-python, PyPDF2, python-docx, pdfplumber, openai, anthropic, boto3, ollama, httpx, cryptography, speechrecognition, pydub, opencv-python, pyaudio, requests, beautifulsoup4.
- Provide README.md and INSTALLATION.md with quick start steps.
- Create config/settings.py that loads environment variables, exposes Settings class, ensures data directories exist.
- Add utils/logger.py with setup_logger() returning a module-level logger.
```

### Prompt 1.2 – Database & Core Utilities
```
Build database/schema.py containing CREATE TABLE statements for:
- users, user_profiles
- resumes, job_descriptions, compatibility_analyses
- question_sets, questions
- llm_settings

Implement database/connection.py with mysql-connector pooling (DatabaseManager.get_cursor()).
Add database/create_db.py that runs CREATE DATABASE, all tables, inserts default user, and syncs alias columns (resume_id, jd_id, etc.).
```

### Prompt 1.3 – Profile Analysis Service & UI
```
Service layer:
- services/compatibility_service.py with analyze_compatibility(user_id, resume_id, jd_id) that:
  1. Fetches resume/JD text.
  2. Truncates inputs intelligently (~1k chars total).
  3. Calls LLMService to get provider.
  4. Uses config/prompts COMPATIBILITY prompts.
  5. Normalizes the response via core/response_normalizer.py.
  6. Persists results in compatibility_analyses.

UI:
- ui/views/profile_analysis_view.py with:
  - Resume dropdown + upload option.
  - JD upload/paste area.
  - Analyze button wired to CompatibilityService.
  - Score card (ui/components/score_card.py).
  - Chips for matched/missing skills.
  - List of strengths & suggestions.
  - Previous analyses list with reload button.
```

### Prompt 1.4 – Question Generation Service & UI
```
Service:
- services/question_service.py with generate_questions(user_id, resume_id, jd_id, question_type, count) that:
  1. Pulls resume/JD text.
  2. Calls LLMService.generate_json() using config/prompts QUESTION prompts.
  3. Repairs malformed JSON if necessary (_extract_json_block helper).
  4. Persists a question_set (name + metadata) and its questions.
  5. Returns the saved set.

UI:
- ui/views/questions_view.py providing:
  - Resume + JD dropdowns.
  - Question type selector (behavioral, technical, situational, company-specific).
  - Count slider (3–15).
  - Generate button.
  - Rendered list of questions with ideal answer bullets.
  - Previous sets table with reload/export actions.
  - Dropdown refresh once build() completes (avoid stale controls).
```

### Prompt 1.5 – Settings & LLM Configuration
```
LLM plumbing:
- ai/providers/base_provider.py (abstract generate/generate_json + message formatting).
- ai/providers/openai_provider.py, anthropic_provider.py, bedrock_provider.py, ollama_provider.py implementing provider-specific logic.
- services/llm_service.py that:
  - Fetches active llm_settings for a user (decrypts API keys via core/encryption.py).
  - Instantiates provider objects.
  - Saves new settings (activates one provider, deactivates others).

UI:
- ui/views/settings_view.py with:
  - Provider dropdown.
  - Model dropdown bound to provider-specific options.
  - API key/password fields.
  - Temperature slider, max tokens numeric input.
  - Test Connection button (modal feedback).
  - Save button with success toast.
```

---

## Phase 2 – Interview Practice & Writer

Goal: extend the MVP with hands-on practice sessions (written/audio/video) and AI-powered document writing.

### Prompt 2.1 – Practice Service & View
```
Service (services/practice_service.py):
- create_session(user_id, question_set_id, mode) -> session_id.
- save_response(session_id, question_id, response_mode, payloads) storing text/audio/video paths.
- evaluate_response(session_id, question_id, response_text) using PRACTICE_EVALUATION prompt and storing score + STAR breakdown.
- get_session_stats(user_id) returning total sessions, avg score, etc.

UI (ui/views/practice_view.py):
- Question set dropdown -> loads questions.
- Radio buttons for response mode (written/audio/video).
- Start Practice button -> shows timer & response input.
- For audio/video, integrate core/recording_service.py (later) with start/stop controls.
- Submit button triggers evaluation & renders:
  - Score indicator.
  - STAR table.
  - Lists for strengths, weaknesses, suggestions.
- Session history panel.
```

### Prompt 2.2 – Document Writer Service & View
```
Service (services/document_service.py):
- generate_resume(user_info, job_description) using RESUME_GENERATION prompt.
- generate_cover_letter(resume_summary, company, position, job_description, length).
- generate_cold_email(purpose, recipient_type, company, resume_summary).
- export_document(content, format="txt"|"docx") saving under data/documents/.

UI (ui/views/writer_view.py):
- Tab control: Resume | Cover Letter | Cold Email.
- Resume selector / upload for context.
- JD selector for cover letters/emails.
- Generate button -> displays editable text area.
- Export buttons: TXT, DOCX.
- History list of generated docs with reopen option.
- Refresh dropdowns after build().
```

---

## Phase 3 – Opportunities & Planner (JSearch + Application Tracking)

Goal: help users discover jobs and track application pipelines.

### Prompt 3.1 – JSearch Integration
```
Service (services/jsearch_service.py):
- search_jobs(user_id, keywords, location, remote_only) hitting RapidAPI JSearch.
- Map API response into standardized structure (title, company, location, salary, remote flag, job_url, apply_url, description).
- Score each job using CompatibilityService (resume vs job description) when possible.
- Cache results in jsearch_jobs and record history in jsearch_history.
- Provide get_saved_jobs(), toggle_save_job(job_id), get_search_history().

UI (ui/views/opportunities_view.py):
- Search form with keywords, location, remote checkbox.
- Search button triggers JSearchService.search_jobs.
- Render list of JobCardComponent instances:
  - Title, company, location, remote chip, compatibility score badge.
  - Buttons: Save, View Details (dialog showing description), Add to Planner.
- Sidebar with recent searches.
```

### Prompt 3.2 – Application Planner
```
Service (services/application_service.py):
- create_application(user_id, job_data, status, dates, notes, salary_expectation).
- update_status(application_id, new_status).
- get_applications(user_id, status_filter) returning enriched data (job URLs, resume used, etc.).
- get_application_stats(user_id) -> totals, by-status counts, interview rate.
- delete_application(application_id).

UI (ui/views/planner_view.py):
- Top stats: Total, Saved, Applied, Interview, Offer, Rejected.
- Status filter dropdown + search box.
- Application cards/table with actions (Update Status, Edit, Delete).
- "➕ New Application" dialog capturing company, role, location, status, salary, notes, key dates.
- Button on job cards to prefill this dialog.
- Pipeline visualization (status chips with counts).
```

---

## Phase 4 – Agentic AI Career Coach

Goal: provide an always-on coaching agent that references user data, remembers context, and offers quick advice.

### Prompt 4.1 – Coach Agent & Services
```
Agent (ai/agents/career_coach.py):
- Accepts user_context (resume summary, skills, job interests).
- Maintains conversation objectives, action items, suggested next steps.
- Supports quick advice templates (resume tips, interview prep, job search, skills dev, salary negotiation).

Service (services/coach_service.py):
- create_conversation(user_id, title, initial_context).
- add_message(conversation_id, role, content) storing in coach_messages + aggregated JSON on coach_conversations.
- get_conversation(conversation_id), get_user_conversations(user_id), archive_conversation(conversation_id).
- get_quick_advice(user_id, advice_type, target_role, industry) using QUICK_ADVICE_PROMPTS.

UI (ui/views/coach_view.py):
- Chat history pane with markdown rendering.
- Message input + "Send" button.
- Quick advice buttons -> auto-send templated prompts.
- Attachment button to upload resume/JD (adds context to conversation).
- Conversation list sidebar (reload previous sessions, search, archive).
- Session controls (Start New Session, End Session).
- Persistent state so chats survive tab switches.
```

---

## Phase 5 – Mock Interview & Final Polish

Goal: deliver advanced practice features plus production-ready polish (logging, migrations, QA).

### Prompt 5.1 – Mock Interview Hub
```
Service (services/mock_interview_service.py):
- create_session(user_id, session_name, format_type, question_source, question_set_id, resume_id, jd_id, config).
- start_session(session_id) sets status=in_progress.
- get_session_questions(session_id) either pulls question set or generates on the fly (maps format -> question type).
- save_response(session_id, question_id, response_mode, media paths, transcript, notes, flags).
- save_feedback(session_id, response_id, feedback_type, score_content/delivery/overall, STAR breakdown, strengths/weaknesses/suggestions).
- complete_session(session_id) -> status=completed, store analytics.

UI (ui/views/mock_interview_view.py):
- Dashboard with recent sessions + "➕ New Mock Interview".
- Setup wizard:
  1. Choose format (Traditional, Technical, Behavioral, Case).
  2. Select question source (Auto, Question Set, Custom).
  3. Configure number of questions, difficulty, timing per question, feedback mode (real-time/per-question/post-session).
  4. Review summary & start.
- Live interview screen:
  - Question display + progress indicator.
  - Notes area, Flag button, Skip (with limit), Pause/Resume.
  - Response capture (text/audio/video).
- Results screen:
  - Scores (content, delivery, overall) + radar chart.
  - Strengths/weaknesses.
  - Actionable suggestions + download report.
- Practice library: list/search sessions, open transcripts, play recordings, export PDFs.
```

### Prompt 5.2 – Polishing Checklist
```
1. Audio/Video Recording:
   - core/recording_service.py supporting start/stop for audio (PyAudio) and video (OpenCV).
   - Transcription via SpeechRecognition.
2. Logging & Telemetry:
   - Expand utils/logger usage across services/views.
   - Persist logs under data/logs/.
3. Database Migrations:
   - database/migrations/00X_description.sql files (initial schema, indexes, jsearch history, mock interview tables).
   - Migration runner instructions in INSTALLATION.md.
4. Error Handling:
   - User-friendly toasts/dialogs on failures (LLM errors, DB issues, file uploads).
   - Retry logic for DB pool initialization.
5. Testing & QA:
   - pytest setup for services (mock DB + LLM).
   - Manual QA checklist (profile analysis, questions, practice, writer, opportunities, planner, coach, mock interview).
6. Packaging:
   - run_app.bat / shell script for quick start.
   - Update README with feature matrix, screenshots, troubleshooting.
```

---

## Usage Tips
- Treat each phase as a self-contained sprint; only move forward when the current phase feels stable.
- When prompting an AI pair-programmer, copy the relevant prompt block verbatim, then follow up with incremental adjustments as the implementation evolves.
- Keep environment secrets in `.env`; never commit actual API keys.
- After each phase, run quick smoke tests (launch app, click through new views, confirm database writes).

This roadmap now mirrors the requested rollout: **Phase 1 Flet MVP (Profile Analysis + Questions + Settings), Phase 2 Practice + Writer, Phase 3 JSearch + Planner, Phase 4 Agentic Coach, Phase 5 Mock Interview + Polish**. Happy building!
```

### Prompt 3.4: AWS Bedrock Provider
```
Implement AWS Bedrock LLM provider.

Requirements:
- Use boto3 for AWS integration
- Support Claude, Titan models
- Handle AWS credentials from environment
- Region configuration
- Implement generate() and generate_json() methods

Create:
1. ai/providers/bedrock_provider.py extending BaseLLMProvider
```

### Prompt 3.5: Ollama Provider (Local LLM)
```
Implement Ollama local LLM provider.

Requirements:
- Use ollama library or httpx for API calls
- Support local models (llama3.2, mistral, phi-3, tinyllama)
- Configurable endpoint URL (default: http://localhost:11434)
- Memory-aware error handling (suggest smaller models on 500 errors)
- Implement generate() and generate_json() methods
- Handle streaming responses

Create:
1. ai/providers/ollama_provider.py extending BaseLLMProvider
2. Special handling for memory errors with helpful messages
```

### Prompt 3.6: LLM Service & Settings Management
```
Create LLM service for provider management and user settings.

Requirements:
- Singleton pattern for service instance
- Get user's active LLM settings from database
- Create provider instances based on user settings
- Save/update LLM settings with encrypted API keys
- Fallback to default providers if user settings not found
- Support for multiple providers per user (one active at a time)

Create:
1. services/llm_service.py with LLMService class
2. Methods: get_instance(), get_user_llm_settings(), get_provider(), save_llm_settings()
3. Integration with database/connection.py and core/encryption.py
```

### Prompt 3.7: AI Prompts Library
```
Create a comprehensive prompts library for all AI features.

Requirements:
- System prompts for role definition and format instructions
- User prompts for specific tasks
- Prompts for: compatibility analysis, question generation, practice evaluation, document generation, career coaching

Create:
1. config/prompts.py with prompt templates
2. Separate system and user prompts for better LLM adherence
3. Format strings for dynamic content insertion
4. Backwards compatibility wrapper class "Prompts"
```

---

## **PHASE 4: Business Logic Services**

### Prompt 4.1: Resume Service
```
Create service for resume management.

Requirements:
- Upload and parse resumes (PDF, DOCX, TXT)
- Extract text using DocumentParser
- Store in database with metadata
- Get resumes by user, by ID
- Update resume metadata
- Mark resumes as active/inactive

Create:
1. services/resume_service.py with ResumeService class
2. Methods: upload_resume(), get_resume_by_id(), get_user_resumes(), update_resume()
3. Integration with core/document_parser.py and database
```

### Prompt 4.2: Job Description Service
```
Create service for job description management.

Requirements:
- Upload/paste job descriptions
- Parse and extract text
- Store with metadata (company, job title, location)
- Get JDs by user, by ID
- Support for JSearch API integration

Create:
1. services/jd_service.py with JobDescriptionService class
2. Methods: create_jd(), get_jd_by_id(), get_user_jds(), update_jd()
3. Support for both file upload and text paste
```

### Prompt 4.3: Compatibility Analysis Service
```
Create service for resume-JD compatibility analysis.

Requirements:
- Analyze compatibility between resume and job description
- Use LLM to generate compatibility score (0-100)
- Extract matched skills, missing skills, strengths, suggestions
- Intelligent text truncation to fit prompt limits (preserve format instructions)
- Use response normalizer to handle inconsistent LLM outputs
- Save analysis results to database
- Retrieve previous analyses
- Support for viewing analysis history

Create:
1. services/compatibility_service.py with CompatibilityService class
2. Methods: analyze_compatibility(), get_recent_analyses(), get_analysis_by_id()
3. Integration with LLMService, ResponseNormalizer, ResumeService, JDService
4. System/user prompt separation for better LLM adherence
```

### Prompt 4.4: Question Generation Service
```
Create service for interview question generation.

Requirements:
- Generate questions based on resume and job description
- Support question types: behavioral, technical, situational, case_study
- Configurable question count (3-15)
- Save questions to question sets
- Retrieve question sets and questions
- Parse LLM responses (handle JSON and text formats)
- Extract JSON blocks from text responses

Create:
1. services/question_service.py with QuestionService class
2. Methods: generate_questions(), get_question_sets(), get_questions(), get_question_set_with_questions(), delete_question_set()
3. Integration with LLMService and prompts library
```

### Prompt 4.5: Practice Session Service
```
Create service for practice interview sessions.

Requirements:
- Create practice sessions with question sets
- Support response modes: written, audio, video
- Save responses with transcripts
- Evaluate responses using LLM
- Calculate scores and provide feedback
- Track session history and statistics

Create:
1. services/practice_service.py with PracticeService class
2. Methods: create_session(), save_response(), evaluate_response(), get_session_stats()
3. Integration with LLMService for evaluation
```

### Prompt 4.6: Mock Interview Service
```
Create comprehensive mock interview service.

Requirements:
- Create mock interview sessions with configuration
- Support interview formats: traditional, technical, behavioral, case
- Question sources: auto-generate, question set, custom
- Session setup wizard with config (num_questions, difficulty, timing, feedback_mode)
- Save responses per question (written/audio/video)
- Track session progress (current_question_index)
- Save AI feedback per question or per session
- Support for flagging/skipping questions
- Session analytics

Create:
1. services/mock_interview_service.py with MockInterviewService class
2. Methods: create_session(), start_session(), save_response(), save_feedback(), complete_session(), get_session(), get_session_questions(), get_session_responses(), get_session_feedback()
3. Integration with QuestionService for question generation
```

### Prompt 4.7: Job Search Service (JSearch Integration)
```
Create service for job search using JSearch API.

Requirements:
- Search jobs by keywords and location
- Filter remote jobs
- Calculate compatibility scores for jobs
- Save jobs to database
- Track search history
- Rank jobs by compatibility

Create:
1. services/jsearch_service.py with JSearchService class
2. Methods: search_jobs(), save_job(), get_saved_jobs(), get_search_history()
3. Integration with RapidAPI JSearch endpoint
4. Compatibility scoring using CompatibilityService
```

### Prompt 4.8: Document Generation Service
```
Create service for generating resumes, cover letters, and cold emails.

Requirements:
- Generate resumes based on user info and job description
- Generate cover letters personalized to job
- Generate cold emails for networking
- Export to TXT and DOCX formats
- Save generated documents to database

Create:
1. services/document_service.py with DocumentService class
2. Methods: generate_resume(), generate_cover_letter(), generate_cold_email(), export_document()
3. Integration with LLMService and python-docx for DOCX export
```

### Prompt 4.9: Career Coach Service
```
Create service for AI career coaching conversations.

Requirements:
- Create and manage coaching conversations
- Store message history
- Support quick advice buttons (resume tips, interview prep, job search, skills development, salary negotiation)
- Context-aware coaching (knows user's resume, skills, job interests)
- Support file attachments (resume, JD)
- Markdown support in responses
- Session management (start/end sessions)

Create:
1. services/coach_service.py with CoachService class
2. Methods: create_conversation(), add_message(), get_conversation(), get_user_conversations(), get_quick_advice()
3. Integration with LLMService and career coach agent
4. ai/agents/career_coach.py for coach agent logic
```

### Prompt 4.10: Application Tracking Service
```
Create service for tracking job applications.

Requirements:
- Create applications with status pipeline (saved, applied, screening, interview, offer, rejected)
- Update application status
- Track dates (applied, interview, follow-up)
- Add notes and salary expectations
- Convert saved jobs to tracked applications
- Get application statistics
- Filter by status

Create:
1. services/application_service.py with ApplicationService class
2. Methods: create_application(), update_application(), update_status(), get_applications(), get_application_stats(), delete_application()
3. Integration with JSearchService for job conversion
```

---

## **PHASE 5: UI Framework & Core Components**

### Prompt 5.1: UI Theme & Styling
```
Create consistent UI theme and styling system.

Requirements:
- Color scheme with primary, secondary, success, error, info colors
- Card styling with elevation and padding
- Consistent spacing and typography
- Window size constants
- Theme class with static methods

Create:
1. ui/styles/theme.py with AppTheme class
2. ui/styles/constants.py with WINDOW_WIDTH, WINDOW_HEIGHT, padding constants
3. Methods: get_theme(), card_style()
```

### Prompt 5.2: Navigation Component
```
Create left navigation rail component.

Requirements:
- NavigationRail with 10 destinations: Home, Profile Analysis, Questions, Practice, Mock Interview, Opportunities, Writer, Planner, Career Coach, Settings
- Icons for each destination (outlined and filled)
- Label display
- Navigation change handler
- Selected index tracking

Create:
1. ui/components/navigation.py with NavigationRailComponent class
2. Methods: build() returns ft.NavigationRail
3. Integration with main.py routing
```

### Prompt 5.3: File Uploader Component
```
Create reusable file uploader component.

Requirements:
- Support PDF, DOCX, TXT file types
- File picker dialog
- File validation (type, size)
- Progress indication
- Error handling

Create:
1. ui/components/file_uploader.py with FileUploaderComponent class
2. Methods: build(), on_file_selected()
```

### Prompt 5.4: Score Card Component
```
Create score display component.

Requirements:
- Display compatibility score (0-100)
- Color coding (red < 50, yellow 50-70, green > 70)
- Circular or linear progress indicator
- Large, readable number display

Create:
1. ui/components/score_card.py with ScoreCardComponent class
2. Methods: build(score) returns score display widget
```

### Prompt 5.5: Job Card Component
```
Create job listing card component.

Requirements:
- Display job title, company, location
- Compatibility score badge
- Remote indicator
- Action buttons (save, view details, add to planner)
- Responsive layout

Create:
1. ui/components/job_card.py with JobCardComponent class
2. Methods: build(job_data) returns job card widget
```

---

## **PHASE 6: Feature Views**

### Prompt 6.1: Main Application Entry & Routing
```
Create main application entry point with routing system.

Requirements:
- Flet app initialization
- Window configuration (size, min size, theme)
- Navigation rail integration
- Route change handler
- View caching for state persistence
- Error handling for view loading
- Support for 10 routes: /, /profile_analysis, /questions, /practice, /mock-interview, /opportunities, /writer, /planner, /coach, /settings

Create:
1. main.py with main(page) function
2. Route change handler
3. View cache dictionary
4. Navigation change handler
5. Database connection check on startup
```

### Prompt 6.2: Home Dashboard View
```
Create home dashboard view with statistics and quick actions.

Requirements:
- Welcome header
- Statistics cards: Practice Sessions, Average Score, Applications, Interview Rate
- Quick action cards: Profile Analysis, Practice Interview, Find Jobs
- Responsive layout
- Data from PracticeService and ApplicationService

Create:
1. ui/views/home_view.py with HomeView class
2. Methods: build(), _build_stat_card(), _build_feature_card()
3. Integration with services for data
```

### Prompt 6.3: Profile Analysis View
```
Create profile analysis view for resume-JD compatibility.

Requirements:
- Resume upload/selection dropdown
- Job description input (upload file or paste text)
- Optional fields: resume name, company name, job title
- Analyze button
- Results display: compatibility score, matched skills (green chips), missing skills (red chips), strengths, suggestions
- Previous analyses section with reload functionality
- Two-column layout with persistent results
- Intelligent text truncation for long resumes/JDs

Create:
1. ui/views/profile_analysis_view.py with ProfileAnalysisView class
2. Methods: build(), _analyze_compatibility(), _load_previous_analyses(), _reload_analysis()
3. Integration with ResumeService, JDService, CompatibilityService
4. Use ScoreCardComponent for score display
```

### Prompt 6.4: Questions Generator View
```
Create questions generator view.

Requirements:
- Resume selection dropdown
- Job description selection/upload
- Question type selection (behavioral, technical, situational, company-specific)
- Question count slider (3-15)
- Generate button
- Generated questions display
- Save question set functionality
- Previous question sets list
- Export questions option

Create:
1. ui/views/questions_view.py with QuestionsView class
2. Methods: build(), _generate_questions(), _save_question_set(), _load_question_sets()
3. Integration with QuestionService
4. Dropdown refresh after view build
```

### Prompt 6.5: Practice Session View
```
Create practice session view.

Requirements:
- Question set selection dropdown
- Question selection
- Response mode selection (Written, Audio, Video)
- Start practice button
- Response input area (text, audio recorder, video recorder)
- Timer display
- Submit button
- AI evaluation display: score, STAR method breakdown, strengths, weaknesses, suggestions
- Session history list

Create:
1. ui/views/practice_view.py with PracticeView class
2. Methods: build(), _start_practice(), _submit_response(), _evaluate_response(), _load_history()
3. Integration with PracticeService, RecordingService
4. Support for audio/video recording
```

### Prompt 6.6: Mock Interview View
```
Create comprehensive mock interview hub view.

Requirements:
- New Mock Interview button
- Setup wizard dialog:
  - Interview format selection (Traditional, Technical, Behavioral, Case)
  - Question source (Auto-generate, Question Set, Custom)
  - Configuration: number of questions, difficulty, timing, feedback mode
  - Session name input
- Live interview flow:
  - One question at a time with progress indicator
  - Notes area for keywords
  - Flag/Skip buttons
  - Response input (written/audio/video)
  - Submit response button
- Results view:
  - AI evaluation with scores
  - Strengths and weaknesses
  - Improvement suggestions
- Practice library:
  - Searchable session history
  - View transcripts, audio, video
  - Export session reports

Create:
1. ui/views/mock_interview_view.py with MockInterviewView class
2. Methods: build(), _create_session(), _start_interview(), _submit_response(), _view_results(), _load_library()
3. Integration with MockInterviewService
4. Multi-step wizard UI
5. Session state management
```

### Prompt 6.7: Job Opportunities View
```
Create job search and opportunities view.

Requirements:
- Search form: keywords, location, remote only checkbox
- Search button
- Results display with job cards
- Compatibility score for each job
- Save job button
- Add to planner button
- View job details
- Search history

Create:
1. ui/views/opportunities_view.py with OpportunitiesView class
2. Methods: build(), _search_jobs(), _save_job(), _add_to_planner()
3. Integration with JSearchService
4. Use JobCardComponent for job display
```

### Prompt 6.8: Document Writer View
```
Create document writer view for generating resumes, cover letters, and emails.

Requirements:
- Tab selection: Resume, Cover Letter, Cold Email
- Resume selection/upload
- Job description selection (for cover letter/email)
- Generate button
- Generated document display with editing
- Export buttons (TXT, DOCX)
- Document history

Create:
1. ui/views/writer_view.py with WriterView class
2. Methods: build(), _generate_document(), _export_document()
3. Integration with DocumentService
4. Tab-based UI
5. Dropdown refresh after view build
```

### Prompt 6.9: Application Planner View
```
Create application tracking planner view.

Requirements:
- Statistics dashboard (total, by status, interview rate)
- New Application button (opens dialog)
- Application form: company, position, dates, status, notes, salary
- Applications list with status filter
- Update status button
- Edit/Delete actions
- Convert saved jobs to applications
- Status pipeline visualization

Create:
1. ui/views/planner_view.py with PlannerView class
2. Methods: build(), _add_application(), _update_status(), _edit_application(), _load_applications(), _get_stats()
3. Integration with ApplicationService
4. Status filter dropdown
5. Dialog for add/edit
```

### Prompt 6.10: Career Coach View
```
Create AI career coach chat interface.

Requirements:
- Chat message history display
- Message input field
- Send button
- Quick advice buttons: Resume Tips, Interview Prep, Job Search, Skills Development, Salary Negotiation
- Start/End session buttons
- Previous sessions list with reload
- File attachment button (resume, JD)
- Markdown rendering in responses
- Persistent chat state

Create:
1. ui/views/coach_view.py with CoachView class
2. Methods: build(), _send_message(), _get_quick_advice(), _start_session(), _end_session(), _load_previous_sessions()
3. Integration with CoachService
4. Chat UI with message bubbles
5. Markdown support for formatting
```

### Prompt 6.11: Settings View
```
Create settings view for LLM configuration.

Requirements:
- LLM provider selection (OpenAI, Anthropic, Bedrock, Ollama)
- Model selection dropdown (provider-specific)
- API key input (with encryption)
- Endpoint URL input (for Ollama/Bedrock)
- Temperature slider
- Max tokens input
- Test Connection button (with modal feedback)
- Save Settings button (with confirmation)
- Connection status indicator

Create:
1. ui/views/settings_view.py with SettingsView class
2. Methods: build(), _test_connection(), _save_settings(), _load_settings()
3. Integration with LLMService, LLMSettingsService
4. Modal dialogs for feedback
5. Form validation
```

---

## **PHASE 7: Advanced Features & Polish**

### Prompt 7.1: Audio/Video Recording Service
```
Create audio and video recording service.

Requirements:
- Audio recording using pyaudio
- Video recording using opencv-python
- Transcription using speech recognition
- File saving to data/recordings/audio and data/recordings/video
- Duration tracking
- Start/stop/pause functionality

Create:
1. core/recording_service.py with RecordingService class
2. Methods: start_audio_recording(), stop_audio_recording(), start_video_recording(), stop_video_recording(), transcribe_audio()
3. Integration with PracticeView and MockInterviewView
```

### Prompt 7.2: Text Extractor Utilities
```
Create text extraction utilities for various formats.

Requirements:
- Extract text from PDFs with formatting preservation
- Extract text from DOCX with structure
- Clean and normalize extracted text
- Handle encoding issues

Create:
1. core/text_extractor.py with TextExtractor class
2. Integration with DocumentParser
```

### Prompt 7.3: Logging & Error Handling
```
Enhance logging throughout the application.

Requirements:
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- File logging to data/logs/
- Console logging
- Error tracking and reporting
- Log rotation

Create:
1. utils/logger.py with setup_logger() function
2. Integration across all services and views
3. Error handling in critical paths
```

### Prompt 7.4: Database Migrations System
```
Create database migration system.

Requirements:
- Numbered migration files (001_initial_schema.sql, 002_add_indexes.sql, etc.)
- Migration runner script
- Version tracking
- Rollback support (optional)

Create:
1. database/migrations/ directory with SQL files
2. Migration files for: initial schema, indexes, jsearch_history, mock_interview_tables, missing columns, sync operations
3. Documentation for applying migrations
```

### Prompt 7.5: Installation & Setup Scripts
```
Create installation and verification scripts.

Requirements:
- Database setup script (create_db.py)
- Setup verification script (check_setup.py)
- Batch file for Windows (run_app.bat)
- Comprehensive installation documentation

Create:
1. database/create_db.py (already in Phase 1, enhance)
2. check_setup.py for verifying installation
3. run_app.bat for easy Windows launch
4. Update INSTALLATION.md with troubleshooting
```

---

## **PHASE 8: Testing & Documentation**

### Prompt 8.1: Documentation
```
Create comprehensive documentation.

Requirements:
- README.md with features, quick start, usage guide
- INSTALLATION.md with step-by-step setup, troubleshooting
- API documentation for services
- Code comments throughout
- Architecture overview

Update existing documentation files with complete information.
```

### Prompt 8.2: Error Handling & Edge Cases
```
Enhance error handling throughout the application.

Requirements:
- Graceful degradation when LLM fails
- Database connection retry logic
- File upload error handling
- Validation for all user inputs
- User-friendly error messages
- Fallback behaviors

Review and enhance error handling in all services and views.
```

### Prompt 8.3: Performance Optimization
```
Optimize application performance.

Requirements:
- Database query optimization
- Connection pooling (already implemented)
- Lazy loading for large datasets
- Caching for frequently accessed data
- Efficient file handling
- UI responsiveness improvements

Review and optimize critical paths.
```

---

## **Usage Instructions**

To recreate this project, follow the phases in order:

1. **Phase 1**: Set up project structure, database, and core infrastructure
2. **Phase 2**: Build core utilities (auth, document parsing, encryption, normalizer)
3. **Phase 3**: Implement AI/LLM provider integrations
4. **Phase 4**: Create all business logic services
5. **Phase 5**: Build UI framework and reusable components
6. **Phase 6**: Implement all feature views
7. **Phase 7**: Add advanced features and polish
8. **Phase 8**: Testing, documentation, and optimization

Each prompt can be used independently or in sequence. Adjust prompts based on specific requirements or preferences.

---

**Note**: This is a comprehensive recreation guide. Some prompts may need to be broken down further or combined based on the AI assistant's capabilities and context window size.

