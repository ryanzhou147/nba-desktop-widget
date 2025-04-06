import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QScrollArea, QFrame)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

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

# Data Models
class Game:
    def __init__(self, game_id, home_team, away_team, game_time):
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        self.game_time = game_time

class Player:
    def __init__(self, player_name, minutes_played, points, rebounds, assists):
        self.player_name = player_name
        self.minutes_played = minutes_played
        self.points = points
        self.rebounds = rebounds
        self.assists = assists

class GameUpdate:
    def __init__(self, game_id, status, period, clock, home_score, away_score, 
                 home_players, away_players, recent_plays, best_overall_player):
        self.game_id = game_id
        self.status = status
        self.period = period
        self.clock = clock
        self.home_score = home_score
        self.away_score = away_score
        self.home_players = home_players or []
        self.away_players = away_players or []
        self.recent_plays = recent_plays or []
        self.best_overall_player = best_overall_player or ""

# Mock API functions
def fetch_games_list():
    # In a real app, this would make an API call
    # For now, return mock data
    return [
        Game("1", "Lakers", "Celtics", "7:30 PM"),
        Game("2", "Warriors", "Nets", "8:00 PM"),
        Game("3", "Bulls", "Heat", "6:30 PM"),
        Game("4", "Suns", "Bucks", "7:00 PM"),
    ]

def fetch_live_game_updates(game_id):
    # Mock data based on game_id
    if game_id == "1":
        return GameUpdate(
            game_id="1",
            status="In Progress",
            period=2,
            clock="5:32",
            home_score=54,
            away_score=48,
            home_players=[],
            away_players=[],
            recent_plays=[],
            best_overall_player="LeBron James: 18 PTS, 6 REB, 5 AST"
        )
    elif game_id == "2":
        return GameUpdate(
            game_id="2",
            status="Not Started",
            period=0,
            clock="00:00",
            home_score=0,
            away_score=0,
            home_players=[],
            away_players=[],
            recent_plays=[],
            best_overall_player=""
        )
    elif game_id == "3":
        return GameUpdate(
            game_id="3",
            status="Final",
            period=4,
            clock="00:00",
            home_score=104,
            away_score=98,
            home_players=[],
            away_players=[],
            recent_plays=[],
            best_overall_player="Jimmy Butler: 32 PTS, 10 REB, 8 AST"
        )
    else:
        return GameUpdate(
            game_id="4",
            status="1st Quarter",
            period=1,
            clock="9:45",
            home_score=12,
            away_score=8,
            home_players=[],
            away_players=[],
            recent_plays=[],
            best_overall_player="Devin Booker: 6 PTS, 1 REB, 2 AST"
        )

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

class GameCell(QWidget):
    def __init__(self, game, parent=None):
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
        
        # Home team layout
        home_layout = QHBoxLayout()
        self.home_logo = QLabel()
        logo_path = f"nba-logos/{self.game.home_team}.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio)
            self.home_logo.setPixmap(pixmap)
        else:
            self.home_logo.setText(self.game.home_team)
        self.home_logo.setFixedSize(40, 40)
        
        self.home_score = QLabel("--")
        self.home_score.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        home_layout.addWidget(self.home_logo)
        home_layout.addWidget(self.home_score)
        
        # Away team layout
        away_layout = QHBoxLayout()
        self.away_logo = QLabel()
        logo_path = f"nba-logos/{self.game.away_team}.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio)
            self.away_logo.setPixmap(pixmap)
        else:
            self.away_logo.setText(self.game.away_team)
        self.away_logo.setFixedSize(40, 40)
        
        self.away_score = QLabel("--")
        self.away_score.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        away_layout.addWidget(self.away_logo)
        away_layout.addWidget(self.away_score)
        
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
        
    def update_game_status(self, game_update):
        if not game_update:
            self.status_label.setText(self.game.game_time)
            return
        
        self.home_score.setText(str(game_update.home_score))
        self.away_score.setText(str(game_update.away_score))
        
        if "Final" in game_update.status:
            self.status_label.setText(f"{game_update.status}")
            self.player_stats.setText(f"{game_update.best_overall_player}")
        elif "Not Started" in game_update.status or "PM" in game_update.status:
            self.status_label.setText(f"{self.game.game_time}")
        else:
            self.status_label.setText(f"Q{game_update.period} - {game_update.clock}")
            self.player_stats.setText(f"{game_update.best_overall_player}")
    
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        theme = DARK_THEME if is_dark_mode else LIGHT_THEME
        
        self.frame.setStyleSheet(f"QFrame {{ background-color: {theme['bg_color']}; border-radius: 10px; }}")
        self.home_score.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; font-weight: bold; font-size: 16px; }}")
        self.away_score.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; font-weight: bold; font-size: 16px; }}")
        self.status_label.setStyleSheet(f"QLabel {{ color: {theme['text_color']}; }}")
        self.player_stats.setStyleSheet(f"QLabel {{ color: {theme['secondary_text']}; font-size: 10px; }}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_cells = {}
        self.is_dark_mode = False
        self.init_ui()
        
        # Set up timer for auto-updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_games)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        self.update_games()
        
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
        self.dark_mode_toggle.theme_changed.connect(self.apply_theme)
        
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
        
        # Apply initial light theme
        self.apply_theme(False)
        
    def update_games(self):
        try:
            # Fetch games list
            games = fetch_games_list()
            
            # Remove widgets from grid first
            self._clear_grid_layout()
            
            # Add or update game cells
            for i, game in enumerate(games):
                row, col = i // 2, i % 2
                
                if game.game_id not in self.game_cells:
                    # Create new game cell
                    game_cell = GameCell(game)
                    self.game_cells[game.game_id] = game_cell
                
                # Add to layout and update
                cell = self.game_cells[game.game_id]
                self.grid_layout.addWidget(cell, row, col)
                
                # Apply theme and update state
                cell.apply_theme(self.is_dark_mode)
                
                # Update game status
                try:
                    game_update = fetch_live_game_updates(game.game_id)
                    if game_update:
                        cell.update_game_status(game_update)
                    else:
                        cell.update_game_status(None)
                except Exception as e:
                    print(f"Error updating game {game.game_id}: {e}")
                    cell.update_game_status(None)
                
        except Exception as e:
            print(f"Error in update_games: {e}")
    
    def _clear_grid_layout(self):
        """Remove all widgets from grid layout without deleting them"""
        for i in reversed(range(self.grid_layout.count())):
            widget_item = self.grid_layout.itemAt(i)
            if widget_item and widget_item.widget():
                self.grid_layout.removeWidget(widget_item.widget())
    
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        theme = DARK_THEME if is_dark_mode else LIGHT_THEME
        
        # Apply theme to all game cells
        for game_id, cell in self.game_cells.items():
            cell.apply_theme(is_dark_mode)
            
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