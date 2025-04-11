import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QTabWidget, QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSizePolicy, QFrame, QStackedWidget)
from PyQt5.QtGui import QPixmap, QPixmapCache
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QEvent
from apiServices import fetch_games_list, fetch_live_game_updates, Game, GameUpdate

_logo_cache = {}

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

# GameCell
# Represents a single game card in the main view. It:

# Displays basic game information (teams, logos, scores)
# Shows game status and basic player stats
# Handles click events to navigate to detail view
# Updates dynamically as game data changes
# Applies theming to all its components
# Has a fixed height for consistent UI

class GameCell(QWidget, ThemedWidget):
    clicked_signal = pyqtSignal(str)
    
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self.game_id = game.game_id
        self.is_dark_mode = False
        self.init_ui()
        
    def init_ui(self):
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
        
        # Create frame for better visual separation
        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.frame)
        
        # Frame layout
        layout = QHBoxLayout(self.frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side (team logos and scores)
        left_layout = QVBoxLayout()
        
        # Team layouts
        self.home_logo, self.home_score, home_layout = self._create_team_layout(self.game.home_team)
        self.away_logo, self.away_score, away_layout = self._create_team_layout(self.game.away_team)
        
        left_layout.addLayout(home_layout)
        left_layout.addLayout(away_layout)
        
        # Right side (game status)
        right_layout = QVBoxLayout()
        self.status_label = QLabel(self.game.game_time)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.player_stats = QLabel("")
        self.player_stats.setAlignment(Qt.AlignCenter)
        self.player_stats.setWordWrap(True)
        
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.player_stats)
        
        # Add layouts to main layout
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 1)
        
        self.setFixedHeight(120)
        self.setStyleSheet("GameCell { border-radius: 10px; }")

    def _create_team_layout(self, team_name):
        layout = QHBoxLayout()
        
        logo = QLabel()
        logo.setFixedSize(40, 40)
        
        # Try to get logo from cache first
        if team_name in _logo_cache:
            logo.setPixmap(_logo_cache[team_name])
        else:
            logo_path = f"nba-logos/{team_name}.png"
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Store in cache for future use
                _logo_cache[team_name] = pixmap
                logo.setPixmap(pixmap)
            else:
                logo.setText(team_name)
        
        score = QLabel("--")
        score.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(logo)
        layout.addWidget(score)
        
        return logo, score, layout
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked_signal.emit(self.game_id)
        super().mousePressEvent(event)
    
    def update_game_status(self, game_update: GameUpdate = None):
        if not game_update:
            self.status_label.setText(self.game.game_time)
            return
        
        self.home_score.setText(str(game_update.home_score))
        self.away_score.setText(str(game_update.away_score))
        
        match game_update.status:
            case status if "Final" in status:
                self.status_label.setText(f"{game_update.status}")
                self.player_stats.setText(f"{game_update.best_overall_player}")
            case status if "Not Started" in status or "PM" in status or "AM" in status:
                self.status_label.setText(f"{self.game.game_time}")
            case _:
                # For cases not handled above, check the period and clock
                match (game_update.period, game_update.clock):
                    case (2, "00:00"):
                        self.status_label.setText("Halftime")
                        self.player_stats.setText(f"{game_update.best_overall_player}")
                    case _:
                        if game_update.period <= 4: self.status_label.setText(f"Q{game_update.period} - {game_update.clock}") 
                        elif game_update.period == 5: self.status_label.setText(f"OT - {game_update.clock}")
                        else: self.status_label.setText(f"{game_update.period - 4}OT - {game_update.clock}")
                        self.player_stats.setText(f"{game_update.best_overall_player}")
                    
    def _apply_specific_theme(self, theme):
        self.frame.setStyleSheet(f"QFrame {{ background-color: {theme['bg_color']}; border-radius: 10px; }}")
        self.home_score.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; font-weight: bold; font-size: 16px; }}")
        self.away_score.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; font-weight: bold; font-size: 16px; }}")
        self.status_label.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; }}")
        self.player_stats.setStyleSheet(f"QLabel {{ color: {theme['secondary_text']}; font-size: 10px; }}")

# GameDetailView
# The expanded view for a single game when selected. It:

# Shows detailed information about one specific game
# Contains a tabbed interface with "Feed" and "Box Score" sections
# Displays team logos, names, scores, and game status
# Shows live game updates and recent plays
# Presents player statistics in table format
# Has a back button to return to the main view

class GameDetailView(QWidget, ThemedWidget):
    back_signal = pyqtSignal()
    
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self.game_id = game.game_id
        self.game_update = None
        self.is_dark_mode = False
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setFixedWidth(80)
        self.back_button.clicked.connect(self.back_signal.emit)
        
        # Team layouts
        self.home_logo, self.home_team_name, self.home_score, home_layout = self._create_header_team_layout(self.game.home_team)
        self.away_logo, self.away_team_name, self.away_score, away_layout = self._create_header_team_layout(self.game.away_team)
        
        # Game status
        status_layout = QVBoxLayout()
        self.status_label = QLabel(self.game.game_time)
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        header_layout.addLayout(home_layout)
        header_layout.addLayout(status_layout)
        header_layout.addLayout(away_layout)
        
        main_layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Feed tab
        self.feed_tab = self._create_feed_tab()
        
        # Box score tab
        self.box_score_tab = self._create_box_score_tab()
        
        # Add tabs
        self.tab_widget.addTab(self.feed_tab, "Feed")
        self.tab_widget.addTab(self.box_score_tab, "Box Score")
        
        main_layout.addWidget(self.tab_widget)
        
    def _create_header_team_layout(self, team_name):
        layout = QHBoxLayout()
        
        logo = QLabel()
        logo.setFixedSize(60, 60)
        
        # Try to get logo from cache first (at a different size)
        cache_key = f"{team_name}_large"
        if cache_key in _logo_cache:
            logo.setPixmap(_logo_cache[cache_key])
        else:
            logo_path = f"nba-logos/{team_name}.png"
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Store in cache for future use
                _logo_cache[cache_key] = pixmap
                logo.setPixmap(pixmap)
            else:
                logo.setText(team_name)
        
        name = QLabel(team_name)
        score = QLabel("--")
        score.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        layout.addWidget(logo)
        layout.addWidget(name)
        layout.addWidget(score)
        
        return logo, name, score, layout
    
    def _create_feed_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.feed_layout = QVBoxLayout(content)
        self.feed_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(content)
        
        layout.addWidget(scroll)
        return tab
    
    def _create_box_score_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Home team box score
        self.home_box_score_label = QLabel(f"{self.game.home_team} Players")
        self.home_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.home_box_score = self._create_box_score_table()
        
        # Away team box score
        self.away_box_score_label = QLabel(f"{self.game.away_team} Players")
        self.away_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.away_box_score = self._create_box_score_table()
        
        layout.addWidget(self.home_box_score_label)
        layout.addWidget(self.home_box_score)
        layout.addWidget(self.away_box_score_label)
        layout.addWidget(self.away_box_score)
        
        return tab
    
    def _create_box_score_table(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Player", "MIN", "PTS", "REB", "AST"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        return table
    
    def update_game_status(self, game_update: GameUpdate):
        if not game_update:
            return
            
        self.game_update = game_update
        self.home_score.setText(str(game_update.home_score))
        self.away_score.setText(str(game_update.away_score))
        
        if "Final" in game_update.status:
            self.status_label.setText(f"{game_update.status}")
        elif "PM" in game_update.status or "AM" in game_update.status:
            self.status_label.setText(f"{self.game.game_time}")
        else:
            self.status_label.setText(f"Q{game_update.period} - {game_update.clock}")
            
        # Update feed tab
        self.update_feed(game_update.recent_plays)
        
        # Update box score tab
        self.update_box_score(game_update.home_players, game_update.away_players)
    
    def update_feed(self, recent_plays):
        # Clear existing items
        while self.feed_layout.count():
            child = self.feed_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new items
        for play in recent_plays:
            play_label = QLabel(play)
            play_label.setWordWrap(True)
            play_label.setStyleSheet(f"padding: 5px; border-bottom: 1px solid {DARK_THEME['border_color'] if self.is_dark_mode else LIGHT_THEME['border_color']};")
            self.feed_layout.addWidget(play_label)
    
    def update_box_score(self, home_players, away_players):
        def update_table(table, players):
            table.setRowCount(len(players))
            for i, player in enumerate(players):
                table.setItem(i, 0, QTableWidgetItem(player.player_name))
                table.setItem(i, 1, QTableWidgetItem(str(player.minutes_played)))
                table.setItem(i, 2, QTableWidgetItem(str(player.points)))
                table.setItem(i, 3, QTableWidgetItem(str(player.rebounds)))
                table.setItem(i, 4, QTableWidgetItem(str(player.assists)))
                
        update_table(self.home_box_score, home_players)
        update_table(self.away_box_score, away_players)
            
    def _apply_specific_theme(self, theme):
        self.setStyleSheet(f"background-color: {theme['main_bg']}; color: {theme['text_color']};")
        self.home_score.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {theme['text_color']};")
        self.away_score.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {theme['text_color']};")
        self.home_team_name.setStyleSheet(f"color: {theme['text_color']};")
        self.away_team_name.setStyleSheet(f"color: {theme['text_color']};")
        self.status_label.setStyleSheet(f"color: {theme['text_color']};")
        self.home_box_score_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme['text_color']};")
        self.away_box_score_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme['text_color']};")
        
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme['border_color']}; }}
            QTabBar::tab {{ background-color: {theme['tab_bg']}; color: {theme['tab_text']}; padding: 8px 12px; }}
            QTabBar::tab:selected {{ background-color: {theme['tab_selected_bg']}; color: {theme['text_color']}; }}
        """)
        
        self.home_box_score.setStyleSheet(f"QTableWidget {{ background-color: {theme['bg_color']}; color: {theme['text_color']}; }}")
        self.away_box_score.setStyleSheet(f"QTableWidget {{ background-color: {theme['bg_color']}; color: {theme['text_color']}; }}")
        self.back_button.setStyleSheet(f"QPushButton {{ background-color: {theme['tab_bg']}; color: {theme['text_color']}; }}")
        
        # Update feed labels
        for i in range(self.feed_layout.count()):
            widget = self.feed_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet(f"padding: 5px; border-bottom: 1px solid {theme['border_color']}; color: {theme['text_color']};")

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
        self.setMinimumSize(400, 600)
        
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