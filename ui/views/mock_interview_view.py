from typing import Dict, List, Optional
"""Mock Interview View - Comprehensive practice hub"""

import json
import os
import asyncio
from typing import Dict, List, Optional
import flet as ft
from datetime import datetime
from services.mock_interview_service import MockInterviewService
from services.question_service import QuestionService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from services.practice_service import PracticeService
from core.auth import SessionManager
from ui.styles.theme import AppTheme
from core.recording_service import AudioRecorder, VideoRecorder, TranscriptionService
from config.settings import Settings

class MockInterviewView:
    """Mock Interview Practice Hub"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.current_session_id = None
        self.current_session = None
        self.session_questions = []
        self.current_question_index = 0
        self.session_config = {}
        self.current_question: Optional[Dict] = None
        
        # UI state
        self.setup_wizard_active = False
        self.live_session_active = False
        self.analytics_active = False
        
        # Response/timer state
        self.response_mode = "written"
        self.response_text_field: Optional[ft.TextField] = None
        self.notes_field: Optional[ft.TextField] = None
        self.mode_selector: Optional[ft.RadioGroup] = None
        self.audio_container: Optional[ft.Container] = None
        self.video_container: Optional[ft.Container] = None
        self.audio_record_button: Optional[ft.ElevatedButton] = None
        self.audio_stop_button: Optional[ft.ElevatedButton] = None
        self.audio_status_text: Optional[ft.Text] = None
        self.video_record_button: Optional[ft.ElevatedButton] = None
        self.video_stop_button: Optional[ft.ElevatedButton] = None
        self.video_status_text: Optional[ft.Text] = None
        self.audio_recorder: Optional[AudioRecorder] = None
        self.video_recorder: Optional[VideoRecorder] = None
        self.video_audio_recorder: Optional[AudioRecorder] = None
        self.audio_file_path: Optional[str] = None
        self.video_file_path: Optional[str] = None
        self.video_audio_temp_path: Optional[str] = None
        self.audio_transcript: Optional[str] = None
        self.video_transcript: Optional[str] = None
        self.is_recording_audio = False
        self.is_recording_video = False
        
        self.timer_text_control: Optional[ft.Text] = None
        self.timer_task = None
        self.timer_running = False
        self.timer_paused = False
        self.remaining_seconds = 0
        self.question_start_time: Optional[datetime] = None
        
    def build(self) -> ft.Container:
        """Build mock interview view"""
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("🎯 Mock Interview Hub", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Comprehensive interview practice with AI feedback", size=12, color="grey")
            ], spacing=4),
            padding=ft.padding.only(left=20, top=15, bottom=10)
        )
        
        # Main action buttons
        action_buttons = ft.Row([
            ft.ElevatedButton(
                "➕ New Mock Interview",
                icon=ft.Icons.ADD_CIRCLE,
                on_click=self._show_setup_wizard,
                style=ft.ButtonStyle(
                    bgcolor=AppTheme.PRIMARY,
                    color="white",
                    padding=15
                )
            ),
            ft.ElevatedButton(
                "📊 View Analytics",
                icon=ft.Icons.ANALYTICS,
                on_click=self._show_analytics,
                style=ft.ButtonStyle(
                    bgcolor=AppTheme.INFO,
                    color="white",
                    padding=15
                )
            ),
            ft.ElevatedButton(
                "📚 Practice Library",
                icon=ft.Icons.LIBRARY_BOOKS,
                on_click=self._show_library,
                style=ft.ButtonStyle(
                    bgcolor=AppTheme.SECONDARY,
                    color="white",
                    padding=15
                )
            )
        ], spacing=15, wrap=True)
        
        # Content area (will show setup wizard, live session, or library)
        self.content_area = ft.Container(
            content=self._build_welcome_screen(),
            expand=True,
            padding=20
        )
        
        # Main layout
        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(),
                action_buttons,
                ft.Divider(),
                self.content_area
            ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True),
            padding=10,
            expand=True
        )
    
    def _build_welcome_screen(self) -> ft.Column:
        """Build welcome screen"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECORD_VOICE_OVER, size=80, color=AppTheme.PRIMARY),
                    ft.Text("Welcome to Mock Interview Hub", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Practice realistic interviews with AI-powered feedback", size=14, color="grey"),
                    ft.Divider(),
                    ft.Text("Features:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Column([
                        ft.Text("• Multiple interview formats (Traditional, Technical, Behavioral, Case)", size=12),
                        ft.Text("• Written, Audio, and Video response modes", size=12),
                        ft.Text("• Real-time AI evaluation with detailed feedback", size=12),
                        ft.Text("• Progress tracking and analytics", size=12),
                        ft.Text("• Practice library with searchable history", size=12)
                    ], spacing=5)
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _show_setup_wizard(self, e):
        """Show session setup wizard"""
        self.setup_wizard_active = True
        self.content_area.content = self._build_setup_wizard()
        self.page.update()
    
    def _build_setup_wizard(self) -> ft.Column:
        """Build session setup wizard"""
        # Step 1: Format Selection
        format_options = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="traditional", label="📋 Traditional Interview"),
                ft.Radio(value="technical", label="💻 Technical Interview"),
                ft.Radio(value="behavioral", label="🧠 Behavioral Interview (STAR method)"),
                ft.Radio(value="case", label="📊 Case Study Interview")
            ], spacing=10),
            value="traditional"
        )
        
        # Step 2: Question Source
        question_source_options = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="generated", label="✨ Auto-generate from Resume & JD"),
                ft.Radio(value="set", label="📚 Use Existing Question Set"),
                ft.Radio(value="custom", label="✏️ Custom Questions (Coming Soon)")
            ], spacing=10),
            value="generated"
        )
        
        # Get available question sets
        question_sets = QuestionService.get_question_sets(self.user_id) or []
        question_set_dropdown = ft.Dropdown(
            label="Select Question Set",
            options=[
                ft.dropdown.Option(str(qs['set_id']), qs.get('set_name', 'Unknown'))
                for qs in question_sets
            ],
            disabled=len(question_sets) == 0,
            visible=False
        )
        
        # Get resumes and JDs
        resumes = ResumeService.get_all_resumes(self.user_id) or []
        jds = JobDescriptionService.get_user_job_descriptions(self.user_id) or []
        
        resume_dropdown = ft.Dropdown(
            label="Select Resume",
            options=[
                ft.dropdown.Option(str(r['resume_id']), r.get('file_name', 'Resume'))
                for r in resumes
            ],
            disabled=len(resumes) == 0
        )
        
        jd_dropdown = ft.Dropdown(
            label="Select Job Description",
            options=[
                ft.dropdown.Option(str(jd['jd_id']), jd.get('job_title', 'Job'))
                for jd in jds
            ],
            disabled=len(jds) == 0
        )
        
        # Step 3: Configuration
        session_name_field = ft.TextField(
            label="Session Name",
            hint_text="e.g., Amazon SDE Behavioral Practice",
            value=""
        )
        
        num_questions_slider = ft.Slider(
            min=3, max=15, value=5, divisions=12,
            label="{value} questions"
        )
        num_questions_text = ft.Text("5 questions", size=14, weight=ft.FontWeight.BOLD)
        
        difficulty_dropdown = ft.Dropdown(
            label="Difficulty Level",
            options=[
                ft.dropdown.Option("easy", "Easy"),
                ft.dropdown.Option("medium", "Medium"),
                ft.dropdown.Option("hard", "Hard")
            ],
            value="medium"
        )
        
        time_per_question_field = ft.TextField(
            label="Time per Question (seconds)",
            value="120",
            width=200
        )
        
        prep_time_field = ft.TextField(
            label="Prep Time (seconds)",
            value="30",
            width=200
        )
        
        feedback_mode_dropdown = ft.Dropdown(
            label="Feedback Mode",
            options=[
                ft.dropdown.Option("post_session", "After Session"),
                ft.dropdown.Option("per_question", "After Each Question"),
                ft.dropdown.Option("real_time", "Real-time Hints")
            ],
            value="post_session"
        )
        
        # Update slider text
        def update_slider_text(e):
            num_questions_text.value = f"{int(e.control.value)} questions"
            self.page.update()
        
        num_questions_slider.on_change = update_slider_text
        
        # Show/hide question set dropdown based on source
        def on_source_change(e):
            question_set_dropdown.visible = (question_source_options.value == "set")
            self.page.update()
        
        question_source_options.on_change = on_source_change
        
        # Create session button
        def create_session(e):
            if not session_name_field.value:
                self._show_error("Please enter a session name")
                return
            
            if question_source_options.value == "generated":
                if not resume_dropdown.value or not jd_dropdown.value:
                    self._show_error("Please select both resume and job description")
                    return
            elif question_source_options.value == "set":
                if not question_set_dropdown.value:
                    self._show_error("Please select a question set")
                    return
            
            config = {
                'num_questions': int(num_questions_slider.value),
                'difficulty': difficulty_dropdown.value,
                'time_per_question': int(time_per_question_field.value),
                'prep_time': int(prep_time_field.value),
                'feedback_mode': feedback_mode_dropdown.value
            }
            
            session_id = MockInterviewService.create_session(
                user_id=self.user_id,
                session_name=session_name_field.value,
                format_type=format_options.value,
                question_source=question_source_options.value,
                question_set_id=int(question_set_dropdown.value) if question_set_dropdown.value else None,
                resume_id=int(resume_dropdown.value) if resume_dropdown.value else None,
                jd_id=int(jd_dropdown.value) if jd_dropdown.value else None,
                config=config
            )
            
            if session_id:
                self.current_session_id = session_id
                self.session_config = config
                self._start_live_session()
            else:
                self._show_error("Failed to create session")
        
        create_button = ft.ElevatedButton(
            "🚀 Start Mock Interview",
            icon=ft.Icons.PLAY_ARROW,
            on_click=create_session,
            style=ft.ButtonStyle(
                bgcolor=AppTheme.SUCCESS,
                color="white",
                padding=15
            )
        )
        
        # Wizard content
        wizard_content = ft.Column([
            ft.Text("Session Setup", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("Step 1: Interview Format", size=18, weight=ft.FontWeight.BOLD),
            format_options,
            ft.Divider(),
            
            ft.Text("Step 2: Question Source", size=18, weight=ft.FontWeight.BOLD),
            question_source_options,
            question_set_dropdown,
            ft.Row([resume_dropdown, jd_dropdown], spacing=20, wrap=True),
            ft.Divider(),
            
            ft.Text("Step 3: Configuration", size=18, weight=ft.FontWeight.BOLD),
            session_name_field,
            ft.Row([
                ft.Column([
                    num_questions_text,
                    num_questions_slider
                ]),
                difficulty_dropdown
            ], spacing=20, wrap=True),
            ft.Row([
                time_per_question_field,
                prep_time_field,
                feedback_mode_dropdown
            ], spacing=20, wrap=True),
            ft.Divider(),
            
            create_button
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        return wizard_content
    
    def _start_live_session(self):
        """Start the live interview session"""
        if not self.current_session_id:
            return
        
        self.live_session_active = True
        self.setup_wizard_active = False
        
        # Start session in database
        MockInterviewService.start_session(self.current_session_id)
        
        # Get session questions
        self.session_questions = MockInterviewService.get_session_questions(self.current_session_id)
        self.current_question_index = 0
        
        # Load session
        self.current_session = MockInterviewService.get_session(self.current_session_id)
        if self.current_session:
            config_str = self.current_session.get('config', '{}')
            try:
                self.session_config = json.loads(config_str) if isinstance(config_str, str) else config_str
            except:
                self.session_config = {}
        
        self.content_area.content = self._build_live_session()
        self.page.update()
    
    def _build_live_session(self) -> ft.Column:
        """Build live session interface"""
        # Reload questions if needed
        if not self.session_questions and self.current_session_id:
            self.session_questions = MockInterviewService.get_session_questions(self.current_session_id)
        
        if not self.session_questions:
            return ft.Column([
                ft.Text("No questions available", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Please ensure you have selected a question set or have resume/JD for generation", size=12, color="grey"),
                ft.ElevatedButton("Back to Setup", on_click=lambda e: self._reset_view())
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        if self.current_question_index >= len(self.session_questions):
            # Session complete
            return ft.Column([
                ft.Text("✅ Session Complete!", size=24, weight=ft.FontWeight.BOLD, color=AppTheme.SUCCESS),
                ft.Text(f"You completed {len(self.session_questions)} questions", size=16),
                ft.ElevatedButton(
                    "View Results",
                    icon=ft.Icons.ANALYTICS,
                    on_click=lambda e: self._complete_session(),
                    style=ft.ButtonStyle(bgcolor=AppTheme.PRIMARY, color="white")
                ),
                ft.ElevatedButton("Back to Hub", on_click=lambda e: self._reset_view())
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        current_question = self.session_questions[self.current_question_index]
        self.current_question = current_question
        self._reset_response_state()
        self.question_start_time = datetime.now()
        self.remaining_seconds = max(0, int(self.session_config.get('time_per_question', 120) or 0))
        total_questions = len(self.session_questions)
        
        # Progress indicator
        progress_text = ft.Text(
            f"Question {self.current_question_index + 1} of {total_questions}",
            size=16,
            weight=ft.FontWeight.BOLD
        )
        
        progress_bar = ft.ProgressBar(
            value=(self.current_question_index + 1) / total_questions,
            width=400
        )
        
        # Question display
        question_display_text = self._get_question_text(current_question)
        question_text = ft.Container(
            content=ft.Column([
                ft.Text("Question:", size=14, weight=ft.FontWeight.BOLD, color="grey"),
                ft.Text(
                    question_display_text,
                    size=18,
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=5),
            padding=20,
            bgcolor="#F5F5F5",
            border_radius=8,
            width=600
        )
        
        # Timer display
        self.timer_text_control = ft.Text(
            self._format_time(self.remaining_seconds),
            size=24,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.PRIMARY
        )
        
        # Notes area
        self.notes_field = ft.TextField(
            label="Notes / Keywords",
            hint_text="Jot down key points before responding...",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=600
        )
        
        # Response controls
        response_controls = self._build_response_controls()
        
        # Action buttons
        flag_button = ft.OutlinedButton(
            "🚩 Flag for Review",
            icon=ft.Icons.FLAG,
            on_click=lambda e: self._flag_question()
        )
        
        skip_button = ft.OutlinedButton(
            "⏭ Skip",
            icon=ft.Icons.SKIP_NEXT,
            on_click=lambda e: self._skip_question()
        )
        
        self.submit_button = ft.ElevatedButton(
            "✓ Submit Response",
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=lambda e: self._submit_response(),
            style=ft.ButtonStyle(
                bgcolor=AppTheme.PRIMARY,
                color="white"
            )
        )
        
        next_button = ft.ElevatedButton(
            "➡ Next Question",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda e: self._next_question(),
            visible=False
        )
        
        # Store button reference
        self.next_button = next_button
        
        # Session controls
        self.pause_button = ft.OutlinedButton(
            "⏸ Pause",
            icon=ft.Icons.PAUSE,
            on_click=lambda e: self._pause_session()
        )
        
        exit_button = ft.OutlinedButton(
            "Exit Session",
            icon=ft.Icons.EXIT_TO_APP,
            on_click=lambda e: self._exit_session()
        )
        
        # Live session layout
        layout = ft.Column([
            ft.Row([
                progress_text,
                ft.Container(expand=True),
                self.timer_text_control,
                self.pause_button,
                exit_button
            ], spacing=10),
            progress_bar,
            ft.Divider(),
            question_text,
            ft.Divider(),
            ft.Text("Notes:", size=14, weight=ft.FontWeight.BOLD),
            self.notes_field,
            ft.Divider(),
            response_controls,
            ft.Divider(),
            ft.Row([
                flag_button,
                skip_button,
                ft.Container(expand=True),
                self.submit_button,
                next_button
            ], spacing=10, wrap=True)
        ], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        self._start_timer()
        
        return layout
    
    def _build_response_controls(self) -> ft.Column:
        """Build response controls for the current mode"""
        question_hint = self._get_question_text(self.current_question)[:100] if self.current_question else ""
        
        self.mode_selector = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="written", label="📝 Written"),
                ft.Radio(value="audio", label="🎤 Audio"),
                ft.Radio(value="video", label="🎥 Video")
            ], spacing=20, wrap=True),
            value=self.response_mode,
            on_change=self._on_response_mode_change
        )
        
        self.response_text_field = ft.TextField(
            label="Your Response",
            hint_text=f"Question: {question_hint}..." if question_hint else "Type your response here...",
            multiline=True,
            min_lines=8,
            max_lines=18,
            width=600,
            visible=self.response_mode == "written"
        )
        
        # Audio controls
        self.audio_record_button = ft.ElevatedButton(
            "🔴 Start Recording",
            icon=ft.Icons.MIC,
            on_click=self._on_audio_record,
            disabled=self.response_mode != "audio"
        )
        self.audio_stop_button = ft.ElevatedButton(
            "⏹ Stop Recording",
            icon=ft.Icons.STOP,
            on_click=self._on_audio_stop,
            disabled=True
        )
        self.audio_status_text = ft.Text(
            "Ready to record",
            size=12,
            color="grey",
            italic=True
        )
        self.audio_container = ft.Container(
            content=ft.Column([
                ft.Text("🎤 Audio Response", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.audio_record_button, self.audio_stop_button], spacing=10),
                self.audio_status_text,
                ft.Text("Your audio will be transcribed automatically.", size=11, color="grey")
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            visible=self.response_mode == "audio"
        )
        
        # Video controls
        self.video_record_button = ft.ElevatedButton(
            "🔴 Start Recording",
            icon=ft.Icons.VIDEOCAM,
            on_click=self._on_video_record,
            disabled=self.response_mode != "video"
        )
        self.video_stop_button = ft.ElevatedButton(
            "⏹ Stop Recording",
            icon=ft.Icons.STOP,
            on_click=self._on_video_stop,
            disabled=True
        )
        self.video_status_text = ft.Text(
            "Ready to record",
            size=12,
            color="grey",
            italic=True
        )
        self.video_container = ft.Container(
            content=ft.Column([
                ft.Text("🎥 Video Response", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.video_record_button, self.video_stop_button], spacing=10),
                self.video_status_text,
                ft.Text("We'll capture audio for transcription along with your video.", size=11, color="grey")
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            visible=self.response_mode == "video"
        )
        
        controls = ft.Column([
            ft.Text("Response Mode", size=14, weight=ft.FontWeight.BOLD),
            self.mode_selector,
            self.response_text_field,
            self.audio_container,
            self.video_container
        ], spacing=10)
        
        self._update_response_mode_visibility()
        return controls
    
    def _submit_response(self):
        """Submit response for current question"""
        if not self.current_session_id or not self.session_questions:
            return
        
        current_question = self.session_questions[self.current_question_index]
        question_id = current_question.get('question_id') or current_question.get('id')
        if not question_id:
            self._show_error("Question data is incomplete.")
            return
        
        notes_value = self.notes_field.value if self.notes_field else ""
        duration = self._calculate_response_duration()
        
        response_text = ""
        transcript = None
        audio_path = None
        video_path = None
        
        if self.response_mode == "written":
            response_text = (self.response_text_field.value if self.response_text_field else "").strip()
            if not response_text:
                self._show_error("Please enter your response")
                return
        elif self.response_mode == "audio":
            if not self.audio_file_path:
                self._show_error("Please record an audio response first")
                return
            transcript = self.audio_transcript or ""
            response_text = transcript or "[Audio response]"
            audio_path = self.audio_file_path
        elif self.response_mode == "video":
            if not self.video_file_path:
                self._show_error("Please record a video response first")
                return
            if not self.video_transcript:
                self._show_error("Transcript not available yet. Please wait for transcription or re-record.")
                return
            transcript = self.video_transcript
            response_text = transcript
            video_path = self.video_file_path
        else:
            self._show_error("Invalid response mode selected.")
            return
        
        response_id = MockInterviewService.save_response(
            session_id=self.current_session_id,
            question_id=question_id,
            question_index=self.current_question_index,
            response_mode=self.response_mode,
            response_text=response_text,
            audio_file_path=audio_path,
            video_file_path=video_path,
            transcript=transcript,
            notes=notes_value,
            duration_seconds=duration
        )
        
        if response_id:
            # Show success and enable next button
            self.next_button.visible = True
            if self.response_text_field:
                self.response_text_field.disabled = True
            if self.notes_field:
                self.notes_field.disabled = True
            if self.submit_button:
                self.submit_button.disabled = True
            self._stop_timer()
            self._stop_recordings()
            self.page.update()
        else:
            self._show_error("Failed to save response")
    
    def _on_response_mode_change(self, e):
        self.response_mode = self.mode_selector.value if self.mode_selector else "written"
        self._update_response_mode_visibility()
        self.page.update()
    
    def _update_response_mode_visibility(self):
        if self.response_text_field:
            self.response_text_field.visible = (self.response_mode == "written")
            self.response_text_field.disabled = False
        if self.audio_container:
            self.audio_container.visible = (self.response_mode == "audio")
        if self.video_container:
            self.video_container.visible = (self.response_mode == "video")
        if self.audio_record_button:
            self.audio_record_button.disabled = not (self.response_mode == "audio")
        if self.video_record_button:
            self.video_record_button.disabled = not (self.response_mode == "video")
        if self.submit_button:
            self.submit_button.disabled = False
    
    def _format_time(self, seconds: int) -> str:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def _start_timer(self):
        self._stop_timer()
        if self.remaining_seconds <= 0:
            self._update_timer_text()
            return
        self.timer_running = True
        self.timer_paused = False
        self.timer_task = self.page.run_task(self._timer_loop)
    
    def _stop_timer(self):
        self.timer_running = False
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
    
    async def _timer_loop(self):
        try:
            while self.timer_running and self.remaining_seconds >= 0:
                self._update_timer_text()
                await asyncio.sleep(1)
                if not self.timer_paused:
                    self.remaining_seconds -= 1
            if self.timer_running and self.remaining_seconds < 0:
                self._handle_time_expired()
        except asyncio.CancelledError:
            pass
    
    def _update_timer_text(self):
        if self.timer_text_control:
            self.timer_text_control.value = self._format_time(max(0, self.remaining_seconds))
            try:
                self.timer_text_control.update()
            except Exception:
                pass
    
    def _handle_time_expired(self):
        self.timer_running = False
        self.remaining_seconds = 0
        self._update_timer_text()
        self._show_error("Time is up for this question. Please submit your response or skip to the next question.")
    
    def _calculate_response_duration(self) -> int:
        if not self.question_start_time:
            return 0
        delta = datetime.now() - self.question_start_time
        return max(0, int(delta.total_seconds()))
    
    def _reset_response_state(self):
        self._stop_timer()
        self._stop_recordings()
        self.audio_file_path = None
        self.video_file_path = None
        self.video_audio_temp_path = None
        self.audio_transcript = None
        self.video_transcript = None
        self.is_recording_audio = False
        self.is_recording_video = False
        self.response_mode = "written"
        
        if self.response_text_field:
            self.response_text_field.value = ""
            self.response_text_field.disabled = False
            self.response_text_field.visible = True
        if self.notes_field:
            self.notes_field.value = ""
            self.notes_field.disabled = False
        if self.mode_selector:
            self.mode_selector.value = "written"
        if self.submit_button:
            self.submit_button.disabled = False
        if hasattr(self, "next_button") and self.next_button:
            self.next_button.visible = False
    
    def _stop_recordings(self):
        if self.is_recording_audio and self.audio_recorder:
            try:
                self.audio_recorder.stop_recording()
            except Exception:
                pass
        if self.is_recording_video and self.video_recorder:
            try:
                self.video_recorder.stop_recording()
            except Exception:
                pass
        if self.video_audio_recorder:
            try:
                self.video_audio_recorder.stop_recording()
            except Exception:
                pass
        self.is_recording_audio = False
        self.is_recording_video = False
        self.audio_recorder = None
        self.video_recorder = None
        self.video_audio_recorder = None
        self.video_audio_temp_path = None
    
    def _on_audio_record(self, e):
        try:
            if self.is_recording_audio:
                return
            if not self.current_session_id:
                self._show_error("Start the session first.")
                return
            self.audio_recorder = AudioRecorder()
            self.audio_recorder.start_recording()
            self.is_recording_audio = True
            if self.audio_record_button:
                self.audio_record_button.disabled = True
            if self.audio_stop_button:
                self.audio_stop_button.disabled = False
            if self.audio_status_text:
                self.audio_status_text.value = "🔴 Recording... Click stop when finished."
                self.audio_status_text.color = ft.Colors.RED
            self.page.update()
        except Exception as ex:
            self._show_error(f"Error starting audio recording: {ex}")
    
    def _on_audio_stop(self, e):
        try:
            if not self.audio_recorder or not self.is_recording_audio:
                return
            audio_data = self.audio_recorder.stop_recording()
            self.is_recording_audio = False
            if self.audio_record_button:
                self.audio_record_button.disabled = False
            if self.audio_stop_button:
                self.audio_stop_button.disabled = True
            if audio_data is None:
                self._show_error("No audio captured.")
                return
            os.makedirs(Settings.AUDIO_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.audio_file_path = os.path.join(
                Settings.AUDIO_DIR,
                f"mock_{self.current_session_id}_{timestamp}.wav"
            )
            if not self.audio_recorder.save_recording(audio_data, self.audio_file_path):
                self._show_error("Failed to save audio recording.")
                return
            if self.audio_status_text:
                self.audio_status_text.value = "⏳ Transcribing audio..."
                self.audio_status_text.color = "grey"
                self.page.update()
            transcript = TranscriptionService.transcribe_audio(self.audio_file_path)
            if transcript:
                self.audio_transcript = transcript
                if self.audio_status_text:
                    self.audio_status_text.value = f"✓ Transcribed: {transcript[:100]}..."
                    self.audio_status_text.color = ft.Colors.GREEN
            else:
                if self.audio_status_text:
                    self.audio_status_text.value = "⚠️ Transcription failed. Audio saved."
                    self.audio_status_text.color = ft.Colors.ORANGE
            self.page.update()
        except Exception as ex:
            self._show_error(f"Error stopping audio recording: {ex}")
    
    def _on_video_record(self, e):
        try:
            if self.is_recording_video:
                return
            if not self.current_session_id:
                self._show_error("Start the session first.")
                return
            os.makedirs(Settings.VIDEO_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_file_path = os.path.join(
                Settings.VIDEO_DIR,
                f"mock_{self.current_session_id}_{timestamp}.mp4"
            )
            self.video_recorder = VideoRecorder()
            self.video_recorder.start_recording(self.video_file_path)
            # Parallel audio capture for transcription
            os.makedirs(Settings.AUDIO_DIR, exist_ok=True)
            self.video_audio_temp_path = os.path.join(
                Settings.AUDIO_DIR,
                f"mock_video_audio_{self.current_session_id}_{timestamp}.wav"
            )
            self.video_audio_recorder = AudioRecorder()
            self.video_audio_recorder.start_recording()
            self.is_recording_video = True
            if self.video_record_button:
                self.video_record_button.disabled = True
            if self.video_stop_button:
                self.video_stop_button.disabled = False
            if self.video_status_text:
                self.video_status_text.value = "🔴 Recording video... Click stop when done."
                self.video_status_text.color = ft.Colors.RED
            self.page.update()
        except Exception as ex:
            self._show_error(f"Error starting video recording: {ex}")
    
    def _on_video_stop(self, e):
        try:
            if not self.video_recorder or not self.is_recording_video:
                return
            video_path = self.video_recorder.stop_recording()
            self.is_recording_video = False
            if self.video_record_button:
                self.video_record_button.disabled = False
            if self.video_stop_button:
                self.video_stop_button.disabled = True
            if not video_path or not os.path.exists(video_path):
                self._show_error("No video captured.")
                return
            transcript = None
            if self.video_audio_recorder:
                try:
                    audio_data = self.video_audio_recorder.stop_recording()
                    if audio_data is not None and self.video_audio_temp_path:
                        self.video_audio_recorder.save_recording(audio_data, self.video_audio_temp_path)
                        transcript = TranscriptionService.transcribe_audio(self.video_audio_temp_path)
                        self.video_transcript = transcript
                except Exception:
                    transcript = None
                finally:
                    self.video_audio_recorder = None
            if transcript:
                if self.video_status_text:
                    self.video_status_text.value = "✓ Video saved and transcribed."
                    self.video_status_text.color = ft.Colors.GREEN
            else:
                if self.video_status_text:
                    self.video_status_text.value = "Video saved. Transcript unavailable."
                    self.video_status_text.color = ft.Colors.ORANGE
            self.page.update()
        except Exception as ex:
            self._show_error(f"Error stopping video recording: {ex}")
    
    def _get_question_text(self, question: Optional[Dict]) -> str:
        if not question:
            return "No question text"
        return (
            question.get('question_text')
            or question.get('question')
            or question.get('prompt')
            or "No question text"
        )
    
    def _next_question(self):
        """Move to next question"""
        self._stop_timer()
        self._stop_recordings()
        if self.current_question_index < len(self.session_questions) - 1:
            self.current_question_index += 1
            self.content_area.content = self._build_live_session()
            self.page.update()
        else:
            # Session complete
            self._complete_session()
    
    def _flag_question(self):
        """Flag current question for review"""
        # Implementation for flagging
        self._show_success("Question flagged for review")
    
    def _skip_question(self):
        """Skip current question"""
        # Implementation for skipping
        self._next_question()
    
    def _pause_session(self):
        """Pause the session"""
        if not self.timer_running:
            self._show_error("Timer is not running.")
            return
        self.timer_paused = not self.timer_paused
        if self.pause_button:
            self.pause_button.text = "▶ Resume" if self.timer_paused else "⏸ Pause"
        self.page.update()
    
    def _exit_session(self):
        """Exit session and return to main view"""
        self._stop_timer()
        self._stop_recordings()
        self._reset_view()
    
    def _complete_session(self):
        """Complete the session and show results"""
        self._stop_timer()
        self._stop_recordings()
        MockInterviewService.complete_session(self.current_session_id)
        self._show_analytics(None)
    
    def _show_analytics(self, e):
        """Show analytics dashboard"""
        self.analytics_active = True
        self.live_session_active = False
        
        # Get user sessions
        sessions = MockInterviewService.get_user_sessions(self.user_id, limit=10)
        
        # Build analytics view
        analytics_content = ft.Column([
            ft.Text("📊 Analytics Dashboard", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Total Sessions: {len(sessions)}", size=16),
            ft.Divider(),
            ft.Text("Recent Sessions:", size=18, weight=ft.FontWeight.BOLD),
            ft.Column([
                self._build_session_card(session) for session in sessions
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
        ], spacing=15)
        
        self.content_area.content = analytics_content
        self.page.update()
    
    def _build_session_card(self, session: Dict) -> ft.Container:
        """Build a session card for display"""
        session_name = session.get('session_name', 'Unnamed Session')
        format_type = session.get('format_type', 'traditional')
        status = session.get('status', 'draft')
        created_at = session.get('created_at', '')
        
        return ft.Container(
            content=ft.Column([
                ft.Text(session_name, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"Format: {format_type.title()} | Status: {status.title()}", size=12, color="grey"),
                ft.Text(f"Created: {created_at}", size=10, color="grey"),
                ft.ElevatedButton(
                    "View Details",
                    on_click=lambda e, sid=session['session_id']: self._view_session_details(sid),
                    height=30
                )
            ], spacing=5),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            border=ft.border.all(1, "#E0E0E0")
        )
    
    def _view_session_details(self, session_id: int):
        """View detailed session information"""
        # Implementation for viewing session details
        self._show_success(f"Viewing session {session_id}")
    
    def _show_library(self, e):
        """Show practice library"""
        sessions = MockInterviewService.get_user_sessions(self.user_id)
        
        library_content = ft.Column([
            ft.Text("📚 Practice Library", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Total Sessions: {len(sessions)}", size=16),
            ft.Divider(),
            ft.Column([
                self._build_session_card(session) for session in sessions
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
        ], spacing=15)
        
        self.content_area.content = library_content
        self.page.update()
    
    def _reset_view(self):
        """Reset view to welcome screen"""
        self.setup_wizard_active = False
        self.live_session_active = False
        self.analytics_active = False
        self.current_session_id = None
        self.current_question = None
        self._stop_timer()
        self._stop_recordings()
        self.content_area.content = self._build_welcome_screen()
        self.page.update()
    
    def _show_error(self, message: str):
        """Show error dialog"""
        dialog = ft.AlertDialog(
            title=ft.Text("Error"),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(dialog))]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success message"""
        dialog = ft.AlertDialog(
            title=ft.Text("Success"),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(dialog))]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()

