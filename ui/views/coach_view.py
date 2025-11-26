"""Career Coach view - AI-powered career guidance"""

import flet as ft
import re
from ui.styles.theme import AppTheme
from ui.components.file_uploader import FileUploadComponent
from services.coach_service import CoachService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from core.auth import SessionManager

class CoachView:
    """Career Coach view with chat interface"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.current_session_id = None
        self.chat_messages = []
        
        # Initialize file uploaders (for attachment feature in chat)
        # These will be initialized in build() method to ensure page is available
        self.resume_uploader = None
        self.jd_uploader = None
        
        # Messages container - created once and reused
        self.messages_container = None
        self._should_load_messages = False
        
    def build(self) -> ft.Container:
        """Build coach view"""
        # Initialize file uploaders (need page reference)
        if not self.resume_uploader:
            self.resume_uploader = FileUploadComponent(
                label="Upload Resume",
                allowed_extensions=['.pdf', '.docx', '.txt'],
                on_file_selected=self._on_resume_uploaded,
                help_text="PDF, DOCX, or TXT"
            )
            self.resume_uploader.build(page=self.page)
        
        if not self.jd_uploader:
            self.jd_uploader = FileUploadComponent(
                label="Upload Job Description",
                allowed_extensions=['.pdf', '.docx', '.txt'],
                on_file_selected=self._on_jd_uploaded,
                help_text="PDF, DOCX, or TXT"
            )
            self.jd_uploader.build(page=self.page)
        
        # Load previous session if exists (for persistence)
        if not self.current_session_id:
            self._load_latest_session()
        
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("🧠 AI Career Coach", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Get personalized career advice and guidance",
                       size=14, color="grey")
            ], spacing=8),
            padding=AppTheme.PADDING_MEDIUM
        )
        
        # Quick advice buttons
        quick_advice_buttons = ft.Row([
            ft.ElevatedButton(
                "Resume Advice",
                icon=ft.Icons.DESCRIPTION,
                on_click=lambda _: self._get_quick_advice("resume")
            ),
            ft.ElevatedButton(
                "Interview Tips",
                icon=ft.Icons.PSYCHOLOGY,
                on_click=lambda _: self._get_quick_advice("interview")
            ),
            ft.ElevatedButton(
                "Job Search Strategy",
                icon=ft.Icons.SEARCH,
                on_click=lambda _: self._get_quick_advice("job_search")
            ),
            ft.ElevatedButton(
                "Skills Plan",
                icon=ft.Icons.SCHOOL,
                on_click=lambda _: self._get_quick_advice("skills")
            ),
        ], wrap=True, spacing=8)
        
        # Chat messages container - use ListView for proper scrolling
        # Reuse existing container if it exists (for persistence)
        if self.messages_container is None:
            self.messages_container = ft.ListView(
                spacing=10,
                padding=10,
                expand=True,
                auto_scroll=True
            )
        
        # Load conversation history if session exists
        if self.current_session_id:
            # Delay loading until after UI is built
            self._should_load_messages = True
        
        # Message input
        self.message_input = ft.TextField(
            label="Type your message...",
            hint_text="Start a session first to begin chatting",
            multiline=True,
            min_lines=1,
            max_lines=3,
            expand=True,
            on_submit=self._send_message,
            disabled=True  # Disabled until session starts
        )
        
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            icon_color=AppTheme.PRIMARY,
            on_click=self._send_message,
            disabled=True  # Disabled until session starts
        )
        
        # Attachment button for file uploads
        self.attach_button = ft.PopupMenuButton(
            icon=ft.Icons.ATTACH_FILE,
            tooltip="Attach file",
            disabled=True,  # Disabled until session starts
            items=[
                ft.PopupMenuItem(
                    text="Upload Resume",
                    icon=ft.Icons.DESCRIPTION,
                    on_click=lambda _: self._show_resume_upload()
                ),
                ft.PopupMenuItem(
                    text="Upload Job Description",
                    icon=ft.Icons.WORK,
                    on_click=lambda _: self._show_jd_upload()
                )
            ]
        )
        
        input_row = ft.Row([
            self.attach_button,
            self.message_input,
            self.send_button
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Chat section
        chat_section = ft.Container(
            content=ft.Column([
                self.messages_container,
                ft.Divider(),
                input_row
            ], spacing=10, expand=True),
            **AppTheme.card_style(),
            expand=True
        )
        
        # Start session button
        self.start_button = ft.ElevatedButton(
            "Start New Coaching Session",
            icon=ft.Icons.CHAT,
            on_click=self._start_session,
            style=ft.ButtonStyle(bgcolor=AppTheme.PRIMARY, color="white")
        )
        
        # End session button (hidden initially)
        self.end_button = ft.ElevatedButton(
            "End Session",
            icon=ft.Icons.CLOSE,
            on_click=self._end_session,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color="white"),
            visible=False
        )
        
        # Previous sessions section
        self.previous_sessions_container = ft.Container(
            content=ft.Column([
                ft.Text("Previous Sessions", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("No previous sessions", size=12, color="grey", italic=True)
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            visible=True
        )
        
        # Load previous sessions
        self._load_previous_sessions()
        
        # Main content
        content = ft.Column([
            header,
            ft.Text("Quick Advice:", size=16, weight=ft.FontWeight.BOLD),
            quick_advice_buttons,
            ft.Divider(),
            ft.Row([
                ft.Text("Coaching Session", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.end_button,
                self.start_button
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                chat_section,
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=self.previous_sessions_container,
                    width=300,
                    padding=10
                )
            ], spacing=10, expand=True)
        ], spacing=16, expand=True)
        
        container = ft.Container(
            content=content,
            padding=AppTheme.PADDING_MEDIUM,
            expand=True
        )
        
        # Load messages after UI is built (if session exists)
        if hasattr(self, '_should_load_messages') and self._should_load_messages:
            self._load_conversation_history()
            self._should_load_messages = False
        
        return container
    
    def _start_session(self, e):
        """Start a new coaching session"""
        # Disable button during creation
        self.start_button.disabled = True
        self.start_button.text = "Starting session..."
        self.page.update()
        
        result = CoachService.create_session(self.user_id)
        
        if "error" not in result:
            self.current_session_id = result['session_id']
            self.chat_messages.clear()
            self.messages_container.controls.clear()
            
            # Enable message input, send button, and attach button
            self.message_input.disabled = False
            self.message_input.hint_text = "Type your message..."
            self.send_button.disabled = False
            self.attach_button.disabled = False
            
            # Add greeting
            self._add_message("assistant", result['greeting'])
            
            self.start_button.disabled = True
            self.start_button.text = "Session Active"
            self.end_button.visible = True
            
            # Reload previous sessions to show new session
            self._load_previous_sessions()
            
            self.page.update()
        else:
            self.start_button.disabled = False
            self.start_button.text = "Start New Coaching Session"
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] {result['error']}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _send_message(self, e):
        """Send user message"""
        # Check if input is disabled
        if self.message_input.disabled:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("[WARNING] Please start a session first"),
                bgcolor=ft.Colors.ORANGE
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        message = self.message_input.value
        
        if not message or not message.strip():
            return
        
        if not self.current_session_id:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("[WARNING] Please start a session first"),
                bgcolor=ft.Colors.ORANGE
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Disable input while sending
        self.message_input.disabled = True
        self.send_button.disabled = True
        self.attach_button.disabled = True
        self.page.update()
        
        # Add user message to UI
        self._add_message("user", message)
        message_text = message  # Store before clearing
        self.message_input.value = ""
        
        # Show loading
        loading_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16),
                ft.Text("Thinking...", size=12, color="grey", italic=True)
            ], spacing=8),
            padding=10
        )
        self.messages_container.controls.append(loading_indicator)
        self.page.update()
        
        try:
        # Send to coach
            result = CoachService.chat(self.user_id, self.current_session_id, message_text)
            
            # Remove loading
            if loading_indicator in self.messages_container.controls:
                self.messages_container.controls.remove(loading_indicator)
            
            if result and "error" not in result:
                self._add_message("assistant", result.get('response', 'No response received'))
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response from service'
                self._add_message("assistant", f"Sorry, I encountered an error: {error_msg}")
                print(f"[ERROR] Chat error: {error_msg}")
        except Exception as ex:
            # Remove loading on error
            if loading_indicator in self.messages_container.controls:
                self.messages_container.controls.remove(loading_indicator)
            
            error_msg = f"Error sending message: {str(ex)}"
            self._add_message("assistant", f"Sorry, I encountered an error: {error_msg}")
            print(f"[ERROR] Exception in _send_message: {ex}")
            import traceback
            traceback.print_exc()
        finally:
            # Re-enable input
            self.message_input.disabled = False
            self.send_button.disabled = False
            self.attach_button.disabled = False
            self.page.update()
    
    def _parse_markdown(self, text: str):
        """Parse markdown text and convert to Flet Text with spans
        
        Supports:
        - **bold** -> bold text
        - Numbered lists (1., 2., etc.) - formatted as text
        - Bullet points (-, *, •) - formatted as text
        
        Returns a single Text component with all spans to avoid nested structures
        """
        if not text:
            return ft.Text("", size=14, selectable=True)
        
        lines = text.split('\n')
        all_spans = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Add newline span
                all_spans.append(ft.TextSpan("\n", ft.TextStyle(size=14)))
                continue
            
            # Check for numbered list (e.g., "4. **Emphasize soft skills**")
            num_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if num_match:
                number = num_match.group(1)
                content = num_match.group(2)
                
                # Add numbered prefix in bold
                all_spans.append(ft.TextSpan(f"{number}. ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=AppTheme.PRIMARY)))
                
                # Parse bold text in the content
                if '**' in content:
                    parts = re.split(r'(\*\*.+?\*\*)', content)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**'):
                            bold_text = part[2:-2]
                            all_spans.append(ft.TextSpan(bold_text, ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)))
                        elif part:
                            all_spans.append(ft.TextSpan(part, ft.TextStyle(size=14)))
                else:
                    all_spans.append(ft.TextSpan(content, ft.TextStyle(size=14)))
            
            # Check for bullet points
            elif re.match(r'^[-•*]\s+(.+)$', line):
                bullet_text = re.sub(r'^[-•*]\s+', '', line)
                
                # Add bullet prefix in bold
                all_spans.append(ft.TextSpan("• ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=AppTheme.PRIMARY)))
                
                # Parse bold in bullet text
                if '**' in bullet_text:
                    parts = re.split(r'(\*\*.+?\*\*)', bullet_text)
                    for part in parts:
                        if part.startswith('**') and part.endswith('**'):
                            bold_text = part[2:-2]
                            all_spans.append(ft.TextSpan(bold_text, ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)))
                        elif part:
                            all_spans.append(ft.TextSpan(part, ft.TextStyle(size=14)))
                else:
                    all_spans.append(ft.TextSpan(bullet_text, ft.TextStyle(size=14)))
            
            # Regular text with potential bold markers
            elif '**' in line:
                # Build spans for bold text
                parts = re.split(r'(\*\*.+?\*\*)', line)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        bold_text = part[2:-2]
                        all_spans.append(ft.TextSpan(bold_text, ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)))
                    elif part:
                        all_spans.append(ft.TextSpan(part, ft.TextStyle(size=14)))
            else:
                all_spans.append(ft.TextSpan(line, ft.TextStyle(size=14)))
            
            # Add newline after each line (except last)
            if i < len(lines) - 1:
                all_spans.append(ft.TextSpan("\n", ft.TextStyle(size=14)))
        
        # Return single Text component with all spans
        if all_spans:
            return ft.Text(spans=all_spans, size=14, selectable=True)
        else:
            return ft.Text("", size=14, selectable=True)
    
    def _add_message(self, role: str, content: str, update_page: bool = True):
        """Add message to chat with markdown support"""
        is_user = role == "user"
        
        # Parse markdown for assistant messages, plain text for user
        if is_user:
            message_content = ft.Text(content, size=14, selectable=True)
        else:
            message_content = self._parse_markdown(content)
        
        # Always use a simple Column structure (message_content is now always a single Text component)
        message_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "You" if is_user else "Career Coach",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.PRIMARY if is_user else AppTheme.SECONDARY
                ),
                message_content
            ], spacing=4),
            bgcolor=AppTheme.SURFACE_LIGHT if is_user else "#E3F2FD",
            padding=12,
            border_radius=AppTheme.RADIUS_MEDIUM,
            alignment=ft.alignment.center_left if not is_user else ft.alignment.center_right
        )
        
        self.messages_container.controls.append(message_container)
        if update_page:
            self.page.update()
    
    def _get_quick_advice(self, advice_type: str):
        """Get quick advice"""
        print(f"[DEBUG] Quick advice requested: {advice_type}")
        
        # Check if session exists, if not create one
        if not self.current_session_id:
            # Auto-start a session for quick advice
            result = CoachService.create_session(self.user_id)
            if "error" not in result:
                self.current_session_id = result['session_id']
                self.chat_messages.clear()
                if self.messages_container:
                    self.messages_container.controls.clear()
                
                # Enable message input, send button, and attach button
                if self.message_input:
                    self.message_input.disabled = False
                    self.message_input.hint_text = "Type your message..."
                if self.send_button:
                    self.send_button.disabled = False
                if self.attach_button:
                    self.attach_button.disabled = False
                if self.start_button:
                    self.start_button.disabled = True
                    self.start_button.text = "Session Active"
                if self.end_button:
                    self.end_button.visible = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"[ERROR] Failed to start session: {result.get('error', 'Unknown error')}"),
                    bgcolor=ft.Colors.RED,
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
        
        # Show loading indicator in chat
        loading_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16),
                ft.Text("Generating advice...", size=12, color="grey", italic=True)
            ], spacing=8),
            padding=10
        )
        if self.messages_container:
            self.messages_container.controls.append(loading_indicator)
            self.page.update()
        
        try:
            # Get advice
            result = CoachService.get_quick_advice(self.user_id, advice_type)
            
            # Remove loading indicator
            if loading_indicator in self.messages_container.controls:
                self.messages_container.controls.remove(loading_indicator)
            
            if not result or "error" in result:
                error_msg = result.get('error', 'Unknown error') if result else 'No response from service'
                self._add_message("assistant", f"Sorry, I encountered an error: {error_msg}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"[ERROR] {error_msg}"),
                    bgcolor=ft.Colors.RED,
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
                print(f"[ERROR] Quick advice error: {error_msg}")
                return
            
            # Get advice text
            advice_text = result.get('advice', 'No advice generated')
            if not advice_text or len(advice_text.strip()) == 0:
                self._add_message("assistant", "Sorry, I couldn't generate advice. Please try again.")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("[ERROR] Empty response from AI"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Format advice type for display
            advice_title_map = {
                "resume": "Resume Advice",
                "interview": "Interview Tips",
                "job_search": "Job Search Strategy",
                "skills": "Skills Development Plan"
            }
            title = advice_title_map.get(advice_type, f"{advice_type.replace('_', ' ').title()} Advice")
            
            # Add title and advice to chat
            title_message = f"📋 **{title}**\n\n{advice_text}"
            self._add_message("assistant", title_message)
            
            # Show success snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ {title} generated successfully!"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            # Remove loading on error
            if loading_indicator in self.messages_container.controls:
                self.messages_container.controls.remove(loading_indicator)
            
            error_msg = f"Error getting advice: {str(ex)}"
            self._add_message("assistant", f"Sorry, I encountered an error: {error_msg}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] {error_msg}"),
                bgcolor=ft.Colors.RED,
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()
            print(f"[ERROR] Exception in _get_quick_advice: {ex}")
            import traceback
            traceback.print_exc()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()
        
    def _load_latest_session(self):
        """Load the most recent active session if available"""
        try:
            conversations = CoachService.get_conversations(self.user_id, limit=1)
            if conversations:
                latest = conversations[0]
                session_id = latest.get('conversation_id')
                if session_id:
                    self.current_session_id = session_id
                    # Load messages when view is built
                    self._should_load_messages = True
                    print(f"[DEBUG] Loaded latest session: {session_id}")
        except Exception as e:
            print(f"[DEBUG] No previous session found: {e}")
    
    def _load_conversation_history(self):
        """Load and display conversation history for current session"""
        if not self.current_session_id:
            return
        
        try:
            # Get messages from database
            messages = CoachService.get_messages(self.current_session_id)
            
            if messages and len(messages) > 0:
                # Clear current messages container
                if self.messages_container:
                    self.messages_container.controls.clear()
                
                # Add all messages to UI
                for msg in messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if content:  # Skip empty messages
                        self._add_message(role, content, update_page=False)
                
                # Update page once after loading all messages
                self.page.update()
                
                # Update UI state
                if self.message_input:
                    self.message_input.disabled = False
                    self.message_input.hint_text = "Type your message..."
                if self.send_button:
                    self.send_button.disabled = False
                if self.attach_button:
                    self.attach_button.disabled = False
                if self.start_button:
                    self.start_button.disabled = True
                    self.start_button.text = "Session Active"
                if self.end_button:
                    self.end_button.visible = True
        except Exception as e:
            print(f"[ERROR] Error loading conversation history: {e}")
            import traceback
            traceback.print_exc()
    
    def _end_session(self, e):
        """End the current coaching session"""
        try:
            # Clear session
            self.current_session_id = None
            self.chat_messages.clear()
            
            # Clear messages container
            if self.messages_container:
                self.messages_container.controls.clear()
            
            # Disable inputs
            if self.message_input:
                self.message_input.disabled = True
                self.message_input.hint_text = "Start a session first to begin chatting"
                self.message_input.value = ""
            if self.send_button:
                self.send_button.disabled = True
            if self.attach_button:
                self.attach_button.disabled = True
            
            # Update buttons
            if self.start_button:
                self.start_button.disabled = False
                self.start_button.text = "Start New Coaching Session"
            if self.end_button:
                self.end_button.visible = False
            
            # Reload previous sessions to update active indicator
            self._load_previous_sessions()
            
            # Show confirmation
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Session ended. Start a new session to continue chatting."),
                bgcolor=ft.Colors.BLUE_GREY,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            print(f"[DEBUG] Session ended")
        except Exception as ex:
            print(f"[ERROR] Error ending session: {ex}")
            import traceback
            traceback.print_exc()
    
    def _load_previous_sessions(self):
        """Load and display previous chat sessions"""
        try:
            conversations = CoachService.get_conversations(self.user_id, limit=10)
            
            if not conversations:
                self.previous_sessions_container.content = ft.Column([
                    ft.Text("Previous Sessions", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("No previous sessions yet", size=12, color="grey", italic=True)
                ], spacing=5)
                if hasattr(self, 'page'):
                    try:
                        self.previous_sessions_container.update()
                    except:
                        pass
                return
            
            session_cards = []
            for conv in conversations:
                conversation_id = conv.get('conversation_id')
                updated_at = conv.get('updated_at')
                
                # Get first message for preview
                messages = CoachService.get_messages(conversation_id)
                preview = "New conversation"
                if messages and len(messages) > 0:
                    first_msg = messages[0].get('content', '')
                    if first_msg:
                        preview = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
                
                # Format date
                date_str = "Recently"
                if updated_at:
                    try:
                        from datetime import datetime
                        if isinstance(updated_at, str):
                            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        else:
                            dt = updated_at
                        date_str = dt.strftime("%b %d, %Y")
                    except:
                        date_str = str(updated_at)[:10] if updated_at else "Recently"
                
                # Create session card
                is_active = (conversation_id == self.current_session_id)
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(
                                f"Session {conversation_id}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=AppTheme.PRIMARY if is_active else ft.Colors.BLACK
                            ),
                            ft.Container(
                                content=ft.Text("Active", size=10, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.GREEN_100,
                                padding=ft.padding.symmetric(4, 8),
                                border_radius=4,
                                visible=is_active
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(preview, size=11, color="grey", max_lines=2),
                        ft.Text(date_str, size=10, color="grey", italic=True)
                    ], spacing=4, tight=True),
                    padding=10,
                    border=ft.border.all(1, AppTheme.PRIMARY if is_active else ft.Colors.OUTLINE),
                    border_radius=6,
                    bgcolor=ft.Colors.BLUE_50 if is_active else ft.Colors.WHITE,
                    on_click=lambda e, cid=conversation_id: self._load_session(cid),
                    ink=True
                )
                session_cards.append(card)
            
            self.previous_sessions_container.content = ft.Column([
                ft.Text("Previous Sessions", size=14, weight=ft.FontWeight.BOLD),
                ft.Column(session_cards, spacing=8, scroll=ft.ScrollMode.AUTO, height=400)
            ], spacing=8)
            
            if hasattr(self, 'page'):
                try:
                    self.previous_sessions_container.update()
                except:
                    pass
                    
        except Exception as e:
            print(f"[ERROR] Error loading previous sessions: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_session(self, conversation_id: int):
        """Load a previous conversation session"""
        try:
            # Set as current session
            self.current_session_id = conversation_id
            
            # Clear current messages
            if self.messages_container:
                self.messages_container.controls.clear()
            
            # Load messages
            messages = CoachService.get_messages(conversation_id)
            
            if messages and len(messages) > 0:
                # Add all messages to UI
                for msg in messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if content:
                        self._add_message(role, content, update_page=False)
                
                # Update page once
                self.page.update()
            
            # Update UI state
            if self.message_input:
                self.message_input.disabled = False
                self.message_input.hint_text = "Type your message..."
            if self.send_button:
                self.send_button.disabled = False
            if self.attach_button:
                self.attach_button.disabled = False
            if self.start_button:
                self.start_button.disabled = True
                self.start_button.text = "Session Active"
            if self.end_button:
                self.end_button.visible = True
            
            # Reload previous sessions to update active indicator
            self._load_previous_sessions()
            
            # Show confirmation
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Loaded session from {len(messages)} messages"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"[ERROR] Error loading session: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] Failed to load session: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _show_resume_upload(self):
        """Show resume upload file picker - no file type filter"""
        if self.resume_uploader and self.resume_uploader.file_picker:
            self.resume_uploader.file_picker.pick_files(
                file_type=ft.FilePickerFileType.ANY
            )
    
    def _show_jd_upload(self):
        """Show job description upload file picker - no file type filter"""
        if self.jd_uploader and self.jd_uploader.file_picker:
            self.jd_uploader.file_picker.pick_files(
                file_type=ft.FilePickerFileType.ANY
            )
    
    def _on_resume_uploaded(self, file_path: str, file_name: str):
        """Handle resume upload"""
        try:
            print(f"[DEBUG] Resume uploaded: {file_name}")
            
            # Upload resume using ResumeService
            result = ResumeService.upload_resume(
                user_id=self.user_id,
                file_path=file_path,
                resume_name=file_name
            )
            
            if result:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"[OK] Resume '{file_name}' uploaded successfully!"),
                    bgcolor=ft.Colors.GREEN,
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()
                
                # If session is active, let the coach know about the new resume
                if self.current_session_id:
                    self._add_message("assistant", 
                        f"Great! I've received your resume '{file_name}'. I can now provide more personalized advice based on your background.")
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("[ERROR] Failed to upload resume"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"[ERROR] Error uploading resume: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] Error: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _on_jd_uploaded(self, file_path: str, file_name: str):
        """Handle job description upload"""
        try:
            print(f"[DEBUG] JD uploaded: {file_name}")
            
            # Read file content as bytes
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Upload JD using JobDescriptionService
            result = JobDescriptionService.save_jd_from_file(
                user_id=self.user_id,
                file_name=file_name,
                file_content=file_content,
                company_name=None,  # User can specify later if needed
                job_title=None
            )
            
            if result:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"[OK] Job description '{file_name}' uploaded successfully!"),
                    bgcolor=ft.Colors.GREEN,
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()
                
                # If session is active, let the coach know about the new JD
                if self.current_session_id:
                    self._add_message("assistant", 
                        f"Perfect! I've received the job description '{file_name}'. I can now provide advice tailored to this position.")
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("[ERROR] Failed to upload job description"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"[ERROR] Error uploading JD: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] Error: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()

