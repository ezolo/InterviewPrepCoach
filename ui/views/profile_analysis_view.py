"""Profile analysis view - Resume vs JD compatibility"""

import json
import flet as ft
from ui.styles.theme import AppTheme
from ui.components.file_uploader import FileUploadComponent
from ui.components.score_card import ScoreCard
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from services.compatibility_service import CompatibilityService
from core.auth import SessionManager
from datetime import datetime

class ProfileAnalysisView:
    """Profile analysis view"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.resume_file_path = None
        self.resume_id = None
        self.jd_id = None
        self.analysis_result = None
        
        # Initialize file uploaders
        self.resume_uploader = None
        self.jd_uploader = None
        self.jd_text_field = None
        
        # JD info storage
        self.pending_jd_text = None
        self.pending_jd_file_path = None
        self.pending_jd_file_name = None
        
    def build(self) -> ft.Container:
        """Build profile analysis view"""
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("📄 Profile Analysis", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Analyze compatibility between your resume and job description",
                           size=12, color="grey")
                ], spacing=4, expand=True),
            ], spacing=8),
            padding=ft.padding.only(left=20, top=15, bottom=10)
        )
        
        # Resume upload section (compact)
        self.resume_uploader = FileUploadComponent(
            label="📤 Upload Resume",
            allowed_extensions=['.pdf', '.docx', '.txt'],
            on_file_selected=self._on_resume_selected,
            help_text="PDF, DOCX, or TXT"
        )
        
        resume_uploader_ui = self.resume_uploader.build(page=self.page)
        
        # Ensure file picker is in overlay
        resume_file_picker = self.resume_uploader.get_file_picker()
        if resume_file_picker and resume_file_picker not in self.page.overlay:
            self.page.overlay.append(resume_file_picker)
        
        # Resume name input (hidden initially)
        self.resume_name_field = ft.TextField(
            label="Resume Name",
            hint_text="Enter a name for this resume",
            width=250,
            autofocus=False
        )
        
        self.resume_name_save_button = ft.ElevatedButton(
            text="Save Resume",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=lambda e: self._save_resume_with_name(
                self.resume_file_path, 
                self.resume_name_field.value.strip() if self.resume_name_field.value else self.pending_resume_name
            )
        )
        
        self.resume_name_cancel_button = ft.TextButton(
            text="Cancel",
            on_click=lambda e: self._cancel_resume_naming()
        )
        
        self.resume_name_section = ft.Container(
            content=ft.Column([
                ft.Text("Name Your Resume", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Row([
                    self.resume_name_field,
                    self.resume_name_save_button,
                    self.resume_name_cancel_button
                ], spacing=10, wrap=True, expand=True)
            ], spacing=10, tight=False),
            visible=False,
            padding=15,
            margin=ft.margin.only(top=10),
            border=ft.border.all(2, ft.Colors.PRIMARY),
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50
        )
        
        resume_section = ft.Container(
            content=ft.Column([
                ft.Text("Resume", size=14, weight=ft.FontWeight.BOLD),
                resume_uploader_ui,
                self.resume_name_section
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50
        )
        
        # JD input section - Toggle buttons
        self.jd_mode = ft.Ref[ft.RadioGroup]()  # "paste" or "upload"
        self.jd_mode_value = "paste"  # Default to paste
        
        paste_section = self._build_paste_jd_tab()
        upload_section = self._build_upload_jd_tab()
        
        # Toggle buttons for JD input method
        jd_toggle = ft.RadioGroup(
            ref=self.jd_mode,
            content=ft.Row([
                ft.Radio(value="paste", label="📋 Paste JD"),
                ft.Radio(value="upload", label="📤 Upload JD"),
            ], spacing=20),
            value="paste",
            on_change=self._on_jd_mode_change
        )
        
        # JD sections container (show/hide based on toggle)
        self.paste_jd_container = ft.Container(
            content=paste_section,
            visible=True,
            padding=10
        )
        
        self.upload_jd_container = ft.Container(
            content=upload_section,
            visible=False,
            padding=10
        )
        
        # JD company and title input (hidden initially)
        self.jd_company_field = ft.TextField(
            label="Company Name",
            hint_text="Enter company name",
            width=200
        )
        
        self.jd_title_field = ft.TextField(
            label="Job Title",
            hint_text="Enter job title",
            width=200
        )
        
        self.jd_info_save_button = ft.ElevatedButton(
            text="Save JD",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=lambda e: self._save_jd_with_info()
        )
        
        self.jd_info_cancel_button = ft.TextButton(
            text="Cancel",
            on_click=lambda e: self._cancel_jd_info()
        )
        
        self.jd_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Job Details", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                ft.Row([
                    self.jd_company_field,
                    self.jd_title_field,
                    self.jd_info_save_button,
                    self.jd_info_cancel_button
                ], spacing=10, wrap=True, expand=True)
            ], spacing=10, tight=False),
            visible=False,
            padding=15,
            margin=ft.margin.only(top=10),
            border=ft.border.all(2, ft.Colors.PRIMARY),
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50
        )
        
        jd_section = ft.Container(
            content=ft.Column([
                ft.Text("Job Description", size=14, weight=ft.FontWeight.BOLD),
                jd_toggle,
                self.paste_jd_container,
                self.upload_jd_container,
                self.jd_info_section
            ], spacing=8),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50
        )
        
        # Analyze button (compact)
        self.analyze_button = ft.ElevatedButton(
            text="🔍 Analyze",
            icon=ft.Icons.ANALYTICS,
            on_click=self._on_analyze_click,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=AppTheme.PRIMARY,
                color="white",
                padding=10
            )
        )
        
        # Results section (top right) - larger now
        self.results_container = ft.Container(
            visible=False,
            padding=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
        
        # Previous analyses section
        self.previous_analyses_container = ft.Container(
            content=ft.Column([
                ft.Text("Previous Analyses", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("No previous analyses", size=12, color="grey", italic=True)
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            visible=True
        )
        
        # Load previous analyses
        self._load_previous_analyses()
        
        # Left column: Inputs (more compact)
        left_column = ft.Container(
            content=ft.Column([
                resume_section,
                ft.Divider(height=5),
                jd_section,
                ft.Divider(height=5),
                ft.Container(
                    content=self.analyze_button,
                    alignment=ft.alignment.center,
                    padding=5
                ),
                ft.Divider(height=10),
                self.previous_analyses_container
            ], spacing=5, scroll=ft.ScrollMode.AUTO),
            width=350,  # Fixed smaller width for inputs
            padding=10
        )
        
        # Right column: Results (larger)
        right_column = ft.Container(
            content=self.results_container,
            expand=True,
            padding=10
        )
        
        # Main content: Two columns layout
        content = ft.Column([
            header,
            ft.Divider(height=1),
            ft.Row([
                left_column,
                ft.VerticalDivider(width=1),
                right_column
            ], spacing=10, expand=True)
        ], spacing=0, expand=True)
        
        container = ft.Container(
            content=content,
            padding=10,
            expand=True
        )
        
        # Restore analysis results if they exist (for persistence)
        if self.analysis_result:
            self._show_results(self.analysis_result)
        
        return container
    
    def _on_jd_mode_change(self, e):
        """Handle JD input mode toggle"""
        mode = e.control.value
        self.jd_mode_value = mode
        
        if mode == "paste":
            self.paste_jd_container.visible = True
            self.upload_jd_container.visible = False
        else:
            self.paste_jd_container.visible = False
            self.upload_jd_container.visible = True
        
        self.page.update()
    
    def _load_previous_analyses(self):
        """Load and display previous analyses"""
        try:
            analyses = CompatibilityService.get_recent_analyses(self.user_id, limit=5)
            
            if not analyses:
                self.previous_analyses_container.content = ft.Column([
                    ft.Text("Previous Analyses", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("No previous analyses yet", size=12, color="grey", italic=True)
                ], spacing=5)
                return
            
            analysis_cards = []
            for analysis in analyses:
                score = analysis.get('compatibility_score') or 0
                if score is None:
                    score = 0
                
                # Get resume name - the query returns it as 'resume_name' from r.file_name
                resume_name = analysis.get('resume_name')
                
                # Handle None, empty string, or string 'None'
                if not resume_name or resume_name == 'None' or (isinstance(resume_name, str) and resume_name.strip() == ''):
                    resume_name = 'Unknown Resume'
                
                # Debug logging to see what we're getting
                print(f"[DEBUG] Analysis {analysis.get('analysis_id')}: resume_name='{resume_name}' (type: {type(resume_name)}), company='{analysis.get('company_name')}'")
                
                job_title = analysis.get('job_title')
                if not job_title or job_title == 'None' or job_title == '':
                    job_title = 'Job Position'
                
                company = analysis.get('company_name')
                # Only use company if it's a valid non-empty string
                if not company or company == 'None' or company == '':
                    company = None  # Don't show company if it's missing
                
                analyzed_at = analysis.get('analyzed_at')
                analysis_id = analysis.get('analysis_id')
                
                # Format date
                date_str = "Recently"
                if analyzed_at:
                    try:
                        if isinstance(analyzed_at, str):
                            dt = datetime.fromisoformat(analyzed_at.replace('Z', '+00:00'))
                        else:
                            dt = analyzed_at
                        date_str = dt.strftime("%b %d, %Y")
                    except:
                        date_str = "Recently"
                
                # Skip if no valid analysis_id
                if not analysis_id:
                    continue
                
                # Build card content - conditionally show company
                card_content_items = []
                
                # Header row with company (if available) or job title, and score
                if company:
                    header_row = ft.Row([
                        ft.Text(company, size=12, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Container(
                            content=ft.Text(f"{int(score)}%", size=14, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.GREEN_100 if score >= 70 else ft.Colors.ORANGE_100 if score >= 50 else ft.Colors.RED_100,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4
                        )
                    ])
                else:
                    # No company, show job title in header instead
                    header_row = ft.Row([
                        ft.Text(job_title, size=12, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Container(
                            content=ft.Text(f"{int(score)}%", size=14, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.GREEN_100 if score >= 70 else ft.Colors.ORANGE_100 if score >= 50 else ft.Colors.RED_100,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4
                        )
                    ])
                
                card_content_items.append(header_row)
                
                # Show job title only if we showed company in header
                if company:
                    card_content_items.append(ft.Text(job_title, size=11, color="grey600"))
                
                # Always show resume name
                card_content_items.append(ft.Text(f"Resume: {resume_name}", size=11, color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_500))
                
                # Date
                card_content_items.append(ft.Text(date_str, size=10, color="grey", italic=True))
                
                # Create card
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(card_content_items, spacing=4, tight=True),
                        padding=10,
                        on_click=lambda e, aid=analysis_id: self._view_previous_analysis(aid)
                    ),
                    elevation=1
                )
                analysis_cards.append(card)
            
            if not analysis_cards:
                # No valid cards, show empty message
                self.previous_analyses_container.content = ft.Column([
                    ft.Text("Previous Analyses", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("No previous analyses yet", size=12, color="grey", italic=True)
                ], spacing=5)
            else:
                # Limit height to prevent overflow
                cards_column = ft.Column(
                    analysis_cards, 
                    spacing=5, 
                    scroll=ft.ScrollMode.AUTO,
                    height=200  # Fixed height for scrollable area
                )
                
                self.previous_analyses_container.content = ft.Column([
                    ft.Text("Previous Analyses", size=14, weight=ft.FontWeight.BOLD),
                    cards_column
                ], spacing=8)
            
            # Only update if container is already on page
            try:
                self.previous_analyses_container.update()
            except:
                # Container not on page yet, will update when page loads
                pass
        except Exception as e:
            print(f"[ERROR] Error loading previous analyses: {e}")
            import traceback
            traceback.print_exc()
            self.previous_analyses_container.content = ft.Column([
                ft.Text("Previous Analyses", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("Error loading analyses", size=12, color="red", italic=True)
            ], spacing=5)
    
    def _view_previous_analysis(self, analysis_id: int):
        """Load and display a previous analysis"""
        try:
            print(f"[INFO] Loading previous analysis ID: {analysis_id}")
            analysis = CompatibilityService.get_analysis_by_id(analysis_id, self.user_id)
            
            if not analysis:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Analysis not found"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Convert to format expected by _show_results
            result = {
                'compatibility_score': analysis.get('compatibility_score', 0),
                'matched_skills': analysis.get('matched_skills', []),
                'missing_skills': analysis.get('missing_skills', []),
                'missing_qualifications': analysis.get('missing_qualifications', []),
                'strengths': [],  # Not stored in DB, but we can try to extract
                'suggestions': analysis.get('suggestions', []),
                'analysis_id': analysis_id
            }
            
            # Show results
            self._show_results(result)
            
            # Show info message
            resume_name = analysis.get('resume_name') or 'Unknown'
            if resume_name == 'None' or resume_name is None:
                resume_name = 'Unknown'
            
            job_title = analysis.get('job_title') or 'Unknown'
            if job_title == 'None' or job_title is None:
                job_title = 'Unknown'
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Loaded: {resume_name} vs {job_title}"), 
                bgcolor=ft.Colors.GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            print(f"[ERROR] Error viewing previous analysis: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error loading analysis: {str(e)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _build_paste_jd_tab(self) -> ft.Container:
        """Build paste JD tab content"""
        self.jd_text_field = ft.TextField(
            label="Paste job description here",
            hint_text="Copy and paste the full job description text...",
            multiline=True,
            min_lines=4,
            max_lines=6,
            on_change=self._on_jd_input_change,
            border_color=ft.Colors.PRIMARY,
            expand=True
        )
        
        return ft.Column([
            self.jd_text_field,
        ], spacing=3, expand=True)
    
    def _build_upload_jd_tab(self) -> ft.Container:
        """Build upload JD tab content"""
        self.jd_uploader = FileUploadComponent(
            label="📤 Upload Job Description File",
            allowed_extensions=['.pdf', '.docx', '.txt'],
            on_file_selected=self._on_jd_file_selected,
            help_text="PDF, DOCX, or TXT"
        )
        
        # Build the uploader UI (this creates and adds file picker to overlay)
        jd_uploader_ui = self.jd_uploader.build(page=self.page)
        
        # Ensure file picker is in overlay (double-check)
        jd_file_picker = self.jd_uploader.get_file_picker()
        if jd_file_picker:
            if jd_file_picker not in self.page.overlay:
                self.page.overlay.append(jd_file_picker)
                self.page.update()
            print(f"[DEBUG] JD file picker ready: {jd_file_picker is not None}")
        
        return ft.Column([
            jd_uploader_ui,
        ], spacing=5, expand=True)
    
    def _on_resume_selected(self, file_path: str, file_name: str):
        """Handle resume file selection"""
        print(f"[INFO] Resume selected: {file_name}")
        
        try:
            # Store file info for later use
            self.resume_file_path = file_path
            # Remove extension for default name
            default_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            self.pending_resume_name = default_name
            
            # Show inline name input instead of dialog
            self.resume_name_field.value = default_name
            self.resume_name_section.visible = True
            
            print(f"[DEBUG] Showing resume name input for: {default_name}, section visible: {self.resume_name_section.visible}")
            self.page.update()
            print(f"[DEBUG] After update, section visible: {self.resume_name_section.visible}")
        except Exception as e:
            print(f"[ERROR] Error in _on_resume_selected: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: save with default name
            self._save_resume_with_name(file_path, file_name.rsplit('.', 1)[0] if '.' in file_name else file_name)
    
    def _cancel_resume_naming(self):
        """Cancel resume naming and hide the input"""
        self.resume_name_section.visible = False
        self.resume_file_path = None
        self.pending_resume_name = None
        self.resume_name_field.value = ""
        self.page.update()
    
    
    def _save_resume_with_name(self, file_path: str, resume_name: str):
        """Save resume with the given name"""
        if not resume_name or not resume_name.strip():
            resume_name = self.pending_resume_name or "Resume"
        
        print(f"[INFO] Saving resume with name: {resume_name}")
        
        # Hide the name input section
        self.resume_name_section.visible = False
        self.resume_name_field.value = ""
        
        # Save resume using the file path and custom name
        self.resume_id = ResumeService.upload_resume(self.user_id, file_path, resume_name=resume_name.strip())
        
        if self.resume_id:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[OK] Resume '{resume_name}' uploaded successfully!"), 
                bgcolor=ft.Colors.GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()
            self._check_ready_to_analyze()
            # Reload previous analyses to show updated resume names
            self._load_previous_analyses()
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("[ERROR] Error uploading resume. Please try again."), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _on_jd_input_change(self, e):
        """Handle JD text input change"""
        jd_text = self.jd_text_field.value.strip() if self.jd_text_field.value else ""
        
        if len(jd_text) > 100:
            print(f"[INFO] JD text entered (length: {len(jd_text)})")
            # Store the text and show company/job title input
            self.pending_jd_text = jd_text
            self.jd_info_section.visible = True
            self.page.update()
        elif len(jd_text) > 0:
            # Text entered but too short
            self.jd_text_field.suffix_icon = None
            self.jd_text_field.update()
    
    def _on_jd_file_selected(self, file_path: str, file_name: str):
        """Handle JD file selection"""
        print(f"[INFO] JD file selected: {file_name}, path: {file_path}")
        
        try:
            # Store file info and show company/job title input
            self.pending_jd_file_path = file_path
            self.pending_jd_file_name = file_name
            
            # Try to extract company/job title from filename as hints
            filename_base = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            # Common pattern: "Company_JobTitle" or "Company - JobTitle"
            if '_' in filename_base:
                parts = filename_base.split('_', 1)
                if len(parts) == 2:
                    self.jd_company_field.value = parts[0].replace('_', ' ')
                    self.jd_title_field.value = parts[1].replace('_', ' ')
            elif ' - ' in filename_base:
                parts = filename_base.split(' - ', 1)
                if len(parts) == 2:
                    self.jd_company_field.value = parts[0]
                    self.jd_title_field.value = parts[1]
            
            # Show the info input section
            self.jd_info_section.visible = True
            self.page.update()
        except Exception as e:
            print(f"[ERROR] Error processing JD file: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] Error: {str(e)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _save_jd_with_info(self):
        """Save JD with company name and job title"""
        company_name = self.jd_company_field.value.strip() if self.jd_company_field.value else None
        job_title = self.jd_title_field.value.strip() if self.jd_title_field.value else None
        
        if not company_name or company_name == '':
            company_name = None
        if not job_title or job_title == '':
            job_title = None
        
        print(f"[INFO] Saving JD with company='{company_name}', title='{job_title}'")
        
        # Hide the info section
        self.jd_info_section.visible = False
        self.page.update()
        
        try:
            # Save based on whether we have text or file
            if self.pending_jd_text:
                # Save from pasted text
                self.jd_id = JobDescriptionService.save_jd_from_text(
                    self.user_id,
                    self.pending_jd_text,
                    company_name=company_name,
                    job_title=job_title
                )
            elif self.pending_jd_file_path:
                # Save from uploaded file
                with open(self.pending_jd_file_path, 'rb') as f:
                    file_content = f.read()
                
                self.jd_id = JobDescriptionService.save_jd_from_file(
                    self.user_id,
                    self.pending_jd_file_name,
                    file_content,
                    company_name=company_name,
                    job_title=job_title
                )
            else:
                raise ValueError("No JD text or file to save")
            
            if self.jd_id:
                print(f"[INFO] JD saved successfully with ID: {self.jd_id}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"[OK] Job description saved successfully!"), 
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()
                self._check_ready_to_analyze()
                
                # Clear pending data
                self.pending_jd_text = None
                self.pending_jd_file_path = None
                self.pending_jd_file_name = None
                self.jd_company_field.value = ""
                self.jd_title_field.value = ""
            else:
                print("[ERROR] JD save returned None")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("[ERROR] Error saving job description. Please try again."), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"[ERROR] Error saving JD: {e}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"[ERROR] Error: {str(e)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _cancel_jd_info(self):
        """Cancel JD info input and hide the section"""
        self.jd_info_section.visible = False
        self.pending_jd_text = None
        self.pending_jd_file_path = None
        self.pending_jd_file_name = None
        self.jd_company_field.value = ""
        self.jd_title_field.value = ""
        self.page.update()
    
    def _check_ready_to_analyze(self):
        """Check if ready to analyze"""
        if self.resume_id and self.jd_id:
            self.analyze_button.disabled = False
            self.analyze_button.text = "🔍 Analyze Compatibility"
            self.analyze_button.update()
        else:
            self.analyze_button.disabled = True
            missing = []
            if not self.resume_id:
                missing.append("resume")
            if not self.jd_id:
                missing.append("job description")
            self.analyze_button.text = f"⚠️ Missing: {', '.join(missing)}"
            self.analyze_button.update()
    
    def _on_analyze_click(self, e):
        """Handle analyze button click"""
        print(f"[INFO] Analyze button clicked - resume_id: {self.resume_id}, jd_id: {self.jd_id}")
        
        if not self.resume_id or not self.jd_id:
            print("[WARNING] Missing resume or JD")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Please upload resume and job description first"), 
                bgcolor=ft.Colors.ORANGE
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Show loading
        self.analyze_button.disabled = True
        self.analyze_button.text = "⏳ Analyzing... Please wait"
        self.analyze_button.update()
        self.page.update()
        
        print(f"[INFO] Starting compatibility analysis...")
        
        try:
            # Perform analysis
            result = CompatibilityService.analyze_compatibility(
                self.user_id,
                self.resume_id,
                self.jd_id
            )
            
            print(f"[INFO] Analysis result: {result}")
            
            if result and "error" not in result:
                print("[INFO] Analysis successful, showing results")
                self.analysis_result = result
                self._show_results(result)
                
                # Reload previous analyses to include the new one
                self._load_previous_analyses()
                
                # Show success message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("[OK] Analysis complete!"), 
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Analysis failed'
                print(f"[ERROR] Analysis failed: {error_msg}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error: {error_msg}"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            print(f"[ERROR] Exception during analysis: {ex}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(ex)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
        finally:
            # Reset button - update via page, not directly
            self.analyze_button.text = "🔍 Analyze Compatibility"
            self.analyze_button.disabled = False
            # Don't call update() directly on button - update page instead
            self.page.update()
    
    def _show_results(self, result: dict):
        """Display analysis results"""
        print(f"[DEBUG] _show_results called with result keys: {result.keys()}")
        score = result.get('compatibility_score', 0)
        print(f"[DEBUG] Compatibility score: {score}")
        
        # Score card
        score_card = ScoreCard.build(score, "Compatibility Score")
        
        # Matched skills - ensure we have a list
        matched_skills = result.get('matched_skills', [])
        print(f"[DEBUG] Matched skills type: {type(matched_skills)}, value: {matched_skills}, length: {len(matched_skills) if isinstance(matched_skills, list) else 'N/A'}")
        if not isinstance(matched_skills, list):
            if isinstance(matched_skills, str):
                # Try to parse if it's a JSON string
                try:
                    matched_skills = json.loads(matched_skills)
                except:
                    matched_skills = [matched_skills] if matched_skills else []
            else:
                matched_skills = []
        
        if matched_skills and len(matched_skills) > 0:
            # Simple text-based display - more reliable than chips
            skill_texts = [str(skill).strip() for skill in matched_skills[:20] if str(skill).strip()]
            print(f"[DEBUG] Creating matched_chips with {len(skill_texts)} skills: {skill_texts[:5]}")
            if skill_texts:
                matched_chips = ft.Column(
                    [
                        ft.Text(f"• {skill}", size=12, color=ft.Colors.GREEN_700)
                        for skill in skill_texts
                    ],
                    spacing=3
                )
                print(f"[DEBUG] Matched chips created with {len(matched_chips.controls)} items")
            else:
                matched_chips = ft.Text("No matched skills found", color="grey", italic=True, size=12)
                print("[DEBUG] No skill texts, using fallback text")
        else:
            matched_chips = ft.Text("No matched skills found", color="grey", italic=True, size=12)
            print("[DEBUG] No matched skills list or empty, using fallback text")
        
        # Missing skills - ensure we have a list
        missing_skills = result.get('missing_skills', [])
        print(f"[DEBUG] Missing skills type: {type(missing_skills)}, value: {missing_skills}")
        if not isinstance(missing_skills, list):
            if isinstance(missing_skills, str):
                # Try to parse if it's a JSON string
                try:
                    missing_skills = json.loads(missing_skills)
                except:
                    missing_skills = [missing_skills] if missing_skills else []
            else:
                missing_skills = []
        
        if missing_skills and len(missing_skills) > 0:
            # Simple text-based display - more reliable than chips
            skill_texts = [str(skill).strip() for skill in missing_skills[:20] if str(skill).strip()]
            print(f"[DEBUG] Creating missing_chips with {len(skill_texts)} skills: {skill_texts[:5]}")
            if skill_texts:
                missing_chips = ft.Column(
                    [
                        ft.Text(f"• {skill}", size=12, color=ft.Colors.RED_700)
                        for skill in skill_texts
                    ],
                    spacing=3
                )
                print(f"[DEBUG] Missing chips created with {len(missing_chips.controls)} items")
            else:
                missing_chips = ft.Text("No missing skills identified", color="green", italic=True, size=12)
                print("[DEBUG] No skill texts, using fallback text")
        else:
            missing_chips = ft.Text("No missing skills identified", color="green", italic=True, size=12)
            print("[DEBUG] No missing skills list or empty, using fallback text")
        
        # Suggestions - check both 'suggestions' and 'improvement_suggestions' keys
        suggestions = result.get('suggestions', []) or result.get('improvement_suggestions', [])
        if suggestions:
            suggestion_items = [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB, color=AppTheme.WARNING, size=20),
                        ft.Text(str(s), size=14, expand=True)
                    ], spacing=8),
                    padding=ft.padding.only(left=10, top=5, bottom=5),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
                ) for s in suggestions[:10]  # Show up to 10 suggestions
            ]
        else:
            suggestion_items = [
                ft.Text("No suggestions available", color="grey", italic=True)
            ]
        
        # Additional sections
        missing_qualifications = result.get('missing_qualifications', [])
        qualifications_text = None
        if missing_qualifications and isinstance(missing_qualifications, list) and len(missing_qualifications) > 0:
            qualifications_text = ft.Column([
                ft.Text("📋 Missing Qualifications", size=14, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text(f"• {str(q)}", size=12) for q in missing_qualifications[:5]
                ], spacing=3)
            ], spacing=5)
        
        strengths = result.get('strengths', [])
        strengths_text = None
        if strengths and isinstance(strengths, list) and len(strengths) > 0:
            strengths_text = ft.Column([
                ft.Text("💪 Strengths", size=14, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text(f"• {str(s)}", size=12) for s in strengths[:5]
                ], spacing=3)
            ], spacing=5)
        
        # Build results content, filtering out None values
        print(f"[DEBUG] Building results_items, matched_chips type: {type(matched_chips)}, missing_chips type: {type(missing_chips)}")
        results_items = [
            ft.Text("Results", size=20, weight=ft.FontWeight.BOLD),
            score_card,
            ft.Divider(height=1),
            ft.Text("Matched Skills", size=14, weight=ft.FontWeight.BOLD),
            matched_chips,
            ft.Divider(height=1),
            ft.Text("Missing Skills", size=14, weight=ft.FontWeight.BOLD),
            missing_chips,
        ]
        
        # Add optional sections if they exist
        if strengths_text:
            results_items.append(ft.Divider(height=1))
            results_items.append(strengths_text)
        
        if qualifications_text:
            results_items.append(ft.Divider(height=1))
            results_items.append(qualifications_text)
        
        # Add suggestions
        results_items.extend([
            ft.Divider(height=1),
            ft.Text("Suggestions", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(suggestion_items, spacing=2),
                padding=ft.padding.only(top=3, bottom=5)
            )
        ])
        
        results_content = ft.Column(
            results_items,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Update results container content
        print(f"[DEBUG] Updating results container, visible={self.results_container.visible}")
        print(f"[DEBUG] Results content has {len(results_items)} items")
        self.results_container.content = results_content
        self.results_container.visible = True
        print(f"[DEBUG] Results container updated, visible={self.results_container.visible}")
        
        # Update the page instead of the container directly
        try:
            self.page.update()
            print("[DEBUG] Page update called successfully")
        except Exception as update_error:
            print(f"[ERROR] Failed to update page: {update_error}")
            import traceback
            traceback.print_exc()
