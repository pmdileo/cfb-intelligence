"""Conservative read-only model promotion diagnostics.

A challenger is NOT automatically promoted. Metrics are computed only on
identical game IDs and a user-declared held-out season range.
"""
from __future__ import annotations
from collections import defaultdict
from math import sqrt


def _valid_pair(b, c):
    keys = ('home_id', 'away_id', 'date', 'home_score', 'away_score', 'season')
    if any(b.get(k) != c.get(k) for k in keys):
        raise ValueError(f"Inconsistent game metadata for {b.get('id')}")
    return (b.get('completed') and c.get('completed') and
            b.get('home_score') is not None and b.get('away_score') is not None and
            all(x.get('home_margin') is not None and x.get('total') is not None for x in (b,c)))


def aligned_pairs(baseline, challenger, *, test_seasons):
    """Restrict to declared held-out seasons and identical completed games."""
    if not test_seasons:
        raise ValueError('Specify at least one held-out test season explicitly')
    seasons = {int(s) for s in test_seasons}
    bmap = {str(r['id']): r for r in baseline}
    cmap = {str(r['id']): r for r in challenger}
    pairs = []
    for gid in sorted(set(bmap) & set(cmap)):
        b,c = bmap[gid],cmap[gid]
        if int(b['season']) not in seasons:
            continue
        if _valid_pair(b,c):
            pairs.append((b,c))
    return pairs


def _metrics(rows):
    n=len(rows)
    if not n:
        return {'games':0,'margin_mae':None,'total_mae':None,'brier':None,'winner_accuracy':None}
    me=[float(r['home_margin'])-(r['home_score']-r['away_score']) for r in rows]
    te=[float(r['total'])-(r['home_score']+r['away_score']) for r in rows]
    decided=[r for r in rows if r['home_score'] != r['away_score'] and r['home_margin'] != 0]
    probs=[r for r in rows if r.get('home_win_prob') is not None and 0<=float(r['home_win_prob'])<=1]
    return {'games':n,'margin_mae':sum(map(abs,me))/n,'total_mae':sum(map(abs,te))/n,
            'brier':sum((float(r['home_win_prob']) - (1 if r['home_score']>r['away_score'] else 0 if r['home_score']<r['away_score'] else .5))**2 for r in probs)/len(probs) if probs else None,
            'winner_accuracy':sum((r['home_margin']>0)==(r['home_score']>r['away_score']) for r in decided)/len(decided) if decided else None}


def assess(baseline, challenger, *, test_seasons, min_games=100, min_seasons=2):
    """Make a diagnostic recommendation; requires manual review, never changes production.

    Safety gate demands both better margin and total MAE and no worse Brier.
    This is a heuristic gate, not a significance test nor proof of edge.
    """
    pairs=aligned_pairs(baseline, challenger,test_seasons=test_seasons)
    b,c=zip(*pairs) if pairs else ((),())
    baseline_metrics=_metrics(b); challenger_metrics=_metrics(c)
    seasons=sorted({int(x['season']) for x in b})
    groups=defaultdict(lambda: [[],[]])
    for left,right in pairs:
        groups[int(left['season'])][0].append(left)
        groups[int(left['season'])][1].append(right)
    by_season={str(s):{'baseline':_metrics(groups[s][0]),'challenger':_metrics(groups[s][1])} for s in sorted(groups)}
    sample_ok=len(pairs)>=min_games and len(seasons)>=min_seasons
    both_brier=(baseline_metrics['brier'] is not None and challenger_metrics['brier'] is not None)
    improvements=(sample_ok and
        challenger_metrics['margin_mae'] < baseline_metrics['margin_mae'] and
        challenger_metrics['total_mae'] < baseline_metrics['total_mae'] and
        both_brier and challenger_metrics['brier'] <= baseline_metrics['brier'])
    return {'decision':'REVIEW_CANDIDATE' if improvements else 'KEEP_BASELINE',
            'manual_approval_required':True,'test_seasons':sorted({int(s) for s in test_seasons}),
            'paired_games':len(pairs),'covered_seasons':seasons,'minimum_games':min_games,
            'minimum_seasons':min_seasons,'baseline':baseline_metrics,'challenger':challenger_metrics,
            'by_season':by_season,
            'caveats':['Chronological replay is not a saved pregame prediction record.',
                       'Never choose feature weights or hyperparameters on these test seasons.',
                       'Evaluate future seasons after freezing model parameters.',
                       'Historical sportsbook lines lack verified pregame timestamps.']}
