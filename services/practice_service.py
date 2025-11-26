"""
Practice session service
"""
import json
import os
from typing import List, Dict, Optional
from database.connection import execute_query
from services.llm_service import LLMService
from services.question_service import QuestionService
from config.prompts import Prompts
from core.recording_service import TranscriptionService
from config.settings import Settings

class PracticeService:
    """Handle practice sessions and evaluations"""
    
    @staticmethod
    def create_session(
        user_id: int,
        question_id: Optional[int],
        response_mode: str = 'written',
        question_set_id: Optional[int] = None,
        skill_focus: Optional[str] = None,
        session_type: str = 'question_drill'
    ) -> Optional[int]:
        """Create a practice session
        
        Args:
            user_id: User ID
            question_id: Question ID (optional for custom drills)
            response_mode: Response mode ('written', 'audio', 'video')
            question_set_id: Optional question set ID for context
            skill_focus: Optional skill/topic focus label
            session_type: Optional session type label
            
        Returns:
            Session ID or None if failed
        """
        try:
            session_label = session_type or 'question_drill'
            if skill_focus:
                label = f"skill:{skill_focus.strip()}"
                session_label = label[:50]
            
            query = """
            INSERT INTO practice_sessions (user_id, question_set_id, question_id, session_type, response_mode)
            VALUES (%s, %s, %s, %s, %s)
            """
            session_id = execute_query(
                query,
                (user_id, question_set_id, question_id, session_label, response_mode),
                commit=True
            )
            return session_id
        except Exception as e:
            print(f"[ERROR] Error creating practice session: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_sessions(user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's practice sessions"""
        query = """
        SELECT ps.*, q.question_text, qs.set_name, jd.job_title, jd.company_name
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.question_id
        JOIN question_sets qs ON q.set_id = qs.set_id
        LEFT JOIN job_descriptions jd ON qs.jd_id = jd.jd_id
        WHERE ps.user_id = %s 
        ORDER BY ps.session_date DESC
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
    
    @staticmethod
    def get_session_by_id(session_id: int) -> Optional[Dict]:
        """Get a practice session by ID"""
        query = """
        SELECT ps.*, q.question_text, q.ideal_answer_points, qs.set_name, 
               jd.job_title, jd.company_name
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.question_id
        JOIN question_sets qs ON q.set_id = qs.set_id
        LEFT JOIN job_descriptions jd ON qs.jd_id = jd.jd_id
        WHERE ps.session_id = %s
        """
        return execute_query(query, (session_id,), fetch_one=True)
    
    @staticmethod
    def evaluate_response(user_id: int, session_id: int, question_id: int, 
                         response_text: str, duration_seconds: int = 0) -> Optional[Dict]:
        """Evaluate a practice response with AI
        
        Args:
            user_id: User ID
            session_id: Session ID
            question_id: Question ID
            response_text: User's response text
            duration_seconds: Time taken to respond
            
        Returns:
            Evaluation dict with score, feedback, etc. or None if failed
        """
        try:
            # Get question details
            question_query = """
            SELECT q.*, qs.set_name
            FROM questions q
            JOIN question_sets qs ON q.set_id = qs.set_id
            WHERE q.question_id = %s
            """
            question = execute_query(question_query, (question_id,), fetch_one=True)
            
            if not question:
                print(f"[ERROR] Question {question_id} not found")
                return None
            
            question_text = question.get('question_text', '')
            ideal_points_str = question.get('ideal_answer_points', '[]')
            
            # Parse ideal answer points
            try:
                if isinstance(ideal_points_str, str):
                    ideal_points = json.loads(ideal_points_str)
                else:
                    ideal_points = ideal_points_str or []
            except:
                ideal_points = []
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            # Format prompt
            prompt = Prompts.PRACTICE_EVALUATION.format(
                question=question_text,
                response=response_text,
                ideal_points=json.dumps(ideal_points) if ideal_points else "[]"
            )
            
            # Get LLM response
            print(f"[INFO] Evaluating practice response for session {session_id}")
            llm_response = provider.generate(prompt)
            
            if not llm_response:
                print("[ERROR] LLM returned empty response")
                return None
            
            # Parse JSON response
            evaluation = PracticeService._parse_evaluation(llm_response)
            
            if not evaluation:
                print("[ERROR] Failed to parse evaluation response")
                return None
            
            # Update session with response and evaluation
            strengths = evaluation.get('strengths', [])
            improvements = evaluation.get('weaknesses', []) + evaluation.get('suggestions', [])
            
            update_query = """
            UPDATE practice_sessions
            SET response_text = %s,
                evaluation_score = %s,
                evaluation_feedback = %s,
                strengths = %s,
                improvements = %s,
                duration_seconds = %s
            WHERE session_id = %s
            """
            
            execute_query(
                update_query,
                (
                    response_text,
                    evaluation.get('score', 0),
                    json.dumps(evaluation),
                    json.dumps(strengths),
                    json.dumps(improvements),
                    duration_seconds,
                    session_id
                ),
                commit=True
            )
            
            return evaluation
            
        except Exception as e:
            print(f"[ERROR] Error evaluating response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def save_audio_response(session_id: int, audio_file_path: str, 
                           duration_seconds: int = 0) -> Optional[str]:
        """Save audio response and transcribe it
        
        Args:
            session_id: Session ID
            audio_file_path: Path to audio file
            duration_seconds: Duration of recording
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Transcribe audio
            transcript = TranscriptionService.transcribe_audio(audio_file_path, use_api=False)
            
            if not transcript:
                print("[WARNING] Transcription failed, but continuing...")
                transcript = ""
            
            # Update session with audio file path and transcript
            update_query = """
            UPDATE practice_sessions
            SET audio_file_path = %s,
                transcript = %s,
                duration_seconds = %s
            WHERE session_id = %s
            """
            
            execute_query(
                update_query,
                (audio_file_path, transcript, duration_seconds, session_id),
                commit=True
            )
            
            return transcript
            
        except Exception as e:
            print(f"[ERROR] Error saving audio response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def save_video_response(session_id: int, video_file_path: str,
                           duration_seconds: int = 0,
                           transcript: Optional[str] = None) -> bool:
        """Save video response
        
        Args:
            session_id: Session ID
            video_file_path: Path to video file
            duration_seconds: Duration of recording
            transcript: Optional transcript text
            
        Returns:
            True if successful
        """
        try:
            # Update session with video file path
            update_query = """
            UPDATE practice_sessions
            SET video_file_path = %s,
                transcript = %s,
                duration_seconds = %s
            WHERE session_id = %s
            """
            
            execute_query(
                update_query,
                (video_file_path, transcript, duration_seconds, session_id),
                commit=True
            )
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error saving video response: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def evaluate_audio_or_video_response(user_id: int, session_id: int, 
                                        question_id: int, transcript: str,
                                        duration_seconds: int = 0) -> Optional[Dict]:
        """Evaluate audio or video response using transcript
        
        Args:
            user_id: User ID
            session_id: Session ID
            question_id: Question ID
            transcript: Transcribed text from audio/video
            duration_seconds: Duration of recording
            
        Returns:
            Evaluation dict or None if failed
        """
        try:
            # Get question details
            question_query = """
            SELECT q.*, qs.set_name
            FROM questions q
            JOIN question_sets qs ON q.set_id = qs.set_id
            WHERE q.question_id = %s
            """
            question = execute_query(question_query, (question_id,), fetch_one=True)
            
            if not question:
                print(f"[ERROR] Question {question_id} not found")
                return None
            
            question_text = question.get('question_text', '')
            ideal_points_str = question.get('ideal_answer_points', '[]')
            
            # Parse ideal answer points
            try:
                if isinstance(ideal_points_str, str):
                    ideal_points = json.loads(ideal_points_str)
                else:
                    ideal_points = ideal_points_str or []
            except:
                ideal_points = []
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            # Format prompt (same as written, but can add audio/video specific notes)
            prompt = Prompts.PRACTICE_EVALUATION.format(
                question=question_text,
                response=transcript,
                ideal_points=json.dumps(ideal_points) if ideal_points else "[]"
            )
            
            # Get LLM response
            print(f"[INFO] Evaluating audio/video response for session {session_id}")
            llm_response = provider.generate(prompt)
            
            if not llm_response:
                print("[ERROR] LLM returned empty response")
                return None
            
            # Parse JSON response
            evaluation = PracticeService._parse_evaluation(llm_response)
            
            if not evaluation:
                print("[ERROR] Failed to parse evaluation response")
                return None
            
            # Update session with transcript and evaluation
            strengths = evaluation.get('strengths', [])
            improvements = evaluation.get('weaknesses', []) + evaluation.get('suggestions', [])
            
            update_query = """
            UPDATE practice_sessions
            SET transcript = %s,
                response_text = %s,
                evaluation_score = %s,
                evaluation_feedback = %s,
                strengths = %s,
                improvements = %s,
                duration_seconds = %s
            WHERE session_id = %s
            """
            
            execute_query(
                update_query,
                (
                    transcript,
                    transcript,  # Also store in response_text for consistency
                    evaluation.get('score', 0),
                    json.dumps(evaluation),
                    json.dumps(strengths),
                    json.dumps(improvements),
                    duration_seconds,
                    session_id
                ),
                commit=True
            )
            
            return evaluation
            
        except Exception as e:
            print(f"[ERROR] Error evaluating audio/video response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _parse_evaluation(llm_response: str) -> Optional[Dict]:
        """Parse LLM evaluation response"""
        try:
            # Try to extract JSON from response
            import re
            
            # Remove markdown code blocks if present
            llm_response = re.sub(r'```json\s*', '', llm_response)
            llm_response = re.sub(r'```\s*', '', llm_response)
            llm_response = llm_response.strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = llm_response
            
            # Parse JSON
            evaluation = json.loads(json_str)
            
            # Ensure required fields
            if 'score' not in evaluation:
                evaluation['score'] = 0
            if 'strengths' not in evaluation:
                evaluation['strengths'] = []
            if 'weaknesses' not in evaluation:
                evaluation['weaknesses'] = []
            if 'suggestions' not in evaluation:
                evaluation['suggestions'] = []
            if 'star_method_used' not in evaluation:
                evaluation['star_method_used'] = False
            if 'star_analysis' not in evaluation:
                evaluation['star_analysis'] = {
                    'situation': 'missing',
                    'task': 'missing',
                    'action': 'missing',
                    'result': 'missing'
                }
            
            return evaluation
            
        except Exception as e:
            print(f"[ERROR] Error parsing evaluation: {e}")
            print(f"[DEBUG] LLM Response: {llm_response[:500]}")
            return None
    
    @staticmethod
    def get_session_stats(user_id: int) -> Dict:
        """Get practice session statistics for a user"""
        query = """
        SELECT 
            COUNT(*) as total_sessions,
            AVG(evaluation_score) as average_score
        FROM practice_sessions 
        WHERE user_id = %s AND evaluation_score IS NOT NULL
        """
        result = execute_query(query, (user_id,), fetch_one=True)
        
        if result:
            return {
                'total_sessions': result.get('total_sessions', 0) or 0,
                'average_score': round(result.get('average_score', 0) or 0, 1)
            }
        
        return {'total_sessions': 0, 'average_score': 0}