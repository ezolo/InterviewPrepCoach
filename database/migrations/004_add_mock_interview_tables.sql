-- Mock Interview Sessions
-- This migration adds tables for comprehensive mock interview functionality

-- Mock interview sessions (full interview sessions with multiple questions)
CREATE TABLE IF NOT EXISTS mock_interview_sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_name VARCHAR(255),
    format_type ENUM('traditional', 'technical', 'behavioral', 'case') DEFAULT 'traditional',
    question_source ENUM('set', 'generated', 'custom') DEFAULT 'generated',
    question_set_id INT,
    resume_id INT,
    jd_id INT,
    config JSON,  -- Stores: num_questions, difficulty, time_per_question, feedback_mode, etc.
    status ENUM('draft', 'in_progress', 'completed', 'paused') DEFAULT 'draft',
    current_question_index INT DEFAULT 0,
    total_questions INT DEFAULT 0,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (question_set_id) REFERENCES question_sets(set_id) ON DELETE SET NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE SET NULL,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE SET NULL
);

-- Mock interview responses (one per question in a session)
CREATE TABLE IF NOT EXISTS mock_interview_responses (
    response_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    question_id INT NOT NULL,
    question_index INT NOT NULL,
    response_mode ENUM('written', 'audio', 'video') DEFAULT 'written',
    response_text TEXT,
    audio_file_path VARCHAR(500),
    video_file_path VARCHAR(500),
    transcript TEXT,
    notes TEXT,  -- User's notes/keywords
    is_flagged BOOLEAN DEFAULT FALSE,
    is_skipped BOOLEAN DEFAULT FALSE,
    duration_seconds INT,
    prep_time_seconds INT,
    response_time_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE,
    INDEX idx_session_question (session_id, question_index)
);

-- Mock interview feedback (AI evaluation per question and session summary)
CREATE TABLE IF NOT EXISTS mock_interview_feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    response_id INT,  -- NULL for session-level feedback
    feedback_type ENUM('question', 'session') NOT NULL,
    score_content DECIMAL(5,2),
    score_delivery DECIMAL(5,2),
    score_overall DECIMAL(5,2),
    star_analysis JSON,  -- STAR breakdown for behavioral questions
    strengths JSON,
    weaknesses JSON,
    suggestions JSON,
    delivery_metrics JSON,  -- pace, tone, filler_words, eye_contact, etc.
    recommendations TEXT,
    skill_tags JSON,  -- Tags like: communication, problem-solving, leadership
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (response_id) REFERENCES mock_interview_responses(response_id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_response (response_id)
);

-- Mock interview analytics (aggregated stats for dashboard)
CREATE TABLE IF NOT EXISTS mock_interview_analytics (
    analytics_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    format_type VARCHAR(50),
    total_questions INT,
    completed_questions INT,
    average_score DECIMAL(5,2),
    total_duration_seconds INT,
    skill_scores JSON,  -- Radar chart data
    trend_data JSON,  -- Comparison with previous sessions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES mock_interview_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_session (session_id)
);

