"""Questions Generator View"""

import flet as ft
from services.question_service import QuestionService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from core.auth import SessionManager

class QuestionsView:
    """View for generating and managing interview questions"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.current_questions = []
        self.jd_dropdown = None  # Will be set in build
        
    def _refresh_jd_dropdown(self):
        """Refresh JD dropdown with latest JDs"""
        if self.jd_dropdown:
            from services.jd_service import JobDescriptionService
            jds = JobDescriptionService.get_user_job_descriptions(self.user_id) or []
            self.jd_dropdown.options = [
                ft.dropdown.Option(str(jd['jd_id']), jd.get('job_title', 'Job')) 
                for jd in jds
            ]
            self.jd_dropdown.disabled = len(jds) == 0
            self.jd_dropdown.hint_text = "Choose a job description" if jds else "Add a job description first"
            # Only update if the control is already added to the page
            try:
                if hasattr(self.jd_dropdown, '_Control__page') and self.jd_dropdown._Control__page:
                    self.jd_dropdown.update()
            except (AttributeError, AssertionError):
                # Control not yet added to page, skip update - it will be refreshed when view is built
                pass
        
    def build(self) -> ft.Container:
        """Build the questions view"""
        
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("❓ Interview Questions Generator", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Generate personalized interview questions based on your resume and job description", size=14, color="grey")
            ], spacing=8),
            padding=ft.padding.only(bottom=20)
        )
        
        # Get resumes and JDs - use get_all_resumes to show all resumes, not just active ones
        resumes = ResumeService.get_all_resumes(self.user_id) or []
        jds = JobDescriptionService.get_user_job_descriptions(self.user_id) or []
        
        # Form controls
        self.resume_dropdown = ft.Dropdown(
            label="Select Resume",
            hint_text="Choose a resume" if resumes else "Upload a resume first",
            options=[ft.dropdown.Option(str(r['resume_id']), r.get('file_name', 'Resume')) for r in resumes],
            width=350,
            border_color=ft.Colors.PRIMARY,
            disabled=len(resumes) == 0
        )
        
        self.jd_dropdown = ft.Dropdown(
            label="Select Job Description",
            hint_text="Choose a job description" if jds else "Add a job description first",
            options=[ft.dropdown.Option(str(jd['jd_id']), jd.get('job_title', 'Job')) for jd in jds],
            width=350,
            border_color=ft.Colors.PRIMARY,
            disabled=len(jds) == 0
        )
        
        self.type_dropdown = ft.Dropdown(
            label="Question Type",
            value="behavioral",
            options=[
                ft.dropdown.Option("behavioral", "Behavioral (STAR method)"),
                ft.dropdown.Option("technical", "Technical (Skills & knowledge)"),
                ft.dropdown.Option("situational", "Situational (Scenarios)"),
                ft.dropdown.Option("company_specific", "Company-specific"),
            ],
            width=300,
            border_color=ft.Colors.PRIMARY
        )
        
        self.count_text = ft.Text("5 questions", size=14, weight=ft.FontWeight.BOLD)
        self.count_slider = ft.Slider(
            min=3, 
            max=15, 
            value=5, 
            divisions=12,
            label="{value}",
            width=300,
            on_change=lambda e: setattr(self.count_text, 'value', f"{int(e.control.value)} questions") or self.page.update()
        )
        
        generate_btn = ft.ElevatedButton(
            "✨ Generate Questions",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self.on_generate,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                padding=15
            )
        )
        
        # Form container
        form = ft.Container(
            content=ft.Column([
                ft.Row([self.resume_dropdown, self.jd_dropdown], spacing=20, wrap=True),
                ft.Row([
                    ft.Column([
                        ft.Text("Question Type:", size=12, weight=ft.FontWeight.BOLD),
                        self.type_dropdown
                    ]),
                    ft.Column([
                        ft.Text("Number of Questions:", size=12, weight=ft.FontWeight.BOLD),
                        self.count_text,
                        self.count_slider
                    ])
                ], spacing=30, wrap=True),
                generate_btn
            ], spacing=20),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            bgcolor=ft.Colors.GREY_100
        )
        
        # Questions display area
        self.questions_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            expand=True
        )
        
        # Previous sets
        self.sets_container = ft.Column(spacing=10)
        self.load_previous_sets()
        
        previous_sets_section = ft.Container(
            content=ft.Column([
                ft.Text("📚 Previous Question Sets", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.sets_container
            ], spacing=10),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            visible=len(self.sets_container.controls) > 0
        )
        
        # Main layout
        content = ft.Column([
            header,
            form,
            ft.Divider(height=30),
            ft.Text("📝 Generated Questions", size=20, weight=ft.FontWeight.BOLD),
            self.questions_container,
            ft.Divider(height=30),
            previous_sets_section
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
        
        return ft.Container(
            content=content,
            padding=30,
            expand=True
        )
    
    def on_generate(self, e):
        """Handle generate button click"""
        # Validate inputs
        if not self.resume_dropdown.value:
            self.show_error("Please select a resume")
            return
        
        if not self.jd_dropdown.value:
            self.show_error("Please select a job description")
            return
        
        # Show loading
        self.questions_container.controls.clear()
        self.questions_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text("Generating questions with AI...", size=16)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                padding=50
            )
        )
        self.page.update()
        
        # Generate questions
        result = QuestionService.generate_questions(
            user_id=self.user_id,
            resume_id=int(self.resume_dropdown.value),
            jd_id=int(self.jd_dropdown.value),
            question_type=self.type_dropdown.value,
            count=int(self.count_slider.value)
        )
        
        # Display results
        self.questions_container.controls.clear()
        
        if result and result.get('questions'):
            questions = result['questions']
            
            # Success message
            self.questions_container.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=24),
                        ft.Text(f"Successfully generated {len(questions)} questions!", 
                               size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.GREEN_100,
                    border_radius=5,
                    margin=ft.margin.only(bottom=20)
                )
            )
            
            # Display each question
            for i, q in enumerate(questions, 1):
                self.questions_container.controls.append(
                    self.build_question_card(i, q)
                )
            
            # Reload previous sets
            self.load_previous_sets()
            
        else:
            self.questions_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=48),
                        ft.Text("Failed to generate questions", size=18, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                        ft.Text("Please check your LLM settings and try again.", size=14, color="grey"),
                        ft.ElevatedButton("Go to Settings", icon=ft.Icons.SETTINGS, on_click=lambda _: self.page.go("/settings"))
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        
        self.page.update()
    
    def build_question_card(self, number: int, question: dict) -> ft.Card:
        """Build a question card"""
        difficulty_colors = {
            'easy': ft.Colors.GREEN,
            'medium': ft.Colors.ORANGE,
            'hard': ft.Colors.RED
        }
        
        difficulty = question.get('difficulty', 'medium')
        ideal_points = question.get('ideal_answer_points', [])
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"Q{number}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_PRIMARY),
                            bgcolor=ft.Colors.PRIMARY,
                            padding=10,
                            border_radius=5
                        ),
                        ft.Container(
                            content=ft.Text(difficulty.upper(), size=11, weight=ft.FontWeight.BOLD, 
                                          color=ft.Colors.ON_SURFACE),
                            bgcolor=difficulty_colors.get(difficulty, ft.Colors.GREY),
                            padding=ft.padding.symmetric(8, 4),
                            border_radius=3
                        )
                    ], spacing=10),
                    ft.Text(question.get('question', ''), size=15, weight=ft.FontWeight.W_500),
                    ft.Divider(),
                    *([ft.Text("💡 Ideal Answer Points:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY)] if ideal_points else []),
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.GREEN),
                            ft.Text(point, size=12)
                        ], spacing=5) for point in ideal_points
                    ], spacing=5) if ideal_points else ft.Column([], spacing=0),
                ], spacing=10),
                padding=20
            ),
            elevation=2
        )
    
    def load_previous_sets(self):
        """Load previous question sets"""
        self.sets_container.controls.clear()
        sets = QuestionService.get_question_sets(self.user_id, limit=5)
        
        for qs in sets:
            self.sets_container.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.QUIZ, color=ft.Colors.PRIMARY),
                    title=ft.Text(qs.get('set_name', 'Question Set'), weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"{qs.get('question_count', 0)} questions • {qs.get('job_title', 'No JD')}"),
                    trailing=ft.IconButton(
                        icon=ft.Icons.VISIBILITY,
                        tooltip="View questions",
                        on_click=lambda e, set_id=qs['set_id']: self.view_question_set(set_id)
                    ),
                    on_click=lambda e, set_id=qs['set_id']: self.view_question_set(set_id)
                )
            )
    
    def view_question_set(self, set_id: int):
        """View a specific question set"""
        questions = QuestionService.get_questions(set_id)
        
        self.questions_container.controls.clear()
        
        if questions:
            for i, q in enumerate(questions, 1):
                # Parse ideal_answer_points if it's a JSON string
                ideal_points = q.get('ideal_answer_points', [])
                if isinstance(ideal_points, str):
                    try:
                        import json
                        ideal_points = json.loads(ideal_points)
                    except:
                        ideal_points = []
                
                q['ideal_answer_points'] = ideal_points
                self.questions_container.controls.append(
                    self.build_question_card(i, q)
                )
        
        self.page.update()
    
    def show_error(self, message: str):
        """Show error snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400
        )
        self.page.snack_bar.open = True
        self.page.update()

