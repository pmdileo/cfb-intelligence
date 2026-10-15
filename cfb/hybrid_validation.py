"""CFB v0.6.2: independent, read-only, chronological tournament diagnostics.

Does NOT claim legacy model forecasts were available pregame. The legacy replay
updates at kickoff (rather than final whistle), so use results only as research.
"""
from __future__ import annotations
from collections import defaultdict
from math import exp
from cfb.promotion_gate import aligned_pairs

TRAIN_SEASONS = (2021, 2022, 2023)
TEST_SEASONS = (2024, 2025, 2026)
WEIGHTS = (0., .25, .5, .75, 1.)  # share of shadow model


def blend(baseline, shadow, shadow_weight):
    """Fixed convex blend, with probability derived from the blended margin."""
    w = float(shadow_weight)
    if not 0 <= w <= 1:
        raise ValueError('shadow_weight must be between 0 and 1')
    m = (1-w)*float(baseline['home_margin']) + w*float(shadow['home_margin'])
    t = (1-w)*float(baseline['total']) + w*float(shadow['total'])
    prob = 1/(1+exp(-max(-100., min(100., m))/9.))
    return {'home_margin':m, 'total':t,'home_win_prob':prob}


def score_pairs(pairs, weight):
    """Returns matched-game scores; all metrics are lower-is-better except accuracy."""
    errors_margin=[]; errors_total=[]; briers=[]; wins=[]
    for b,s in pairs:
        p=blend(b,s,weight)
        am=float(b['home_score'])-float(b['away_score'])
        at=float(b['home_score'])+float(b['away_score'])
        errors_margin.append(abs(p['home_margin']-am))
        errors_total.append(abs(p['total']-at))
        actual=1. if am>0 else 0. if am<0 else .5
        briers.append((p['home_win_prob']-actual)**2)
        if am!=0 and p['home_margin']!=0:
            wins.append((p['home_margin']>0)==(am>0))
    n=len(pairs)
    return {'games':n,'winner_accuracy':sum(wins)/len(wins) if wins else None,
            'margin_mae':sum(errors_margin)/n if n else None,
            'total_mae':sum(errors_total)/n if n else None,
            'brier':sum(briers)/n if n else None}


def validate_tournament(baseline, shadow, train_seasons=TRAIN_SEASONS, test_seasons=TEST_SEASONS):
    """Choose weight ONLY on train years; report performance on later years.

    Earlier tuning of constituent models can compromise holdout independence.
    """
    train=set(map(int,train_seasons)); test=set(map(int,test_seasons))
    if not train or not test or train & test or max(train)>=min(test):
        raise ValueError('Require separate chronological train and later test seasons')
    training=aligned_pairs(baseline,shadow,test_seasons=sorted(train))
    testing=aligned_pairs(baseline,shadow,test_seasons=sorted(test))
    train_scores=[{'shadow_weight':w, **score_pairs(training,w)} for w in WEIGHTS]
    if not training:
        raise ValueError('No aligned completed training games')
    # Primary optimization criterion defined before test access: margin MAE.
    chosen=min(train_scores,key=lambda x:(x['margin_mae'],x['shadow_weight']))['shadow_weight']
    test_scores=[{'model':name,'shadow_weight':w,**score_pairs(testing,w)} for name,w in
                 (('Elo baseline',0.),('Shadow',1.),('Selected hybrid',chosen))]
    by_season=[]
    season_groups=defaultdict(list)
    for b,s in testing: season_groups[int(b['season'])].append((b,s))
    for year, group in sorted(season_groups.items()):
        for name,w in (('Elo baseline',0.),('Shadow',1.),('Selected hybrid',chosen)):
            by_season.append({'season':year,'model':name,'shadow_weight':w,**score_pairs(group,w)})
    return {'train_seasons':sorted(train),'test_seasons':sorted(test),
            'train_games':len(training),'test_games':len(testing),
            'selected_shadow_weight':chosen,'training_candidates':train_scores,
            'test_results':test_scores,'test_by_season':by_season,
            'leakage_warning':'Existing baseline/shadow replays may incorporate earlier kickoff results before final whistle. This is retrospective exploratory evidence, NOT leakage-free pregame accuracy.',
            'holdout_warning':'The declared test split is not a pristine holdout if any model parameters were already chosen after seeing these seasons.',
            'deployment':'No model automatically promoted.'}


def kickoff_overlap_audit(games, hours=4):
    """Counts completed games starting <hours earlier than another kickoff.

    This is a risk screen, NOT proof of leakage: it assumes no final-whistle times.
    """
    from datetime import datetime, timezone, timedelta
    ordered=[]
    for g in games:
        if not g.get('date'):continue
        d=datetime.fromisoformat(str(g['date']).replace('Z','+00:00'))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        ordered.append((d,g))
    ordered.sort(key=lambda x:x[0])
    recent=[]; risk_ids=set(); pairs=0
    for current,g in ordered:
        recent=[(d,h) for d,h in recent if current-d<timedelta(hours=hours)]
        for prior,h in recent:
            if h.get('completed') and h.get('home_score') is not None:
                pairs+=1;risk_ids.add(str(g.get('id')))
        recent.append((current,g))
    return {'examined_games':len(ordered),'at_risk_games':len(risk_ids),
            'overlap_pairs':pairs,'assumed_game_duration_hours':hours,
            'note':'Risk only; actual completion timestamps unavailable.'}
