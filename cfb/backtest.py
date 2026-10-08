"""Chronological season-level scorecards; no retrospective market claims."""
from collections import defaultdict
from cfb.model import evaluation


def seasons_report(predictions, min_games=1):
    grouped = defaultdict(list)
    for game in predictions:
        if game.get('completed') and game.get('home_score') is not None and game.get('away_score') is not None:
            grouped[int(game['season'])].append(game)
    rows=[]
    for season, games in sorted(grouped.items()):
        if len(games) < min_games:
            continue
        results = evaluation(games)
        rows.append({'season':season, **results})
    return rows
