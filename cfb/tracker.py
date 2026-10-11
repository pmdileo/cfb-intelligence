"""Grade frozen pre-kickoff forecasts against final scores and saved market prices."""
from __future__ import annotations
from collections import Counter
from .model import timestamp
from .snapshots import _read, DEFAULT_PATH


def _side(value, market, tol=1e-9):
    if market is None or value is None:
        return None
    delta = float(value) - float(market)
    return 1 if delta > tol else -1 if delta < -tol else 0


def grade_pick(pick_side, actual_minus_line, tol=1e-9):
    """Value from perspective of home team: + means home; - means away."""
    if pick_side is None:
        return 'no_line'
    if pick_side == 0:
        return 'no_pick'
    if abs(actual_minus_line) < tol:
        return 'push'
    return 'win' if pick_side * actual_minus_line > 0 else 'loss'


def grade_game(prediction, game):
    if not game.get('completed') or game.get('home_score') is None or game.get('away_score') is None:
        return {'su':'pending','ats':'pending','ou':'pending'}
    margin = game['home_score']-game['away_score']
    total = game['home_score']+game['away_score']
    side = _side(prediction['home_margin'], 0)
    su = grade_pick(side, margin)
    # market_home_margin is the market's expected HOME minus AWAY points.
    # If home is -3.5 favorite, market_home_margin=+3.5.
    market_margin = prediction.get('market_home_margin')
    ats = ('no_line' if market_margin is None else
           grade_pick(_side(prediction.get('home_margin'),market_margin), margin-market_margin))
    market_total = prediction.get('market_total')
    ou = ('no_line' if market_total is None else
          grade_pick(_side(prediction.get('total'),market_total), total-market_total))
    return {'su':su,'ats':ats,'ou':ou}


def tracker_rows(games, archive_path=DEFAULT_PATH):
    by_id={str(g['id']):g for g in games}
    earliest={}
    for p in sorted(_read(archive_path), key=lambda p: p['snapshot_utc']):
        game=by_id.get(str(p['id']))
        if game and timestamp(p['snapshot_utc']) < timestamp(game['date']):
            earliest.setdefault(str(p['id']),p)
    rows=[]
    for gid,p in earliest.items():
        game=by_id[gid]
        rows.append({**p,'status':grade_game(p,game),'completed':bool(game.get('completed')),
                     'home_score':game.get('home_score'),'away_score':game.get('away_score')})
    return sorted(rows,key=lambda x:(x.get('season',0),x.get('week',0),x['date'],str(x['id'])))


def record(rows, metric):
    count=Counter(row['status'][metric] for row in rows)
    wins=count['win']; losses=count['loss']; pushes=count['push']
    return {'wins':wins,'losses':losses,'pushes':pushes,'pending':count['pending'],
            'no_line':count['no_line'],'no_pick':count['no_pick'],
            'pct':wins/(wins+losses) if wins+losses else None}
