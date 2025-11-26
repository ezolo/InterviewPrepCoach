"""Score card component for displaying compatibility scores"""

import flet as ft
from ui.styles.theme import AppTheme

class ScoreCard:
    """Visual score card component"""
    
    @staticmethod
    def build(score: float, title: str = "Compatibility Score",
              show_details: bool = True) -> ft.Container:
        """Build score card
        
        Args:
            score: Score value (0-100)
            title: Title text
            show_details: Whether to show detailed rating
            
        Returns:
            Score card container
        """
        # Determine color based on score
        if score >= 80:
            color = AppTheme.SUCCESS
            rating = "Excellent Match"
        elif score >= 60:
            color = AppTheme.INFO
            rating = "Good Match"
        elif score >= 40:
            color = AppTheme.WARNING
            rating = "Fair Match"
        else:
            color = AppTheme.ERROR
            rating = "Needs Improvement"
        
        # Build progress ring
        progress_ring = ft.Container(
            content=ft.Stack([
                ft.ProgressRing(
                    value=score / 100,
                    width=120,
                    height=120,
                    stroke_width=10,
                    color=color
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"{int(score)}%",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            rating if show_details else "",
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                            color="grey"
                        ) if show_details else ft.Container()
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=120,
                    height=120,
                    alignment=ft.alignment.center
                )
            ]),
            width=120,
            height=120
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                progress_ring
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            **AppTheme.card_style(),
            alignment=ft.alignment.center
        )

