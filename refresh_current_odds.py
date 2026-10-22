"""Optional current NCAA football lines; requires THE_ODDS_API_KEY secret."""
import json
import os
from cfb.data import load_games
from cfb.current_odds import collect

if __name__ == '__main__':
    key = os.getenv('THE_ODDS_API_KEY', '').strip()
    if key:
        print(json.dumps(collect(load_games(), key), indent=2))
    else:
        print('Skipped current odds refresh: THE_ODDS_API_KEY secret not configured.')
