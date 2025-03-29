from datetime import datetime, timezone
from dateutil import parser
from nba_api.live.nba.endpoints import scoreboard, boxscore

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


#  Fetches today's game data that only needs to be retrieved once.
def fetch_games_list():
    # Get today's scoreboard and games
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()

    if not games:
        return {"error": "No games found today"}
    
    listOfGames = []
    for game in games: 
        game_id = game['gameId']
        home_team = game['homeTeam']['teamName']
        away_team = game['awayTeam']['teamName']

        #convert UTC to local time
        gameTimeUTC = parser.parse(game["gameTimeUTC"])
        gameTimeLTZ = gameTimeUTC.replace(tzinfo=timezone.utc).astimezone(tz=None)
        # Convert to 12 hour clock format
        gameTime12hrClock = gameTimeLTZ.strftime("%I:%M %p")

        processed_game = {
            'gameId': game_id,
            'gameTime': gameTime12hrClock,
            'homeTeam': home_team,
            'awayTeam': away_team
        }

        listOfGames.append(processed_game)
        listOfGames.sort(key=lambda x: x['gameTime']) # Sort the list of games by game time
    
    return listOfGames

print(fetch_games_list())

# Fetches live game updates that need to be updated every 2 seconds.
def get_live_game_updates(game_id):
    # Get the box score for the game and game status
    box = boxscore.BoxScore(game_id)
    game_data = box.game.get_dict()
    game_status = game_data['gameStatusText']

    # Get the clock and period
    period = game_data['period']
    rawClock = game_data['gameClock'] # Returns something like PT00M19.50S
    clock = rawClock[-5:] # Get the last 5 characters of the clock string
    
    # Format the clock to basketball format
    period_display = f"Q{period}" if period <= 4 else f"OT{period-4}"
    clock_display = f"{period_display} {clock}"

    # Get the score for the game
    home_score = game_data['homeTeam']['score']
    away_score = game_data['awayTeam']['score']
    score_display = f"{away_score} - {home_score}"

    # Get the players and their stats
    home_players = game_data['homeTeam']['players']
    away_players = game_data['awayTeam']['players']

    home_player_stats = []
    for player in home_players:
        name = player['name']
        player_name = player['name']
        player_minutes_played_raw = player['statistics']['minutesCalculated'] #Returns something like PT33M
        player_minutes_played = int(''.join(c for c in player_minutes_played_raw if c.isdigit())) #Returns only the numbers
        player_points = player['statistics']['points']
        player_rebounds = player['statistics']['reboundsTotal']
        player_assists = player['statistics']['assists']
        home_player_stats.append(f"{player_name}: {player_minutes_played} MIN, {player_points} PTS, {player_rebounds} REB, {player_assists} AST")
        
    away_player_stats = []
    for player in away_players:
        name = player['name']
        player_name = player['name']
        player_minutes_played_raw = player['statistics']['minutesCalculated'] #Returns something like PT33M
        player_minutes_played = int(''.join(c for c in player_minutes_played_raw if c.isdigit())) #Returns only the numbers
        player_points = player['statistics']['points']
        player_rebounds = player['statistics']['reboundsTotal']
        player_assists = player['statistics']['assists']
        away_player_stats.append(f"{player_name}: {player_minutes_played} MIN, {player_points} PTS, {player_rebounds} REB, {player_assists} AST")
    
    best_home_player = max(home_players, key=lambda x: x['statistics']['points'] + 2 * x['statistics']['reboundsTotal'] + 3* x['statistics']['assists'])
    best_away_player = max(away_players, key=lambda x: x['statistics']['points'] + 2 * x['statistics']['reboundsTotal'] + 3* x['statistics']['assists'])
    best_home_player_display = f"{best_home_player['name']}: {best_home_player['statistics']['points']} PTS, {best_home_player['statistics']['reboundsTotal']} REB, {best_home_player['statistics']['assists']} AST"
    best_away_player_display = f"{best_away_player['name']}: {best_away_player['statistics']['points']} PTS, {best_away_player['statistics']['reboundsTotal']} REB, {best_away_player['statistics']['assists']} AST"

    return {
        "status": game_status,
        "clock": clock_display,
        "score": score_display,
        "home_players": home_player_stats,
        "away_players": away_player_stats,
        "best_home_player": best_home_player_display,
        "best_away_player": best_away_player_display
    }

print(get_live_game_updates('0022401073')) # Example gameId: 0022401073


