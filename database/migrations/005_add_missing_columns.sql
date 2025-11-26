-- Migration 005: Add missing columns to align with code expectations
-- Run this after creating the database if you see column errors

-- Add uploaded_at to resumes table
ALTER TABLE resumes ADD COLUMN uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX idx_uploaded_at ON resumes(uploaded_at);

-- Add company_name and job_title to job_descriptions table
ALTER TABLE job_descriptions ADD COLUMN company_name VARCHAR(255);
ALTER TABLE job_descriptions ADD COLUMN job_title VARCHAR(255);
CREATE INDEX idx_company_name ON job_descriptions(company_name);

-- Add evaluation_score and other practice columns to practice_sessions table
ALTER TABLE practice_sessions ADD COLUMN evaluation_score DECIMAL(5,2);
ALTER TABLE practice_sessions ADD COLUMN question_id INT;
ALTER TABLE practice_sessions ADD COLUMN response_mode ENUM('written', 'audio', 'video');
ALTER TABLE practice_sessions ADD COLUMN response_text TEXT;
ALTER TABLE practice_sessions ADD COLUMN audio_file_path VARCHAR(500);
ALTER TABLE practice_sessions ADD COLUMN video_file_path VARCHAR(500);
ALTER TABLE practice_sessions ADD COLUMN transcript TEXT;
ALTER TABLE practice_sessions ADD COLUMN evaluation_feedback TEXT;
ALTER TABLE practice_sessions ADD COLUMN strengths JSON;
ALTER TABLE practice_sessions ADD COLUMN improvements JSON;
ALTER TABLE practice_sessions ADD COLUMN session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX idx_evaluation_score ON practice_sessions(evaluation_score);
ALTER TABLE practice_sessions ADD FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE SET NULL;

-- Add updated_at to coach_conversations table
ALTER TABLE coach_conversations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
CREATE INDEX idx_updated_at ON coach_conversations(updated_at);

-- Add model_name, endpoint_url, top_p to llm_settings table
ALTER TABLE llm_settings ADD COLUMN IF NOT EXISTS model_name VARCHAR(100);
ALTER TABLE llm_settings ADD COLUMN IF NOT EXISTS endpoint_url VARCHAR(500);
ALTER TABLE llm_settings ADD COLUMN IF NOT EXISTS top_p DECIMAL(3,2) DEFAULT 1.0;

-- Update model_name to match model if model_name is NULL
UPDATE llm_settings SET model_name = model WHERE model_name IS NULL OR model_name = '';

