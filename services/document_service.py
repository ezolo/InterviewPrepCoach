"""
Document generation service - AI-powered document generation
"""
from typing import Optional, Dict, Any
from database.connection import execute_query
from services.llm_service import LLMService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from config.prompts import Prompts
import json

class DocumentService:
    """Handle AI-powered document generation"""
    
    @staticmethod
    def generate_resume(user_id: int, jd_id: int,
                       template: str = 'professional',
                       resume_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Generate optimized resume
        
        Args:
            user_id: User ID
            jd_id: Job description ID
            template: Resume template style
            resume_id: Optional specific resume ID (uses active resume if not provided)
            
        Returns:
            Dict with document_id and content, or None if failed
        """
        try:
            # Get resume (specific or active)
            if resume_id:
                resume = ResumeService.get_resume_by_id(resume_id)
            else:
                resume = ResumeService.get_active_resume(user_id)
            
            jd = JobDescriptionService.get_jd(jd_id)
            
            if not resume:
                return {"error": "No resume found. Please upload a resume first."}
            
            if not jd:
                return {"error": "Job description not found."}
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            # Prepare user info from resume
            user_info = f"""
Resume Text:
{resume.get('resume_text', '')[:3000]}

Skills: {json.dumps(resume.get('parsed_data', {}).get('skills', [])) if isinstance(resume.get('parsed_data'), dict) else 'N/A'}
"""
            
            # Format prompt
            prompt = Prompts.RESUME_GENERATION.format(
                user_info=user_info,
                job_description=jd.get('jd_text', '')[:2000]
            )
            
            print(f"[INFO] Generating resume with template: {template}")
            
            # Generate with LLM
            resume_content = provider.generate(prompt)
            
            if not resume_content or "error" in resume_content.lower():
                return {"error": "Failed to generate resume content"}
            
            # Save to database
            query = """
                INSERT INTO generated_documents
                (user_id, document_type, job_description_id, title, content, template_used)
                VALUES (%s, 'resume', %s, %s, %s, %s)
            """
            title = f"Resume - {template.title()}"
            document_id = execute_query(
                query,
                (user_id, jd_id, title, resume_content, template),
                commit=True
            )
            
            if document_id:
                return {
                    "document_id": document_id,
                    "content": resume_content,
                    "document_type": "resume"
                }
            else:
                return {"error": "Failed to save resume"}
                
        except Exception as e:
            print(f"[ERROR] Error generating resume: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def generate_cover_letter(user_id: int, jd_id: int,
                             length: str = 'medium',
                             resume_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Generate cover letter
        
        Args:
            user_id: User ID
            jd_id: Job description ID
            length: Letter length (short, medium, long)
            resume_id: Optional specific resume ID (uses active resume if not provided)
            
        Returns:
            Dict with document_id and content, or None if failed
        """
        try:
            # Get resume (specific or active)
            if resume_id:
                resume = ResumeService.get_resume_by_id(resume_id)
            else:
                resume = ResumeService.get_active_resume(user_id)
            
            jd = JobDescriptionService.get_jd(jd_id)
            
            if not resume:
                return {"error": "No resume found. Please upload a resume first."}
            
            if not jd:
                return {"error": "Job description not found."}
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            # Prepare comprehensive resume summary with structured data
            resume_text = resume.get('resume_text', '')
            parsed_data = resume.get('parsed_data', {})
            if isinstance(parsed_data, str):
                try:
                    parsed_data = json.loads(parsed_data)
                except:
                    parsed_data = {}
            
            # Build detailed resume summary
            resume_summary_parts = []
            
            # Add full resume text (truncated if needed)
            resume_text_portion = resume_text[:2000] if len(resume_text) > 2000 else resume_text
            resume_summary_parts.append(f"Full Resume Text:\n{resume_text_portion}")
            
            # Add structured information if available
            if isinstance(parsed_data, dict):
                if parsed_data.get('skills'):
                    skills = parsed_data['skills']
                    if isinstance(skills, list):
                        resume_summary_parts.append(f"\nKey Skills: {', '.join(skills[:20])}")
                
                if parsed_data.get('experience'):
                    resume_summary_parts.append(f"\nExperience: {parsed_data['experience']}")
                
                if parsed_data.get('education'):
                    resume_summary_parts.append(f"\nEducation: {parsed_data['education']}")
            
            resume_summary = "\n".join(resume_summary_parts)
            
            # Format prompt
            prompt = Prompts.COVER_LETTER_GENERATION.format(
                resume_summary=resume_summary,
                company_name=jd.get('company_name', 'the company'),
                position=jd.get('job_title', 'the position'),
                job_description=jd.get('jd_text', '')[:2000],
                length=length
            )
            
            print(f"[INFO] Generating cover letter with length: {length}")
            
            # Generate with LLM
            cover_letter_content = provider.generate(prompt)
            
            if not cover_letter_content or "error" in cover_letter_content.lower():
                return {"error": "Failed to generate cover letter content"}
            
            # Save to database
            query = """
                INSERT INTO generated_documents
                (user_id, document_type, job_description_id, title, content, template_used)
                VALUES (%s, 'cover_letter', %s, %s, %s, %s)
            """
            title = f"Cover Letter - {length.title()}"
            document_id = execute_query(
                query,
                (user_id, jd_id, title, cover_letter_content, length),
                commit=True
            )
            
            if document_id:
                return {
                    "document_id": document_id,
                    "content": cover_letter_content,
                    "document_type": "cover_letter"
                }
            else:
                return {"error": "Failed to save cover letter"}
                
        except Exception as e:
            print(f"[ERROR] Error generating cover letter: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def generate_cold_email(user_id: int, purpose: str, company: str,
                           recipient_type: str = 'recruiter',
                           jd_id: Optional[int] = None,
                           resume_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Generate cold email
        
        Args:
            user_id: User ID
            purpose: Purpose of the email (e.g., "networking", "job inquiry", "follow-up")
            company: Company name
            recipient_type: Type of recipient (recruiter, hiring_manager, employee, etc.)
            jd_id: Optional job description ID if related to a specific job
            resume_id: Optional specific resume ID (uses active resume if not provided)
            
        Returns:
            Dict with document_id and content, or None if failed
        """
        try:
            # Get resume (specific or active)
            if resume_id:
                resume = ResumeService.get_resume_by_id(resume_id)
            else:
                resume = ResumeService.get_active_resume(user_id)
            
            if not resume:
                return {"error": "No resume found. Please upload a resume first."}
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            # Prepare comprehensive resume summary with structured data
            resume_text = resume.get('resume_text', '')
            parsed_data = resume.get('parsed_data', {})
            if isinstance(parsed_data, str):
                try:
                    parsed_data = json.loads(parsed_data)
                except:
                    parsed_data = {}
            
            # Build detailed resume summary
            resume_summary_parts = []
            
            # Add full resume text (truncated if needed)
            resume_text_portion = resume_text[:1500] if len(resume_text) > 1500 else resume_text
            resume_summary_parts.append(f"Resume Text:\n{resume_text_portion}")
            
            # Add structured information if available
            if isinstance(parsed_data, dict):
                if parsed_data.get('skills'):
                    skills = parsed_data['skills']
                    if isinstance(skills, list):
                        resume_summary_parts.append(f"\nKey Skills: {', '.join(skills[:15])}")
                
                if parsed_data.get('experience'):
                    resume_summary_parts.append(f"\nExperience Highlights: {parsed_data['experience']}")
            
            resume_summary = "\n".join(resume_summary_parts)
            
            # Get JD if provided
            jd_context = ""
            if jd_id:
                jd = JobDescriptionService.get_jd(jd_id)
                if jd:
                    jd_text = jd.get('jd_text', '')[:800]
                    job_title = jd.get('job_title', '')
                    company_name = jd.get('company_name', '')
                    jd_context = f"\n\nRelevant Job Context:\nPosition: {job_title} at {company_name}\nJob Description:\n{jd_text}"
            
            # Format prompt
            prompt = Prompts.COLD_EMAIL_GENERATION.format(
                purpose=purpose,
                recipient_type=recipient_type,
                company=company,
                resume_summary=resume_summary
            )
            
            # Add JD context if available
            if jd_context:
                prompt += jd_context
            
            print(f"[INFO] Generating cold email for {purpose} to {recipient_type} at {company}")
            
            # Generate with LLM
            email_content = provider.generate(prompt)
            
            if not email_content or "error" in email_content.lower():
                return {"error": "Failed to generate email content"}
            
            # Save to database
            query = """
                INSERT INTO generated_documents
                (user_id, document_type, job_description_id, title, content, template_used)
                VALUES (%s, 'cold_email', %s, %s, %s, %s)
            """
            title = f"Cold Email - {purpose.title()}"
            document_id = execute_query(
                query,
                (user_id, jd_id, title, email_content, recipient_type),
                commit=True
            )
            
            if document_id:
                return {
                    "document_id": document_id,
                    "content": email_content,
                    "document_type": "cold_email"
                }
            else:
                return {"error": "Failed to save email"}
                
        except Exception as e:
            print(f"[ERROR] Error generating cold email: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def get_documents(user_id: int, document_type: Optional[str] = None) -> list:
        """Get user's generated documents
        
        Args:
            user_id: User ID
            document_type: Optional filter by type (resume, cover_letter, cold_email)
            
        Returns:
            List of documents
        """
        if document_type:
            query = """
            SELECT * FROM generated_documents 
            WHERE user_id = %s AND document_type = %s
            ORDER BY created_at DESC
            """
            return execute_query(query, (user_id, document_type), fetch_all=True) or []
        else:
            query = """
            SELECT * FROM generated_documents 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """
            return execute_query(query, (user_id,), fetch_all=True) or []
