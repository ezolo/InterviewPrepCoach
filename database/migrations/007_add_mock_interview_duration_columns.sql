-- Add missing duration columns to mock_interview_responses table
-- This migration adds duration_seconds, prep_time_seconds, and response_time_seconds columns
-- Run this migration if you get "Unknown column 'duration_seconds'" error

-- Check and add duration_seconds column
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'mock_interview_responses'
    AND COLUMN_NAME = 'duration_seconds'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE mock_interview_responses ADD COLUMN duration_seconds INT DEFAULT 0 AFTER is_skipped;',
    'SELECT "Column duration_seconds already exists" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check and add prep_time_seconds column
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'mock_interview_responses'
    AND COLUMN_NAME = 'prep_time_seconds'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE mock_interview_responses ADD COLUMN prep_time_seconds INT DEFAULT 0 AFTER duration_seconds;',
    'SELECT "Column prep_time_seconds already exists" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check and add response_time_seconds column
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'mock_interview_responses'
    AND COLUMN_NAME = 'response_time_seconds'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE mock_interview_responses ADD COLUMN response_time_seconds INT DEFAULT 0 AFTER prep_time_seconds;',
    'SELECT "Column response_time_seconds already exists" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Migrate data from time_taken_seconds if it exists
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'mock_interview_responses'
    AND COLUMN_NAME = 'time_taken_seconds'
);

SET @sql = IF(@col_exists > 0,
    'UPDATE mock_interview_responses SET duration_seconds = time_taken_seconds WHERE duration_seconds = 0 AND time_taken_seconds IS NOT NULL;',
    'SELECT "Column time_taken_seconds does not exist, skipping data migration" AS message;'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

