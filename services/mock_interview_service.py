"""
Mock Interview Service - Comprehensive mock interview session management
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from database.connection import execute_query
from services.question_service import QuestionService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService

class MockInterviewService:
    """Handle mock interview sessions, responses, and feedback"""
    
    @staticmethod
    def create_session(
        user_id: int,
        session_name: str,
        format_type: str = 'traditional',
        question_source: str = 'generated',
        question_set_id: Optional[int] = None,
        resume_id: Optional[int] = None,
        jd_id: Optional[int] = None,
        config: Optional[Dict] = None
    ) -> Optional[int]:
        """Create a new mock interview session
        
        Args:
            user_id: User ID
            session_name: Name for the session
            format_type: traditional, technical, behavioral, case
            question_source: set, generated, custom
            question_set_id: ID of question set (if source is 'set')
            resume_id: Resume ID for context
            jd_id: Job description ID for context
            config: Configuration dict with num_questions, difficulty, etc.
            
        Returns:
            Session ID or None if failed
        """
        try:
            if not config:
                config = {
                    'num_questions': 5,
                    'difficulty': 'medium',
                    'time_per_question': 120,  # seconds
                    'prep_time': 30,  # seconds
                    'feedback_mode': 'post_session'
                }
            
            query = """
            INSERT INTO mock_interview_sessions 
            (user_id, session_name, format_type, question_source, question_set_id, 
             resume_id, jd_id, config, status, total_questions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft', %s)
            """
            
            total_questions = config.get('num_questions', 5)
            
            session_id = execute_query(
                query,
                (
                    user_id, session_name, format_type, question_source,
                    question_set_id, resume_id, jd_id,
                    json.dumps(config), total_questions
                ),
                commit=True
            )
            
            if session_id:
                # Generate or load questions based on source
                MockInterviewService._prepare_questions(
                    session_id=session_id,
                    user_id=user_id,
                    question_source=question_source,
                    question_set_id=question_set_id,
                    resume_id=resume_id,
                    jd_id=jd_id,
                    format_type=format_type,
                    num_questions=total_questions
                )
            
            return session_id
            
        except Exception as e:
            print(f"[ERROR] Error creating mock interview session: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _prepare_questions(
        session_id: int,
        user_id: int,
        question_source: str,
        question_set_id: Optional[int],
        resume_id: Optional[int],
        jd_id: Optional[int],
        format_type: str,
        num_questions: int
    ):
        """Prepare questions for the session"""
        try:
            if question_source == 'set' and question_set_id:
                # Use existing question set
                questions = QuestionService.get_questions(question_set_id) or []
                # Limit to num_questions
                questions = questions[:num_questions]
            elif question_source == 'generated' and resume_id and jd_id:
                # Generate questions
                question_type_map = {
                    'traditional': 'behavioral',
                    'technical': 'technical',
                    'behavioral': 'behavioral',
                    'case': 'situational'
                }
                
                result = QuestionService.generate_questions(
                    user_id=user_id,
                    resume_id=resume_id,
                    jd_id=jd_id,
                    question_type=question_type_map.get(format_type, 'behavioral'),
                    count=num_questions
                )
                
                if result and result.get('questions'):
                    questions = result['questions']
                    if result.get('set_id'):
                        execute_query(
                            """
                            UPDATE mock_interview_sessions
                            SET question_set_id = %s,
                                question_source = 'set'
                            WHERE session_id = %s
                            """,
                            (result['set_id'], session_id),
                            commit=True
                        )
                else:
                    questions = []
            else:
                questions = []
            
            # Store question IDs in session config or create a mapping
            # For now, we'll fetch questions when needed
            print(f"[INFO] Prepared {len(questions)} questions for session {session_id}")
            
        except Exception as e:
            print(f"[ERROR] Error preparing questions: {e}")
            import traceback
            traceback.print_exc()
    
    @staticmethod
    def get_session(session_id: int) -> Optional[Dict]:
        """Get mock interview session by ID"""
        query = """
        SELECT * FROM mock_interview_sessions WHERE session_id = %s
        """
        return execute_query(query, (session_id,), fetch_one=True)
    
    @staticmethod
    def get_user_sessions(user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's mock interview sessions"""
        query = """
        SELECT * FROM mock_interview_sessions 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
    
    @staticmethod
    def start_session(session_id: int) -> bool:
        """Start a mock interview session"""
        try:
            query = """
            UPDATE mock_interview_sessions
            SET status = 'in_progress',
                started_at = NOW(),
                current_question_index = 0
            WHERE session_id = %s
            """
            execute_query(query, (session_id,), commit=True)
            return True
        except Exception as e:
            print(f"[ERROR] Error starting session: {e}")
            return False
    
    @staticmethod
    def get_session_questions(session_id: int) -> List[Dict]:
        """Get all questions for a session"""
        try:
            session = MockInterviewService.get_session(session_id)
            if not session:
                return []
            
            question_source = session.get('question_source')
            question_set_id = session.get('question_set_id')
            resume_id = session.get('resume_id')
            jd_id = session.get('jd_id')
            format_type = session.get('format_type', 'traditional')
            config_str = session.get('config', '{}')
            
            try:
                config = json.loads(config_str) if isinstance(config_str, str) else config_str
            except:
                config = {}
            
            num_questions = config.get('num_questions', 5)
            
            if question_source == 'set' and question_set_id:
                questions = QuestionService.get_questions(question_set_id) or []
                # Limit to requested number
                questions = questions[:num_questions]
            elif question_source == 'generated' and resume_id and jd_id:
                # Generate questions on the fly
                question_type_map = {
                    'traditional': 'behavioral',
                    'technical': 'technical',
                    'behavioral': 'behavioral',
                    'case': 'situational'
                }
                
                result = QuestionService.generate_questions(
                    user_id=session.get('user_id', 1),
                    resume_id=resume_id,
                    jd_id=jd_id,
                    question_type=question_type_map.get(format_type, 'behavioral'),
                    count=num_questions
                )
                
                if result and result.get('questions'):
                    questions = result['questions']
                else:
                    questions = []
            else:
                questions = []
            
            return questions
            
        except Exception as e:
            print(f"[ERROR] Error getting session questions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def save_response(
        session_id: int,
        question_id: int,
        question_index: int,
        response_mode: str,
        response_text: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        video_file_path: Optional[str] = None,
        transcript: Optional[str] = None,
        notes: Optional[str] = None,
        is_flagged: bool = False,
        is_skipped: bool = False,
        duration_seconds: int = 0,
        prep_time_seconds: int = 0,
        response_time_seconds: int = 0
    ) -> Optional[int]:
        """Save a response for a question in the session"""
        try:
            query = """
            INSERT INTO mock_interview_responses
            (session_id, question_id, question_index, response_mode, response_text,
             audio_file_path, video_file_path, transcript, notes, is_flagged, is_skipped,
             duration_seconds, prep_time_seconds, response_time_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            response_id = execute_query(
                query,
                (
                    session_id, question_id, question_index, response_mode,
                    response_text, audio_file_path, video_file_path, transcript,
                    notes, is_flagged, is_skipped, duration_seconds,
                    prep_time_seconds, response_time_seconds
                ),
                commit=True
            )
            
            # Update session progress
            MockInterviewService._update_session_progress(session_id, question_index)
            
            return response_id
            
        except Exception as e:
            print(f"[ERROR] Error saving response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _update_session_progress(session_id: int, question_index: int):
        """Update session progress"""
        try:
            query = """
            UPDATE mock_interview_sessions
            SET current_question_index = %s,
                updated_at = NOW()
            WHERE session_id = %s
            """
            execute_query(query, (question_index + 1, session_id), commit=True)
        except Exception as e:
            print(f"[ERROR] Error updating session progress: {e}")
    
    @staticmethod
    def complete_session(session_id: int) -> bool:
        """Mark session as completed"""
        try:
            query = """
            UPDATE mock_interview_sessions
            SET status = 'completed',
                completed_at = NOW()
            WHERE session_id = %s
            """
            execute_query(query, (session_id,), commit=True)
            return True
        except Exception as e:
            print(f"[ERROR] Error completing session: {e}")
            return False
    
    @staticmethod
    def get_session_responses(session_id: int) -> List[Dict]:
        """Get all responses for a session"""
        query = """
        SELECT mr.*, q.question_text
        FROM mock_interview_responses mr
        JOIN questions q ON mr.question_id = q.question_id
        WHERE mr.session_id = %s
        ORDER BY mr.question_index ASC
        """
        return execute_query(query, (session_id,), fetch_all=True) or []
    
    @staticmethod
    def save_feedback(
        session_id: int,
        response_id: Optional[int],
        feedback_type: str,
        score_content: Optional[float] = None,
        score_delivery: Optional[float] = None,
        score_overall: Optional[float] = None,
        star_analysis: Optional[Dict] = None,
        strengths: Optional[List] = None,
        weaknesses: Optional[List] = None,
        suggestions: Optional[List] = None,
        delivery_metrics: Optional[Dict] = None,
        recommendations: Optional[str] = None,
        skill_tags: Optional[List] = None
    ) -> Optional[int]:
        """Save AI feedback for a question or session"""
        try:
            query = """
            INSERT INTO mock_interview_feedback
            (session_id, response_id, feedback_type, score_content, score_delivery,
             score_overall, star_analysis, strengths, weaknesses, suggestions,
             delivery_metrics, recommendations, skill_tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            feedback_id = execute_query(
                query,
                (
                    session_id, response_id, feedback_type,
                    score_content, score_delivery, score_overall,
                    json.dumps(star_analysis) if star_analysis else None,
                    json.dumps(strengths) if strengths else None,
                    json.dumps(weaknesses) if weaknesses else None,
                    json.dumps(suggestions) if suggestions else None,
                    json.dumps(delivery_metrics) if delivery_metrics else None,
                    recommendations,
                    json.dumps(skill_tags) if skill_tags else None
                ),
                commit=True
            )
            
            return feedback_id
            
        except Exception as e:
            print(f"[ERROR] Error saving feedback: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_session_feedback(session_id: int) -> List[Dict]:
        """Get all feedback for a session"""
        query = """
        SELECT * FROM mock_interview_feedback
        WHERE session_id = %s
        ORDER BY feedback_type DESC, created_at ASC
        """
        return execute_query(query, (session_id,), fetch_all=True) or []

