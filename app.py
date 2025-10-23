import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QScrollArea, QStackedWidget)
from PyQt5.QtGui import QPixmap, QPixmapCache
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QEvent
from services.api_services import fetch_games_list, fetch_live_game_updates
from services.logo_handler import _preload_logos
from services.theme_handler import DarkModeToggle, DARK_THEME, LIGHT_THEME
from services.main_view_handler import GameCell
from services.detail_view_handler import GameDetailView


# MainWindow
# This is the top-level container class for the entire application. It:

# Creates the main UI layout with header and content area
# Manages navigation between the main view (list of games) and detail views
# Maintains a timer to update game data every 1 seconds
# Contains collections of game cells and detail views
# Handles the dark/light theme switching functionality
# Organizes the UI with QStackedWidget for page switching

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Preload available logos into memory for fast access
        _preload_logos()
        self.game_cells = {}
        self.game_detail_views = {}
        self.is_dark_mode = False
        self.init_ui()
        
        # Set up timer for auto-updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_games)
        self.update_timer.start(1000)  # Update every 1 second
        
        # Initial update
        self.update_games()
        QTimer.singleShot(100, self.fix_layout_with_navigation)

    def fix_layout_with_navigation(self):
        # Get the first game ID if any exist
        games = fetch_games_list()
        if games:
            # Simulate clicking the first game
            first_game_id = games[0].game_id
            self.cell_clicked(first_game_id)
            
            # Then go back to main view after a very short delay
            QTimer.singleShot(50, self.show_main_view)
            
    def init_ui(self):
        self.setWindowTitle("NBA Desktop Widget")
        self.setMinimumSize(450, 600)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create header with title and dark mode toggle
        self.header_layout = QHBoxLayout()
        
        # Create a stack for the left side of header (title or back button)
       # Create a stack for the left side of header (title or back button)
        self.header_left_stack = QStackedWidget()
        
        # Title for main view - keep original positioning
        self.title_widget = QWidget()
        title_layout = QHBoxLayout(self.title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("NBA Games")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_layout.addWidget(self.title_label)
        
        # Back button for detail view - aligned far left
        self.back_widget = QWidget()
        back_layout = QHBoxLayout(self.back_widget)
        # Remove all margins to align with window edge
        back_layout.setContentsMargins(0, 0, 0, 0)
        self.back_button = QPushButton("← Back")
        self.back_button.setFixedWidth(80)
        self.back_button.clicked.connect(self.show_main_view)
        back_layout.addWidget(self.back_button)
        back_layout.addStretch()  # Push everything to the left
        
        # Add both to stack
        self.header_left_stack.addWidget(self.title_widget)
        self.header_left_stack.addWidget(self.back_widget)
        self.header_left_stack.setCurrentWidget(self.title_widget)
        
        # Dark mode toggle remains the same
        self.dark_mode_toggle = DarkModeToggle(self)
        self.dark_mode_toggle.theme_changed.connect(self.apply_theme)
        
        # Add to header layout
        self.header_layout.addWidget(self.header_left_stack, 1)
        self.header_layout.addWidget(self.dark_mode_toggle)
        
        # Adjust main layout to position back button at edge
        original_margins = self.main_layout.contentsMargins()
        self.main_layout.addLayout(self.header_layout)
        
        # Create stacked widget for main content views
        self.stacked_widget = QStackedWidget()
        
        # Rest of the code remains the same...
        
        # Create main view with grid layout
        self.main_view = QWidget()
        
        # Create main view with grid layout
        self.main_view = QWidget()
        self.main_view_layout = QVBoxLayout(self.main_view)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.main_view_layout.addWidget(self.scroll_area)
        
        self.stacked_widget.addWidget(self.main_view)
        self.main_layout.addWidget(self.stacked_widget)
        
        # Apply initial theme
        self.apply_theme(False)
        
    def update_games(self):
        try:
            # Fetch games list
            games = fetch_games_list()
            
            # Get current game IDs for comparison
            current_game_ids = [game.game_id for game in games]
            
            # Remove widgets from grid first
            self._clear_grid_layout()
            
            # Add or update game cells
            for i, game in enumerate(games):
                row, col = i // 2, i % 2
                
                if game.game_id not in self.game_cells:
                    # Create new game cell and detail view
                    self._create_game_widgets(game)
                
                # Add to layout and update
                cell = self.game_cells[game.game_id]
                self.grid_layout.addWidget(cell, row, col)
                
                # Apply theme and update state
                self._update_game_cell(game.game_id)
            
            # Clean up cells that are no longer needed
            self._remove_stale_games(current_game_ids)
            
                
        except Exception as e:
            print(f"Error in update_games: {e}")
    
    def _clear_grid_layout(self):
        """Remove all widgets from grid layout without deleting them"""
        for i in reversed(range(self.grid_layout.count())):
            widget_item = self.grid_layout.itemAt(i)
            if widget_item and widget_item.widget():
                self.grid_layout.removeWidget(widget_item.widget())
    
    def _create_game_widgets(self, game):
        """Create new game cell and detail view for a game"""
        # Create cell
        game_cell = GameCell(game)
        game_cell.clicked_signal.connect(self.cell_clicked)
        self.game_cells[game.game_id] = game_cell
        
        # Create detail view
        # detail_view = GameDetailView(game)
        # detail_view.back_signal.connect(self.show_main_view)
        # self.game_detail_views[game.game_id] = detail_view
        # self.stacked_widget.addWidget(detail_view)
    
    def _update_game_cell(self, game_id):
        """Apply theme and update game status for a cell"""
        if game_id not in self.game_cells:
            return
            
        cell = self.game_cells[game_id]
        detail_view = self.game_detail_views.get(game_id)
        
        # Apply theme
        cell.apply_theme(self.is_dark_mode)
        if detail_view:
            detail_view.apply_theme(self.is_dark_mode)
        
        # Update game status
        try:
            game_update = fetch_live_game_updates(game_id)
            if game_update:
                cell.update_game_status(game_update)
                if detail_view:
                    detail_view.update_game_status(game_update)
            else:
                cell.update_game_status(None)
        except Exception as e:
            print(f"Error updating game {game_id}: {e}")
            cell.update_game_status(None)
    
    def _remove_stale_games(self, current_game_ids):
        """Remove games that are no longer in the current list"""
        for game_id in list(self.game_cells.keys()):
            if game_id not in current_game_ids:
                if game_id in self.game_detail_views:
                    detail_view = self.game_detail_views.pop(game_id)
                    self.stacked_widget.removeWidget(detail_view)
                    detail_view.deleteLater()
                
                # Only delete cell if it's not on screen
                if self.stacked_widget.currentWidget() == self.main_view:
                    cell = self.game_cells.pop(game_id)
                    cell.deleteLater()
        
    def cell_clicked(self, game_id):
        # Create detail view only when needed
        if game_id not in self.game_detail_views:
            # Find the game object
            for game in fetch_games_list():
                if game.game_id == game_id:
                    # Create the detail view
                    detail_view = GameDetailView(game)
                    detail_view.back_signal.connect(self.show_main_view)
                    detail_view.apply_theme(self.is_dark_mode)
                    self.game_detail_views[game_id] = detail_view
                    self.stacked_widget.addWidget(detail_view)
                    break
        
        # Show the detail view
        detail_view = self.game_detail_views.get(game_id)
        if detail_view:
            self.stacked_widget.setCurrentWidget(detail_view)
            # Switch header to back button
            self.header_left_stack.setCurrentWidget(self.back_widget)
            self._update_game_cell(game_id)
    
    def show_main_view(self):
        self.stacked_widget.setCurrentWidget(self.main_view)
        # Switch header back to title
        self.header_left_stack.setCurrentWidget(self.title_widget)
    
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        theme = DARK_THEME if is_dark_mode else LIGHT_THEME
        
        # Apply theme to all game cells and detail views
        for game_id in self.game_cells:
            self._update_game_cell(game_id)
            
        # Apply theme to main window and header elements
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