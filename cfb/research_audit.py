"""Independent data availability and consistency diagnostics (no data mutation)."""
from collections import Counter
from datetime import datetime
import math


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def inspect_boxscores(boxscores):
    stats = Counter()
    stats['cached_games'] = len(boxscores)
    for game in boxscores.values():
        if not isinstance(game, dict):
            stats['malformed_games'] += 1
            continue
        for team in game.values():
            stats['team_records'] += 1
            if not isinstance(team, dict):
                stats['malformed_teams'] += 1
                continue
            for field in ('total_yards', 'offensive_plays', 'yards_per_play', 'turnovers', 'first_downs'):
                if valid_number(team.get(field)):
                    stats[field + '_available'] += 1
            yards, plays, ypp = (team.get(k) for k in ('total_yards', 'offensive_plays', 'yards_per_play'))
            if valid_number(plays) and plays <= 0:
                stats['invalid_play_counts'] += 1
            if all(valid_number(x) for x in (yards, plays, ypp)) and plays > 0:
                if abs(yards / plays - ypp) > 0.15:
                    stats['ypp_inconsistent'] += 1
    return dict(stats)


def market_coverage(games, markets):
    by_season = {}
    for g in games:
        if not g.get('completed') or g.get('home_score') is None or g.get('away_score') is None:
            continue
        season = str(g['season'])
        c = by_season.setdefault(season, Counter())
        c['completed_games'] += 1
        line = markets.get(str(g['id']), {})
        if line.get('market_home_margin') is not None: c['spreads'] += 1
        if line.get('market_total') is not None: c['totals'] += 1
        if line and line.get('line_timing') != 'PREGAME_VERIFIED': c['timing_unverified'] += 1
    return {s:{**dict(c), 'spread_coverage': round(c['spreads']/c['completed_games'], 4),
                       'total_coverage': round(c['totals']/c['completed_games'], 4)}
            for s,c in sorted(by_season.items())}


def audit(games, boxscores, markets):
    ids = [str(g['id']) for g in games]
    return {'game_rows':len(games), 'unique_game_ids':len(set(ids)),
            'duplicate_game_ids':len(ids)-len(set(ids)),
            'completed_games':sum(bool(g.get('completed')) for g in games),
            'boxscores':inspect_boxscores(boxscores),
            'markets':market_coverage(games, markets)}
