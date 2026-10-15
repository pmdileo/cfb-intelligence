"""Independent, cautious forecast evaluation. Does not train or alter a model."""
from collections import defaultdict
from math import sqrt


def evaluate_rows(rows):
    valid = [r for r in rows if r.get('completed') and r.get('home_score') is not None
             and r.get('away_score') is not None and r.get('home_margin') is not None
             and r.get('total') is not None]
    if not valid:
        return {'games':0, 'winner_accuracy':None, 'margin_mae':None, 'margin_rmse':None,
                'total_mae':None, 'brier':None}
    n = len(valid)
    win_pairs = [(r['home_margin'] > 0, r['home_score'] > r['away_score']) for r in valid
                 if r['home_score'] != r['away_score'] and r['home_margin'] != 0]
    margins = [r['home_margin']-(r['home_score']-r['away_score']) for r in valid]
    totals = [r['total']-(r['home_score']+r['away_score']) for r in valid]
    probs = [r for r in valid if r.get('home_win_prob') is not None and 0<=r['home_win_prob']<=1]
    return {'games':n, 'decided_picks':len(win_pairs),
            'winner_accuracy':sum(p==a for p,a in win_pairs)/len(win_pairs) if win_pairs else None,
            'margin_mae':sum(abs(e) for e in margins)/n,
            'margin_rmse':sqrt(sum(e*e for e in margins)/n),
            'total_mae':sum(abs(e) for e in totals)/n,
            'brier':sum((r['home_win_prob']-(1 if r['home_score']>r['away_score'] else 0 if r['home_score']<r['away_score'] else 0.5))**2 for r in probs)/len(probs) if probs else None}


def compare_same_games(baseline, challenger, minimum_games=25):
    """Pair on game ID; completed games only; record intersection and coverage explicitly."""
    base = {str(r['id']):r for r in baseline}
    new = {str(r['id']):r for r in challenger}
    ids = sorted(set(base) & set(new))
    paired_b, paired_n = [], []
    for game_id in ids:
        b, n = base[game_id], new[game_id]
        if not (b.get('completed') and n.get('completed')): continue
        if any(b.get(k)!=n.get(k) for k in ('home_score','away_score','home_id','away_id','date')):
            raise ValueError('Inconsistent game metadata for '+game_id)
        if b.get('home_score') is None or b.get('away_score') is None: continue
        paired_b.append(b);paired_n.append(n)
    return {'paired_games':len(paired_b),'baseline_total_rows':len(base),
            'challenger_total_rows':len(new),'enough_games':len(paired_b)>=minimum_games,
            'baseline':evaluate_rows(paired_b),'challenger':evaluate_rows(paired_n)}


def by_season(rows):
    groups=defaultdict(list)
    for row in rows:groups[str(row['season'])].append(row)
    return {k:evaluate_rows(v) for k,v in sorted(groups.items())}


def archived_live_rows(snapshots, games):
    """First truly pre-kickoff snapshot per ID; excludes forecasts recorded after kickoff."""
    from datetime import datetime, timezone
    def dt(s):
        value=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    game_map={str(g['id']):g for g in games}
    first={}
    for snap in sorted(snapshots,key=lambda x:x['snapshot_utc']):
        game=game_map.get(str(snap['id']))
        if not game or dt(snap['snapshot_utc'])>=dt(game['date']):continue
        first.setdefault(str(snap['id']),snap)
    return [{**p,**{k:g.get(k) for k in ('completed','home_score','away_score')}}
            for gid,p in first.items() for g in [game_map[gid]]]
