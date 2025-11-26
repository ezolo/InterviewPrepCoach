"""Home dashboard view"""

import flet as ft
from ui.styles.theme import AppTheme
from services.practice_service import PracticeService
from services.application_service import ApplicationService
from core.auth import SessionManager

class HomeView:
    """Main dashboard view"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = SessionManager.get_user_id()
        
    def build(self) -> ft.Container:
        """Build home view"""
        # Get stats
        practice_stats = PracticeService.get_session_stats(self.user_id)
        app_stats = ApplicationService.get_application_stats(self.user_id)
        
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text("🎯 Interview Prep AI", size=36, weight=ft.FontWeight.BOLD),
                ft.Text("Your AI-powered career companion", size=16, color="grey")
            ], spacing=8),
            padding=AppTheme.PADDING_LARGE
        )
        
        # Stats cards
        stats_row = ft.Row([
            self._build_stat_card(
                "Practice Sessions",
                str(practice_stats.get('total_sessions', 0)),
                ft.Icons.PLAY_CIRCLE,
                AppTheme.PRIMARY
            ),
            self._build_stat_card(
                "Average Score",
                f"{practice_stats.get('average_score', 0)}%",
                ft.Icons.ASSESSMENT,
                AppTheme.SUCCESS
            ),
            self._build_stat_card(
                "Applications",
                str(app_stats.get('total', 0)),
                ft.Icons.WORK,
                AppTheme.INFO
            ),
            self._build_stat_card(
                "Interview Rate",
                f"{app_stats.get('interview_rate', 0)}%",
                ft.Icons.TRENDING_UP,
                AppTheme.SECONDARY
            ),
        ], spacing=16, wrap=True)
        
        # Feature cards
        features = ft.Column([
            ft.Text("Quick Actions", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                self._build_feature_card(
                    "Profile Analysis",
                    "Analyze resume & JD compatibility",
                    ft.Icons.ASSESSMENT,
                    lambda _: self.page.go("/profile_analysis")
                ),
                self._build_feature_card(
                    "Practice Interview",
                    "Practice with AI interviewer",
                    ft.Icons.PLAY_CIRCLE,
                    lambda _: self.page.go("/practice")
                ),
                self._build_feature_card(
                    "Find Jobs",
                    "Search & rank opportunities",
                    ft.Icons.WORK,
                    lambda _: self.page.go("/opportunities")
                ),
            ], spacing=16, wrap=True)
        ], spacing=16)
        
        # Main content
        content = ft.Column([
            header,
            ft.Divider(),
            stats_row,
            ft.Divider(),
            features
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(
            content=content,
            padding=AppTheme.PADDING_LARGE,
            expand=True
        )
    
    def _build_stat_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        """Build statistics card"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color=color),
                ft.Text(value, size=32, weight=ft.FontWeight.BOLD),
                ft.Text(title, size=14, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            **AppTheme.card_style(),
            width=250,
            height=150,
            alignment=ft.alignment.center
        )
    
    def _build_feature_card(self, title: str, description: str,
                           icon: str, on_click) -> ft.Container:
        """Build feature card"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=48, color=AppTheme.PRIMARY),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text(description, size=12, color="grey", text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            **AppTheme.card_style(),
            width=300,
            height=180,
            on_click=on_click,
            ink=True,
            alignment=ft.alignment.center
        )

