"""Read-only, paired, retrospective comparison of production and shadow models."""
from collections import defaultdict
from math import sqrt
from cfb.model import evaluation
from cfb.promotion_gate import aligned_pairs
from cfb.historical_markets import retrospective_grade


def tournament(baseline, shadow, market_lines, seasons):
    pairs = aligned_pairs(baseline, shadow, test_seasons=seasons)
    bucket = defaultdict(list)
    details = []
    for b, s in pairs:
        market = market_lines.get(str(b['id']))
        actual_margin = b['home_score']-b['away_score']
        actual_total = b['home_score']+b['away_score']
        line = market.get('market_home_margin') if market else None
        total_line = market.get('market_total') if market else None
        item = {
            'id':str(b['id']), 'season':int(b['season']), 'week':b['week'],
            'date':b['date'], 'matchup':f"{b['away']} @ {b['home']}",
            'actual_margin':actual_margin, 'actual_total':actual_total,
            'baseline_margin':b['home_margin'], 'shadow_margin':s['home_margin'],
            'baseline_total':b['total'], 'shadow_total':s['total'],
            'baseline_home_win_prob':b['home_win_prob'], 'shadow_home_win_prob':s['home_win_prob'],
            'model_disagreement':abs(b['home_margin']-s['home_margin']),
            'historical_market_home_margin':line, 'historical_market_total':total_line,
            'baseline_ats':retrospective_grade(b,market)['ats'],
            'shadow_ats':retrospective_grade(s,market)['ats'],
            'baseline_ou':retrospective_grade(b,market)['ou'],
            'shadow_ou':retrospective_grade(s,market)['ou'],
        }
        details.append(item)
        bucket[int(b['season'])].append((b,s))
    summary=[]
    for season, games in sorted(bucket.items()):
        base=[x for x,_ in games]; challenger=[x for _,x in games]
        summary.append({'season':season, 'baseline':evaluation(base), 'shadow':evaluation(challenger)})
    if pairs:
        base, challenger = zip(*pairs)
        overall={'baseline':evaluation(base),'shadow':evaluation(challenger)}
    else:
        overall={'baseline':{},'shadow':{}}
    return {'summary':summary,'overall':overall,'details':details,'paired_games':len(pairs)}


def calibration_rows(details, model, bins=10):
    """Observed home win fraction versus predicted probability; draws count as half."""
    groups=defaultdict(list)
    key=f'{model}_home_win_prob'
    for d in details:
        p=d.get(key)
        if p is None or not 0<=float(p)<=1: continue
        i=min(bins-1,int(float(p)*bins))
        groups[i].append((float(p), 1 if d['actual_margin']>0 else 0 if d['actual_margin']<0 else .5))
    return [{'bin':f'{i/bins:.0%}–{(i+1)/bins:.0%}', 'games':len(group),
             'mean_probability':sum(x for x,y in group)/len(group),
             'observed_home_win_rate':sum(y for x,y in group)/len(group)}
            for i,group in sorted(groups.items())]


def picks_record(details,model,kind):
    key=f'{model}_{kind}'
    counts={k:sum(x[key]==k for x in details) for k in ('win','loss','push','no_line','no_pick')}
    graded=counts['win']+counts['loss']
    return {**counts,'win_rate':counts['win']/graded if graded else None}
