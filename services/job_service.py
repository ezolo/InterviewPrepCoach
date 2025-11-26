"""
Job description and compatibility analysis service
"""
import json
from typing import Optional, Dict, List
from database.connection import execute_query
from core.text_extractor import TextExtractor
from ai.provider_factory import ProviderFactory
from config.prompts import COMPATIBILITY_ANALYSIS_PROMPT

class JobService:
    """Handle job description operations"""
    
    @staticmethod
    def create_job_description(user_id: int, title: str, company: str, 
                              description_text: str, **kwargs) -> Optional[int]:
        """
        Create a job description entry
        
        Args:
            user_id: User ID
            title: Job title
            company: Company name
            description_text: Job description text
            **kwargs: Additional fields (location, salary_range, etc.)
            
        Returns:
            Job description ID or None
        """
        try:
            # Extract information from description
            skills = TextExtractor.extract_skills(description_text)
            years_exp = TextExtractor.extract_years_experience(description_text)
            
            parsed_data = {
                'skills': skills,
                'years_experience': years_exp,
                'keywords': TextExtractor.extract_keywords(description_text, top_n=15)
            }
            
            query = """
            INSERT INTO job_descriptions 
            (user_id, title, company, location, salary_range, description_text, 
             requirements, parsed_data, source, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            job_id = execute_query(
                query,
                (user_id, title, company, kwargs.get('location'), 
                 kwargs.get('salary_range'), description_text,
                 kwargs.get('requirements'), json.dumps(parsed_data),
                 kwargs.get('source', 'manual'), kwargs.get('source_url')),
                commit=True
            )
            
            return job_id
        except Exception as e:
            print(f"Error creating job description: {e}")
            return None
    
    @staticmethod
    def get_job_description(job_id: int) -> Optional[Dict]:
        """Get job description by ID"""
        query = "SELECT * FROM job_descriptions WHERE id = %s"
        return execute_query(query, (job_id,), fetch_one=True)
    
    @staticmethod
    def get_all_job_descriptions(user_id: int) -> List[Dict]:
        """Get all job descriptions for user"""
        query = """
        SELECT * FROM job_descriptions 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        """
        return execute_query(query, (user_id,), fetch_all=True) or []
    
    @staticmethod
    def analyze_compatibility(resume_id: int, job_description_id: int, 
                            user_id: int, provider_settings: Dict) -> Optional[Dict]:
        """
        Analyze compatibility between resume and job description
        
        Args:
            resume_id: Resume ID
            job_description_id: Job description ID
            user_id: User ID
            provider_settings: LLM provider settings dict
            
        Returns:
            Analysis results dict or None
        """
        try:
            # Get resume and job description
            from services.resume_service import ResumeService
            
            resume = ResumeService.get_resume_by_id(resume_id)
            job_desc = JobService.get_job_description(job_description_id)
            
            if not resume or not job_desc:
                raise ValueError("Resume or job description not found")
            
            # Create prompt
            prompt = COMPATIBILITY_ANALYSIS_PROMPT.format(
                resume_text=resume['extracted_text'],
                job_description=job_desc['description_text']
            )
            
            # Get LLM provider
            provider = ProviderFactory.create_provider(
                provider_name=provider_settings['provider'],
                api_key=provider_settings['api_key'],
                model=provider_settings['model'],
                temperature=provider_settings.get('temperature', 0.7),
                max_tokens=provider_settings.get('max_tokens', 2000)
            )
            
            # Generate analysis
            response = provider.generate(prompt)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(response)
            
            # Store in database
            query = """
            INSERT INTO compatibility_analyses 
            (user_id, resume_id, jd_id, compatibility_score, 
             matched_skills, missing_skills, missing_qualifications, improvement_suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            analysis_id = execute_query(
                query,
                (user_id, resume_id, job_description_id, 
                 analysis['compatibility_score'],
                 json.dumps(analysis['matched_skills']),
                 json.dumps(analysis['missing_skills']),
                 json.dumps(analysis['missing_qualifications']),
                 '\n'.join(analysis['suggestions'])),
                commit=True
            )
            
            analysis['id'] = analysis_id
            return analysis
            
        except Exception as e:
            print(f"Error analyzing compatibility: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_analysis_history(user_id: int, limit: int = 10) -> List[Dict]:
        """Get compatibility analysis history"""
        query = """
        SELECT ca.*, jd.title as job_title, jd.company 
        FROM compatibility_analyses ca
        JOIN job_descriptions jd ON ca.job_description_id = jd.id
        WHERE ca.user_id = %s
        ORDER BY ca.created_at DESC
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
