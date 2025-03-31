import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QTabWidget, QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSizePolicy, QFrame, QStackedWidget)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QEvent
import time
from apiServices import fetch_games_list, fetch_live_game_updates, Game, GameUpdate

class DarkModeToggle(QPushButton):
    theme_changed = pyqtSignal(bool)  # Create a signal to emit when theme changes
    
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
        
        self.dark_mode_toggle = DarkModeToggle(self)
        self.dark_mode_toggle.theme_changed.connect(self.apply_theme)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked_signal.emit(self.game_id)
        super().mousePressEvent(event)
    
    def update_game_status(self, game_update: GameUpdate = None):
        if game_update:
            self.home_score.setText(str(game_update.home_score))
            self.away_score.setText(str(game_update.away_score))
            
            if "Final" in game_update.status:
                self.status_label.setText(f"{game_update.status}")
            elif "PM" in game_update.status or "AM" in game_update.status:
                self.status_label.setText(f"{self.game.game_time}")
            else:
                self.status_label.setText(f"Q{game_update.period} - {game_update.clock}")
                self.player_stats.setText(f"Best: {game_update.best_overall_player}")
        else:
            self.status_label.setText(self.game.game_time)
            
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        if is_dark_mode:
            self.frame.setStyleSheet("QFrame { background-color: #2D2D2D; border-radius: 10px; }")
            self.home_score.setStyleSheet("QLabel { color: #FFFFFF; font-weight: bold; font-size: 16px; }")
            self.away_score.setStyleSheet("QLabel { color: #FFFFFF; font-weight: bold; font-size: 16px; }")
            self.status_label.setStyleSheet("QLabel { color: #FFFFFF; }")
            self.player_stats.setStyleSheet("QLabel { color: #AAAAAA; font-size: 10px; }")
        else:
            self.frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 10px; }")
            self.home_score.setStyleSheet("QLabel { color: #000000; font-weight: bold; font-size: 16px; }")
            self.away_score.setStyleSheet("QLabel { color: #000000; font-weight: bold; font-size: 16px; }")
            self.status_label.setStyleSheet("QLabel { color: #000000; }")
            self.player_stats.setStyleSheet("QLabel { color: #555555; font-size: 10px; }")

class GameDetailView(QWidget):
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
        
        # Home team
        home_layout = QHBoxLayout()
        self.home_logo = QLabel()
        logo_path = f"nba-logos/{self.game.home_team}.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio)
            self.home_logo.setPixmap(pixmap)
        else:
            self.home_logo.setText(self.game.home_team)
        self.home_logo.setFixedSize(60, 60)
        
        self.home_team_name = QLabel(self.game.home_team)
        self.home_score = QLabel("--")
        self.home_score.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        home_layout.addWidget(self.home_logo)
        home_layout.addWidget(self.home_team_name)
        home_layout.addWidget(self.home_score)
        
        # Game status
        status_layout = QVBoxLayout()
        self.status_label = QLabel(self.game.game_time)
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # Away team
        away_layout = QHBoxLayout()
        self.away_logo = QLabel()
        logo_path = f"nba-logos/{self.game.away_team}.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio)
            self.away_logo.setPixmap(pixmap)
        else:
            self.away_logo.setText(self.game.away_team)
        self.away_logo.setFixedSize(60, 60)
        
        self.away_team_name = QLabel(self.game.away_team)
        self.away_score = QLabel("--")
        self.away_score.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        away_layout.addWidget(self.away_logo)
        away_layout.addWidget(self.away_team_name)
        away_layout.addWidget(self.away_score)
        
        header_layout.addWidget(self.back_button)
        header_layout.addLayout(home_layout)
        header_layout.addLayout(status_layout)
        header_layout.addLayout(away_layout)
        
        main_layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Feed tab
        self.feed_tab = QWidget()
        feed_layout = QVBoxLayout(self.feed_tab)
        
        self.feed_scroll = QScrollArea()
        self.feed_scroll.setWidgetResizable(True)
        self.feed_content = QWidget()
        self.feed_layout = QVBoxLayout(self.feed_content)
        self.feed_layout.setAlignment(Qt.AlignTop)
        self.feed_scroll.setWidget(self.feed_content)
        
        feed_layout.addWidget(self.feed_scroll)
        
        # Box score tab
        self.box_score_tab = QWidget()
        box_score_layout = QVBoxLayout(self.box_score_tab)
        
        # Home team box score
        self.home_box_score_label = QLabel(f"{self.game.home_team} Players")
        self.home_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.home_box_score = QTableWidget()
        self.home_box_score.setColumnCount(5)
        self.home_box_score.setHorizontalHeaderLabels(["Player", "MIN", "PTS", "REB", "AST"])
        self.home_box_score.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.home_box_score.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.home_box_score.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.home_box_score.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.home_box_score.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.home_box_score.verticalHeader().setVisible(False)
        
        # Away team box score
        self.away_box_score_label = QLabel(f"{self.game.away_team} Players")
        self.away_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.away_box_score = QTableWidget()
        self.away_box_score.setColumnCount(5)
        self.away_box_score.setHorizontalHeaderLabels(["Player", "MIN", "PTS", "REB", "AST"])
        self.away_box_score.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.away_box_score.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.away_box_score.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.away_box_score.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.away_box_score.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.away_box_score.verticalHeader().setVisible(False)
        
        box_score_layout.addWidget(self.home_box_score_label)
        box_score_layout.addWidget(self.home_box_score)
        box_score_layout.addWidget(self.away_box_score_label)
        box_score_layout.addWidget(self.away_box_score)
        
        # Add tabs
        self.tab_widget.addTab(self.feed_tab, "Feed")
        self.tab_widget.addTab(self.box_score_tab, "Box Score")
        
        main_layout.addWidget(self.tab_widget)
        
    def update_game_status(self, game_update: GameUpdate):
        if game_update:
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
            play_label.setStyleSheet("padding: 5px; border-bottom: 1px solid #CCCCCC;")
            self.feed_layout.addWidget(play_label)
    
    def update_box_score(self, home_players, away_players):
        # Update home team box score
        self.home_box_score.setRowCount(len(home_players))
        for i, player in enumerate(home_players):
            self.home_box_score.setItem(i, 0, QTableWidgetItem(player.player_name))
            self.home_box_score.setItem(i, 1, QTableWidgetItem(str(player.minutes_played)))
            self.home_box_score.setItem(i, 2, QTableWidgetItem(str(player.points)))
            self.home_box_score.setItem(i, 3, QTableWidgetItem(str(player.rebounds)))
            self.home_box_score.setItem(i, 4, QTableWidgetItem(str(player.assists)))
        
        # Update away team box score
        self.away_box_score.setRowCount(len(away_players))
        for i, player in enumerate(away_players):
            self.away_box_score.setItem(i, 0, QTableWidgetItem(player.player_name))
            self.away_box_score.setItem(i, 1, QTableWidgetItem(str(player.minutes_played)))
            self.away_box_score.setItem(i, 2, QTableWidgetItem(str(player.points)))
            self.away_box_score.setItem(i, 3, QTableWidgetItem(str(player.rebounds)))
            self.away_box_score.setItem(i, 4, QTableWidgetItem(str(player.assists)))
            
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        if is_dark_mode:
            self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
            self.home_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
            self.away_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
            self.home_team_name.setStyleSheet("color: #FFFFFF;")
            self.away_team_name.setStyleSheet("color: #FFFFFF;")
            self.status_label.setStyleSheet("color: #FFFFFF;")
            self.home_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
            self.away_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
            self.tab_widget.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #3A3A3A; }
                QTabBar::tab { background-color: #2D2D2D; color: #AAAAAA; padding: 8px 12px; }
                QTabBar::tab:selected { background-color: #3A3A3A; color: #FFFFFF; }
            """)
            self.home_box_score.setStyleSheet("QTableWidget { background-color: #2D2D2D; color: #FFFFFF; }")
            self.away_box_score.setStyleSheet("QTableWidget { background-color: #2D2D2D; color: #FFFFFF; }")
            self.back_button.setStyleSheet("QPushButton { background-color: #333333; color: #FFFFFF; }")
            
            # Update feed labels
            for i in range(self.feed_layout.count()):
                widget = self.feed_layout.itemAt(i).widget()
                if isinstance(widget, QLabel):
                    widget.setStyleSheet("padding: 5px; border-bottom: 1px solid #3A3A3A; color: #FFFFFF;")
        else:
            self.setStyleSheet("background-color: #FFFFFF; color: #000000;")
            self.home_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000;")
            self.away_score.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000;")
            self.home_team_name.setStyleSheet("color: #000000;")
            self.away_team_name.setStyleSheet("color: #000000;")
            self.status_label.setStyleSheet("color: #000000;")
            self.home_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #000000;")
            self.away_box_score_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #000000;")
            self.tab_widget.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #CCCCCC; }
                QTabBar::tab { background-color: #F0F0F0; color: #555555; padding: 8px 12px; }
                QTabBar::tab:selected { background-color: #FFFFFF; color: #000000; }
            """)
            self.home_box_score.setStyleSheet("QTableWidget { background-color: #FFFFFF; color: #000000; }")
            self.away_box_score.setStyleSheet("QTableWidget { background-color: #FFFFFF; color: #000000; }")
            self.back_button.setStyleSheet("QPushButton { background-color: #F0F0F0; color: #000000; }")
            
            # Update feed labels
            for i in range(self.feed_layout.count()):
                widget = self.feed_layout.itemAt(i).widget()
                if isinstance(widget, QLabel):
                    widget.setStyleSheet("padding: 5px; border-bottom: 1px solid #CCCCCC; color: #000000;")

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
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Initial update
        self.update_games()
        
    def init_ui(self):
        self.setWindowTitle("NBA Desktop Widget")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create header with dark mode toggle
        header_layout = QHBoxLayout()
        title_label = QLabel("NBA Games")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.dark_mode_toggle = DarkModeToggle(self)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.dark_mode_toggle)
        
        self.main_layout.addLayout(header_layout)
        
        # Create stacked widget for main view and detail views
        self.stacked_widget = QStackedWidget()
        
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
            games = fetch_games_list()
            
            # Clear existing grid
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Create new game cells
            for i, game in enumerate(games):
                row = i // 2
                col = i % 2
                
                if game.game_id not in self.game_cells:
                    game_cell = GameCell(game)
                    game_cell.clicked_signal.connect(self.cell_clicked)
                    self.game_cells[game.game_id] = game_cell
                    
                    # Create detail view
                    detail_view = GameDetailView(game)
                    detail_view.back_signal.connect(self.show_main_view)
                    self.game_detail_views[game.game_id] = detail_view
                    self.stacked_widget.addWidget(detail_view)
                    
                self.grid_layout.addWidget(self.game_cells[game.game_id], row, col)
                
                # Apply theme
                self.game_cells[game.game_id].apply_theme(self.is_dark_mode)
                self.game_detail_views[game.game_id].apply_theme(self.is_dark_mode)
                
                # Update game status
                try:
                    game_update = fetch_live_game_updates(game.game_id)
                    self.game_cells[game.game_id].update_game_status(game_update)
                    self.game_detail_views[game.game_id].update_game_status(game_update)
                except Exception as e:
                    print(f"Error updating game {game.game_id}: {e}")
                    self.game_cells[game.game_id].update_game_status(None)
                    
        except Exception as e:
            print(f"Error fetching games: {e}")
        
    def cell_clicked(self, game_id):
        # Show detail view for selected game
        detail_view = self.game_detail_views.get(game_id)
        if detail_view:
            self.stacked_widget.setCurrentWidget(detail_view)
            
            # Update game status
            try:
                game_update = fetch_live_game_updates(game_id)
                detail_view.update_game_status(game_update)
            except Exception as e:
                print(f"Error updating game detail {game_id}: {e}")
    
    def show_main_view(self):
        self.stacked_widget.setCurrentWidget(self.main_view)
    
    def apply_theme(self, is_dark_mode):
        self.is_dark_mode = is_dark_mode
        
        # Apply theme to all game cells
        for game_id, cell in self.game_cells.items():
            cell.apply_theme(is_dark_mode)
            
        # Apply theme to all detail views
        for game_id, view in self.game_detail_views.items():
            view.apply_theme(is_dark_mode)
            
        # Apply theme to main window
        if is_dark_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #1E1E1E; }
                QScrollArea { background-color: #1E1E1E; border: none; }
                QWidget { background-color: #1E1E1E; color: #FFFFFF; }
                QLabel { color: #FFFFFF; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #F5F5F5; }
                QScrollArea { background-color: #F5F5F5; border: none; }
                QWidget { background-color: #F5F5F5; color: #000000; }
                QLabel { color: #000000; }
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())