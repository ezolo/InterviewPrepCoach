"""
Question generation and management service
"""
from typing import List, Dict, Optional, Any
from database.connection import execute_query
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from services.llm_service import LLMService
from config.prompts import Prompts
import json

class QuestionService:
    """Handle interview question generation and management"""
    
    @staticmethod
    def generate_questions(user_id: int, resume_id: int, jd_id: int,
                          question_type: str = 'behavioral',
                          count: int = 5,
                          set_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate interview questions using LLM
        
        Args:
            user_id: User ID
            resume_id: Resume ID
            jd_id: Job description ID
            question_type: Type of questions (behavioral, technical, situational)
            count: Number of questions to generate
            set_name: Optional name for the question set
            
        Returns:
            Dict with set_id and questions, or None if failed
        """
        try:
            # 1. Get resume and JD
            resume = ResumeService.get_resume_by_id(resume_id)
            jd = JobDescriptionService.get_job_description(jd_id)
            
            if not resume or not jd:
                print("[ERROR] Resume or JD not found")
                return None
            
            # 2. Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                print("[ERROR] No LLM provider configured")
                return None
            
            # 3. Format prompt
            prompt = Prompts.QUESTION_GENERATION.format(
                count=count,
                difficulty='medium',
                question_type=question_type,
                resume_summary=resume.get('resume_text', '')[:2000],
                job_description=jd.get('jd_text', '')[:2000]
            )
            
            print(f"[INFO] Generating {count} {question_type} questions...")
            
            questions_data = []
            
            # 4. Generate with LLM using generate_json to handle text before JSON
            # Use generate_json if available, otherwise fall back to generate
            if hasattr(provider, 'generate_json'):
                response_data = provider.generate_json(prompt)
                
                # Check for errors and fall back to manual parsing when possible
                if isinstance(response_data, dict) and 'error' in response_data:
                    print(f"[WARN] LLM JSON parse error: {response_data['error']}")
                    raw_response = response_data.get('raw_response')
                    
                    if raw_response:
                        questions_data = QuestionService._parse_questions_from_text(raw_response)
                    
                    if not questions_data:
                        print("[INFO] Retrying question generation using plain text response")
                        raw_response = provider.generate(prompt)
                        questions_data = QuestionService._parse_questions_from_text(raw_response)
                else:
                    # Extract questions from response
                    if isinstance(response_data, list):
                        questions_data = response_data
                    elif isinstance(response_data, dict):
                        questions_data = response_data.get('questions', [])
                    else:
                        print(f"[ERROR] Unexpected response format: {type(response_data)}")
                        return None
            else:
                # Fallback to generate() and manual parsing
                response = provider.generate(prompt)
                questions_data = QuestionService._parse_questions_from_text(response)
            
            if not questions_data:
                print("[ERROR] No questions generated")
                return None
            
            # 6. Create question set
            if not set_name:
                set_name = f"{question_type.title()} Questions - {jd.get('job_title', 'Unknown')}"
            
            # Both 'name' and 'set_name' are required in the schema
            set_query = """
                INSERT INTO question_sets (user_id, name, set_name, jd_id, resume_id, question_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            set_id = execute_query(
                set_query, 
                (user_id, set_name, set_name, jd_id, resume_id, len(questions_data)),
                commit=True
            )
            
            if not set_id:
                print("[ERROR] Failed to create question set")
                return None
            
            # Sync set_id column with id for code compatibility
            execute_query(
                "UPDATE question_sets SET set_id = id WHERE id = %s",
                (set_id,),
                commit=True
            )
            
            print(f"[INFO] Created question set with ID: {set_id}")
            
            # 7. Save questions
            saved_questions = []
            for q_data in questions_data:
                question_text = q_data.get('question', '') if isinstance(q_data, dict) else str(q_data)
                
                if not question_text:
                    continue
                
                question_type = q_data.get('type', 'behavioral') if isinstance(q_data, dict) else 'behavioral'
                difficulty = q_data.get('difficulty', 'medium') if isinstance(q_data, dict) else 'medium'
                ideal_answer_points = json.dumps(q_data.get('ideal_answer_points', [])) if isinstance(q_data, dict) else '[]'
                
                question_query = """
                    INSERT INTO questions 
                    (question_set_id, set_id, question_text, question_type, difficulty, ideal_answer_points)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                question_id = execute_query(
                    question_query,
                    (set_id, set_id, question_text, question_type, difficulty, ideal_answer_points),
                    commit=True
                )
                
                # Sync question_id column with id for code compatibility
                if question_id:
                    execute_query(
                        "UPDATE questions SET question_id = id WHERE id = %s",
                        (question_id,),
                        commit=True
                    )
                
                if question_id:
                    saved_questions.append({
                        'question_id': question_id,
                        'question': question_text,
                        'difficulty': q_data.get('difficulty', 'medium') if isinstance(q_data, dict) else 'medium',
                        'category': q_data.get('category', '') if isinstance(q_data, dict) else '',
                        'ideal_answer_points': q_data.get('ideal_answer_points', []) if isinstance(q_data, dict) else []
                    })
            
            print(f"[INFO] Saved {len(saved_questions)} questions")
            
            return {
                'set_id': set_id,
                'set_name': set_name,
                'questions': saved_questions,
                'count': len(saved_questions)
            }
            
        except Exception as e:
            print(f"[ERROR] Error generating questions: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _parse_questions_from_text(response_text: Optional[str]) -> List[Dict[str, Any]]:
        """Extract questions list from a raw LLM response"""
        if not response_text:
            return []
        
        response_clean = response_text.strip()
        
        # Remove markdown code fences
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()
        
        if not response_clean:
            return []
        
        # Try to locate a complete JSON block (array or object)
        json_block = QuestionService._extract_json_block(response_clean)
        if json_block:
            try:
                parsed = json.loads(json_block)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
                print(f"[DEBUG] Response snippet: {response_text[:500]}")
                parsed = None
        else:
            parsed = None
        
        # Happy path: direct list or wrapped list
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            if 'questions' in parsed and isinstance(parsed['questions'], list):
                return parsed.get('questions', [])
            # Some providers might wrap data differently
            if 'data' in parsed and isinstance(parsed['data'], list):
                return parsed['data']
        
        # Fallback: tolerant parsing like PracticeService, for providers (e.g., Ollama) that
        # return almost-correct JSON. We scan for individual { ... } blocks and parse each.
        try:
            import re
            objs: List[Dict[str, Any]] = []
            for m in re.finditer(r'\{[\s\S]*?\}', response_clean):
                block = m.group(0)
                try:
                    obj = json.loads(block)
                    # Only keep things that look like question objects
                    if isinstance(obj, dict) and ('question' in obj or 'question_text' in obj):
                        objs.append(obj)
                except json.JSONDecodeError:
                    continue
            if objs:
                return objs
        except Exception as fallback_err:
            print(f"[ERROR] Fallback question parsing failed: {fallback_err}")
        
        print(f"[WARN] Parsed JSON did not contain questions list or could not recover questions")
        print(f"[DEBUG] Response snippet: {response_text[:500]}")
        return []
    
    @staticmethod
    def _extract_json_block(text: str) -> Optional[str]:
        """Extract the first complete JSON object/array from text"""
        start_idx = -1
        opening_char = ''
        closing_char = ''
        
        for i, char in enumerate(text):
            if char in ['[', '{']:
                start_idx = i
                opening_char = char
                closing_char = ']' if char == '[' else '}'
                break
        
        if start_idx == -1:
            return None
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"':
                prev_char = text[i-1] if i > 0 else ''
                if prev_char == '\\':
                    continue
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == opening_char:
                depth += 1
            elif char == closing_char:
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        
        return text[start_idx:]  # Return whatever we have (may still fail to parse)
    
    @staticmethod
    def get_question_sets(user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's question sets"""
        query = """
        SELECT qs.*, jd.job_title, jd.company_name 
        FROM question_sets qs
        LEFT JOIN job_descriptions jd ON qs.jd_id = jd.jd_id
        WHERE qs.user_id = %s 
        ORDER BY qs.created_at DESC
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
    
    @staticmethod
    def get_questions(set_id: int) -> List[Dict]:
        """Get questions in a set"""
        query = """
        SELECT * FROM questions 
        WHERE set_id = %s 
        ORDER BY question_id ASC
        """
        return execute_query(query, (set_id,), fetch_all=True) or []
    
    @staticmethod
    def get_question_set_with_questions(set_id: int) -> Optional[Dict]:
        """Get a question set with all its questions"""
        set_query = "SELECT * FROM question_sets WHERE set_id = %s"
        question_set = execute_query(set_query, (set_id,), fetch_one=True)
        
        if not question_set:
            return None
        
        questions = QuestionService.get_questions(set_id)
        question_set['questions'] = questions
        
        return question_set
    
    @staticmethod
    def delete_question_set(set_id: int) -> bool:
        """Delete a question set and all its questions"""
        try:
            # Questions will be deleted automatically due to CASCADE
            query = "DELETE FROM question_sets WHERE set_id = %s"
            execute_query(query, (set_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error deleting question set: {e}")
            return False
