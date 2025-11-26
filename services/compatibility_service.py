"""Compatibility analysis service - analyzes resume vs JD fit"""

from typing import Optional, Dict, Any
from database import DatabaseManager
from services.llm_service import LLMService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from config.prompts import Prompts
from core.response_normalizer import CompatibilityAnalysisNormalizer
import json

class CompatibilityService:
    """Analyzes compatibility between resume and job description"""
    
    @staticmethod
    def _extract_skills_from_list(skills_list):
        """
        Extract skill names from various formats (list of strings, list of dicts, etc.)
        
        Args:
            skills_list: List of skills in various formats
            
        Returns:
            List of skill name strings
        """
        if not skills_list:
            return []
        
        extracted = []
        for item in skills_list:
            if isinstance(item, dict):
                # Handle format: {'area': 'Programming Languages', 'description': ['Python']}
                if 'description' in item:
                    desc = item['description']
                    if isinstance(desc, list):
                        extracted.extend([str(skill) for skill in desc if skill])
                    else:
                        extracted.append(str(desc))
                elif 'area' in item:
                    extracted.append(str(item['area']))
                else:
                    # Try to extract any string values
                    for key, value in item.items():
                        if isinstance(value, str) and value:
                            extracted.append(value)
                        elif isinstance(value, list):
                            extracted.extend([str(v) for v in value if v])
            elif isinstance(item, str):
                extracted.append(item)
            else:
                # Fallback: convert to string
                extracted.append(str(item))
        
        # Remove duplicates and empty strings
        return list(dict.fromkeys([s.strip() for s in extracted if s and s.strip()]))
    
    @staticmethod
    def analyze_compatibility(user_id: int, resume_id: int, jd_id: int) -> Optional[Dict[str, Any]]:
        """Analyze compatibility between resume and JD
        
        Args:
            user_id: User ID
            resume_id: Resume ID
            jd_id: Job description ID
            
        Returns:
            Analysis results dict
        """
        try:
            # Get resume
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT resume_text, extracted_text FROM resumes
                    WHERE resume_id = %s AND user_id = %s
                """, (resume_id, user_id))
                resume_result = cursor.fetchone()
                
                if not resume_result:
                    return {"error": "Resume not found"}
                
                # Get JD (need both id and jd_id for the INSERT)
                cursor.execute("""
                    SELECT id, jd_id, jd_text FROM job_descriptions
                    WHERE jd_id = %s
                """, (jd_id,))
                jd_result = cursor.fetchone()
                
                if not jd_result:
                    return {"error": "Job description not found"}
            
            # Use resume_text if available, fallback to extracted_text
            resume_text = resume_result.get('resume_text') or resume_result.get('extracted_text', '')
            if not resume_text:
                return {"error": "Resume text not found"}
            jd_text = jd_result['jd_text']
            job_description_id = jd_result['id']  # Get the actual id for job_description_id column
            
            print(f"[INFO] Resume text length: {len(resume_text)}, JD text length: {len(jd_text)}")
            
            # Intelligently truncate resume and JD text to fit within prompt limits
            # Reserve ~500 chars for prompt template and format instructions
            # System prompt is ~500 chars, so we have ~1000 chars for data
            max_data_length = 1000
            max_resume_length = max_data_length // 2  # Split between resume and JD
            max_jd_length = max_data_length // 2
            
            def truncate_text(text: str, max_length: int) -> str:
                """Truncate text intelligently, preserving important parts"""
                if len(text) <= max_length:
                    return text
                # Keep first 60% and last 40% to preserve context
                first_part = int(max_length * 0.6)
                last_part = max_length - first_part - 50  # Reserve 50 chars for separator
                return text[:first_part] + "\n\n[... content truncated for length ...]\n\n" + text[-last_part:]
            
            truncated_resume = truncate_text(resume_text, max_resume_length)
            truncated_jd = truncate_text(jd_text, max_jd_length)
            
            if len(resume_text) > max_resume_length or len(jd_text) > max_jd_length:
                print(f"[INFO] Text truncated: resume {len(resume_text)}->{len(truncated_resume)}, JD {len(jd_text)}->{len(truncated_jd)}")
            
            # Call LLM for analysis
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                print("[ERROR] No LLM provider available")
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            print(f"[INFO] Using LLM provider: {type(provider).__name__}")
            
            # Build user prompt with truncated data
            prompt = Prompts.COMPATIBILITY_ANALYSIS.format(
                resume_text=truncated_resume,
                job_description=truncated_jd
            )
            
            # Get system prompt (role definition and instructions)
            system_prompt = Prompts.COMPATIBILITY_ANALYSIS_SYSTEM
            
            print(f"[INFO] Calling LLM for analysis...")
            try:
                raw_analysis = provider.generate_json(prompt, system_prompt=system_prompt)
                print(f"[INFO] LLM analysis complete (raw): {raw_analysis}")
            except Exception as llm_error:
                print(f"[ERROR] LLM generation failed: {llm_error}")
                import traceback
                traceback.print_exc()
                return {"error": f"LLM analysis failed: {str(llm_error)}"}
            
            if "error" in raw_analysis:
                error_msg = raw_analysis.get('error', 'Unknown error')
                print(f"[ERROR] Analysis returned error: {error_msg}")
                return {"error": error_msg, "compatibility_score": 0}
            
            if not raw_analysis:
                return {"error": "Analysis returned empty result", "compatibility_score": 0}
            
            # Normalize the response to canonical format (works with any LLM provider)
            analysis = CompatibilityAnalysisNormalizer.normalize(raw_analysis)
            print(f"[INFO] Normalized analysis (canonical format): {analysis}")
            
            # All data is now in canonical format - extract directly
            compatibility_score = analysis.get('compatibility_score', 0.0)
            matched_skills = analysis.get('matched_skills', [])
            missing_skills = analysis.get('missing_skills', [])
            strengths = analysis.get('strengths', [])
            suggestions = analysis.get('suggestions', [])
            missing_qualifications = analysis.get('missing_qualifications', [])
            
            # Save to database
            # All data is already in canonical format from normalizer
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO compatibility_analyses
                    (user_id, resume_id, job_description_id, jd_id, compatibility_score, matched_skills,
                     missing_skills, missing_qualifications, strengths, improvement_suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, resume_id, job_description_id, jd_id,
                      compatibility_score,
                      json.dumps(matched_skills),
                      json.dumps(missing_skills),
                      json.dumps(missing_qualifications),
                      json.dumps(strengths),
                      json.dumps(suggestions)))
                
                analysis_id = cursor.lastrowid
                # Sync analysis_id column with id for code compatibility
                if analysis_id:
                    cursor.execute(
                        "UPDATE compatibility_analyses SET analysis_id = id WHERE id = %s",
                        (analysis_id,)
                    )
                
                # Analysis is already normalized - all fields are in canonical format
                # Add analysis_id for tracking
                analysis['analysis_id'] = analysis_id
            
            print(f"[INFO] Analysis saved successfully (ID: {analysis_id})")
            print(f"[DEBUG] Final normalized analysis keys: {list(analysis.keys())}")
            print(f"[DEBUG] Compatibility score: {compatibility_score}")
            print(f"[DEBUG] Matched skills count: {len(matched_skills)}")
            print(f"[DEBUG] Missing skills count: {len(missing_skills)}")
            print(f"[DEBUG] Strengths count: {len(strengths)}")
            print(f"[DEBUG] Suggestions count: {len(suggestions)}")
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing compatibility: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recent_analyses(user_id: int, limit: int = 10) -> list:
        """Get recent compatibility analyses
        
        Args:
            user_id: User ID
            limit: Number of results
            
        Returns:
            List of analyses
        """
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT ca.*, r.file_name as resume_name,
                           jd.company_name, jd.job_title
                    FROM compatibility_analyses ca
                    JOIN resumes r ON ca.resume_id = r.resume_id
                    JOIN job_descriptions jd ON ca.jd_id = jd.jd_id
                    WHERE ca.user_id = %s
                    ORDER BY ca.analyzed_at DESC
                    LIMIT %s
                """, (user_id, limit))
                
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching analyses: {e}")
            return []
    
    @staticmethod
    def get_analysis_by_id(analysis_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific analysis by ID
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID (for security)
            
        Returns:
            Analysis dict or None
        """
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT ca.*, r.file_name as resume_name,
                           jd.company_name, jd.job_title
                    FROM compatibility_analyses ca
                    JOIN resumes r ON ca.resume_id = r.resume_id
                    JOIN job_descriptions jd ON ca.jd_id = jd.jd_id
                    WHERE ca.analysis_id = %s AND ca.user_id = %s
                """, (analysis_id, user_id))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                # Parse JSON fields
                analysis = dict(result)
                if analysis.get('matched_skills'):
                    try:
                        analysis['matched_skills'] = json.loads(analysis['matched_skills'])
                    except:
                        analysis['matched_skills'] = []
                
                if analysis.get('missing_skills'):
                    try:
                        analysis['missing_skills'] = json.loads(analysis['missing_skills'])
                    except:
                        analysis['missing_skills'] = []
                
                if analysis.get('missing_qualifications'):
                    try:
                        analysis['missing_qualifications'] = json.loads(analysis['missing_qualifications'])
                    except:
                        analysis['missing_qualifications'] = []
                
                # Parse suggestions
                suggestions_text = analysis.get('improvement_suggestions', '')
                if suggestions_text:
                    try:
                        # Try parsing as JSON first
                        analysis['suggestions'] = json.loads(suggestions_text)
                    except:
                        # If not JSON, split by newlines
                        analysis['suggestions'] = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                else:
                    analysis['suggestions'] = []
                
                return analysis
        except Exception as e:
            print(f"Error fetching analysis: {e}")
            return None

