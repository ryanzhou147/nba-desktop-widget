from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QTabWidget, QScrollArea,
                             QTableWidget, QHeaderView, QTableWidgetItem, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from services.theme_handler import ThemedWidget
from services.logo_handler import _load_logo_pixmap
from services.api_services import Game, GameUpdate

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
        
        # Load logo from disk on demand
        pixmap = _load_logo_pixmap(team_name, 60)
        if pixmap:
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