"""Career Coach Agent - Main orchestrator for career guidance"""

from typing import Dict, Any, List, Optional
from services.llm_service import LLMService
from services.resume_service import ResumeService
from services.application_service import ApplicationService
from services.practice_service import PracticeService
from config.prompts import Prompts
import json

class CareerCoachAgent:
    """Main career coach agent that provides personalized guidance"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm_service = LLMService.get_instance()
        self.conversation_history = []
        self.context = {}
        
    def start_conversation(self):
        """Initialize conversation with greeting"""
        self._load_user_context()
        
        greeting = f"""Hello! I'm your AI Career Coach. I'm here to help you with:

• Resume improvement and career strategy
• Interview preparation and practice
• Job search guidance
• Application tracking and follow-ups
• Skills development roadmap
• Salary negotiation advice

I have access to your profile, practice history, and applications. How can I help you today?"""
        
        self.conversation_history.append({
            "role": "assistant",
            "content": greeting
        })
        
        return greeting
    
    def _load_user_context(self):
        """Load user's current context"""
        # Get resume
        resume = ResumeService.get_active_resume(self.user_id)
        if resume:
            self.context['resume'] = {
                'filename': resume['file_name'],
                'skills': resume.get('parsed_data', {}).get('skills', []) if resume.get('parsed_data') else []
            }
        
        # Get practice stats
        practice_stats = PracticeService.get_session_stats(self.user_id)
        self.context['practice'] = practice_stats
        
        # Get application stats
        app_stats = ApplicationService.get_application_stats(self.user_id)
        self.context['applications'] = app_stats
    
    def chat(self, user_message: str) -> str:
        """Handle user message and generate response
        
        Args:
            user_message: User's message
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Build context-aware prompt
        system_prompt = self._build_system_prompt()
        conversation_prompt = self._build_conversation_prompt(user_message)
        
        # Get LLM response
        provider = self.llm_service.get_provider(self.user_id)
        
        try:
            response = provider.generate(conversation_prompt, system_prompt)
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
        
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error. Please try again or check your LLM settings. Error: {str(e)}"
            return error_msg
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with context"""
        context_str = f"""
USER CONTEXT:
- Resume: {'Uploaded' if 'resume' in self.context else 'Not uploaded'}
- Practice Sessions: {self.context.get('practice', {}).get('total_sessions', 0)}
- Average Practice Score: {self.context.get('practice', {}).get('average_score', 0)}%
- Job Applications: {self.context.get('applications', {}).get('total', 0)}
- Interview Rate: {self.context.get('applications', {}).get('interview_rate', 0)}%
"""
        
        return Prompts.CAREER_COACH_SYSTEM + "\n\n" + context_str
    
    def _build_conversation_prompt(self, user_message: str) -> str:
        """Build conversation prompt with history"""
        # Include last 5 messages for context
        recent_history = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
        
        prompt = "CONVERSATION HISTORY:\n"
        for msg in recent_history:
            role = "User" if msg['role'] == 'user' else "Coach"
            prompt += f"{role}: {msg['content']}\n\n"
        
        prompt += f"User: {user_message}\n\nCoach:"
        
        return prompt
    
    def get_resume_advice(self) -> str:
        """Get specific resume advice"""
        resume = ResumeService.get_active_resume(self.user_id)
        
        if not resume:
            return "Please upload your resume first so I can provide specific advice."
        
        prompt = f"""Based on this resume, provide 5 specific, actionable improvements:

RESUME:
{resume['resume_text'][:2000]}

Focus on:
1. Content and achievements
2. Keywords and ATS optimization
3. Structure and formatting
4. Skills presentation
5. Overall impact"""
        
        provider = self.llm_service.get_provider(self.user_id)
        return provider.generate(prompt)
    
    def get_interview_tips(self, job_title: str = None) -> str:
        """Get interview preparation tips"""
        if job_title:
            prompt = f"Provide 7 key interview tips for a {job_title} position. Include behavioral and technical aspects."
        else:
            prompt = "Provide 7 universal interview tips that apply to most professional positions."
        
        provider = self.llm_service.get_provider(self.user_id)
        return provider.generate(prompt)
    
    def analyze_job_search_strategy(self) -> str:
        """Analyze and provide job search strategy advice"""
        stats = self.context.get('applications', {})
        
        prompt = f"""Analyze this job search performance and provide strategic advice:

- Total Applications: {stats.get('total', 0)}
- Response Rate: {stats.get('response_rate', 0)}%
- Interview Rate: {stats.get('interview_rate', 0)}%
- Applications by Status: {stats.get('by_status', {})}

Provide specific advice on:
1. Whether to apply to more jobs or focus on quality
2. How to improve response rate
3. Application strategy improvements
4. Networking suggestions
5. Timeline and follow-up strategy"""
        
        provider = self.llm_service.get_provider(self.user_id)
        return provider.generate(prompt)
    
    def get_skill_development_plan(self, target_role: str) -> str:
        """Create a skills development plan"""
        current_skills = self.context.get('resume', {}).get('skills', [])
        
        prompt = f"""Create a 90-day skills development plan for someone targeting a {target_role} position.

CURRENT SKILLS:
{', '.join(current_skills) if current_skills else 'Not specified'}

Provide:
1. Priority skills to learn/improve
2. Recommended learning resources
3. Week-by-week plan
4. Practice projects
5. How to demonstrate these skills"""
        
        provider = self.llm_service.get_provider(self.user_id)
        return provider.generate(prompt)
    
    def get_salary_negotiation_advice(self, role: str, offered_salary: float = None) -> str:
        """Get salary negotiation advice"""
        if offered_salary:
            prompt = f"""Provide salary negotiation advice for a {role} position with an offer of ${offered_salary:,.2f}.

Include:
1. Market research suggestions
2. Negotiation strategy
3. What to say and when
4. Benefits beyond salary
5. Red flags to watch for"""
        else:
            prompt = f"""Provide general salary negotiation advice for a {role} position.

Include:
1. How to research market rates
2. When and how to discuss salary
3. Negotiation tactics
4. Total compensation considerations
5. Common mistakes to avoid"""
        
        provider = self.llm_service.get_provider(self.user_id)
        return provider.generate(prompt)

