"""
JSearch API integration service for job opportunities
"""
import os
import json
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from database.connection import execute_query

load_dotenv()

class JSearchService:
    """Handle JSearch API integration"""
    
    API_URL = "https://jsearch.p.rapidapi.com/search"
    API_KEY = os.getenv('JSEARCH_API_KEY', '')
    
    @staticmethod
    def search_jobs(query: str, location: str = "", 
                   remote_only: bool = False, num_pages: int = 1,
                   user_id: Optional[int] = None) -> Dict:
        """
        Search for jobs using JSearch API
        
        Args:
            query: Search query (job title, skills, etc.)
            location: Location filter
            remote_only: Only return remote jobs
            num_pages: Number of pages to fetch
            user_id: Optional user ID for saving search history
            
        Returns:
            Dict with 'jobs' list or 'error' message
        """
        try:
            # Save search history if user_id provided
            if user_id:
                execute_query(
                    """INSERT INTO jsearch_history 
                       (user_id, search_query, location, remote_only, results_count) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, query, location or "", remote_only, 0),
                    commit=True
                )
            
            if not JSearchService.API_KEY or JSearchService.API_KEY.strip() == "":
                print("[WARNING] JSearch API key not found. Using mock data.")
                return {"jobs": JSearchService._get_mock_jobs(query)}
            
            # Use requests params for proper URL encoding
            import urllib.parse
            
            headers = {
                "x-rapidapi-key": JSearchService.API_KEY.strip(),
                "x-rapidapi-host": "jsearch.p.rapidapi.com"
            }
            
            # Build query - include location in query string if provided
            search_query = query
            if location:
                search_query = f"{query} in {location}"
            
            # Build query parameters
            params = {
                "query": search_query,
                "page": "1",
                "num_pages": str(num_pages),
                "country": "us",
                "date_posted": "all"
            }
            
            if remote_only:
                params["remote_jobs_only"] = "true"
            
            print(f"[DEBUG] JSearch API request: query='{search_query}', has_key={bool(JSearchService.API_KEY)}")
            
            response = requests.get(JSearchService.API_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('data', [])
            
            # Save jobs to database if user_id provided
            saved_jobs = []
            if user_id:
                for job in jobs:
                    job_data = JSearchService._save_job(user_id, job)
                    if job_data:
                        saved_jobs.append(job_data)
                
                # Update search history with results count
                execute_query(
                    """UPDATE jsearch_history 
                       SET results_count = %s 
                       WHERE user_id = %s 
                       ORDER BY searched_at DESC LIMIT 1""",
                    (len(saved_jobs), user_id),
                    commit=True
                )
            else:
                # Convert API format to our format
                saved_jobs = [JSearchService._format_job(job) for job in jobs]
            
            return {"jobs": saved_jobs}
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                error_msg = "403 Forbidden - Check your JSearch API key in .env file. Make sure it's valid and your RapidAPI subscription is active."
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Response: {e.response.text if hasattr(e.response, 'text') else 'No response text'}")
                return {"error": error_msg, "jobs": []}
            else:
                error_msg = f"HTTP {e.response.status_code}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return {"error": error_msg, "jobs": []}
        except requests.exceptions.RequestException as e:
            error_msg = f"API connection error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg, "jobs": []}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg, "jobs": []}
    
    @staticmethod
    def _format_job(job_data: Dict) -> Dict:
        """Format job data from API to our format"""
        return {
            'id': job_data.get('job_id'),
            'job_id': job_data.get('job_id'),
            'title': job_data.get('job_title', 'Unknown Position'),
            'job_title': job_data.get('job_title', 'Unknown Position'),
            'company': job_data.get('employer_name', 'Unknown Company'),
            'company_name': job_data.get('employer_name', 'Unknown Company'),
            'employer_name': job_data.get('employer_name', 'Unknown Company'),
            'location': job_data.get('job_city', 'Location not specified'),
            'job_city': job_data.get('job_city', 'Location not specified'),
            'description': job_data.get('job_description', ''),
            'job_description': job_data.get('job_description', ''),
            'salary_min': job_data.get('job_min_salary'),
            'salary_max': job_data.get('job_max_salary'),
            'is_remote': job_data.get('job_is_remote', False),
            'job_is_remote': job_data.get('job_is_remote', False),
            'job_url': job_data.get('job_apply_link', ''),
            'job_apply_link': job_data.get('job_apply_link', ''),
            'job_employment_type': job_data.get('job_employment_type', ''),
            'compatibility_score': 0.0
        }
    
    
    @staticmethod
    def _save_job(user_id: int, job_data: Dict) -> Optional[Dict]:
        """Save job to database - uses migration schema (job_id as PK, external_job_id as external ID)"""
        try:
            # Get external job ID from API response
            external_job_id = (job_data.get('job_id') or 
                             job_data.get('job_employer_job_id') or 
                             str(job_data.get('job_google_link', ''))[:255])
            
            if not external_job_id or external_job_id == 'None':
                print("[WARNING] No external job ID found, skipping save")
                return None
            
            # Check if job already exists by external_job_id (migration schema)
            existing = execute_query(
                "SELECT job_id FROM jsearch_jobs WHERE external_job_id = %s",
                (external_job_id,),
                fetch_one=True
            )
            
            if existing:
                # Mark as saved when saving
                db_job_id = existing['job_id']
                # Mark as saved
                execute_query(
                    "UPDATE jsearch_jobs SET is_saved = TRUE WHERE job_id = %s",
                    (db_job_id,),
                    commit=True
                )
                return JSearchService.get_job_by_id(db_job_id)
            
            # Extract salary info
            salary_min = None
            salary_max = None
            if job_data.get('job_min_salary'):
                try:
                    salary_min = float(job_data['job_min_salary'])
                except (ValueError, TypeError):
                    pass
            if job_data.get('job_max_salary'):
                try:
                    salary_max = float(job_data['job_max_salary'])
                except (ValueError, TypeError):
                    pass
            
            # Map to migration schema structure (001_initial_schema.sql)
            query = """
            INSERT INTO jsearch_jobs 
            (user_id, external_job_id, title, company_name, location, description, 
             salary_min, salary_max, job_url, posted_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            job_title = job_data.get('job_title', job_data.get('title', 'Unknown Position'))
            company_name = job_data.get('employer_name', 'Unknown Company')
            location = job_data.get('job_city', job_data.get('job_country', ''))
            description = job_data.get('job_description', '')
            job_url = job_data.get('job_apply_link', job_data.get('job_google_link', ''))
            if not job_url:
                job_url = 'https://example.com'  # Required field
            
            # Parse and format datetime for MySQL
            posted_date = None
            date_str = job_data.get('job_posted_at_datetime_utc') or job_data.get('job_posted_at_date')
            if date_str:
                try:
                    from datetime import datetime
                    # Handle ISO format: '2025-11-23T10:00:00.000Z'
                    if isinstance(date_str, str):
                        # Remove 'Z' and microseconds if present
                        date_str = date_str.replace('Z', '').split('.')[0]
                        # Parse ISO format
                        dt = datetime.fromisoformat(date_str)
                    else:
                        dt = date_str
                    # Format for MySQL DATETIME
                    posted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"[WARNING] Could not parse date '{date_str}': {e}")
                    posted_date = None
            
            db_job_id = execute_query(
                query,
                (user_id, external_job_id, job_title, company_name, location, description,
                 salary_min, salary_max, job_url, posted_date),
                commit=True
            )
            
            # Mark as saved when saving from search results
            if db_job_id:
                execute_query(
                    "UPDATE jsearch_jobs SET is_saved = TRUE WHERE job_id = %s",
                    (db_job_id,),
                    commit=True
                )
            
            return JSearchService.get_job_by_id(db_job_id)
            
        except Exception as e:
            print(f"Error saving job: {e}")
            return None
    
    @staticmethod
    def get_job_by_external_id(external_job_id: str) -> Optional[Dict]:
        """Get job by external_job_id"""
        query = "SELECT * FROM jsearch_jobs WHERE external_job_id = %s"
        result = execute_query(query, (external_job_id,), fetch_one=True)
        if result:
            # Map migration schema columns to expected format
            job_title = result.get('title', result.get('job_title', 'Unknown Position'))
            return {
                'job_id': result.get('job_id'),
                'external_job_id': result.get('external_job_id'),
                'title': job_title,
                'job_title': job_title,
                'company': result.get('company_name'),
                'company_name': result.get('company_name'),
                'location': result.get('location'),
                'description': result.get('description'),
                'job_url': result.get('job_url'),
                'is_saved': result.get('is_saved', False)
            }
        return None
    
    @staticmethod
    def get_job_by_id(db_job_id: int) -> Optional[Dict]:
        """Get job by database job_id (migration schema)"""
        query = "SELECT * FROM jsearch_jobs WHERE job_id = %s"
        result = execute_query(query, (db_job_id,), fetch_one=True)
        if result:
            # Map migration schema columns to expected format
            # Schema uses 'title', not 'job_title'
            job_title = result.get('title', result.get('job_title', 'Unknown Position'))
            return {
                'id': result.get('job_id'),  # Primary key
                'job_id': result.get('external_job_id'),  # External job ID from API
                'title': job_title,
                'job_title': job_title,
                'company': result.get('company_name'),
                'company_name': result.get('company_name'),
                'employer_name': result.get('company_name'),
                'location': result.get('location'),
                'job_city': result.get('location'),
                'description': result.get('description'),
                'job_description': result.get('description'),
                'salary_min': result.get('salary_min'),
                'salary_max': result.get('salary_max'),
                'is_remote': result.get('remote_type') == 'Remote' if result.get('remote_type') else False,
                'job_is_remote': result.get('remote_type') == 'Remote' if result.get('remote_type') else False,
                'job_url': result.get('job_url'),
                'job_apply_link': result.get('job_url'),
                'compatibility_score': 0.0  # Not in migration schema
            }
        return None
    
    @staticmethod
    def rank_jobs_by_compatibility(jobs: List[Dict], resume_text: str, user_id: int) -> List[Dict]:
        """
        Rank jobs by compatibility with user's resume
        
        Args:
            jobs: List of job dictionaries
            resume_text: User's resume text
            user_id: User ID
            
        Returns:
            Sorted list of jobs by compatibility score
        """
        try:
            from core.text_extractor import TextExtractor
            
            # Extract skills from resume
            resume_skills = set(skill.lower() for skill in TextExtractor.extract_skills(resume_text))
            
            # Calculate compatibility for each job
            for job in jobs:
                job_desc = job.get('description', job.get('job_description', ''))
                if not job_desc:
                    job['compatibility_score'] = 0.0
                    continue
                
                # Extract skills from job description
                job_skills = set(skill.lower() for skill in TextExtractor.extract_skills(job_desc))
                
                if not job_skills:
                    job['compatibility_score'] = 50.0  # Default if no skills found
                    continue
                
                # Calculate match percentage
                matched_skills = resume_skills.intersection(job_skills)
                score = (len(matched_skills) / len(job_skills)) * 100
                job['compatibility_score'] = round(score, 2)
            
            # Sort by compatibility score (descending)
            jobs.sort(key=lambda x: x.get('compatibility_score', 0), reverse=True)
            
            return jobs
            
        except Exception as e:
            print(f"Error ranking jobs: {e}")
            return jobs
    
    @staticmethod
    def save_search(user_id: int, query: str, location: str, remote_only: bool, results_count: int) -> bool:
        """
        Save search to history
        
        Args:
            user_id: User ID
            query: Search query
            location: Location filter
            remote_only: Remote only flag
            results_count: Number of results
            
        Returns:
            True if successful
        """
        try:
            execute_query(
                """INSERT INTO jsearch_history 
                   (user_id, search_query, location, remote_only, results_count) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, query, location or "", remote_only, results_count),
                commit=True
            )
            return True
        except Exception as e:
            print(f"Error saving search: {e}")
            return False
    
    @staticmethod
    def get_search_history(user_id: int, limit: int = 10) -> List[Dict]:
        """
        Get user's search history
        
        Args:
            user_id: User ID
            limit: Maximum number of searches to return
            
        Returns:
            List of search history records
        """
        try:
            query = """
            SELECT * FROM jsearch_history 
            WHERE user_id = %s 
            ORDER BY searched_at DESC 
            LIMIT %s
            """
            return execute_query(query, (user_id, limit), fetch_all=True) or []
        except Exception as e:
            print(f"Error getting search history: {e}")
            return []
    
    @staticmethod
    def get_saved_jobs(user_id: int) -> List[Dict]:
        """Get user's saved jobs"""
        query = """
        SELECT * FROM jsearch_jobs 
        WHERE user_id = %s AND is_saved = TRUE 
        ORDER BY created_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True) or []
    
    @staticmethod
    def save_job(job_id: int, is_saved: bool = True) -> bool:
        """Mark job as saved"""
        try:
            execute_query(
                "UPDATE jsearch_jobs SET is_saved = %s WHERE job_id = %s",
                (is_saved, job_id),
                commit=True
            )
            return True
        except Exception as e:
            print(f"Error saving job: {e}")
            return False
    
    @staticmethod
    def calculate_compatibility(user_id: int, job_id: int) -> float:
        """
        Calculate compatibility score between user's resume and job
        
        Args:
            user_id: User ID
            job_id: Job ID
            
        Returns:
            Compatibility score (0-100)
        """
        try:
            # Get user's resume skills
            from services.resume_service import ResumeService
            resume = ResumeService.get_active_resume(user_id)
            
            if not resume or not resume.get('parsed_data'):
                return 0.0
            
            resume_data = json.loads(resume['parsed_data'])
            resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
            
            # Get job requirements
            job = JSearchService.get_job_by_id(job_id)
            if not job or not job.get('description'):
                return 0.0
            
            # Extract skills from job description
            from core.text_extractor import TextExtractor
            job_skills = set(skill.lower() for skill in TextExtractor.extract_skills(job['description']))
            
            if not job_skills:
                return 50.0  # Default if no skills found
            
            # Calculate match percentage
            matched_skills = resume_skills.intersection(job_skills)
            score = (len(matched_skills) / len(job_skills)) * 100
            
            # Update in database
            execute_query(
                "UPDATE jsearch_jobs SET compatibility_score = %s WHERE job_id = %s",
                (score, job_id),
                commit=True
            )
            
            return round(score, 2)
            
        except Exception as e:
            print(f"Error calculating compatibility: {e}")
            return 0.0
    
    @staticmethod
    def _get_mock_jobs(query: str) -> List[Dict]:
        """Get mock jobs for demo purposes"""
        return [
            {
                'id': 1,
                'title': f'{query} - Senior',
                'company': 'TechCorp Inc.',
                'location': 'San Francisco, CA',
                'description': f'Looking for an experienced {query} professional...',
                'salary_min': 120000,
                'salary_max': 180000,
                'is_remote': True,
                'job_url': 'https://example.com/job1',
                'compatibility_score': 85.0
            },
            {
                'id': 2,
                'title': f'{query}',
                'company': 'StartupHub',
                'location': 'Remote',
                'description': f'Join our team as a {query}...',
                'salary_min': 90000,
                'salary_max': 130000,
                'is_remote': True,
                'job_url': 'https://example.com/job2',
                'compatibility_score': 75.0
            },
            {
                'id': 3,
                'title': f'Junior {query}',
                'company': 'BigTech Corp',
                'location': 'New York, NY',
                'description': f'Entry level position for {query}...',
                'salary_min': 70000,
                'salary_max': 95000,
                'is_remote': False,
                'job_url': 'https://example.com/job3',
                'compatibility_score': 65.0
            }
        ]
