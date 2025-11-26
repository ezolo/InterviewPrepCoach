"""Navigation components"""

import flet as ft
from ui.styles.theme import AppTheme

class NavigationRailComponent:
    """Left navigation rail"""
    
    def __init__(self, on_destination_change):
        self.on_destination_change = on_destination_change
        self.selected_index = 0
        
    def build(self) -> ft.NavigationRail:
        """Build navigation rail"""
        return ft.NavigationRail(
            selected_index=self.selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ASSESSMENT_OUTLINED,
                    selected_icon=ft.Icons.ASSESSMENT,
                    label="Profile Analysis"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.QUIZ_OUTLINED,
                    selected_icon=ft.Icons.QUIZ,
                    label="Questions"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PLAY_CIRCLE_OUTLINED,
                    selected_icon=ft.Icons.PLAY_CIRCLE,
                    label="Practice"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.RECORD_VOICE_OVER_OUTLINED,
                    selected_icon=ft.Icons.RECORD_VOICE_OVER,
                    label="Mock Interview"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.WORK_OUTLINED,
                    selected_icon=ft.Icons.WORK,
                    label="Opportunities"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.EDIT_DOCUMENT,
                    selected_icon=ft.Icons.EDIT_DOCUMENT,
                    label="Writer"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
                    selected_icon=ft.Icons.CALENDAR_TODAY,
                    label="Planner"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PSYCHOLOGY_OUTLINED,
                    selected_icon=ft.Icons.PSYCHOLOGY,
                    label="Career Coach"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings"
                ),
            ],
            on_change=self.on_destination_change
        )

