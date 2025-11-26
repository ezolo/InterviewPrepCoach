"""Job Description service - manages job descriptions"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from database import DatabaseManager
from database.connection import execute_query
from core.document_parser import DocumentParser
from core.text_extractor import extract_skills
from config.settings import Settings
import json
from datetime import datetime

class JobDescriptionService:
    """Manages job description operations"""
    
    @staticmethod
    def save_jd_from_file(user_id: int, file_name: str, file_content: bytes,
                         company_name: Optional[str] = None,
                         job_title: Optional[str] = None) -> Optional[int]:
        """Save JD from uploaded file
        
        Args:
            user_id: User ID
            file_name: Original filename
            file_content: File bytes
            company_name: Company name (optional)
            job_title: Job title (optional)
            
        Returns:
            JD ID if successful
        """
        try:
            # Save file
            file_type = Path(file_name).suffix.lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"jd_{user_id}_{timestamp}{file_type}"
            file_path = Settings.JD_DIR / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Parse text
            jd_text = DocumentParser.parse_file(str(file_path))
            
            if not jd_text:
                return None
            
            # Extract requirements
            parsed_requirements = {
                "required_skills": extract_skills(jd_text),
                "text_length": len(jd_text)
            }
            
            # job_title is NOT NULL in schema, so provide default if not given
            if not job_title:
                # Try to extract from filename or use default
                job_title = Path(file_name).stem.replace('_', ' ').title() or "Job Position"
            
            query = """
                INSERT INTO job_descriptions
                (user_id, source_type, file_path, company_name, job_title, title,
                 jd_text, description_text, parsed_requirements)
                VALUES (%s, 'upload', %s, %s, %s, %s, %s, %s, %s)
            """
            jd_id = execute_query(
                query,
                (user_id, str(file_path), company_name, job_title, job_title or "Job Position",
                 jd_text, jd_text, json.dumps(parsed_requirements)),
                commit=True
            )
            # Sync jd_id column with id for code compatibility
            if jd_id:
                execute_query(
                    "UPDATE job_descriptions SET jd_id = id WHERE id = %s",
                    (jd_id,),
                    commit=True
                )
            print(f"[INFO] JD saved from file with ID: {jd_id}")
            return jd_id
        
        except Exception as e:
            print(f"[ERROR] Error saving JD from file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def save_jd_from_text(user_id: int, jd_text: str,
                         company_name: Optional[str] = None,
                         job_title: Optional[str] = None,
                         job_url: Optional[str] = None) -> Optional[int]:
        """Save JD from pasted text
        
        Args:
            user_id: User ID
            jd_text: Job description text
            company_name: Company name (optional)
            job_title: Job title (optional)
            job_url: Job URL (optional)
            
        Returns:
            JD ID if successful
        """
        try:
            # Extract requirements
            parsed_requirements = {
                "required_skills": extract_skills(jd_text),
                "text_length": len(jd_text)
            }
            
            # job_title is NOT NULL in schema, so provide default if not given
            if not job_title:
                # Try to extract from text or use default
                job_title = "Job Position"  # Default title
            
            # Use execute_query instead of get_cursor for consistency
            query = """
                INSERT INTO job_descriptions
                (user_id, source_type, company_name, job_title, title, job_url,
                 jd_text, description_text, parsed_requirements)
                VALUES (%s, 'paste', %s, %s, %s, %s, %s, %s, %s)
            """
            jd_id = execute_query(
                query,
                (user_id, company_name, job_title, job_title or "Job Position", job_url,
                 jd_text, jd_text, json.dumps(parsed_requirements)),
                commit=True
            )
            # Sync jd_id column with id for code compatibility
            if jd_id:
                execute_query(
                    "UPDATE job_descriptions SET jd_id = id WHERE id = %s",
                    (jd_id,),
                    commit=True
                )
            print(f"[INFO] JD saved from text with ID: {jd_id}")
            return jd_id
        
        except Exception as e:
            print(f"[ERROR] Error saving JD from text: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def save_jd_from_jsearch(user_id: int, job_data: Dict[str, Any]) -> Optional[int]:
        """Save JD from JSearch API result
        
        Args:
            user_id: User ID
            job_data: Job data from JSearch API
            
        Returns:
            JD ID if successful
        """
        try:
            from database.connection import get_connection
            
            print(f"[DEBUG] ===== Saving JD from JSearch =====")
            print(f"[DEBUG] User ID: {user_id}")
            print(f"[DEBUG] Job data keys: {list(job_data.keys())}")
            print(f"[DEBUG] Job data sample: {str(job_data)[:500]}...")
            
            # Get job description text - try multiple possible keys
            jd_text = (job_data.get('job_description') or 
                      job_data.get('description') or 
                      job_data.get('job_highlights', {}).get('description', []) if isinstance(job_data.get('job_highlights'), dict) else '')
            
            if isinstance(jd_text, list):
                jd_text = ' '.join(jd_text)
            
            if not jd_text or len(jd_text.strip()) == 0:
                # Build a basic description from available data
                jd_text = f"Job Title: {job_data.get('job_title', 'Unknown')}\n"
                jd_text += f"Company: {job_data.get('employer_name', 'Unknown')}\n"
                jd_text += f"Location: {job_data.get('job_city', 'Unknown')}\n"
                if job_data.get('job_description'):
                    jd_text += f"\n{job_data.get('job_description')}"
            
            # Ensure jd_text is not empty (required field)
            if not jd_text or len(jd_text.strip()) == 0:
                jd_text = "Job description not available"
            
            # Extract requirements
            parsed_requirements = {
                "required_skills": job_data.get('job_required_skills', []),
                "required_experience": job_data.get('job_required_experience', {}),
                "text_length": len(jd_text)
            }
            
            # Get values with fallbacks - match migration schema exactly
            company_name = job_data.get('employer_name') or job_data.get('company_name') or job_data.get('company', 'Unknown Company')
            job_title = job_data.get('job_title') or job_data.get('title', 'Unknown Position')
            location = job_data.get('job_city') or job_data.get('location', '')
            job_type = job_data.get('job_employment_type', 'Full-time')
            remote_type = 'Remote' if job_data.get('job_is_remote') else 'Onsite'
            external_job_id = job_data.get('job_id') or job_data.get('job_employer_job_id', '')
            job_url = job_data.get('job_apply_link') or job_data.get('job_url') or job_data.get('job_google_link', '')
            salary_min = job_data.get('job_min_salary') or job_data.get('salary_min')
            salary_max = job_data.get('job_max_salary') or job_data.get('salary_max')
            
            print(f"[DEBUG] Prepared data: title='{job_title[:50]}', company='{company_name[:30]}', jd_text_length={len(jd_text)}")
            
            # Match migration schema exactly (001_initial_schema.sql)
            query = """
                INSERT INTO job_descriptions
                (user_id, source_type, company_name, job_title, title, location,
                 job_type, remote_type, jd_text, description_text, parsed_requirements,
                 external_job_id, job_url, salary_min, salary_max)
                VALUES (%s, 'jsearch', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (user_id, company_name, job_title, job_title or "Job Position", location, job_type, remote_type,
                     jd_text, jd_text, json.dumps(parsed_requirements), external_job_id, job_url,
                     salary_min, salary_max)
            
            print(f"[DEBUG] Executing query with {len(params)} parameters")
            
            # Execute query and get lastrowid
            conn = None
            cursor = None
            try:
                from database.connection import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                jd_id = cursor.lastrowid
                # Sync jd_id column with id for code compatibility
                if jd_id:
                    cursor.execute("UPDATE job_descriptions SET jd_id = id WHERE id = %s", (jd_id,))
                    conn.commit()
                cursor.close()
                conn.close()
                
                if jd_id and jd_id > 0:
                    print(f"[DEBUG] Successfully saved JD with ID: {jd_id}")
                    return jd_id
                else:
                    print(f"[DEBUG] lastrowid is {jd_id}, which is invalid")
                    return None
            except Exception as db_error:
                if conn:
                    conn.rollback()
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                raise db_error
        
        except Exception as e:
            print(f"[ERROR] Error saving JD from JSearch: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_job_description(jd_id: int) -> Optional[Dict[str, Any]]:
        """Get job description by ID (alias for get_jd)
        
        Args:
            jd_id: JD ID
            
        Returns:
            JD dict or None
        """
        return JobDescriptionService.get_jd(jd_id)
    
    @staticmethod
    def get_jd(jd_id: int) -> Optional[Dict[str, Any]]:
        """Get job description by ID
        
        Args:
            jd_id: JD ID
            
        Returns:
            JD dict or None
        """
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM job_descriptions
                    WHERE jd_id = %s
                """, (jd_id,))
                
                return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching JD: {e}")
            return None
    
    @staticmethod
    def get_user_jds(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all JDs for user
        
        Args:
            user_id: User ID
            limit: Maximum number to return
            
        Returns:
            List of JD dicts
        """
        query = """
        SELECT jd_id, company_name, job_title, source_type, created_at
        FROM job_descriptions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
    
    @staticmethod
    def delete_jd(jd_id: int, user_id: int) -> bool:
        """Delete a job description
        
        Args:
            jd_id: JD ID
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM job_descriptions
                    WHERE jd_id = %s AND user_id = %s
                """, (jd_id, user_id))
                
                return True
        except Exception as e:
            print(f"Error deleting JD: {e}")
            return False
    
    @staticmethod
    def get_user_job_descriptions(user_id: int, limit: int = 20) -> List[Dict]:
        """Get all job descriptions for a user"""
        query = """
        SELECT * FROM job_descriptions 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []

