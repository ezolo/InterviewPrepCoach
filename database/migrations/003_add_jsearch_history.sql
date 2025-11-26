-- Add jsearch_history table if it doesn't exist
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

