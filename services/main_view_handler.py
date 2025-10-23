from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from services.theme_handler import ThemedWidget
from services.logo_handler import _load_logo_pixmap
from services.api_services import Game, GameUpdate

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
        
        # Load logo from disk on demand
        pixmap = _load_logo_pixmap(team_name, 40)
        if pixmap:
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
