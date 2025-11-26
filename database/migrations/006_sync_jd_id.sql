-- Migration 006: Sync jd_id with id for job_descriptions
-- This ensures jd_id matches id for existing and new records

-- Update existing records to set jd_id = id
UPDATE job_descriptions SET jd_id = id WHERE jd_id IS NULL;

-- Create trigger to auto-set jd_id = id for new records
DELIMITER $$

CREATE TRIGGER IF NOT EXISTS job_descriptions_before_insert
BEFORE INSERT ON job_descriptions
FOR EACH ROW
BEGIN
    IF NEW.jd_id IS NULL THEN
        SET NEW.jd_id = NEW.id;
    END IF;
END$$

CREATE TRIGGER IF NOT EXISTS job_descriptions_after_insert
AFTER INSERT ON job_descriptions
FOR EACH ROW
BEGIN
    UPDATE job_descriptions SET jd_id = id WHERE id = NEW.id AND (jd_id IS NULL OR jd_id != id);
END$$

DELIMITER ;

