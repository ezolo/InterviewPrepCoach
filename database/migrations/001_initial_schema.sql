-- Interview Prep AI Database Schema
-- MySQL 8.0+

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- User profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    years_experience INT,
    target_role VARCHAR(255),
    target_salary_min DECIMAL(10,2),
    target_salary_max DECIMAL(10,2),
    skills JSON,
    profile_data JSON,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Resumes
CREATE TABLE IF NOT EXISTS resumes (
    resume_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    resume_text TEXT,
    parsed_data JSON,
    is_active BOOLEAN DEFAULT TRUE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Job descriptions
CREATE TABLE IF NOT EXISTS job_descriptions (
    jd_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    source_type ENUM('upload', 'paste', 'jsearch') DEFAULT 'paste',
    file_path VARCHAR(500),
    company_name VARCHAR(255),
    job_title VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    job_type VARCHAR(100),
    remote_type VARCHAR(50),
    jd_text TEXT NOT NULL,
    parsed_requirements JSON,
    external_job_id VARCHAR(255),
    job_url VARCHAR(500),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Compatibility analyses
CREATE TABLE IF NOT EXISTS compatibility_analyses (
    analysis_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    resume_id INT NOT NULL,
    jd_id INT NOT NULL,
    compatibility_score DECIMAL(5,2),
    matched_skills JSON,
    missing_skills JSON,
    missing_qualifications JSON,
    improvement_suggestions TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE CASCADE
);

-- Question sets
CREATE TABLE IF NOT EXISTS question_sets (
    set_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    set_name VARCHAR(255) NOT NULL,
    jd_id INT,
    resume_id INT,
    question_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE SET NULL
);

-- Questions
CREATE TABLE IF NOT EXISTS questions (
    question_id INT PRIMARY KEY AUTO_INCREMENT,
    set_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('behavioral', 'technical', 'situational', 'company_specific') NOT NULL,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    category VARCHAR(100),
    ideal_answer_points JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_id) REFERENCES question_sets(set_id) ON DELETE CASCADE
);

-- Practice sessions
CREATE TABLE IF NOT EXISTS practice_sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    response_mode ENUM('written', 'audio', 'video') NOT NULL,
    response_text TEXT,
    audio_file_path VARCHAR(500),
    video_file_path VARCHAR(500),
    transcript TEXT,
    evaluation_score DECIMAL(5,2),
    evaluation_feedback TEXT,
    strengths JSON,
    improvements JSON,
    duration_seconds INT,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- Applications tracker
CREATE TABLE IF NOT EXISTS applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    jd_id INT,
    company_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    job_url VARCHAR(500),
    location VARCHAR(255),
    status ENUM('saved', 'applied', 'screening', 'interview', 'final_round', 'offer', 'rejected', 'withdrawn') DEFAULT 'saved',
    applied_date DATE,
    interview_date DATETIME,
    notes TEXT,
    follow_up_date DATE,
    salary_offered DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL
);

-- Application reminders
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT NOT NULL,
    reminder_date DATETIME NOT NULL,
    reminder_type VARCHAR(100),
    message TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE
);

-- Generated documents
CREATE TABLE IF NOT EXISTS generated_documents (
    document_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    document_type ENUM('resume', 'cover_letter', 'cold_email') NOT NULL,
    jd_id INT,
    content TEXT NOT NULL,
    file_path VARCHAR(500),
    tone VARCHAR(50),
    emphasis_areas JSON,
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL
);

-- Career coach conversations
CREATE TABLE IF NOT EXISTS coach_conversations (
    conversation_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    messages JSON,
    agent_state JSON,
    goals JSON,
    action_items JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- LLM settings
CREATE TABLE IF NOT EXISTS llm_settings (
    setting_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    provider ENUM('openai', 'anthropic', 'bedrock', 'ollama') NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_key_encrypted VARCHAR(500),
    endpoint_url VARCHAR(500),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INT DEFAULT 2000,
    top_p DECIMAL(3,2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- JSearch cached jobs
CREATE TABLE IF NOT EXISTS jsearch_jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    external_job_id VARCHAR(255) UNIQUE NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    company_logo_url VARCHAR(500),
    location VARCHAR(255),
    job_type VARCHAR(100),
    remote_type VARCHAR(50),
    description TEXT,
    requirements TEXT,
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    job_url VARCHAR(500) NOT NULL,
    posted_date DATETIME,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_external_id (external_job_id)
);

-- User job search history
CREATE TABLE IF NOT EXISTS job_searches (
    search_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    search_query VARCHAR(500) NOT NULL,
    location VARCHAR(255),
    remote_only BOOLEAN DEFAULT FALSE,
    results_count INT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- JSearch history table (for JSearch API integration)
CREATE TABLE IF NOT EXISTS jsearch_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    search_query VARCHAR(500) NOT NULL,
    location VARCHAR(255),
    remote_only BOOLEAN DEFAULT FALSE,
    results_count INT DEFAULT 0,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_searched_at (searched_at)
);

