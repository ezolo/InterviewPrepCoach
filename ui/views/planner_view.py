"""Application Planner View"""

import flet as ft
from typing import Optional, List, Dict
from services.application_service import ApplicationService
from services.jsearch_service import JSearchService
from core.auth import SessionManager
from datetime import datetime

class PlannerView:
    """View for tracking job applications"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        self.selected_status_filter = None
        
    def build(self) -> ft.Container:
        """Build the planner view"""
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📅 Application Planner", size=32, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "➕ New Application",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self.show_add_dialog(e),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PRIMARY,
                            color=ft.Colors.ON_PRIMARY
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text("Track your job applications and manage follow-ups", size=14, color="grey")
            ], spacing=8),
            padding=ft.padding.only(bottom=20)
        )
        
        # Stats cards (will be refreshed)
        self.stats_row = self._build_stats_row()
        
        # Status filter buttons
        filter_buttons = ft.Row([
            ft.TextButton("All", on_click=lambda _: self.filter_applications(None)),
            ft.TextButton("Saved", on_click=lambda _: self.filter_applications('saved')),
            ft.TextButton("Applied", on_click=lambda _: self.filter_applications('applied')),
            ft.TextButton("Screening", on_click=lambda _: self.filter_applications('screening')),
            ft.TextButton("Interview", on_click=lambda _: self.filter_applications('interview')),
            ft.TextButton("Offer", on_click=lambda _: self.filter_applications('offer')),
            ft.TextButton("Rejected", on_click=lambda _: self.filter_applications('rejected')),
        ], spacing=5, wrap=True)
        
        # Applications list - always initialize
        self.applications_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            expand=True
        )
        
        # Load applications after container is created
        try:
            self.load_applications()
        except Exception as e:
            print(f"[ERROR] Error in build() while loading applications: {e}")
            import traceback
            traceback.print_exc()
        
        # Main layout
        content = ft.Column([
            header,
            self.stats_row,
            ft.Divider(height=20),
            ft.Text("Filter by Status:", size=14, weight=ft.FontWeight.BOLD),
            filter_buttons,
            ft.Divider(),
            self.applications_container
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
        
        return ft.Container(
            content=content,
            padding=30,
            expand=True
        )
    
    def _build_stats_row(self) -> ft.Row:
        """Build stats row with current data"""
        stats = ApplicationService.get_stats_by_status(self.user_id)
        total_stats = ApplicationService.get_application_stats(self.user_id)
        
        # Count saved jobs from job search
        saved_jobs_count = len(JSearchService.get_saved_jobs(self.user_id) or [])
        total_saved = stats.get('saved', 0) + saved_jobs_count
        
        return ft.Row([
            self.build_stat_card("Total", total_stats.get('total', 0) + saved_jobs_count, ft.Icons.APPS, ft.Colors.BLUE),
            self.build_stat_card("Saved", total_saved, ft.Icons.BOOKMARK, ft.Colors.GREY),
            self.build_stat_card("Applied", stats.get('applied', 0), ft.Icons.SEND, ft.Colors.GREEN),
            self.build_stat_card("Interview", stats.get('interview', 0), ft.Icons.PERSON, ft.Colors.ORANGE),
            self.build_stat_card("Offers", stats.get('offer', 0), ft.Icons.CELEBRATION, ft.Colors.PURPLE),
        ], spacing=15, wrap=True)
    
    def build_stat_card(self, title: str, value: int, icon: str, color: str) -> ft.Container:
        """Build a stat card"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=32),
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD),
                ft.Text(title, size=12, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=120,
            padding=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            bgcolor=ft.Colors.GREY_100
        )
    
    def load_applications(self, status: Optional[str] = None):
        """Load and display applications"""
        # Ensure container exists before using it
        if not hasattr(self, 'applications_container') or self.applications_container is None:
            print(f"[DEBUG] applications_container not initialized yet, skipping load")
            return
        
        # Clear existing controls
        try:
            self.applications_container.controls.clear()
        except Exception as e:
            print(f"[WARNING] Error clearing container: {e}")
            # Try to reinitialize
            self.applications_container = ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                expand=True
            )
        
        print(f"[DEBUG] Loading applications for user_id={self.user_id}, status={status}")
        
        try:
            apps = ApplicationService.get_applications(self.user_id, status)
            print(f"[DEBUG] get_applications returned {len(apps) if apps else 0} applications")
            
            # If status is 'saved', also include saved jobs from job search
            if status == 'saved' or status is None:
                saved_jobs = self._load_saved_jobs()
                print(f"[DEBUG] Found {len(saved_jobs)} saved jobs from job search")
                
                # Convert saved jobs to application format and add to apps list
                for job in saved_jobs:
                    app_from_job = self._convert_job_to_application(job)
                    if app_from_job:
                        apps.append(app_from_job)
            
            if not apps:
                self.applications_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.INBOX, size=64, color="grey"),
                            ft.Text("No applications yet", size=18, color="grey"),
                            ft.Text("Click 'New Application' to track your first job application", size=14, color="grey"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.center,
                        padding=50
                    )
                )
            else:
                for app in apps:
                    print(f"[DEBUG] Building card for app_id={app.get('application_id')}, company={app.get('company_name')}")
                    self.applications_container.controls.append(
                        self.build_application_card(app)
                    )
        except Exception as e:
            print(f"[ERROR] Error loading applications: {e}")
            import traceback
            traceback.print_exc()
            self.applications_container.controls.append(
                ft.Container(
                    content=ft.Text(f"Error loading applications: {str(e)}", color="red"),
                    padding=20
                )
            )
        
        self.page.update()
    
    def _load_saved_jobs(self) -> List[Dict]:
        """Load saved jobs from job search"""
        try:
            saved_jobs = JSearchService.get_saved_jobs(self.user_id)
            return saved_jobs or []
        except Exception as e:
            print(f"[ERROR] Error loading saved jobs: {e}")
            return []
    
    def _convert_job_to_application(self, job: Dict) -> Optional[Dict]:
        """Convert a saved job from jsearch_jobs to application format"""
        try:
            # Map jsearch_jobs fields to application format
            job_title = job.get('title', job.get('job_title', 'Unknown Position'))
            company_name = job.get('company_name', job.get('company', 'Unknown Company'))
            
            return {
                'application_id': f"job_{job.get('job_id')}",  # Prefix to distinguish from real apps
                'company_name': company_name,
                'job_title': job_title,
                'position': job_title,
                'location': job.get('location', ''),
                'status': 'saved',
                'job_url': job.get('job_url', ''),
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
                'description': job.get('description', ''),
                'applied_date': None,
                'interview_date': None,
                'notes': f"Saved from job search",
                'is_from_job_search': True,  # Flag to identify saved jobs
                'external_job_id': job.get('external_job_id'),
                'job_id': job.get('job_id')
            }
        except Exception as e:
            print(f"[ERROR] Error converting job to application: {e}")
            return None
    
    def build_application_card(self, app: dict) -> ft.Card:
        """Build an application card"""
        status_colors = {
            'saved': ft.Colors.GREY_400,
            'applied': ft.Colors.BLUE_400,
            'screening': ft.Colors.LIGHT_BLUE_400,
            'interview': ft.Colors.ORANGE_400,
            'final_round': ft.Colors.DEEP_ORANGE_400,
            'offer': ft.Colors.GREEN_400,
            'rejected': ft.Colors.RED_400,
            'withdrawn': ft.Colors.GREY_600
        }
        
        status = app.get('status', 'saved')
        
        # Format dates - handle multiple formats
        def format_date(date_value):
            if not date_value:
                return None
            try:
                if isinstance(date_value, str):
                    # Handle MySQL DATETIME format: '2024-01-15 10:30:00'
                    if ' ' in date_value:
                        dt = datetime.strptime(date_value.split()[0], '%Y-%m-%d')
                    # Handle ISO format with T
                    elif 'T' in date_value:
                        dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    # Handle DATE format: '2024-01-15'
                    else:
                        dt = datetime.strptime(date_value, '%Y-%m-%d')
                elif isinstance(date_value, datetime):
                    dt = date_value
                elif hasattr(date_value, 'strftime'):  # date object
                    dt = datetime.combine(date_value, datetime.min.time())
                else:
                    return None
                return dt.strftime('%b %d, %Y')
            except Exception as e:
                print(f"[DEBUG] Date formatting error: {e}, value: {date_value}, type: {type(date_value)}")
                return None
        
        applied_date_str = format_date(app.get('applied_date'))
        interview_date_str = format_date(app.get('interview_date'))
        created_date_str = format_date(app.get('created_at'))
        
        # Notes preview
        notes = app.get('notes', '')
        notes_preview = (notes[:100] + '...') if notes and len(notes) > 100 else notes
        
        # Salary info
        salary = app.get('salary_offered')
        salary_text = f"${salary:,.0f}" if salary else None
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(app.get('job_title', 'Untitled'), size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(app.get('company_name', 'Unknown Company'), size=14, color="grey"),
                            ft.Row([
                                ft.Icon(ft.Icons.LOCATION_ON, size=14, color="grey"),
                                ft.Text(app.get('location', 'Not specified'), size=12, color="grey")
                            ], spacing=5) if app.get('location') else ft.Row([], spacing=0),
                        ], spacing=5, expand=True),
                        ft.Column([
                            ft.Container(
                                content=ft.Text(
                                    status.replace('_', ' ').title(),
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=status_colors.get(status, ft.Colors.GREY),
                                padding=ft.padding.symmetric(10, 5),
                                border_radius=5
                            ),
                            ft.Text(
                                f"Added {created_date_str or 'Unknown'}", 
                                size=11,
                                color="grey"
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=5)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    # Date and salary info row
                    ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color="grey"),
                            ft.Text(f"Applied: {applied_date_str}", size=11, color="grey") if applied_date_str else ft.Text("Not applied yet", size=11, color="grey", italic=True)
                        ], spacing=5) if applied_date_str or status != 'saved' else ft.Container(),
                        ft.Row([
                            ft.Icon(ft.Icons.EVENT, size=14, color="grey"),
                            ft.Text(f"Interview: {interview_date_str}", size=11, color="grey")
                        ], spacing=5) if interview_date_str else ft.Container(),
                        ft.Row([
                            ft.Icon(ft.Icons.ATTACH_MONEY, size=14, color="green"),
                            ft.Text(f"Salary: {salary_text}", size=11, color="green", weight=ft.FontWeight.BOLD)
                        ], spacing=5) if salary_text else ft.Container()
                    ], spacing=15, wrap=True) if (applied_date_str or interview_date_str or salary_text) else ft.Container(),
                    
                    # Notes preview
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Notes:", size=12, weight=ft.FontWeight.BOLD, color="grey"),
                            ft.Text(notes_preview or "No notes", size=11, color="grey", italic=not notes)
                        ], spacing=3, tight=True),
                        visible=bool(notes),
                        padding=ft.padding.only(top=5)
                    ),
                    
                    ft.Divider(),
                    ft.Row([
                        # For saved jobs from job search, show "Convert to Application" button
                        ft.ElevatedButton(
                            "Convert to Application",
                            icon=ft.Icons.ADD_TASK,
                            on_click=lambda _, a=app: self._convert_job_to_application_action(a),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, padding=10)
                        ) if app.get('is_from_job_search') else ft.Container(),
                        # For regular applications, show standard buttons
                        ft.ElevatedButton(
                            "Update Status",
                            icon=ft.Icons.UPDATE,
                            on_click=lambda _, app_id=app['application_id']: self.show_status_dialog(app_id),
                            style=ft.ButtonStyle(padding=10)
                        ) if not app.get('is_from_job_search') else ft.Container(),
                        ft.TextButton(
                            "Edit",
                            icon=ft.Icons.EDIT,
                            on_click=lambda _, a=app: self.show_edit_dialog(a)
                        ) if not app.get('is_from_job_search') else ft.Container(),
                        ft.TextButton(
                            "Delete",
                            icon=ft.Icons.DELETE,
                            on_click=lambda _, app_id=app['application_id']: self.delete_application(app_id)
                        ) if not app.get('is_from_job_search') else ft.Container(),
                        # View job URL button (for both types)
                        ft.TextButton(
                            "View URL",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda _, url=app.get('job_url'): self.page.launch_url(url) if url else self.page.update(),
                            disabled=not app.get('job_url')
                        ) if app.get('job_url') else ft.Container()
                    ], spacing=10, wrap=True)
                ], spacing=15),
                padding=20
            ),
            elevation=2
        )
    
    def filter_applications(self, status: Optional[str]):
        """Filter applications by status"""
        self.selected_status_filter = status
        self.load_applications(status)
        self._refresh_stats()
    
    def _refresh_stats(self):
        """Refresh stats row"""
        if hasattr(self, 'stats_row'):
            # Find stats row in parent and replace it
            # This is a simplified approach - in production, you might want to use a ref
            pass  # Stats will refresh on next build
    
    def _open_dialog(self, dialog: ft.AlertDialog):
        """Open dialog helper - matches working pattern from opportunities_view"""
        try:
            print(f"[DEBUG] _open_dialog called, page={self.page}, has dialog attr={hasattr(self.page, 'dialog')}")
            
            # Close any existing dialog first
            if hasattr(self.page, 'dialog') and self.page.dialog:
                print(f"[DEBUG] Closing existing dialog")
                self.page.dialog.open = False
                self.page.dialog = None
                self.page.update()
            
            # Set and open dialog
            print(f"[DEBUG] Setting page.dialog and opening")
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            print(f"[DEBUG] Dialog opened successfully, dialog.open={dialog.open}, page.dialog={self.page.dialog}")
        except Exception as ex:
            print(f"[ERROR] Error in _open_dialog: {ex}")
            import traceback
            traceback.print_exc()
            # Try direct assignment as fallback
            try:
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
            except Exception as ex2:
                print(f"[ERROR] Fallback also failed: {ex2}")
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close dialog - simple and reliable (matches opportunities_view pattern)"""
        try:
            print(f"[DEBUG] Closing dialog")
            # Close dialog first
            dialog.open = False
            # Clear page.dialog (this removes modal backdrop)
            self.page.dialog = None
            # Update page to reflect changes
            self.page.update()
            print(f"[DEBUG] Dialog closed successfully")
        except Exception as ex:
            print(f"[ERROR] Error closing dialog: {ex}")
            import traceback
            traceback.print_exc()
            # Force close as fallback
            try:
                if dialog:
                    dialog.open = False
                self.page.dialog = None
                self.page.update()
            except:
                pass
    
    def show_add_dialog(self, e):
        """Show dialog to add new application"""
        print(f"[DEBUG] show_add_dialog called, e={e}, e.page={getattr(e, 'page', None)}, self.page={self.page}")
        
        # Always use self.page (the page passed to __init__)
        page = self.page
        
        if not page:
            print(f"[ERROR] Page is None!")
            return
        
        company_field = ft.TextField(label="Company Name *", autofocus=True, width=350)
        job_title_field = ft.TextField(label="Job Title *", width=350)
        location_field = ft.TextField(label="Location", width=350)
        job_url_field = ft.TextField(label="Job URL", width=350)
        applied_date_field = ft.TextField(
            label="Applied Date (YYYY-MM-DD)",
            hint_text="2024-01-15",
            width=350
        )
        interview_date_field = ft.TextField(
            label="Interview Date (YYYY-MM-DD)",
            hint_text="2024-01-20",
            width=350
        )
        salary_field = ft.TextField(
            label="Salary Offered",
            hint_text="100000",
            width=350
        )
        notes_field = ft.TextField(label="Notes", multiline=True, min_lines=3, max_lines=5, width=350)
        
        def save_application(e):
            # Validate required fields (strip whitespace)
            company = company_field.value.strip() if company_field.value else ""
            job_title = job_title_field.value.strip() if job_title_field.value else ""
            
            if not company or not job_title:
                self.show_error("Company and Job Title are required")
                return
            
            # Parse dates
            applied_date = None
            interview_date = None
            salary = None
            
            if applied_date_field.value:
                try:
                    applied_date = datetime.strptime(applied_date_field.value, '%Y-%m-%d').date()
                except:
                    self.show_error("Invalid applied date format. Use YYYY-MM-DD")
                    return
            
            if interview_date_field.value:
                try:
                    interview_date = datetime.strptime(interview_date_field.value, '%Y-%m-%d')
                except:
                    self.show_error("Invalid interview date format. Use YYYY-MM-DD")
                    return
            
            if salary_field.value:
                try:
                    salary = float(salary_field.value)
                except:
                    self.show_error("Invalid salary. Enter a number.")
                    return
            
            print(f"[DEBUG] Creating application: user_id={self.user_id}, company={company}, title={job_title}")
            
            try:
                app_id = ApplicationService.create_application(
                    user_id=self.user_id,
                    company_name=company,
                    job_title=job_title,
                    location=location_field.value.strip() if location_field.value and location_field.value.strip() else None,
                    job_url=job_url_field.value.strip() if job_url_field.value and job_url_field.value.strip() else None,
                    notes=notes_field.value.strip() if notes_field.value and notes_field.value.strip() else None,
                    status='saved',
                    applied_date=applied_date,
                    interview_date=interview_date,
                    salary_offered=salary
                )
                
                print(f"[DEBUG] create_application returned: {app_id} (type: {type(app_id)})")
                
                if app_id and app_id > 0:
                    # Use _close_dialog for consistent cleanup
                    self._close_dialog(dialog)
                    # Reload applications and refresh stats
                    self.load_applications(self.selected_status_filter)
                    self._refresh_stats()
                    self.show_success(f"✅ Application added successfully! (ID: {app_id})")
                else:
                    error_msg = f"❌ Failed to add application. Returned ID: {app_id}. Check console for details."
                    print(f"[ERROR] {error_msg}")
                    self.show_error(error_msg)
            except Exception as ex:
                error_msg = f"❌ Error creating application: {str(ex)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                self.show_error(error_msg)
        
        # Create dialog content - wrap in Container with max height for scrolling
        dialog_content = ft.Container(
            content=ft.Column([
                company_field,
                job_title_field,
                location_field,
                job_url_field,
                applied_date_field,
                interview_date_field,
                salary_field,
                notes_field
            ], spacing=15, scroll=ft.ScrollMode.AUTO, tight=True),
            width=400,
            height=450,
            padding=10
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("➕ New Application", size=18, weight=ft.FontWeight.BOLD),
            content=dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Add Application", on_click=save_application, icon=ft.Icons.ADD)
            ],
            modal=True,
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        print(f"[DEBUG] Opening add dialog")
        # Use both page.dialog AND page.overlay to ensure visibility
        try:
            # Close any existing dialog first
            if hasattr(self.page, 'dialog') and self.page.dialog:
                try:
                    self.page.dialog.open = False
                    self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            # Add to overlay first (for rendering)
            if not hasattr(self.page, 'overlay'):
                self.page.overlay = []
            if dialog not in self.page.overlay:
                self.page.overlay.append(dialog)
            
            # Set page.dialog (for modal behavior)
            self.page.dialog = dialog
            dialog.open = True
            
            # Force update
            self.page.update()
            
            print(f"[DEBUG] Dialog opened, open={dialog.open}, in overlay={dialog in self.page.overlay}, page.dialog={self.page.dialog is not None}")
        except Exception as ex:
            print(f"[ERROR] Failed to open add dialog: {ex}")
            import traceback
            traceback.print_exc()
    
    def show_status_dialog(self, app_id):
        """Show dialog to update application status"""
        # Handle both int IDs and string IDs (for saved jobs)
        if isinstance(app_id, str) and app_id.startswith('job_'):
            self.show_error("Cannot update status of saved jobs. Please convert to application first.")
            return
        
        status_dropdown = ft.Dropdown(
            label="New Status",
            options=[
                ft.dropdown.Option("saved", "💾 Saved"),
                ft.dropdown.Option("applied", "📤 Applied"),
                ft.dropdown.Option("screening", "📋 Screening"),
                ft.dropdown.Option("interview", "👤 Interview"),
                ft.dropdown.Option("final_round", "🎯 Final Round"),
                ft.dropdown.Option("offer", "🎉 Offer"),
                ft.dropdown.Option("rejected", "❌ Rejected"),
                ft.dropdown.Option("withdrawn", "🚫 Withdrawn"),
            ],
            width=300
        )
        
        def update_status(e):
            if not status_dropdown.value:
                self.show_error("Please select a status")
                return
            
            if ApplicationService.update_status(app_id, status_dropdown.value):
                self._close_dialog(dialog)
                self.load_applications(self.selected_status_filter)
                self.show_success("Status updated successfully!")
            else:
                self.show_error("Failed to update status")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Update Status"),
            content=status_dropdown,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Update", on_click=update_status)
            ],
            modal=True
        )
        
        # Open dialog - use overlay for visibility
        print(f"[DEBUG] Opening status dialog")
        try:
            # Close any existing dialog first
            if hasattr(self.page, 'dialog') and self.page.dialog:
                try:
                    self.page.dialog.open = False
                    self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            # Add to overlay
            if not hasattr(self.page, 'overlay'):
                self.page.overlay = []
            if dialog not in self.page.overlay:
                self.page.overlay.append(dialog)
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
            print(f"[DEBUG] Status dialog opened, open={dialog.open}")
        except Exception as ex:
            print(f"[ERROR] Failed to open status dialog: {ex}")
    
    def show_edit_dialog(self, app: dict):
        """Show dialog to edit application"""
        def format_date_for_input(date_value):
            if not date_value:
                return ""
            try:
                if isinstance(date_value, str):
                    if 'T' in date_value:
                        dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(date_value, '%Y-%m-%d')
                elif isinstance(date_value, datetime):
                    dt = date_value
                else:
                    return ""
                return dt.strftime('%Y-%m-%d')
            except:
                return ""
        
        company_field = ft.TextField(label="Company Name", value=app.get('company_name', ''), width=300)
        job_title_field = ft.TextField(label="Job Title", value=app.get('job_title', ''), width=300)
        location_field = ft.TextField(label="Location", value=app.get('location', ''), width=300)
        job_url_field = ft.TextField(label="Job URL", value=app.get('job_url', ''), width=300)
        applied_date_field = ft.TextField(
            label="Applied Date (YYYY-MM-DD)",
            value=format_date_for_input(app.get('applied_date')),
            hint_text="2024-01-15",
            width=300
        )
        interview_date_field = ft.TextField(
            label="Interview Date (YYYY-MM-DD)",
            value=format_date_for_input(app.get('interview_date')),
            hint_text="2024-01-20",
            width=300
        )
        salary_field = ft.TextField(
            label="Salary Offered",
            value=str(app.get('salary_offered', '')) if app.get('salary_offered') else '',
            hint_text="100000",
            width=300
        )
        notes_field = ft.TextField(label="Notes", value=app.get('notes', ''), multiline=True, min_lines=3, width=300)
        
        def save_changes(e):
            # Parse dates
            applied_date = None
            interview_date = None
            salary = None
            
            if applied_date_field.value:
                try:
                    applied_date = datetime.strptime(applied_date_field.value, '%Y-%m-%d').date()
                except:
                    self.show_error("Invalid applied date format. Use YYYY-MM-DD")
                    return
            
            if interview_date_field.value:
                try:
                    interview_date = datetime.strptime(interview_date_field.value, '%Y-%m-%d')
                except:
                    self.show_error("Invalid interview date format. Use YYYY-MM-DD")
                    return
            
            if salary_field.value:
                try:
                    salary = float(salary_field.value)
                except:
                    self.show_error("Invalid salary. Enter a number.")
                    return
            
            # Get application_id - handle both real apps and saved jobs
            app_id = app.get('application_id')
            if isinstance(app_id, str) and app_id.startswith('job_'):
                # This is a saved job, not a real application - can't edit
                self.show_error("Cannot edit saved jobs. Please convert to application first.")
                return
            
            if ApplicationService.update_application(
                app_id,
                company_name=company_field.value,
                job_title=job_title_field.value,
                location=location_field.value,
                job_url=job_url_field.value,
                notes=notes_field.value,
                applied_date=applied_date,
                interview_date=interview_date,
                salary_offered=salary
            ):
                # Close dialog first, then reload and show success
                self._close_dialog(dialog)
                # Small delay to ensure dialog is fully closed before reloading
                self.page.update()
                self.load_applications(self.selected_status_filter)
                self.show_success("Application updated!")
            else:
                self.show_error("Failed to update application")
        
        dialog = ft.AlertDialog(
            title=ft.Text("✏️ Edit Application"),
            content=ft.Column([
                company_field,
                job_title_field,
                location_field,
                job_url_field,
                applied_date_field,
                interview_date_field,
                salary_field,
                notes_field
            ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Save Changes", on_click=save_changes)
            ],
            modal=True
        )
        
        # Open dialog - use overlay for visibility
        print(f"[DEBUG] Opening edit dialog")
        try:
            # Close any existing dialog first
            if hasattr(self.page, 'dialog') and self.page.dialog:
                try:
                    self.page.dialog.open = False
                    self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            # Add to overlay
            if not hasattr(self.page, 'overlay'):
                self.page.overlay = []
            if dialog not in self.page.overlay:
                self.page.overlay.append(dialog)
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
            print(f"[DEBUG] Edit dialog opened, open={dialog.open}")
        except Exception as ex:
            print(f"[ERROR] Failed to open edit dialog: {ex}")
    
    def delete_application(self, app_id):
        """Delete an application with confirmation"""
        # Handle both int IDs and string IDs (for saved jobs)
        if isinstance(app_id, str) and app_id.startswith('job_'):
            self.show_error("Cannot delete saved jobs. They are from job search.")
            return
        
        def confirm_delete(e):
            if ApplicationService.delete_application(app_id):
                self._close_dialog(dialog)
                self.load_applications(self.selected_status_filter)
                self.show_success("Application deleted")
            else:
                self.show_error("Failed to delete application")
        
        dialog = ft.AlertDialog(
            title=ft.Text("⚠️ Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this application? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Delete", on_click=confirm_delete, bgcolor=ft.Colors.RED_400)
            ],
            modal=True
        )
        
        # Open dialog - use overlay for visibility
        print(f"[DEBUG] Opening delete confirmation dialog")
        try:
            # Close any existing dialog first
            if hasattr(self.page, 'dialog') and self.page.dialog:
                try:
                    self.page.dialog.open = False
                    self.page.dialog = None
                    self.page.update()
                except:
                    pass
            
            # Add to overlay
            if not hasattr(self.page, 'overlay'):
                self.page.overlay = []
            if dialog not in self.page.overlay:
                self.page.overlay.append(dialog)
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
            print(f"[DEBUG] Delete dialog opened, open={dialog.open}")
        except Exception as ex:
            print(f"[ERROR] Failed to open delete dialog: {ex}")
    
    def show_error(self, message: str):
        """Show error snackbar"""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_400)
        self.page.snack_bar.open = True
        self.page.update()
    
    def _convert_job_to_application_action(self, job_app: dict):
        """Convert a saved job to a real application"""
        try:
            # Pre-fill the add dialog with job data
            self.show_add_dialog_from_job(job_app)
        except Exception as e:
            print(f"[ERROR] Error converting job to application: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error converting job: {str(e)}")
    
    def _open_job_url(self, url: str):
        """Open job URL in browser"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            print(f"[ERROR] Error opening URL: {e}")
            self.show_error("Could not open job URL")
    
    def show_add_dialog_from_job(self, job_app: dict):
        """Show add dialog pre-filled with job data"""
        # Use the existing show_add_dialog but pre-fill with job data
        # We'll modify the dialog after it's created
        dialog = ft.AlertDialog(
            title=ft.Text("Convert to Application", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Convert this saved job to a tracked application:", size=14),
                    ft.TextField(
                        label="Company",
                        value=job_app.get('company_name', ''),
                        width=400
                    ),
                    ft.TextField(
                        label="Position",
                        value=job_app.get('job_title', ''),
                        width=400
                    ),
                    ft.TextField(
                        label="Location",
                        value=job_app.get('location', ''),
                        width=400
                    ),
                    ft.TextField(
                        label="Job URL",
                        value=job_app.get('job_url', ''),
                        width=400
                    ),
                ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO),
                width=450,
                height=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Create Application",
                    on_click=lambda e: self._create_application_from_job(dialog, job_app),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                )
            ],
            modal=True
        )
        
        # Store references to input fields
        dialog.company_field = dialog.content.content.controls[1]
        dialog.position_field = dialog.content.content.controls[2]
        dialog.location_field = dialog.content.content.controls[3]
        dialog.url_field = dialog.content.content.controls[4]
        
        # Close any existing dialog first
        if hasattr(self.page, 'dialog') and self.page.dialog:
            self.page.dialog.open = False
        
        # Add to overlay for visibility
        if not hasattr(self.page, 'overlay'):
            self.page.overlay = []
        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        
        # Verify dialog is open
        if not dialog.open:
            dialog.open = True
            self.page.update()
    
    def _create_application_from_job(self, dialog: ft.AlertDialog, job_app: dict):
        """Create application from saved job"""
        try:
            company = dialog.company_field.value.strip()
            position = dialog.position_field.value.strip()
            location = dialog.location_field.value.strip()
            job_url = dialog.url_field.value.strip()
            
            if not company or not position:
                self.show_error("Company and Position are required")
                return
            
            # Create application (position parameter doesn't exist, only job_title)
            app_id = ApplicationService.create_application(
                user_id=self.user_id,
                company_name=company,
                job_title=position,
                location=location if location else None,
                job_url=job_url if job_url else None,
                status='saved',
                notes=f"Converted from saved job search result"
            )
            
            if app_id:
                self._close_dialog(dialog)
                self.load_applications(self.selected_status_filter)
                self._refresh_stats()
                self.show_success("✅ Application created from saved job!")
            else:
                self.show_error("Failed to create application")
        except Exception as e:
            print(f"[ERROR] Error creating application from job: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error: {str(e)}")
    
    def show_success(self, message: str):
        """Show success snackbar"""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.GREEN_400)
        self.page.snack_bar.open = True
        self.page.update()

