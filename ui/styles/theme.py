"""Theme configuration for Flet UI"""

import flet as ft

class AppTheme:
    """Application theme and colors"""
    
    # Primary colors
    PRIMARY = "#1976D2"  # Blue
    PRIMARY_LIGHT = "#42A5F5"
    PRIMARY_DARK = "#1565C0"
    
    # Secondary colors
    SECONDARY = "#4CAF50"  # Green
    SECONDARY_LIGHT = "#81C784"
    SECONDARY_DARK = "#388E3C"
    
    # Status colors
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    ERROR = "#F44336"
    INFO = "#2196F3"
    
    # Neutral colors
    BG_LIGHT = "#FFFFFF"
    BG_DARK = "#121212"
    SURFACE_LIGHT = "#F5F5F5"
    SURFACE_DARK = "#1E1E1E"
    CARD_LIGHT = "#FFFFFF"
    CARD_DARK = "#2C2C2C"
    
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_LIGHT = "#FFFFFF"
    
    # Spacing
    PADDING_SMALL = 8
    PADDING_MEDIUM = 16
    PADDING_LARGE = 24
    
    # Border radius
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    
    @classmethod
    def get_theme(cls, dark_mode: bool = False):
        """Get Flet theme configuration
        
        Args:
            dark_mode: Whether to use dark theme
            
        Returns:
            Flet theme object
        """
        return ft.Theme(
            color_scheme_seed=cls.PRIMARY,
            use_material3=True
        )
    
    @classmethod
    def card_style(cls, dark_mode: bool = False):
        """Get card container style"""
        return {
            "bgcolor": cls.CARD_DARK if dark_mode else cls.CARD_LIGHT,
            "border_radius": cls.RADIUS_MEDIUM,
            "padding": cls.PADDING_MEDIUM,
            "border": ft.border.all(1, "#E0E0E0" if not dark_mode else "#404040")
        }
    
    @classmethod
    def button_style(cls, button_type: str = "primary"):
        """Get button style
        
        Args:
            button_type: primary, secondary, or outline
        """
        styles = {
            "primary": {
                "bgcolor": cls.PRIMARY,
                "color": cls.TEXT_LIGHT
            },
            "secondary": {
                "bgcolor": cls.SECONDARY,
                "color": cls.TEXT_LIGHT
            },
            "outline": {
                "bgcolor": "transparent",
                "color": cls.PRIMARY
            }
        }
        return styles.get(button_type, styles["primary"])

