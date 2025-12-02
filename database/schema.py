"""
Database schema - SQL statements for creating all tables
Comprehensive schema aligned with all service code
"""

CREATE_DATABASE = """
CREATE DATABASE IF NOT EXISTS interview_prep_ai 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
"""

CREATE_TABLES = [
    # Users table
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # User profiles table
    """
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        full_name VARCHAR(255),
        phone VARCHAR(50),
        location VARCHAR(255),
        linkedin_url VARCHAR(500),
        github_url VARCHAR(500),
        portfolio_url VARCHAR(500),
        target_role VARCHAR(255),
        target_industry VARCHAR(255),
        years_experience INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Resumes table
    """
    CREATE TABLE IF NOT EXISTS resumes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        resume_id INT,
        user_id INT NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_type VARCHAR(50),
        file_size INT,
        extracted_text LONGTEXT,
        resume_text LONGTEXT,
        parsed_data JSON,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_is_active (is_active),
        INDEX idx_uploaded_at (uploaded_at),
        INDEX idx_resume_id (resume_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Job descriptions table
    """
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        jd_id INT,
        user_id INT NOT NULL,
        title VARCHAR(255),
        company VARCHAR(255),
        company_name VARCHAR(255),
        job_title VARCHAR(255),
        location VARCHAR(255),
        salary_range VARCHAR(100),
        description_text LONGTEXT,
        jd_text LONGTEXT,
        requirements LONGTEXT,
        parsed_requirements JSON,
        parsed_data JSON,
        source VARCHAR(100),
        source_type VARCHAR(50),
        source_url VARCHAR(500),
        file_path VARCHAR(500),
        job_url VARCHAR(500),
        job_type VARCHAR(100),
        remote_type VARCHAR(100),
        salary_min DECIMAL(12,2),
        salary_max DECIMAL(12,2),
        external_job_id VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_company (company),
        INDEX idx_company_name (company_name),
        INDEX idx_job_title (job_title),
        INDEX idx_jd_id (jd_id),
        INDEX idx_source_type (source_type),
        UNIQUE INDEX idx_jd_id_unique (jd_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Compatibility analyses table
    """
    CREATE TABLE IF NOT EXISTS compatibility_analyses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        analysis_id INT,
        user_id INT NOT NULL,
        resume_id INT NOT NULL,
        job_description_id INT NOT NULL,
        jd_id INT NOT NULL,
        compatibility_score DECIMAL(5,2),
        matched_skills JSON,
        missing_skills JSON,
        missing_qualifications JSON,
        strengths JSON,
        suggestions LONGTEXT,
        improvement_suggestions JSON,
        analysis_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
        FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE CASCADE,
        FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_score (compatibility_score),
        INDEX idx_jd_id (jd_id),
        INDEX idx_analyzed_at (analyzed_at),
        INDEX idx_analysis_id (analysis_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Question sets table
    """
    CREATE TABLE IF NOT EXISTS question_sets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        set_id INT,
        user_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        set_name VARCHAR(255) NOT NULL,
        description TEXT,
        job_description_id INT,
        jd_id INT,
        resume_id INT,
        difficulty_level ENUM('easy', 'medium', 'hard', 'mixed') DEFAULT 'mixed',
        question_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
        FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_jd_id (jd_id),
        INDEX idx_set_id (set_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Questions table
    """
    CREATE TABLE IF NOT EXISTS questions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        question_id INT,
        question_set_id INT NOT NULL,
        set_id INT NOT NULL,
        question_text LONGTEXT NOT NULL,
        question_type ENUM('behavioral', 'technical', 'situational', 'case_study') NOT NULL,
        difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
        category VARCHAR(255),
        ideal_answer_points LONGTEXT,
        evaluation_criteria JSON,
        tags JSON,
        order_index INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_set_id) REFERENCES question_sets(id) ON DELETE CASCADE,
        FOREIGN KEY (set_id) REFERENCES question_sets(set_id) ON DELETE CASCADE,
        INDEX idx_question_set_id (question_set_id),
        INDEX idx_set_id (set_id),
        INDEX idx_question_id (question_id),
        INDEX idx_type (question_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Practice sessions table
    """
    CREATE TABLE IF NOT EXISTS practice_sessions (
        session_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        question_set_id INT,
        question_id INT,
        session_type VARCHAR(50),
        response_mode ENUM('written', 'audio', 'video') DEFAULT 'written',
        response_text LONGTEXT,
        audio_file_path VARCHAR(500),
        video_file_path VARCHAR(500),
        transcript LONGTEXT,
        evaluation_score DECIMAL(5,2),
        evaluation_feedback JSON,
        strengths JSON,
        improvements JSON,
        status VARCHAR(50) DEFAULT 'in_progress',
        session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_seconds INT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (question_set_id) REFERENCES question_sets(id) ON DELETE SET NULL,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_status (status),
        INDEX idx_evaluation_score (evaluation_score),
        INDEX idx_session_date (session_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Practice responses table
    """
    CREATE TABLE IF NOT EXISTS practice_responses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        question_id INT NOT NULL,
        response_text LONGTEXT,
        audio_file_path VARCHAR(500),
        video_file_path VARCHAR(500),
        transcription LONGTEXT,
        ai_score DECIMAL(5,2),
        ai_feedback LONGTEXT,
        evaluation_data JSON,
        time_taken_seconds INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES practice_sessions(session_id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
        INDEX idx_session_id (session_id),
        INDEX idx_question_id (question_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Applications table
    """
    CREATE TABLE IF NOT EXISTS applications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT,
        user_id INT NOT NULL,
        job_description_id INT,
        jd_id INT,
        company VARCHAR(255) NOT NULL,
        company_name VARCHAR(255),
        job_title VARCHAR(255) NOT NULL,
        position VARCHAR(255),
        location VARCHAR(255),
        application_date DATE,
        applied_date DATE,
        interview_date DATE,
        follow_up_date DATE,
        status ENUM('applied', 'phone_screen', 'technical_interview', 
                    'onsite_interview', 'offer_received', 'rejected', 'withdrawn', 'saved') 
                DEFAULT 'saved',
        job_url VARCHAR(500),
        salary_expectation VARCHAR(100),
        salary_offered DECIMAL(12,2),
        notes LONGTEXT,
        resume_used INT,
        cover_letter_used INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
        FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_status (status),
        INDEX idx_application_date (application_date),
        INDEX idx_applied_date (applied_date),
        INDEX idx_application_id (application_id),
        INDEX idx_jd_id (jd_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Application reminders table
    """
    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        reminder_date DATE NOT NULL,
        reminder_type VARCHAR(50),
        message TEXT,
        is_completed BOOLEAN DEFAULT FALSE,
        sent_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE,
        INDEX idx_application_id (application_id),
        INDEX idx_reminder_date (reminder_date),
        INDEX idx_is_completed (is_completed)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Generated documents table
    """
    CREATE TABLE IF NOT EXISTS generated_documents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        document_type ENUM('resume', 'cover_letter', 'cold_email', 'thank_you', 'other') NOT NULL,
        title VARCHAR(255) NOT NULL,
        content LONGTEXT NOT NULL,
        file_path VARCHAR(500),
        template_used VARCHAR(100),
        job_description_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_document_type (document_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Coach conversations table
    """
    CREATE TABLE IF NOT EXISTS coach_conversations (
        conversation_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        session_id VARCHAR(255),
        title VARCHAR(255),
        messages JSON,
        agent_state JSON,
        goals JSON,
        action_items JSON,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        message_count INT DEFAULT 0,
        is_archived BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_session_id (session_id),
        INDEX idx_last_message_at (last_message_at),
        INDEX idx_updated_at (updated_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Coach messages table
    """
    CREATE TABLE IF NOT EXISTS coach_messages (
        message_id INT AUTO_INCREMENT PRIMARY KEY,
        conversation_id INT NOT NULL,
        role ENUM('user', 'assistant', 'system') NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES coach_conversations(conversation_id) ON DELETE CASCADE,
        INDEX idx_conversation_id (conversation_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # JSearch jobs table
    """
    CREATE TABLE IF NOT EXISTS jsearch_jobs (
        job_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        external_job_id VARCHAR(255) UNIQUE,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255),
        company_name VARCHAR(255),
        location VARCHAR(255),
        description LONGTEXT,
        salary_min DECIMAL(12,2),
        salary_max DECIMAL(12,2),
        is_remote BOOLEAN DEFAULT FALSE,
        job_url VARCHAR(500),
        apply_url VARCHAR(500),
        posted_date DATETIME,
        job_data JSON,
        compatibility_score DECIMAL(5,2),
        is_saved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_external_job_id (external_job_id),
        INDEX idx_is_saved (is_saved),
        INDEX idx_compatibility_score (compatibility_score)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # JSearch history table
    """
    CREATE TABLE IF NOT EXISTS jsearch_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        search_query VARCHAR(500) NOT NULL,
        location VARCHAR(255),
        remote_only BOOLEAN DEFAULT FALSE,
        results_count INT DEFAULT 0,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_searched_at (searched_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # User job search history table
    """
    CREATE TABLE IF NOT EXISTS job_searches (
        search_id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        search_query VARCHAR(500) NOT NULL,
        location VARCHAR(255),
        remote_only BOOLEAN DEFAULT FALSE,
        results_count INT,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_searched_at (searched_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # LLM settings table
    """
    CREATE TABLE IF NOT EXISTS llm_settings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        provider ENUM('openai', 'anthropic', 'bedrock', 'ollama') NOT NULL,
        model VARCHAR(100) NOT NULL,
        model_name VARCHAR(255),
        api_key_encrypted TEXT,
        endpoint_url VARCHAR(500),
        temperature DECIMAL(3,2) DEFAULT 0.70,
        max_tokens INT DEFAULT 2000,
        top_p DECIMAL(3,2),
        additional_config JSON,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_provider (user_id, provider),
        INDEX idx_user_id (user_id),
        INDEX idx_is_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Mock interview sessions table
    """
    CREATE TABLE IF NOT EXISTS mock_interview_sessions (
        session_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        session_name VARCHAR(255),
        format_type ENUM('traditional', 'technical', 'behavioral', 'case') DEFAULT 'traditional',
        question_source ENUM('set', 'generated', 'custom') DEFAULT 'generated',
        question_set_id INT,
        resume_id INT,
        job_description_id INT,
        jd_id INT,
        config JSON,
        status ENUM('draft', 'in_progress', 'completed', 'paused') DEFAULT 'draft',
        current_question_index INT DEFAULT 0,
        total_questions INT DEFAULT 0,
        started_at TIMESTAMP NULL,
        completed_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (question_set_id) REFERENCES question_sets(id) ON DELETE SET NULL,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL,
        FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
        FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL,
        INDEX idx_user_id (user_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Mock interview responses table
    """
    CREATE TABLE IF NOT EXISTS mock_interview_responses (
        response_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        question_id INT NOT NULL,
        question_index INT NOT NULL,
        response_mode ENUM('written', 'audio', 'video') DEFAULT 'written',
        response_text LONGTEXT,
        audio_file_path VARCHAR(500),
        video_file_path VARCHAR(500),
        transcript LONGTEXT,
        notes TEXT,
        is_flagged BOOLEAN DEFAULT FALSE,
        is_skipped BOOLEAN DEFAULT FALSE,
        duration_seconds INT DEFAULT 0,
        prep_time_seconds INT DEFAULT 0,
        response_time_seconds INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
        INDEX idx_session_id (session_id),
        INDEX idx_question_id (question_id),
        INDEX idx_question_index (question_index)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Mock interview feedback table
    """
    CREATE TABLE IF NOT EXISTS mock_interview_feedback (
        feedback_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        response_id INT,
        feedback_type VARCHAR(50),
        score_content DECIMAL(5,2),
        score_delivery DECIMAL(5,2),
        score_overall DECIMAL(5,2),
        star_analysis JSON,
        strengths JSON,
        weaknesses JSON,
        suggestions JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
        FOREIGN KEY (response_id) REFERENCES mock_interview_responses(response_id) ON DELETE CASCADE,
        INDEX idx_session_id (session_id),
        INDEX idx_response_id (response_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    
    # Mock interview analytics table
    """
    CREATE TABLE IF NOT EXISTS mock_interview_analytics (
        analytics_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        total_questions INT DEFAULT 0,
        completed_questions INT DEFAULT 0,
        average_score DECIMAL(5,2),
        strengths_summary JSON,
        weaknesses_summary JSON,
        improvement_areas JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
        INDEX idx_session_id (session_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
]

# Default user for testing
INSERT_DEFAULT_USER = """
INSERT IGNORE INTO users (id, username, email, password_hash) 
VALUES (1, 'default_user', 'user@interviewprep.ai', NULL);
"""
