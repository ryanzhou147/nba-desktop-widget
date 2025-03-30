from datetime import datetime, timezone
from dateutil import parser
from nba_api.live.nba.endpoints import scoreboard, boxscore, playbyplay
from nba_api.stats.static import players
import re
from dataclasses import dataclass
from typing import List, Dict

# Data I need to get.
# These I only need to grab once
# 1. Teams playing                      x vs y
# 2. Game time in local timezone        4:00 PM EST
# 3. Game id                            0022401073

# These I need to update every 2 seconds
# 3. Shot clock time remaining          Q1 12:00
# 4. Game score                         X - Y 
# 5. Box score for each player          M: 20 PTS, 5 REB, 3 AST
# 6. Game status                        In Progress, Final, etc.

@dataclass
class Game:
    game_id: str
    game_time: str
    home_team: str
    away_team: str

@dataclass
class PlayerStats:
    player_name: str
    minutes_played: int
    points: int
    rebounds: int
    assists: int

@dataclass
class GameUpdate:
    status: str
    period: int
    clock: str
    home_score: int
    away_score: int
    home_players: List[PlayerStats]
    away_players: List[PlayerStats]
    best_home_player: str
    best_away_player: str
    best_overall_player: str
    recent_plays: List[str]

def fetch_games_list() -> List[Game]:
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()

    if not games:
        return []
    
    list_of_games = []
    for game in games:
        game_id = game['gameId']
        home_team = game['homeTeam']['teamName']
        away_team = game['awayTeam']['teamName']

        #convert UTC to local time
        game_time_utc = parser.parse(game["gameTimeUTC"])
        game_time_ltz = game_time_utc.replace(tzinfo=timezone.utc).astimezone(tz=None)
        # Convert to 12 hour clock format
        game_time_12hr_clock = game_time_ltz.strftime("%I:%M %p")

        list_of_games.append(Game(game_id, game_time_12hr_clock, home_team, away_team))
    
    list_of_games.sort(key=lambda x: x.game_time)

    return list_of_games


def fetch_live_game_updates(game_id: str) -> GameUpdate:

    box = boxscore.BoxScore(game_id)
    game_data = box.game.get_dict()
    game_status = game_data['gameStatusText']

    # Get the clock and period
    period = game_data['period']
    raw_clock = game_data['gameClock'] # Returns something like PT00M19.50S
    match_time = re.search(r'PT(\d+)M(\d+\.\d+)S', raw_clock) # Outputs something like PT08M47.00S. We want 8:47
    minutes = match_time.group(1)
    seconds = match_time.group(2).split('.')[0]  # Remove decimal part
    clock = f"{minutes}:{seconds}"  # In the form 00:00

    home_score = game_data['homeTeam']['score']
    away_score = game_data['awayTeam']['score']

    home_players = game_data['homeTeam']['players']
    away_players = game_data['awayTeam']['players']

    def fetch_player_stats(players: List[Dict]) -> List[PlayerStats]:
        player_stats = []
        for player in players:
            player_name = player['name']
            player_minutes_played_raw = player['statistics']['minutesCalculated'] #Returns something like PT33M
            player_minutes_played = int(''.join(c for c in player_minutes_played_raw if c.isdigit())) #Returns only the numbers
            player_points = player['statistics']['points']
            player_rebounds = player['statistics']['reboundsTotal']
            player_assists = player['statistics']['assists']
            player_stats.append(PlayerStats(player_name, player_minutes_played, player_points, player_rebounds, player_assists))
        return player_stats
    
    home_player_stats = fetch_player_stats(home_players)
    away_player_stats = fetch_player_stats(away_players)

    def best_player(players: List[Dict]) -> str:
        best = max(players, key=lambda x: x['statistics']['points'] + 2 * x['statistics']['reboundsTotal'] + 3* x['statistics']['assists'])
        return f"{best['name']}: {best['statistics']['points']} PTS, {best['statistics']['reboundsTotal']} REB, {best['statistics']['assists']} AST"
    
    best_home_player = best_player(home_players)
    best_away_player = best_player(away_players)
    best_overall_player = best_player(home_players+away_players)

    pbp = playbyplay.PlayByPlay(game_id)
    plays = pbp.get_dict()['game']['actions']
    recent_plays = []

    if plays:
        sorted_plays = sorted(plays, key=lambda x: x.get('actionNumber', 0), reverse=True)

        for play in sorted_plays[:5]:
            match_time = re.search(r'PT(\d+)M(\d+\.\d+)S', play['clock'])
            if match_time:
                minutes = match_time.group(1)
                seconds = match_time.group(2).split('.')[0]
                time_str = f"{minutes}:{seconds}"

            play_period = play.get('period', 0)
            period_str = f"Q{play_period}" if play_period <= 4 else f"OT{play_period - 4}"

            play_description = play.get('description', 'Unknown action')
            play_text = f"{period_str} {time_str} | {play_description}"
            recent_plays.append(play_text)

    recent_plays.reverse()

    return GameUpdate(game_status, period, clock, home_score, away_score, home_player_stats, away_player_stats, best_home_player, best_away_player, best_overall_player, recent_plays)

print(fetch_games_list())
print(fetch_live_game_updates('0022401073'))