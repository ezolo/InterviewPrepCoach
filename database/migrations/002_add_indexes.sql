-- Performance indexes for Interview Prep AI

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Resumes
CREATE INDEX IF NOT EXISTS idx_resumes_user_active ON resumes(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_resumes_uploaded ON resumes(uploaded_at DESC);

-- Job descriptions
CREATE INDEX IF NOT EXISTS idx_jd_user_company ON job_descriptions(user_id, company_name);
CREATE INDEX IF NOT EXISTS idx_jd_created ON job_descriptions(created_at DESC);

-- Compatibility analyses
CREATE INDEX IF NOT EXISTS idx_compat_score ON compatibility_analyses(compatibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_compat_user ON compatibility_analyses(user_id, analyzed_at DESC);

-- Questions
CREATE INDEX IF NOT EXISTS idx_questions_set_type ON questions(set_id, question_type);

-- Practice sessions
CREATE INDEX IF NOT EXISTS idx_practice_user_date ON practice_sessions(user_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_practice_question ON practice_sessions(question_id);

-- Applications
CREATE INDEX IF NOT EXISTS idx_app_user_status ON applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_app_dates ON applications(user_id, applied_date DESC, interview_date);

-- Reminders
CREATE INDEX IF NOT EXISTS idx_reminder_date ON reminders(reminder_date, is_completed);

-- Documents
CREATE INDEX IF NOT EXISTS idx_docs_user_type ON generated_documents(user_id, document_type, created_at DESC);

-- Coach conversations
CREATE INDEX IF NOT EXISTS idx_coach_user_updated ON coach_conversations(user_id, updated_at DESC);

-- LLM settings
CREATE INDEX IF NOT EXISTS idx_llm_user_active ON llm_settings(user_id, is_active);

-- JSearch jobs
CREATE INDEX IF NOT EXISTS idx_jsearch_title_company ON jsearch_jobs(job_title, company_name);
CREATE INDEX IF NOT EXISTS idx_jsearch_cached ON jsearch_jobs(cached_at DESC);

-- Job searches
CREATE INDEX IF NOT EXISTS idx_searches_user ON job_searches(user_id, searched_at DESC);

