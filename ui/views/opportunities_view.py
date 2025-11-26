"""Job opportunities view with JSearch integration"""

import flet as ft
from ui.styles.theme import AppTheme
from ui.components.job_card import JobCard
from services.jsearch_service import JSearchService
from services.resume_service import ResumeService
from services.jd_service import JobDescriptionService
from core.auth import SessionManager

class OpportunitiesView:
    """Job search and opportunities view"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.current_jobs = []
        
    def build(self) -> ft.Container:
        """Build opportunities view"""
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("💼 Job Opportunities", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Search and find jobs ranked by compatibility",
                       size=14, color="grey")
            ], spacing=8),
            padding=AppTheme.PADDING_MEDIUM
        )
        
        # Search section
        self.search_query = ft.TextField(
            label="Search keywords (e.g., 'Python Developer')",
            expand=True,
            on_submit=self._on_search
        )
        
        self.location_field = ft.TextField(
            label="Location (optional)",
            width=300,
            on_submit=self._on_search
        )
        
        self.remote_only_checkbox = ft.Checkbox(
            label="Remote only",
            value=False
        )
        
        self.search_button = ft.ElevatedButton(
            text="Search Jobs",
            icon=ft.Icons.SEARCH,
            on_click=self._on_search,
            style=ft.ButtonStyle(bgcolor=AppTheme.PRIMARY, color="white")
        )
        
        search_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.search_query,
                    self.location_field
                ], spacing=12),
                ft.Row([
                    self.remote_only_checkbox,
                    self.search_button
                ], spacing=12)
            ], spacing=12),
            **AppTheme.card_style()
        )
        
        # Results section
        self.results_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
        self.results_container = ft.Column([], spacing=12)
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        self.results_section = ft.Column([
            self.results_title,
            self.loading_indicator,
            self.results_container
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Search history section
        self.search_history_container = ft.Container(
            content=ft.Column([
                ft.Text("Recent Searches", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("No recent searches", size=12, color="grey", italic=True)
            ], spacing=5),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            visible=True
        )
        
        # Load search history
        self._load_search_history()
        
        # Results wrapper container
        card_style = AppTheme.card_style()
        card_style.pop('padding', None)  # Remove padding from card_style
        self.results_wrapper = ft.Container(
            content=self.results_section,
            **card_style,
            visible=False,
            padding=10,
            expand=True
        )
        
        # Main content - simple vertical layout
        content = ft.Column([
            header,
            ft.Divider(),
            search_section,
            ft.Divider(height=10),
            self.search_history_container,
            ft.Divider(height=10),
            self.results_wrapper
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
        
        return ft.Container(
            content=content,
            padding=AppTheme.PADDING_MEDIUM,
            expand=True
        )
    
    def _on_search(self, e):
        """Handle search"""
        query = self.search_query.value
        location = self.location_field.value
        remote_only = self.remote_only_checkbox.value
        
        if not query:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Please enter search keywords"), 
                bgcolor="orange"
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # Show loading
        self.loading_indicator.visible = True
        self.results_container.controls.clear()
        self.results_title.value = "Searching..."
        self.results_wrapper.visible = True
        self.search_button.disabled = True
        self.page.update()
        
        # Search jobs
        result = JSearchService.search_jobs(
            query=query,
            location=location or "",
            remote_only=remote_only,
            user_id=self.user_id
        )
        
        # Hide loading
        self.loading_indicator.visible = False
        self.search_button.disabled = False
        
        if "error" in result:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {result['error']}"), 
                bgcolor="red"
            )
            self.page.snack_bar.open = True
            self.results_title.value = "Search failed"
            self.page.update()
            return
        
        jobs = result.get('jobs', [])
        
        if not jobs:
            self.results_title.value = "No jobs found"
            self.results_container.controls.append(
                ft.Text("Try different keywords or location", color="grey")
            )
            self.page.update()
            return
        
        # Rank by compatibility if user has resume
        resume = ResumeService.get_active_resume(self.user_id)
        if resume and resume.get('resume_text'):
            jobs = JSearchService.rank_jobs_by_compatibility(
                jobs,
                resume['resume_text'],
                self.user_id
            )
        
        # Save search
        JSearchService.save_search(self.user_id, query, location or "", remote_only, len(jobs))
        
        # Reload search history
        self._load_search_history()
        
        # Display results
        self.current_jobs = jobs
        self.results_title.value = f"Found {len(jobs)} jobs"
        self.results_wrapper.visible = True
        
        for job in jobs:
            job_card = JobCard.build(
                job=job,
                on_save=self._on_save_job,
                on_view_details=self._on_view_job_details,  # Opens job URL
                on_show_details=self._show_job_details_dialog  # Shows details dialog
            )
            self.results_container.controls.append(job_card)
        
        self.page.update()
    
    def _on_save_job(self, job: dict):
        """Handle save job button - saves as JD"""
        self._save_job_from_dialog(job, None)
    
    def _save_job_from_dialog(self, job: dict, dialog: ft.AlertDialog = None):
        """Save job as JD from dialog"""
        try:
            print(f"[DEBUG] _save_job_from_dialog called with job keys: {list(job.keys())[:10]}")
            
            # Close dialog first if provided
            if dialog:
                self._close_dialog(dialog)
            
            # Save JD
            jd_id = JobDescriptionService.save_jd_from_jsearch(self.user_id, job)
            
            print(f"[DEBUG] save_jd_from_jsearch returned: {jd_id} (type: {type(jd_id)})")
            
            # Also mark job as saved in jsearch_jobs if it exists there
            try:
                from services.jsearch_service import JSearchService
                # Try to find and mark the job as saved
                external_job_id = job.get('job_id') or job.get('external_job_id')
                if external_job_id:
                    # Check if job exists in jsearch_jobs
                    saved_job = JSearchService.get_job_by_external_id(external_job_id)
                    if saved_job and saved_job.get('job_id'):
                        # Mark as saved
                        JSearchService.save_job(saved_job['job_id'], is_saved=True)
                        print(f"[DEBUG] Marked job {saved_job['job_id']} as saved in jsearch_jobs")
                    else:
                        # Job doesn't exist in jsearch_jobs yet, save it first
                        saved_job_result = JSearchService._save_job(self.user_id, job)
                        if saved_job_result and saved_job_result.get('job_id'):
                            JSearchService.save_job(saved_job_result['job_id'], is_saved=True)
                            print(f"[DEBUG] Saved and marked job {saved_job_result['job_id']} as saved in jsearch_jobs")
            except Exception as e:
                print(f"[WARNING] Could not mark job as saved in jsearch_jobs: {e}")
                import traceback
                traceback.print_exc()
            
            if jd_id and jd_id > 0:
                # Show success dialog (more visible than snackbar)
                job_title = job.get('job_title', job.get('title', 'Job'))
                company = job.get('employer_name', job.get('company_name', 'Company'))
                
                success_dialog = ft.AlertDialog(
                    title=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=32),
                        ft.Text("✅ Saved Successfully!", size=18, weight=ft.FontWeight.BOLD)
                    ], spacing=10),
                    content=ft.Column([
                        ft.Text(f"Job description saved successfully!", size=14),
                        ft.Text(f"Company: {company}", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Position: {job_title}", size=12),
                        ft.Text(f"JD ID: {jd_id}", size=11, color=ft.Colors.GREY_600, italic=True)
                    ], spacing=8, tight=True),
                    actions=[
                        ft.ElevatedButton(
                            "OK",
                            on_click=lambda e: self._close_dialog(success_dialog),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_400, color="white")
                        )
                    ],
                    modal=True
                )
                
                self.page.dialog = success_dialog
                success_dialog.open = True
                self.page.update()
                print(f"[SUCCESS] Job saved with ID: {jd_id} - Success dialog shown")
                
                # Also show snackbar as backup
                success_snackbar = ft.SnackBar(
                    content=ft.Text(f"✅ Job description saved! (ID: {jd_id})"), 
                    bgcolor=ft.Colors.GREEN_400,
                    duration=3000
                )
                self.page.snack_bar = success_snackbar
                success_snackbar.open = True
            else:
                error_msg = f"❌ Failed to save job description. Returned ID: {jd_id}."
                print(f"[ERROR] {error_msg}")
                
                # Show error dialog
                error_dialog = ft.AlertDialog(
                    title=ft.Row([
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=32),
                        ft.Text("❌ Save Failed", size=18, weight=ft.FontWeight.BOLD)
                    ], spacing=10),
                    content=ft.Text(f"Failed to save job description.\n\nReturned ID: {jd_id}\n\nPlease check the console for details.", size=14),
                    actions=[
                        ft.ElevatedButton(
                            "OK",
                            on_click=lambda e: self._close_dialog(error_dialog),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_400, color="white")
                        )
                    ],
                    modal=True
                )
                
                self.page.dialog = error_dialog
                error_dialog.open = True
                self.page.update()
                print(f"[ERROR] Error dialog shown")
        except Exception as e:
            error_msg = f"❌ Exception saving job: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            error_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=32),
                    ft.Text("❌ Error", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                content=ft.Text(f"An error occurred while saving:\n\n{str(e)}", size=14),
                actions=[
                    ft.ElevatedButton(
                        "OK",
                        on_click=lambda e: self._close_dialog(error_dialog),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_400, color="white")
                    )
                ],
                modal=True
            )
            
            self.page.dialog = error_dialog
            error_dialog.open = True
            self.page.update()
            print(f"[ERROR] Exception dialog shown")
    
    def _add_to_planner(self, job: dict, dialog: ft.AlertDialog = None):
        """Add job to application planner"""
        try:
            from services.application_service import ApplicationService
            
            # Extract job information
            company_name = job.get('employer_name', job.get('company_name', job.get('company', 'Unknown Company')))
            job_title = job.get('job_title', job.get('title', 'Unknown Position'))
            location = job.get('job_city', job.get('location', ''))
            job_url = job.get('job_apply_link', job.get('job_url', ''))
            
            print(f"[DEBUG] Adding to planner: user_id={self.user_id}, company={company_name}, title={job_title}")
            
            # Create application in planner
            app_id = ApplicationService.create_application(
                user_id=self.user_id,
                company_name=company_name,
                job_title=job_title,
                location=location if location else None,
                job_url=job_url if job_url else None,
                status='saved',
                notes=f"Added from job search"
            )
            
            print(f"[DEBUG] create_application returned: {app_id}")
            
            if app_id and app_id > 0:
                # Close dialog if provided
                if dialog:
                    self._close_dialog(dialog)
                else:
                    self._close_dialog(self.page.dialog)
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Added '{job_title}' at {company_name} to Application Planner! (ID: {app_id})"), 
                    bgcolor=ft.Colors.GREEN_400,
                    duration=4000
                )
                self.page.snack_bar.open = True
                self.page.update()
                print(f"[SUCCESS] Application added to planner with ID: {app_id}")
            else:
                error_msg = f"❌ Failed to add to planner. Returned ID: {app_id}. Check console for details."
                print(f"[ERROR] {error_msg}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(error_msg), 
                    bgcolor=ft.Colors.RED_400,
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            error_msg = f"Error adding to planner: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ {error_msg}"), 
                bgcolor=ft.Colors.RED_400,
                duration=5000
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _on_view_job_details(self, job: dict):
        """Handle view job details - opens job URL in browser"""
        # Get job URL
        apply_url = job.get('job_apply_link') or job.get('job_url') or job.get('job_google_link', '')
        
        if apply_url:
            self._open_job_url(apply_url)
        else:
            # If no URL, show details dialog instead
            self._show_job_details_dialog(job)
    
    def _show_job_details_dialog(self, job: dict):
        """Show job details in a dialog"""
        description = job.get('job_description', job.get('description', 'No description available'))
        title = job.get('job_title', job.get('title', 'Job Details'))
        company = job.get('employer_name', job.get('company_name', job.get('company', 'N/A')))
        location = job.get('job_city', job.get('location', 'N/A'))
        employment_type = job.get('job_employment_type', 'N/A')
        salary_min = job.get('salary_min', job.get('job_min_salary'))
        salary_max = job.get('salary_max', job.get('job_max_salary'))
        apply_url = job.get('job_apply_link', job.get('job_url', ''))
        compatibility = job.get('compatibility_score', 0)
        
        # Build salary text
        salary_text = "Not specified"
        if salary_min or salary_max:
            if salary_min and salary_max:
                salary_text = f"${salary_min:,.0f} - ${salary_max:,.0f}"
            elif salary_min:
                salary_text = f"${salary_min:,.0f}+"
            elif salary_max:
                salary_text = f"Up to ${salary_max:,.0f}"
        
        dialog = ft.AlertDialog(
            title=ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"Company: {company}", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Container(
                            content=ft.Text(f"{int(compatibility)}%", size=14, weight=ft.FontWeight.BOLD, color="white"),
                            bgcolor=AppTheme.SUCCESS if compatibility >= 70 else AppTheme.WARNING if compatibility >= 50 else AppTheme.ERROR,
                            padding=8,
                            border_radius=4
                        ) if compatibility > 0 else ft.Container()
                    ]),
                    ft.Text(f"Location: {location}", size=14),
                    ft.Text(f"Employment Type: {employment_type}", size=14),
                    ft.Text(f"Salary: {salary_text}", size=14, weight=ft.FontWeight.BOLD, color=AppTheme.PRIMARY),
                    ft.Divider(),
                    ft.Text("Description:", weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(description, size=12, selectable=True)
                ], spacing=8, scroll=ft.ScrollMode.AUTO, tight=True),
                width=600,
                height=500,
                padding=10
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save JD",
                    icon=ft.Icons.BOOKMARK,
                    on_click=lambda e: self._save_job_from_dialog(job, dialog)
                ),
                ft.ElevatedButton(
                    "Add to Planner",
                    icon=ft.Icons.ADD_TASK,
                    on_click=lambda e: self._add_to_planner(job, dialog)
                ),
                ft.ElevatedButton(
                    "Apply",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: self._open_job_url(apply_url) if apply_url else None
                ) if apply_url else None
            ],
            modal=True
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog"""
        dialog.open = False
        self.page.dialog = None
        self.page.update()
    
    def _open_job_url(self, url: str):
        """Open job URL in browser"""
        if url:
            self.page.launch_url(url)
    
    def _load_search_history(self):
        """Load and display search history"""
        try:
            history = JSearchService.get_search_history(self.user_id, limit=5)
            
            if not history:
                self.search_history_container.content = ft.Column([
                    ft.Text("Recent Searches", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("No recent searches", size=12, color="grey", italic=True)
                ], spacing=5)
                if hasattr(self, 'page'):
                    try:
                        self.search_history_container.update()
                    except:
                        pass
                return
            
            history_cards = []
            for search in history:
                query = search.get('search_query', '')
                location = search.get('location', '')
                remote = search.get('remote_only', False)
                results_count = search.get('results_count', 0)
                searched_at = search.get('searched_at', '')
                
                # Format date
                date_str = "Recently"
                if searched_at:
                    try:
                        from datetime import datetime
                        if isinstance(searched_at, str):
                            dt = datetime.fromisoformat(searched_at.replace('Z', '+00:00'))
                        else:
                            dt = searched_at
                        date_str = dt.strftime("%b %d, %Y")
                    except:
                        date_str = str(searched_at)[:10] if searched_at else "Recently"
                
                # Build search text
                search_text = query
                if location:
                    search_text += f" in {location}"
                if remote:
                    search_text += " (Remote)"
                
                card = ft.Container(
                    content=ft.Column([
                        ft.Text(search_text, size=12, weight=ft.FontWeight.BOLD, max_lines=2),
                        ft.Row([
                            ft.Text(f"{results_count} results", size=10, color="grey"),
                            ft.Text(date_str, size=10, color="grey", italic=True)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ], spacing=4, tight=True),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=6,
                    bgcolor=ft.Colors.WHITE,
                    on_click=lambda e, q=query, loc=location, rem=remote: self._reuse_search(q, loc, rem),
                    ink=True
                )
                history_cards.append(card)
            
            self.search_history_container.content = ft.Column([
                ft.Text("Recent Searches", size=14, weight=ft.FontWeight.BOLD),
                ft.Column(history_cards, spacing=8, scroll=ft.ScrollMode.AUTO, height=200)
            ], spacing=8)
            
            if hasattr(self, 'page'):
                try:
                    self.search_history_container.update()
                except:
                    pass
                    
        except Exception as e:
            print(f"[ERROR] Error loading search history: {e}")
            import traceback
            traceback.print_exc()
    
    def _reuse_search(self, query: str, location: str, remote_only: bool):
        """Reuse a previous search"""
        self.search_query.value = query
        self.location_field.value = location
        self.remote_only_checkbox.value = remote_only
        self.page.update()
        
        # Trigger search
        self._on_search(None)

