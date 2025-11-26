"""Practice Sessions View"""

import json
import os
import flet as ft
from datetime import datetime
from services.practice_service import PracticeService
from services.question_service import QuestionService
from core.auth import SessionManager
from core.recording_service import AudioRecorder, VideoRecorder
from ui.styles.theme import AppTheme
from config.settings import Settings

class PracticeView:
    """View for practice interview sessions"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.current_session_id = None
        self.current_question_id = None
        self.current_question = None
        self.start_time = None
        self.response_mode = "written"  # written, audio, video
        
        # Recording state
        self.audio_recorder = None
        self.video_recorder = None
        self.audio_file_path = None
        self.video_file_path = None
        self.is_recording = False
        
        # UI components
        self.question_set_dropdown = None
        self.question_dropdown = None
        self.mode_selector = None
        self.response_text_field = None
        self.audio_container = None
        self.video_container = None
        self.evaluation_container = None
        self.sessions_container = None
        self.sessions_list = None
        self.skill_focus_field = None
        self.question_card = None
        self.video_audio_recorder = None
        self.video_audio_temp_path = None
        
    def build(self) -> ft.Container:
        """Build practice view"""
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("🎯 Practice Sessions", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Practice interview questions with AI feedback", size=12, color="grey")
                ], spacing=4, expand=True),
                ft.ElevatedButton(
                    "🎯 Mock Interview Hub",
                    icon=ft.Icons.RECORD_VOICE_OVER,
                    on_click=lambda e: self.page.go("/mock-interview"),
                    style=ft.ButtonStyle(
                        bgcolor=AppTheme.PRIMARY,
                        color="white"
                    )
                )
            ], spacing=10),
            padding=ft.padding.only(left=20, top=15, bottom=10)
        )
        
        # Question set selection
        question_sets = QuestionService.get_question_sets(self.user_id) or []
        
        self.question_set_dropdown = ft.Dropdown(
            label="Select Question Set",
            hint_text="Choose a question set" if question_sets else "Generate questions first",
            options=[
                ft.dropdown.Option(
                    str(qs['set_id']),
                    f"{qs.get('set_name', 'Unknown')} - {qs.get('job_title', 'Job')}"
                )
                for qs in question_sets
            ],
            width=400,
            border_color=ft.Colors.PRIMARY,
            disabled=len(question_sets) == 0,
            on_change=self._on_question_set_selected
        )
        
        self.question_dropdown = ft.Dropdown(
            label="Select Question",
            hint_text="Select a question set first",
            width=400,
            border_color=ft.Colors.PRIMARY,
            disabled=True,
            on_change=self._on_question_selected
        )
        
        # Skill focus input
        self.skill_focus_field = ft.TextField(
            label="Skill focus (optional)",
            hint_text="E.g., Storytelling, Technical depth, Executive presence",
            width=300,
            border_color=ft.Colors.PRIMARY,
            on_change=lambda _: self._update_question_card()
        )
        
        # Question details card placeholder
        self.question_card = ft.Container(
            content=ft.Column([
                ft.Text("Question focus", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Select a question to view details and ideal answer points.",
                        size=12, color="grey")
            ], spacing=6),
            padding=15,
            bgcolor="#F8F9FA",
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
        
        # Mode selection
        self.mode_selector = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="written", label="📝 Written"),
                ft.Radio(value="audio", label="🎤 Audio"),
                ft.Radio(value="video", label="🎥 Video"),
            ], spacing=20),
            value="written",
            on_change=self._on_mode_changed
        )
        
        mode_container = ft.Container(
            content=ft.Column([
                ft.Text("Response mode", size=14, weight=ft.FontWeight.BOLD),
                self.mode_selector
            ], spacing=5),
            padding=10,
            bgcolor="#F5F5F5",
            border_radius=8
        )
        
        # Written mode response area
        self.response_text_field = ft.TextField(
            label="Your Response",
            hint_text="Type your answer here...",
            multiline=True,
            min_lines=8,
            max_lines=15,
            expand=True,
            border_color=ft.Colors.PRIMARY,
            disabled=True,
            visible=True
        )
        
        # Audio mode response area
        self.audio_record_button = ft.ElevatedButton(
            "🔴 Start Recording",
            icon=ft.Icons.MIC,
            on_click=self._on_audio_record,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED,
                color=ft.Colors.WHITE
            ),
            disabled=True
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
                ft.Text("🎤 Audio Recording", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.audio_record_button,
                    self.audio_stop_button
                ], spacing=10),
                self.audio_status_text,
                ft.Text("Your recorded response will be transcribed automatically", 
                       size=12, color="grey", italic=True)
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            visible=False
        )
        
        # Video mode response area
        self.video_record_button = ft.ElevatedButton(
            "🔴 Start Recording",
            icon=ft.Icons.VIDEOCAM,
            on_click=self._on_video_record,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED,
                color=ft.Colors.WHITE
            ),
            disabled=True
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
        
        self.video_preview = ft.Container(
            content=ft.Text("Video preview will appear here", size=12, color="grey"),
            width=640,
            height=360,
            bgcolor=ft.Colors.BLACK,
            border_radius=8,
            alignment=ft.alignment.center
        )
        
        self.video_container = ft.Container(
            content=ft.Column([
                ft.Text("🎥 Video Recording", size=16, weight=ft.FontWeight.BOLD),
                self.video_preview,
                ft.Row([
                    self.video_record_button,
                    self.video_stop_button
                ], spacing=10),
                self.video_status_text,
                ft.Text("Your video response will be analyzed", 
                       size=12, color="grey", italic=True)
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            visible=False
        )
        
        # Buttons
        submit_button = ft.ElevatedButton(
            "✓ Submit Response",
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self._on_submit_response,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE
            ),
            disabled=True
        )
        
        reset_button = ft.OutlinedButton(
            "↻ Reset",
            icon=ft.Icons.REFRESH,
            on_click=self._on_reset,
            disabled=True
        )
        
        # Store button references
        self.submit_button = submit_button
        self.reset_button = reset_button
        
        learning_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SELF_IMPROVEMENT, color=ft.Colors.PRIMARY),
                ft.Text(
                    "Learning mode • take your time, focus on skill-building",
                    size=12,
                    color=ft.Colors.PRIMARY
                )
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            padding=12,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            border_radius=8
        )
        
        # Evaluation container (initially hidden)
        self.evaluation_container = ft.Container(
            content=ft.Column([
                ft.Text("📊 Evaluation Results", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Submit a response to see evaluation", size=14, color="grey", italic=True)
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            visible=False
        )
        
        # Main practice area
        practice_area = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.question_set_dropdown,
                    self.question_dropdown
                ], spacing=20, wrap=True),
                ft.Row([
                    self.skill_focus_field
                ], spacing=20, wrap=True),
                self.question_card,
                ft.Divider(),
                mode_container,
                ft.Divider(),
                learning_banner,
                ft.Row([
                    submit_button,
                    reset_button
                ], spacing=10, wrap=True),
                ft.Divider(),
                # Mode-specific response areas
                self.response_text_field,
                self.audio_container,
                self.video_container,
                ft.Container(height=10),
                self.evaluation_container
            ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True),
            padding=20,
            expand=True
        )
        
        # Previous sessions list with dedicated scrollbar
        self.sessions_list = ft.ListView(
            spacing=10,
            auto_scroll=False,
            expand=True
        )
        
        self.sessions_container = ft.Container(
            content=ft.Column([
                ft.Text("📚 Previous Sessions", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(
                    content=self.sessions_list,
                    height=520,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=6,
                    padding=ft.padding.all(6)
                )
            ], spacing=10),
            padding=15,
            bgcolor="#F5F5F5",
            border_radius=8,
            width=360
        )
        
        # Load previous sessions
        self._load_previous_sessions()
        
        # Main layout
        main_content = ft.Row([
            ft.Container(
                content=practice_area,
                expand=True,
                padding=10
            ),
            ft.Container(
                content=self.sessions_container,
                padding=10
            )
        ], spacing=10, expand=True)
        
        return ft.Container(
            content=ft.Column([
                header,
                main_content
            ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
            padding=10,
            expand=True
        )
    
    def _on_question_set_selected(self, e):
        """Handle question set selection"""
        if not self.question_set_dropdown.value:
            return
        
        set_id = int(self.question_set_dropdown.value)
        questions = QuestionService.get_questions(set_id) or []
        
        # Update question dropdown
        self.question_dropdown.options = [
            ft.dropdown.Option(
                str(q['question_id']),
                q.get('question_text', 'Question')[:80] + ('...' if len(q.get('question_text', '')) > 80 else '')
            )
            for q in questions
        ]
        self.question_dropdown.disabled = len(questions) == 0
        self.question_dropdown.value = None
        self.question_dropdown.hint_text = f"Choose from {len(questions)} questions" if questions else "No questions available"
        
        # Reset state
        self._reset_practice_state()
        self._update_question_card()
        self.page.update()
    
    def _start_new_session(self):
        """Create a fresh practice session for the selected question"""
        if not self.current_question_id:
            return
        
        # Preserve selected question while clearing previous session state
        self._reset_practice_state(preserve_question=True)
        
        question_set_id = (
            self.current_question.get('question_set_id')
            or self.current_question.get('set_id')
        )
        skill_focus = (self.skill_focus_field.value or "").strip() or None
        
        session_id = PracticeService.create_session(
            self.user_id,
            self.current_question_id,
            self.response_mode,
            question_set_id=question_set_id,
            skill_focus=skill_focus
        )
        
        if not session_id:
            self._show_error("Failed to start practice session. Please try again.")
            return
        
        self.current_session_id = session_id
        self.start_time = datetime.now()
        self.submit_button.disabled = False
        self.reset_button.disabled = False
        
        if self.response_mode == "written":
            self.response_text_field.disabled = False
            self.response_text_field.focus()
        elif self.response_mode == "audio":
            self.audio_status_text.value = "Ready to record. Click 'Start Recording' when you feel prepared."
            self.audio_status_text.color = "grey"
        elif self.response_mode == "video":
            self.video_status_text.value = "Ready to record. Click 'Start Recording' whenever you're ready."
            self.video_status_text.color = "grey"
        else:
            self.response_text_field.disabled = True
        
        self._update_mode_controls()
    
    def _update_question_card(self):
        """Update the question focus card with current details"""
        if not self.question_card:
            return
        
        if not self.current_question:
            self.question_card.content = ft.Column([
                ft.Text("Question focus", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Select a question to review its prompt and ideal answer points.",
                    size=12,
                    color="grey"
                )
            ], spacing=6)
            return
        
        question_text = self.current_question.get('question_text', 'Question')
        ideal_points = self.current_question.get('ideal_answer_points', [])
        if isinstance(ideal_points, str):
            try:
                ideal_points = json.loads(ideal_points)
            except Exception:
                ideal_points = []
        
        content_items = [
            ft.Text("Question focus", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(question_text, size=14, weight=ft.FontWeight.W_500)
        ]
        
        skill_focus_value = (self.skill_focus_field.value or "").strip()
        if skill_focus_value:
            content_items.append(
                ft.Chip(
                    label=ft.Text(f"Skill: {skill_focus_value}", size=12),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    color=ft.Colors.PRIMARY
                )
            )
        
        if ideal_points:
            content_items.append(ft.Text("Ideal answer points", size=12, weight=ft.FontWeight.BOLD))
            content_items.append(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.PRIMARY),
                        ft.Text(point, size=12)
                    ], spacing=6)
                    for point in ideal_points[:5]
                ], spacing=4)
            )
        
        self.question_card.content = ft.Column(content_items, spacing=8)
    
    def _on_question_selected(self, e):
        """Handle question selection"""
        if not self.question_dropdown.value:
            return
        
        question_id = int(self.question_dropdown.value)
        set_id = int(self.question_set_dropdown.value)
        
        # Get question details
        questions = QuestionService.get_questions(set_id) or []
        self.current_question = next((q for q in questions if q['question_id'] == question_id), None)
        
        if self.current_question:
            self.current_question_id = question_id
            self._update_question_card()
            self._start_new_session()
        else:
            self.submit_button.disabled = True
            self.reset_button.disabled = True
        
        self.page.update()
    
    def _on_mode_changed(self, e):
        """Handle mode selection change"""
        self.response_mode = self.mode_selector.value
        
        # Reset recordings but keep the current question
        self._reset_practice_state(preserve_question=True)
        if self.current_question_id:
            self._start_new_session()
        
        self._update_mode_controls()
        self.page.update()
    
    def _update_mode_controls(self):
        """Update UI controls based on selected mode"""
        # Written mode
        written_visible = (self.response_mode == "written")
        self.response_text_field.visible = written_visible
        if written_visible:
            self.response_text_field.disabled = not bool(self.current_session_id)
            hint_question = self.current_question.get('question_text', '') if self.current_question else ''
            self.response_text_field.hint_text = (
                f"Question: {hint_question[:100]}..." if hint_question else "Type your answer here..."
            )
        
        # Audio mode
        audio_visible = (self.response_mode == "audio")
        self.audio_container.visible = audio_visible
        self.audio_record_button.disabled = not (audio_visible and self.current_session_id)
        self.audio_stop_button.disabled = True
        
        # Video mode
        video_visible = (self.response_mode == "video")
        self.video_container.visible = video_visible
        self.video_record_button.disabled = not (video_visible and self.current_session_id)
        self.video_stop_button.disabled = True
    
    def _on_audio_record(self, e):
        """Start audio recording"""
        try:
            if not self.current_session_id:
                self._show_error("Please start a practice session first")
                return
            
            # Initialize audio recorder
            self.audio_recorder = AudioRecorder()
            self.audio_recorder.start_recording()
            self.is_recording = True
            
            # Update UI
            self.audio_record_button.disabled = True
            self.audio_stop_button.disabled = False
            self.audio_status_text.value = "🔴 Recording... Click 'Stop Recording' when done."
            self.audio_status_text.color = ft.Colors.RED
            
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error starting audio recording: {ex}")
            self._show_error(f"Error starting recording: {str(ex)}")
    
    def _on_audio_stop(self, e):
        """Stop audio recording"""
        try:
            if not self.audio_recorder or not self.is_recording:
                return
            
            # Stop recording
            audio_data = self.audio_recorder.stop_recording()
            self.is_recording = False
            
            if audio_data is None:
                self._show_error("No audio recorded")
                return
            
            # Save audio file
            os.makedirs(Settings.AUDIO_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.audio_file_path = os.path.join(
                Settings.AUDIO_DIR,
                f"practice_{self.current_session_id}_{timestamp}.wav"
            )
            
            if not self.audio_recorder.save_recording(audio_data, self.audio_file_path):
                self._show_error("Failed to save audio recording")
                return
            
            # Update UI
            self.audio_record_button.disabled = True
            self.audio_stop_button.disabled = True
            self.audio_status_text.value = "✓ Recording saved. Click 'Submit Response' to evaluate."
            self.audio_status_text.color = ft.Colors.GREEN
            
            # Calculate duration
            if self.start_time:
                duration = int((datetime.now() - self.start_time).total_seconds())
            else:
                duration = 0
            
            # Save audio response and transcribe
            self.audio_status_text.value = "⏳ Transcribing audio..."
            self.page.update()
            
            transcript = PracticeService.save_audio_response(
                self.current_session_id,
                self.audio_file_path,
                duration
            )
            
            if transcript:
                self.audio_status_text.value = f"✓ Transcribed: {transcript[:100]}..."
            else:
                self.audio_status_text.value = "⚠ Transcription failed, but audio saved."
            
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error stopping audio recording: {ex}")
            self._show_error(f"Error: {str(ex)}")
            self.is_recording = False
    
    def _on_video_record(self, e):
        """Start video recording"""
        try:
            if not self.current_session_id:
                self._show_error("Please start a practice session first")
                return
            
            # Initialize video recorder
            os.makedirs(Settings.VIDEO_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_file_path = os.path.join(
                Settings.VIDEO_DIR,
                f"practice_{self.current_session_id}_{timestamp}.mp4"
            )
            self.video_audio_temp_path = os.path.join(
                Settings.AUDIO_DIR,
                f"practice_audio_{self.current_session_id}_{timestamp}.wav"
            )
            
            self.video_recorder = VideoRecorder()
            self.video_recorder.start_recording(self.video_file_path)
            
            # Start parallel audio capture for transcription
            try:
                os.makedirs(Settings.AUDIO_DIR, exist_ok=True)
                self.video_audio_recorder = AudioRecorder()
                self.video_audio_recorder.start_recording()
            except Exception as audio_ex:
                print(f"[WARNING] Unable to start audio capture for video: {audio_ex}")
                self.video_audio_recorder = None
                self.video_audio_temp_path = None
            
            self.is_recording = True
            
            # Update UI
            self.video_record_button.disabled = True
            self.video_stop_button.disabled = False
            self.video_status_text.value = "🔴 Recording... Click 'Stop Recording' when done."
            self.video_status_text.color = ft.Colors.RED
            
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error starting video recording: {ex}")
            self._show_error(f"Error starting recording: {str(ex)}")
    
    def _on_video_stop(self, e):
        """Stop video recording"""
        try:
            if not self.video_recorder or not self.is_recording:
                return
            
            # Stop recording
            video_path = self.video_recorder.stop_recording()
            self.is_recording = False
            
            if not video_path or not os.path.exists(video_path):
                self._show_error("No video recorded")
                return
            
            # Calculate duration
            if self.start_time:
                duration = int((datetime.now() - self.start_time).total_seconds())
            else:
                duration = 0
            
            # Stop accompanying audio capture for transcription
            transcript = None
            if self.video_audio_recorder:
                try:
                    audio_data = self.video_audio_recorder.stop_recording()
                    if audio_data is not None and self.video_audio_temp_path:
                        saved = self.video_audio_recorder.save_recording(audio_data, self.video_audio_temp_path)
                        if saved:
                            transcript = PracticeService.save_audio_response(
                                self.current_session_id,
                                self.video_audio_temp_path,
                                duration
                            )
                except Exception as audio_ex:
                    print(f"[WARNING] Video audio capture error: {audio_ex}")
                finally:
                    self.video_audio_recorder = None
            
            # Save video response
            if PracticeService.save_video_response(
                self.current_session_id,
                video_path,
                duration,
                transcript=transcript
            ):
                self.video_status_text.value = "✓ Video saved. Click 'Submit Response' to evaluate."
                self.video_status_text.color = ft.Colors.GREEN
            else:
                self._show_error("Failed to save video recording")
            
            # Update UI
            self.video_record_button.disabled = True
            self.video_stop_button.disabled = True
            
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error stopping video recording: {ex}")
            self._show_error(f"Error: {str(ex)}")
            self.is_recording = False
    
    def _on_submit_response(self, e):
        """Submit response for evaluation"""
        if not self.current_session_id:
            self._show_error("Please start a practice session first")
            return
        
        # Calculate duration
        if self.start_time:
            duration = int((datetime.now() - self.start_time).total_seconds())
        else:
            duration = 0
        
        # Disable buttons during evaluation
        self.submit_button.disabled = True
        self.submit_button.text = "⏳ Evaluating..."
        self.page.update()
        
        try:
            evaluation = None
            
            if self.response_mode == "written":
                # Written mode: use text field
                response_text = self.response_text_field.value.strip()
                if not response_text:
                    self._show_error("Please enter your response")
                    self.submit_button.disabled = False
                    self.submit_button.text = "✓ Submit Response"
                    self.page.update()
                    return
                
                evaluation = PracticeService.evaluate_response(
                    self.user_id,
                    self.current_session_id,
                    self.current_question_id,
                    response_text,
                    duration
                )
            
            elif self.response_mode == "audio":
                # Audio mode: use transcript from saved audio
                if not self.audio_file_path:
                    self._show_error("Please record an audio response first")
                    self.submit_button.disabled = False
                    self.submit_button.text = "✓ Submit Response"
                    self.page.update()
                    return
                
                # Get transcript from session
                session = PracticeService.get_session_by_id(self.current_session_id)
                transcript = session.get('transcript', '') if session else ''
                
                if not transcript:
                    self._show_error("No transcript available. Please record again.")
                    self.submit_button.disabled = False
                    self.submit_button.text = "✓ Submit Response"
                    self.page.update()
                    return
                
                evaluation = PracticeService.evaluate_audio_or_video_response(
                    self.user_id,
                    self.current_session_id,
                    self.current_question_id,
                    transcript,
                    duration
                )
            
            elif self.response_mode == "video":
                if not self.video_file_path:
                    self._show_error("Please record a video response first")
                    self.submit_button.disabled = False
                    self.submit_button.text = "✓ Submit Response"
                    self.page.update()
                    return
                
                session = PracticeService.get_session_by_id(self.current_session_id)
                transcript = session.get('transcript', '') if session else ''
                
                if not transcript:
                    self._show_error("Transcript not available. Please stop your recording to save it before submitting.")
                    self.submit_button.disabled = False
                    self.submit_button.text = "✓ Submit Response"
                    self.page.update()
                    return
                
                evaluation = PracticeService.evaluate_audio_or_video_response(
                    self.user_id,
                    self.current_session_id,
                    self.current_question_id,
                    transcript,
                    duration
                )
            
            if not evaluation:
                self._show_error("Failed to evaluate response. Please try again.")
                self.submit_button.disabled = False
                self.submit_button.text = "✓ Submit Response"
                self.page.update()
                return
            
            # Display evaluation
            self._display_evaluation(evaluation)
            
            # Reload previous sessions
            self._load_previous_sessions()
            
            # Reset buttons
            self.submit_button.disabled = True
            self.submit_button.text = "✓ Submit Response"
            self.reset_button.disabled = False
            
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error submitting response: {ex}")
            self._show_error(f"Error: {str(ex)}")
            self.submit_button.disabled = False
            self.submit_button.text = "✓ Submit Response"
            self.page.update()
    
    def _display_evaluation(self, evaluation: dict):
        """Display evaluation results"""
        score = evaluation.get('score', 0)
        strengths = evaluation.get('strengths', [])
        weaknesses = evaluation.get('weaknesses', [])
        suggestions = evaluation.get('suggestions', [])
        star_used = evaluation.get('star_method_used', False)
        star_analysis = evaluation.get('star_analysis', {})
        
        # Score display
        score_color = ft.Colors.GREEN if score >= 70 else ft.Colors.ORANGE if score >= 50 else ft.Colors.RED
        score_text = ft.Container(
            content=ft.Row([
                ft.Text(f"Score: ", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"{score}/100", size=24, weight=ft.FontWeight.BOLD, color=score_color)
            ], spacing=5),
            padding=10,
            bgcolor="#F5F5F5",
            border_radius=8
        )
        
        # STAR method indicator
        star_indicator = None
        if star_analysis:
            star_parts = ['Situation', 'Task', 'Action', 'Result']
            star_status = [
                star_analysis.get('situation', 'missing'),
                star_analysis.get('task', 'missing'),
                star_analysis.get('action', 'missing'),
                star_analysis.get('result', 'missing')
            ]
            
            star_items = []
            for part, status in zip(star_parts, star_status):
                color = ft.Colors.GREEN if status == 'present' else ft.Colors.ORANGE if status == 'weak' else ft.Colors.RED
                icon = ft.Icons.CHECK_CIRCLE if status == 'present' else ft.Icons.WARNING if status == 'weak' else ft.Icons.CANCEL
                star_items.append(
                    ft.Row([
                        ft.Icon(icon, color=color, size=16),
                        ft.Text(f"{part}: {status.title()}", size=12, color=color)
                    ], spacing=5)
                )
            
            star_indicator = ft.Container(
                content=ft.Column([
                    ft.Text("STAR Method Analysis", size=14, weight=ft.FontWeight.BOLD),
                    ft.Column(star_items, spacing=5)
                ], spacing=8),
                padding=10,
                bgcolor="#F5F5F5",
                border_radius=8
            )
        
        # Strengths
        strengths_list = None
        if strengths:
            strengths_list = ft.Container(
                content=ft.Column([
                    ft.Text("✅ Strengths", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ft.Column([
                        ft.Text(f"• {s}", size=12) for s in strengths[:5]
                    ], spacing=3)
                ], spacing=5),
                padding=10,
                bgcolor="#F5F5F5",
                border_radius=8
            )
        
        # Weaknesses
        weaknesses_list = None
        if weaknesses:
            weaknesses_list = ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ Areas for Improvement", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                    ft.Column([
                        ft.Text(f"• {w}", size=12) for w in weaknesses[:5]
                    ], spacing=3)
                ], spacing=5),
                padding=10,
                bgcolor="#F5F5F5",
                border_radius=8
            )
        
        # Suggestions
        suggestions_list = None
        if suggestions:
            suggestions_list = ft.Container(
                content=ft.Column([
                    ft.Text("💡 Suggestions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    ft.Column([
                        ft.Text(f"• {s}", size=12) for s in suggestions[:5]
                    ], spacing=3)
                ], spacing=5),
                padding=10,
                bgcolor="#F5F5F5",
                border_radius=8
            )
        
        # Build evaluation content
        eval_content = [
            ft.Text("📊 Evaluation Results", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            score_text
        ]
        
        if star_indicator:
            eval_content.append(star_indicator)
        
        if strengths_list:
            eval_content.append(strengths_list)
        
        if weaknesses_list:
            eval_content.append(weaknesses_list)
        
        if suggestions_list:
            eval_content.append(suggestions_list)
        
        self.evaluation_container.content = ft.Column(eval_content, spacing=10)
        self.evaluation_container.visible = True
        self.page.update()
    
    def _on_reset(self, e):
        """Reset practice session"""
        self._reset_practice_state()
        self.page.update()
    
    def _reset_practice_state(self, preserve_question: bool = False):
        """Reset practice state, optionally keeping the selected question"""
        prev_question_id = self.current_question_id
        prev_question = self.current_question
        prev_dropdown_value = self.question_dropdown.value if self.question_dropdown else None
        
        # Stop any ongoing recordings
        if self.is_recording:
            if self.audio_recorder:
                try:
                    self.audio_recorder.stop_recording()
                except Exception:
                    pass
            if self.video_recorder:
                try:
                    self.video_recorder.stop_recording()
                except Exception:
                    pass
            if self.video_audio_recorder:
                try:
                    self.video_audio_recorder.stop_recording()
                except Exception:
                    pass
            self.is_recording = False
        
        self.current_session_id = None
        self.start_time = None
        
        # Reset written mode
        self.response_text_field.value = ""
        self.response_text_field.disabled = True
        self.response_text_field.hint_text = "Type your answer here..."
        
        # Reset audio mode
        self.audio_file_path = None
        self.audio_record_button.disabled = True
        self.audio_stop_button.disabled = True
        self.audio_status_text.value = "Ready to record"
        self.audio_status_text.color = "grey"
        
        # Reset video mode
        self.video_file_path = None
        self.video_audio_temp_path = None
        self.video_audio_recorder = None
        self.video_record_button.disabled = True
        self.video_stop_button.disabled = True
        self.video_status_text.value = "Ready to record"
        self.video_status_text.color = "grey"
        
        self.submit_button.disabled = True
        self.reset_button.disabled = True
        
        self.evaluation_container.visible = False
        
        if preserve_question:
            self.current_question_id = prev_question_id
            self.current_question = prev_question
            if self.question_dropdown:
                self.question_dropdown.value = prev_dropdown_value
        else:
            self.current_question_id = None
            self.current_question = None
            if self.question_dropdown:
                self.question_dropdown.value = None
        
        self._update_question_card()
    
    def _load_previous_sessions(self):
        """Load previous practice sessions"""
        try:
            sessions = PracticeService.get_sessions(self.user_id, limit=10) or []
            
            if not self.sessions_list:
                return
            
            self.sessions_list.controls.clear()
            
            if not sessions:
                self.sessions_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("No previous sessions", size=14, color="grey", italic=True),
                            ft.Text("Complete a practice to see it here.", size=11, color="grey")
                        ], spacing=4),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
                self.sessions_list.update()
                return
            
            session_cards = []
            for session in sessions:
                question_text = session.get('question_text', 'Unknown question')
                score = session.get('evaluation_score')
                session_date = session.get('session_date')
                
                # Format date
                date_str = "Unknown date"
                if session_date:
                    if isinstance(session_date, str):
                        try:
                            dt = datetime.fromisoformat(session_date.replace('Z', '+00:00'))
                            date_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            date_str = session_date[:16]
                    elif isinstance(session_date, datetime):
                        date_str = session_date.strftime("%Y-%m-%d %H:%M")
                
                # Score display
                score_text = ""
                if score is not None:
                    score_color = ft.Colors.GREEN if score >= 70 else ft.Colors.ORANGE if score >= 50 else ft.Colors.RED
                    score_text = ft.Text(
                        f"Score: {score}/100",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=score_color
                    )
                else:
                    score_text = ft.Text("Not evaluated", size=12, color="grey", italic=True)
                
                card = ft.Container(
                    content=ft.Column([
                        ft.Text(
                            question_text[:60] + ('...' if len(question_text) > 60 else ''),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            max_lines=2
                        ),
                        ft.Text(date_str, size=10, color="grey"),
                        score_text,
                        ft.ElevatedButton(
                            "View Details",
                            icon=ft.Icons.VISIBILITY,
                            on_click=lambda e, sid=session['session_id']: self._view_session_details(sid),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.PRIMARY,
                                color=ft.Colors.WHITE
                            ),
                            height=30
                        )
                    ], spacing=5, tight=True),
                    padding=10,
                    bgcolor=ft.Colors.SURFACE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    width=320
                )
                session_cards.append(card)
            
            self.sessions_list.controls.extend(session_cards)
            self.sessions_list.update()
            
        except Exception as ex:
            print(f"[ERROR] Error loading previous sessions: {ex}")
            import traceback
            traceback.print_exc()
    
    def _view_session_details(self, session_id: int):
        """View session details in a dialog"""
        try:
            session = PracticeService.get_session_by_id(session_id)
            if not session:
                self._show_error("Session not found")
                return
            
            question_text = session.get('question_text', 'Unknown')
            response_text = session.get('response_text', 'No response')
            score = session.get('evaluation_score')
            feedback_str = session.get('evaluation_feedback', '{}')
            
            # Parse feedback
            try:
                if isinstance(feedback_str, str):
                    feedback = json.loads(feedback_str)
                else:
                    feedback = feedback_str or {}
            except:
                feedback = {}
            
            # Build dialog content
            content_items = [
                ft.Text("Session Details", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Question:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(question_text, size=12),
                ft.Divider(),
                ft.Text("Your Response:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(response_text, size=12),
                ft.Divider()
            ]
            
            if score is not None:
                score_color = ft.Colors.GREEN if score >= 70 else ft.Colors.ORANGE if score >= 50 else ft.Colors.RED
                content_items.append(
                    ft.Text(f"Score: {score}/100", size=18, weight=ft.FontWeight.BOLD, color=score_color)
                )
            
            if feedback:
                if feedback.get('strengths'):
                    content_items.extend([
                        ft.Divider(),
                        ft.Text("Strengths:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                        ft.Column([ft.Text(f"• {s}", size=12) for s in feedback.get('strengths', [])[:5]], spacing=3)
                    ])
                
                if feedback.get('weaknesses'):
                    content_items.extend([
                        ft.Divider(),
                        ft.Text("Weaknesses:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                        ft.Column([ft.Text(f"• {w}", size=12) for w in feedback.get('weaknesses', [])[:5]], spacing=3)
                    ])
                
                if feedback.get('suggestions'):
                    content_items.extend([
                        ft.Divider(),
                        ft.Text("Suggestions:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                        ft.Column([ft.Text(f"• {s}", size=12) for s in feedback.get('suggestions', [])[:5]], spacing=3)
                    ])
            
            dialog = ft.AlertDialog(
                title=ft.Text("Practice Session Details"),
                content=ft.Container(
                    content=ft.Column(content_items, spacing=10, scroll=ft.ScrollMode.AUTO),
                    width=500,
                    height=500
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))
                ],
                modal=True
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"[ERROR] Error viewing session details: {ex}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Error: {str(ex)}")
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()
    
    def _show_error(self, message: str):
        """Show error message"""
        dialog = ft.AlertDialog(
            title=ft.Text("Error"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: self._close_dialog(dialog))
            ],
            modal=True
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

