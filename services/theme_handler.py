from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal
# Theme constants
LIGHT_THEME = {
    "bg_color": "#FFFFFF",
    "main_bg": "#F5F5F5",
    "text_color": "#000000",
    "secondary_text": "#555555",
    "border_color": "#CCCCCC",
    "tab_bg": "#F0F0F0",
    "tab_selected_bg": "#FFFFFF",
    "tab_text": "#555555"
}

DARK_THEME = {
    "bg_color": "#2D2D2D",
    "main_bg": "#1E1E1E",
    "text_color": "#FFFFFF",
    "secondary_text": "#AAAAAA",
    "border_color": "#3A3A3A",
    "tab_bg": "#2D2D2D",
    "tab_selected_bg": "#3A3A3A",
    "tab_text": "#AAAAAA"
}

# DarkModeToggle
# A specialized button widget that:

# Handles theme switching between dark and light modes
# Emits signals when the theme changes
# Toggles its text between "Dark Mode" and "Light Mode"

class DarkModeToggle(QPushButton):
    theme_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText("Dark Mode")
        self.clicked.connect(self.toggle_mode)
        self.dark_mode = False
        self.setFixedSize(100, 30)
        
    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.setText("Light Mode" if self.dark_mode else "Dark Mode")
        self.theme_changed.emit(self.dark_mode)

# ThemedWidget
# A mixin class (not instantiated directly) that:

# Provides shared functionality for theme application
# Defines a common interface for themed components
# Contains methods for applying specific theme properties
# Uses the DARK_THEME and LIGHT_THEME constants

class ThemedWidget:
    """Mixin for theming widgets"""
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        theme = DARK_THEME if is_dark_mode else LIGHT_THEME
        self._apply_specific_theme(theme)
    
    def _apply_specific_theme(self, theme):
        # To be overridden by child classes
        pass