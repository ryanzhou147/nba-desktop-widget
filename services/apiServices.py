from datetime import datetime, timezone
from dateutil import parser
from nba_api.live.nba.endpoints import scoreboard, boxscore, playbyplay
from nba_api.stats.static import players
import re

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
    matchTime = re.search(r'PT(\d+)M(\d+\.\d+)S', rawClock) # Outputs something like PT08M47.00S. We want 8:47
    minutes = matchTime.group(1)
    seconds = matchTime.group(2).split('.')[0]  # Remove decimal part
    clock = f"{minutes}:{seconds}"       # In the form 00:00

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

    # Add home players to list (name, minutes played, points, rebounds, assists)
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
        
    # Add away players to list (name, minutes played, points, rebounds, assists)
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
    
    # Find the best player on each team based on points, rebounds, and assists
    # The formula for the best player is: points + 2 * rebounds + 3 * assists
    # TODO: Reserach if this is the best formula for determining the best player
    best_home_player = max(home_players, key=lambda x: x['statistics']['points'] + 2 * x['statistics']['reboundsTotal'] + 3* x['statistics']['assists'])
    best_away_player = max(away_players, key=lambda x: x['statistics']['points'] + 2 * x['statistics']['reboundsTotal'] + 3* x['statistics']['assists'])
    best_home_player_display = f"{best_home_player['name']}: {best_home_player['statistics']['points']} PTS, {best_home_player['statistics']['reboundsTotal']} REB, {best_home_player['statistics']['assists']} AST"
    best_away_player_display = f"{best_away_player['name']}: {best_away_player['statistics']['points']} PTS, {best_away_player['statistics']['reboundsTotal']} REB, {best_away_player['statistics']['assists']} AST"

    # Get play-by-play updates
    recent_plays = []
    line = "{play_number}: Q{period} {clock} {player_id} ({action_type})" #Displayed in this form

    pbp = playbyplay.PlayByPlay(game_id)
    plays = pbp.get_dict()['game']['actions'] #plays are referred to in the live data as `actions`

    if plays:
        # Sort plays by action number for most recent
        sorted_plays = sorted(plays, key=lambda x: x.get('actionNumber', 0), reverse=True)

        for play in sorted_plays[:5]:

            # Find time that the play happened
            matchTime = re.search(r'PT(\d+)M(\d+\.\d+)S', play['clock']) # Outputs something like PT08M47.00S. We want 8:47
            if matchTime:
                minutes = matchTime.group(1)
                seconds = matchTime.group(2).split('.')[0]  # Remove decimal part
                time_str = f"{minutes}:{seconds}"       # In the form 00:00
            
            # Find the period the play happened in
            play_period = play.get('period', 0)
            period_str = f"Q{play_period}" if play_period <= 4 else f"OT{play_period-4}"
            
            # Find teh description of the play
            play_description = play.get('description', 'Unknown action')
            
            # Format the play text
            play_text = f"{period_str} {time_str} | {play_description}"
            recent_plays.append(play_text)
    
    # Reverse plays so most recent play comes first

    recent_plays.reverse()

    return {
        "status": game_status,
        "clock": clock_display,
        "score": score_display,
        "home_players": home_player_stats,
        "away_players": away_player_stats,
        "best_home_player": best_home_player_display,
        "best_away_player": best_away_player_display,
        "recent_plays": recent_plays
    }

print(get_live_game_updates('0022401067')) # Example gameId: 0022401073

