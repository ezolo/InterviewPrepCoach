"""
Career coach service - AI-powered career coaching
"""
import json
from typing import List, Dict, Optional, Any
from database.connection import execute_query
from services.llm_service import LLMService
from config.prompts import Prompts

class CoachService:
    """Handle career coach operations"""
    
    @staticmethod
    def create_conversation(user_id: int, title: str = "New Conversation") -> Optional[int]:
        """Create a new conversation"""
        try:
            import uuid
            # Generate unique session_id
            session_id = str(uuid.uuid4())
            
            # Insert conversation with session_id and empty messages JSON
            query = """
            INSERT INTO coach_conversations (user_id, session_id, messages) 
            VALUES (%s, %s, %s)
            """
            conversation_id = execute_query(
                query, 
                (user_id, session_id, json.dumps([])), 
                commit=True
            )
            
            return conversation_id
        except Exception as e:
            print(f"[ERROR] Error creating conversation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[Dict]:
        """Get conversation by ID"""
        query = "SELECT * FROM coach_conversations WHERE conversation_id = %s"
        return execute_query(query, (conversation_id,), fetch_one=True)
    
    @staticmethod
    def get_conversations(user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's conversations"""
        query = """
        SELECT * FROM coach_conversations 
        WHERE user_id = %s 
        ORDER BY updated_at DESC 
        LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []
    
    @staticmethod
    def get_messages(conversation_id: int) -> List[Dict]:
        """Get messages in a conversation"""
        try:
            query = """
            SELECT messages FROM coach_conversations 
            WHERE conversation_id = %s
            """
            result = execute_query(query, (conversation_id,), fetch_one=True)
            
            if result and result.get('messages'):
                messages_json = result['messages']
                if isinstance(messages_json, str):
                    messages = json.loads(messages_json)
                else:
                    messages = messages_json
                return messages if isinstance(messages, list) else []
            return []
        except Exception as e:
            print(f"[ERROR] Error getting messages: {e}")
            return []
    
    @staticmethod
    def add_message(conversation_id: int, role: str, content: str) -> Optional[int]:
        """Add a message to conversation"""
        try:
            # Get current messages
            current_messages = CoachService.get_messages(conversation_id)
            
            # Add new message
            new_message = {
                "role": role,
                "content": content,
                "timestamp": str(json.dumps({"created_at": "now"}))  # Simple timestamp
            }
            current_messages.append(new_message)
            
            # Update conversation with new messages
            query = """
            UPDATE coach_conversations 
            SET messages = %s, updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
            """
            execute_query(
                query,
                (json.dumps(current_messages), conversation_id),
                commit=True
            )
            
            return len(current_messages)  # Return message count as ID
        except Exception as e:
            print(f"[ERROR] Error adding message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_session(user_id: int) -> Dict[str, Any]:
        """Create a new coaching session with greeting
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with 'session_id' (conversation_id) and 'greeting', or 'error'
        """
        try:
            # Create conversation
            conversation_id = CoachService.create_conversation(user_id, "New Coaching Session")
            
            if not conversation_id:
                return {"error": "Failed to create conversation"}
            
            # Get user context for personalized greeting
            user_context = CoachService.get_user_context(user_id)
            
            # Generate personalized greeting
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                # Fallback greeting if no LLM configured
                greeting = "Hello! I'm your AI Career Coach. How can I help you today?"
            else:
                # Generate personalized greeting based on user's profile
                context_info = ""
                if user_context and user_context != "No context available yet.":
                    context_info = f"\n\nBased on your profile:\n{user_context}"
                
                prompt = f"""You are a friendly and professional AI Career Coach. 
Generate a warm, personalized greeting for the user. Keep it brief (2-3 sentences).
{context_info}

Greeting:"""
                
                try:
                    greeting = provider.generate(prompt, system_prompt=None)
                    if greeting.startswith("Error:") or not greeting.strip():
                        greeting = "Hello! I'm your AI Career Coach. How can I help you today?"
                except Exception as e:
                    print(f"[ERROR] Error generating greeting: {e}")
                    greeting = "Hello! I'm your AI Career Coach. How can I help you today?"
            
            # Add greeting as first message
            CoachService.add_message(conversation_id, 'assistant', greeting)
            
            return {
                "session_id": conversation_id,
                "greeting": greeting
            }
            
        except Exception as e:
            print(f"[ERROR] Error creating session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def get_user_context(user_id: int) -> str:
        """Get user context for personalized coaching - automatically fetches from profile"""
        try:
            context_parts = []
            
            # Get resume info from profile (automatically fetched)
            from services.resume_service import ResumeService
            resume = ResumeService.get_active_resume(user_id)
            if resume and resume.get('parsed_data'):
                try:
                    parsed = json.loads(resume['parsed_data']) if isinstance(resume.get('parsed_data'), str) else resume.get('parsed_data', {})
                    skills = parsed.get('skills', [])
                    if skills:
                        context_parts.append(f"Skills: {', '.join(skills[:15])}")  # Limit to 15 skills
                    if parsed.get('years_experience'):
                        context_parts.append(f"Experience: {parsed['years_experience']} years")
                    if parsed.get('education'):
                        edu = parsed.get('education', '')
                        if isinstance(edu, list):
                            edu = ', '.join(edu[:2])  # First 2 education entries
                        context_parts.append(f"Education: {str(edu)[:100]}")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[DEBUG] Error parsing resume data: {e}")
            
            # Get recent job descriptions from profile (automatically fetched)
            recent_jobs = execute_query(
                """SELECT job_title, company_name FROM job_descriptions 
                   WHERE user_id = %s 
                   ORDER BY jd_id DESC LIMIT 3""",
                (user_id,),
                fetch_all=True
            )
            
            if recent_jobs:
                jobs_list = [f"{j.get('job_title', 'Position')} at {j.get('company_name', 'Company')}" 
                            for j in recent_jobs if j]
                if jobs_list:
                    context_parts.append(f"Recent job interests: {', '.join(jobs_list)}")
            
            return "\n".join(context_parts) if context_parts else "No profile information available yet. You can upload your resume and job descriptions in the Profile Analysis section."
            
        except Exception as e:
            print(f"[ERROR] Error getting user context: {e}")
            import traceback
            traceback.print_exc()
            return "No profile information available yet."
    
    @staticmethod
    def chat(user_id: int, conversation_id: int, user_message: str) -> Dict[str, Any]:
        """
        Send a message and get AI response
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            user_message: User's message
            
        Returns:
            Dict with 'response' or 'error'
        """
        try:
            # Add user message
            CoachService.add_message(conversation_id, 'user', user_message)
            
            # Get conversation history
            messages = CoachService.get_messages(conversation_id)
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            # Build message history for LLM
            llm_messages = []
            
            # Add system prompt with context
            user_context = CoachService.get_user_context(user_id)
            system_prompt = Prompts.CAREER_COACH_SYSTEM.format(user_context=user_context)
            
            # Add conversation history (last 8 messages to avoid token limits)
            recent_messages = messages[-8:] if len(messages) > 8 else messages
            
            # Build prompt - keep it concise
            prompt_parts = []
            
            # Add system context (truncate if too long)
            if system_prompt:
                if len(system_prompt) > 1000:
                    system_prompt = system_prompt[:1000] + "..."
                prompt_parts.append(system_prompt)
            
            # Add conversation history
            if recent_messages:
                prompt_parts.append("\n\nConversation:\n")
                for msg in recent_messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    # Truncate long messages
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    if role == 'user':
                        prompt_parts.append(f"User: {content}\n")
                    elif role == 'assistant':
                        prompt_parts.append(f"Assistant: {content}\n")
            
            # Add current user message
            user_msg_truncated = user_message[:500] if len(user_message) > 500 else user_message
            prompt_parts.append(f"\nUser: {user_msg_truncated}\n")
            prompt_parts.append("Assistant: ")
            
            full_prompt = "".join(prompt_parts)
            
            # Limit total prompt length to avoid Ollama errors
            if len(full_prompt) > 3000:
                # Keep system prompt and last few messages
                prompt_parts = [system_prompt[:500]] if system_prompt else []
                prompt_parts.append(f"\n\nUser: {user_msg_truncated}\n")
                prompt_parts.append("Assistant: ")
                full_prompt = "".join(prompt_parts)
            
            # Use generate method (works for all providers)
            print(f"[DEBUG] Sending prompt to LLM (length: {len(full_prompt)})")
            response = provider.generate(full_prompt, system_prompt=None)  # System prompt already in full_prompt
            
            # Check if response contains an error
            if response and response.startswith("Error:"):
                error_msg = response
                print(f"[ERROR] LLM returned error: {error_msg}")
                return {"error": error_msg}
            
            if not response or len(response.strip()) == 0:
                error_msg = "Empty response from LLM"
                print(f"[ERROR] {error_msg}")
                return {"error": error_msg}
            
            print(f"[DEBUG] Received response from LLM (length: {len(response)})")
            
            # Add assistant response
            CoachService.add_message(conversation_id, 'assistant', response)
            
            return {"response": response}
            
        except Exception as e:
            print(f"[ERROR] Error in chat: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def get_quick_advice_prompt(advice_type: str, target_role: str = "your target role",
                                industry: str = "your industry") -> str:
        """Get a quick advice prompt"""
        prompt_template = Prompts.QUICK_ADVICE.get(advice_type, "")
        return prompt_template.format(target_role=target_role, industry=industry)
    
    @staticmethod
    def get_quick_advice(user_id: int, advice_type: str) -> Dict[str, Any]:
        """
        Get quick advice for a specific topic
        
        Args:
            user_id: User ID
            advice_type: Type of advice (resume_tips, interview_prep, job_search, skills_development, salary_negotiation)
            
        Returns:
            Dict with 'advice' or 'error'
        """
        try:
            # Map UI advice types to prompt keys
            advice_type_map = {
                "resume": "resume_tips",
                "interview": "interview_prep",
                "job_search": "job_search",
                "skills": "skills_development",
                "salary": "salary_negotiation"
            }
            
            prompt_key = advice_type_map.get(advice_type, advice_type)
            
            print(f"[DEBUG] Getting quick advice: advice_type={advice_type}, prompt_key={prompt_key}")
            
            # Get user context for personalized advice
            user_context = CoachService.get_user_context(user_id)
            
            # Get prompt template
            prompt_template = Prompts.QUICK_ADVICE.get(prompt_key, "")
            if not prompt_template:
                return {"error": f"Unknown advice type: {advice_type}"}
            
            # Get target role from user's recent job descriptions
            from services.jd_service import JobDescriptionService
            recent_jds = JobDescriptionService.get_user_job_descriptions(user_id)[:1]
            target_role = recent_jds[0].get('job_title', 'your target role') if recent_jds else 'your target role'
            industry = recent_jds[0].get('company_name', 'your industry') if recent_jds else 'your industry'
            
            # Build full prompt
            prompt = prompt_template.format(target_role=target_role, industry=industry)
            
            # Add user context
            if user_context and user_context != "No context available.":
                prompt = f"User Context:\n{user_context}\n\n{prompt}"
            
            # Get LLM provider
            llm_service = LLMService.get_instance()
            provider = llm_service.get_provider(user_id)
            
            if not provider:
                return {"error": "No LLM provider configured. Please configure an LLM in Settings."}
            
            # Generate advice with simple prompt (no system prompt to avoid Ollama issues)
            print(f"[DEBUG] Generating quick advice with prompt length: {len(prompt)}")
            advice = provider.generate(prompt, system_prompt=None)
            
            # Check for errors
            if advice and advice.startswith("Error:"):
                return {"error": advice}
            
            if not advice or len(advice.strip()) == 0:
                return {"error": "Empty response from LLM"}
            
            print(f"[DEBUG] Received advice (length: {len(advice)})")
            return {"advice": advice}
            
        except Exception as e:
            print(f"[ERROR] Error getting quick advice: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def create_session(user_id: int) -> Dict[str, Any]:
        """
        Create a new coaching conversation session
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with 'session_id' and 'greeting' or 'error'
        """
        try:
            conversation_id = CoachService.create_conversation(user_id, "New Coaching Session")
            
            if not conversation_id:
                return {"error": "Failed to create conversation"}
            
            # Generate greeting
            user_context = CoachService.get_user_context(user_id)
            greeting = f"""Hello! I'm your AI Career Coach. I'm here to help you with:

• Resume improvement and career strategy
• Interview preparation and practice
• Job search guidance
• Application tracking and follow-ups
• Skills development roadmap
• Salary negotiation advice

I have access to your profile and can provide personalized advice. How can I help you today?"""
            
            # Add greeting as first message
            CoachService.add_message(conversation_id, 'assistant', greeting)
            
            return {
                "session_id": conversation_id,
                "greeting": greeting
            }
            
        except Exception as e:
            print(f"[ERROR] Error creating session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def send_message(user_id: int, conversation_id: int, message: str) -> Dict[str, Any]:
        """
        Send a message in a conversation
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            message: User's message
            
        Returns:
            Dict with 'response' or 'error'
        """
        return CoachService.chat(user_id, conversation_id, message)
