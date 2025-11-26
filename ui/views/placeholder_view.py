"""Placeholder view for features under development"""

import flet as ft
from ui.styles.theme import AppTheme

class PlaceholderView:
    """Placeholder view for features under development"""
    
    def __init__(self, page: ft.Page, feature_name: str, description: str, icon: str):
        self.page = page
        self.feature_name = feature_name
        self.description = description
        self.icon = icon
        
    def build(self) -> ft.Container:
        """Build placeholder view"""
        content = ft.Column([
            ft.Icon(self.icon, size=100, color=AppTheme.PRIMARY),
            ft.Text(f"🚧 {self.feature_name}", size=32, weight=ft.FontWeight.BOLD),
            ft.Text(self.description, size=16, color="grey", text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Text("This feature is coming soon!", size=14, color="grey"),
            ft.ElevatedButton(
                "Go Back to Home",
                icon=ft.Icons.HOME,
                on_click=lambda _: self.page.go("/"),
                style=ft.ButtonStyle(bgcolor=AppTheme.PRIMARY, color="white")
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20)
        
        return ft.Container(
            content=content,
            padding=AppTheme.PADDING_LARGE,
            alignment=ft.alignment.center,
            expand=True
        )

