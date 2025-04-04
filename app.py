import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QScrollArea)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Theme constants
LIGHT_THEME = {
    "bg_color": "#FFFFFF",
    "main_bg": "#F5F5F5",
    "text_color": "#000000",
    "secondary_text": "#555555",
    "border_color": "#CCCCCC"
}

DARK_THEME = {
    "bg_color": "#2D2D2D",
    "main_bg": "#1E1E1E",
    "text_color": "#FFFFFF",
    "secondary_text": "#AAAAAA",
    "border_color": "#3A3A3A"
}

class DarkModeToggle(QPushButton):
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
        # In Stage 1, we'll just print the mode change
        print(f"Mode changed to {'Dark' if self.dark_mode else 'Light'}")

class GameCell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_mode = False
        self.init_ui()
        
    def init_ui(self):
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create a simple layout with placeholders
        layout = QHBoxLayout()
        
        # Left side (team logos and scores)
        left_layout = QVBoxLayout()
        
        # Home team row
        home_layout = QHBoxLayout()
        home_logo = QLabel("Logo")
        home_team = QLabel("Home Team")
        home_score = QLabel("--")
        home_layout.addWidget(home_logo)
        home_layout.addWidget(home_team)
        home_layout.addWidget(home_score)
        
        # Away team row
        away_layout = QHBoxLayout()
        away_logo = QLabel("Logo")
        away_team = QLabel("Away Team")
        away_score = QLabel("--")
        away_layout.addWidget(away_logo)
        away_layout.addWidget(away_team)
        away_layout.addWidget(away_score)
        
        left_layout.addLayout(home_layout)
        left_layout.addLayout(away_layout)
        
        # Right side (game status)
        right_layout = QVBoxLayout()
        status_label = QLabel("Game Time")
        status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(status_label)
        
        # Add layouts to main layout
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 1)
        main_layout.addLayout(layout)
        
        self.setStyleSheet("GameCell { border: 1px solid #CCCCCC; border-radius: 5px; background-color: #FFFFFF; }")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("NBA Desktop Widget")
        self.setMinimumSize(400, 600)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create header with title and dark mode toggle
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("NBA Games")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.dark_mode_toggle = DarkModeToggle(self)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.dark_mode_toggle)
        
        self.main_layout.addLayout(self.header_layout)
        
        # Create scrollable area for game cells
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Add some sample game cells for testing
        for i in range(10):
            row, col = i // 2, i % 2
            game_cell = GameCell()
            self.grid_layout.addWidget(game_cell, row, col)
        
        # Apply initial light theme
        self.apply_theme(False)
        
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        theme = DARK_THEME if is_dark_mode else LIGHT_THEME
        
        # Apply theme to main window
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {theme['main_bg']}; }}
            QScrollArea {{ background-color: {theme['main_bg']}; border: none; }}
            QWidget {{ background-color: {theme['main_bg']}; color: {theme['text_color']}; }}
            QLabel {{ color: {theme['text_color']}; }}
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())