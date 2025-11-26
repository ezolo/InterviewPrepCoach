"""Job listing card component"""

import flet as ft
from ui.styles.theme import AppTheme
from typing import Dict, Any, Callable

class JobCard:
    """Job listing card component"""
    
    @staticmethod
    def build(job: Dict[str, Any], on_save: Callable = None,
              on_view_details: Callable = None, on_show_details: Callable = None) -> ft.Container:
        """Build job card
        
        Args:
            job: Job data dict
            on_save: Callback when save button clicked
            on_view_details: Callback when "View Details" button clicked (opens job URL)
            on_show_details: Callback when card is clicked (shows details dialog)
            
        Returns:
            Job card container
        """
        company = job.get('company_name', job.get('employer_name', 'Unknown Company'))
        title = job.get('job_title', 'Unknown Position')
        location = job.get('location', job.get('job_city', 'Location not specified'))
        score = job.get('compatibility_score', 0)
        remote = job.get('job_is_remote', False) or job.get('remote_type') == 'Remote'
        
        # Score badge
        if score > 0:
            score_color = (AppTheme.SUCCESS if score >= 70
                          else AppTheme.WARNING if score >= 50
                          else AppTheme.ERROR)
            score_badge = ft.Container(
                content=ft.Text(f"{int(score)}%", size=14, weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=score_color,
                padding=8,
                border_radius=AppTheme.RADIUS_SMALL
            )
        else:
            score_badge = ft.Container()
        
        # Remote badge
        remote_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.HOME_WORK, size=14, color="white"),
                ft.Text("Remote", size=12, color="white")
            ], spacing=4),
            bgcolor=AppTheme.INFO,
            padding=6,
            border_radius=AppTheme.RADIUS_SMALL
        ) if remote else ft.Container()
        
        # Main content
        content = ft.Column([
            # Header row
            ft.Row([
                ft.Column([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(company, size=14, color="grey"),
                ], expand=True),
                score_badge
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Location and remote
            ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, size=16, color="grey"),
                ft.Text(location, size=12, color="grey"),
                remote_badge
            ], spacing=8),
            
            # Action buttons
            ft.Row([
                ft.TextButton("View Details", icon=ft.Icons.OPEN_IN_NEW,
                             on_click=lambda _: on_view_details(job) if on_view_details else None,
                             tooltip="Open job posting in browser"),
                ft.TextButton("Save JD", icon=ft.Icons.BOOKMARK_BORDER,
                             on_click=lambda _: on_save(job) if on_save else None,
                             tooltip="Save as Job Description"),
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=10)
        
        card = ft.Container(
            content=content,
            **AppTheme.card_style(),
            on_click=lambda _: on_show_details(job) if on_show_details else None,
            ink=True,
            tooltip="Click to view full job details"
        )
        
        return card

