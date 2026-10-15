"""Experimental pregame opponent-adjusted scoring ratings; NOT the production model.

Sequential updates use only completed games preceding the current kickoff.
Ratings are point offsets from a league scoring prior; parameters are fixed
heuristics awaiting season-separated validation.
"""
from collections import defaultdict
from datetime import datetime, timezone
from math import exp

LEAGUE_PPG = 27.5
HOME_ADV = 2.5
LEARNING_RATE = 0.12
SEASON_RETENTION = 0.65

def kickoff(game):
    date = datetime.fromisoformat(str(game['date']).replace('Z', '+00:00'))
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)

def predict(game, offense, defense):
    h, a = str(game['home_id']), str(game['away_id'])
    advantage = 0 if game.get('neutral') else HOME_ADV / 2
    home = max(0., LEAGUE_PPG + offense[h] - defense[a] + advantage)
    away = max(0., LEAGUE_PPG + offense[a] - defense[h] - advantage)
    margin = home - away
    return {'home_points': round(home, 2), 'away_points': round(away, 2),
            'home_margin': round(margin, 2), 'total': round(home + away, 2),
            'home_win_prob': round(1/(1+exp(-max(-100,min(100,margin))/9)), 4),
            'model_version': 'shadow_adj_scoring_v0.6_experimental'}

def replay(games, as_of=None):
    ordered = sorted(games, key=lambda g: (kickoff(g), str(g.get('id', ''))))
    offense, defense = defaultdict(float), defaultdict(float)
    forecasts = []
    season = None
    cutoff = None
    if as_of is not None:
        cutoff = datetime.fromisoformat(as_of.replace('Z', '+00:00')) if isinstance(as_of,str) else as_of
        if cutoff.tzinfo is None:
            raise ValueError('as_of must be timezone-aware')
    # Hold same-kickoff games together so their results cannot inform one another.
    from itertools import groupby
    for _, kickoff_group in groupby(ordered, key=kickoff):
        batch = list(kickoff_group)
        pending_updates = []
        for game in batch:
            if season is not None and game['season'] != season:
                for ratings in (offense, defense):
                    for k in ratings:
                        ratings[k] *= SEASON_RETENTION
            season = game['season']
            pred = predict(game, offense, defense)
            forecasts.append({**game, **pred})
            if (not game.get('completed') or game.get('home_score') is None or
                    game.get('away_score') is None or
                    (cutoff is not None and kickoff(game) >= cutoff)):
                continue
            pending_updates.append((game, pred))
        for game, pred in pending_updates:
            h, a = str(game['home_id']), str(game['away_id'])
            home_error = float(game['home_score']) - pred['home_points']
            away_error = float(game['away_score']) - pred['away_points']
            offense[h] += LEARNING_RATE * home_error / 2
            defense[a] -= LEARNING_RATE * home_error / 2
            offense[a] += LEARNING_RATE * away_error / 2
            defense[h] -= LEARNING_RATE * away_error / 2
    return forecasts
