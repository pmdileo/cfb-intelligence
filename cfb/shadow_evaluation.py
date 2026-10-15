"""Apples-to-apples chronological diagnostic for production vs shadow predictions."""
from collections import defaultdict
from cfb.model import build_predictions, evaluation
from cfb.shadow_ratings import replay

def compare(games, boxscores=None):
    baseline = build_predictions(games, boxscores=boxscores or {})
    shadow = replay(games)
    by_id = {str(x['id']):x for x in baseline}
    rows = defaultdict(lambda: {'baseline': [], 'shadow': []})
    for s in shadow:
        b = by_id.get(str(s['id']))
        if b is None or not s.get('completed') or s.get('home_score') is None or s.get('away_score') is None:
            continue
        season = int(s['season'])
        rows[season]['baseline'].append(b)
        rows[season]['shadow'].append(s)
    out=[]
    for season, members in sorted(rows.items()):
        out.append({'season':season, 'baseline':evaluation(members['baseline']),
                    'shadow':evaluation(members['shadow'])})
    return out
