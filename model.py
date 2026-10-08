"""Chronological Elo + recent-margin baseline; no leakage from future games.

This is deliberately a baseline, not a fitted/validated betting model.
"""
from __future__ import annotations
import math
from collections import defaultdict, deque
from datetime import datetime,timezone

START_ELO=1500.0
HOME_ADV_PTS=2.5
ELO_TO_POINTS=25.0  # ~25 Elo points per point of margin
K=24.0
REGRESSION=0.70


def timestamp(value):
    if not value: return datetime(1970,1,1,tzinfo=timezone.utc)
    try: return datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError: return datetime(1970,1,1,tzinfo=timezone.utc)


def expected_home_margin(home,away,neutral=False):
    return (home-away)/ELO_TO_POINTS + (0 if neutral else HOME_ADV_PTS)


def win_prob(margin):
    # Logistic normal approximation using 13.5-point game variability.
    return 1/(1+math.exp(-margin/9.0))


def predict_from_state(game,ratings,recent):
    h,a=game['home_id'],game['away_id']
    er=ratings.get(h,START_ELO); ar=ratings.get(a,START_ELO)
    base=expected_home_margin(er,ar,bool(game.get('neutral')))
    hr=list(recent.get(h,[])); aa=list(recent.get(a,[]))
    # Elo already assimilates wins/margins: restrained, shrink-to-zero recent-form adjustment.
    form=(sum(z['margin'] for z in hr[-4:])/max(4,len(hr[-4:]))-
          sum(z['margin'] for z in aa[-4:])/max(4,len(aa[-4:]))) * .08
    margin=max(-50,min(50,base+form))
    hsc=[x['points_for'] for x in hr[-5:]]; asc=[x['points_for'] for x in aa[-5:]]
    hallow=[x['points_against'] for x in hr[-5:]]; aallow=[x['points_against'] for x in aa[-5:]]
    # Conservative average-shrunk scoring pace; not EPA or possession-adjusted.
    def shrunk(xs,prior=27.5,n=5): return (sum(xs)+prior*n)/(len(xs)+n)
    total=(shrunk(hsc)+shrunk(aallow)+shrunk(asc)+shrunk(hallow))/2
    total=max(30,min(85,total))
    home_points=(total+margin)/2
    away_points=(total-margin)/2
    return dict(home_margin=round(margin,1),home_win_prob=round(win_prob(margin),4),
                total=round(total,1),home_points=round(home_points,1),away_points=round(away_points,1),
                home_elo=round(er),away_elo=round(ar),home_form=round(form,1),
                home_games=len(hr),away_games=len(aa),model_version='elo_form_v0.1')


def build_predictions(games,as_of=None):
    """Returns pregame forecasts for all games. Updates ratings only after completed games.

    During retrospective replay, historical game results are applied even when as_of is later;
    for an as_of snapshot, results after cutoff are ignored.
    """
    ordered=sorted(games,key=lambda g:(timestamp(g.get('date')),g.get('id','')))
    as_of=timestamp(as_of) if isinstance(as_of,str) else as_of
    ratings={}; recent=defaultdict(lambda:deque(maxlen=8)); predictions=[]; season=None
    for g in ordered:
        if as_of and timestamp(g.get('date'))>as_of:
            # Future games are still predicted from pre-cutoff ratings; no future results used.
            pass
        if season is None: season=g['season']
        if g['season']!=season:
            ratings={k:START_ELO+REGRESSION*(v-START_ELO) for k,v in ratings.items()}
            recent=defaultdict(lambda:deque(maxlen=8))
            season=g['season']
        p=predict_from_state(g,ratings,recent)
        predictions.append({**g,**p})
        if not g.get('completed') or (as_of and timestamp(g.get('date'))>as_of): continue
        hs,as_=g.get('home_score'),g.get('away_score')
        if hs is None or as_ is None: continue
        h,a=g['home_id'],g['away_id']; raw=hs-as_
        prob=win_prob(p['home_margin'])
        result=1.0 if raw>0 else .5 if raw==0 else 0.0
        # Modest surprise multiplier, avoids reacting too much to blowouts.
        mult=min(2.0,max(.6,math.log1p(abs(raw))/math.log(15)))
        d=K*mult*(result-prob)
        ratings[h]=ratings.get(h,START_ELO)+d
        ratings[a]=ratings.get(a,START_ELO)-d
        recent[h].append({'margin':raw,'points_for':hs,'points_against':as_})
        recent[a].append({'margin':-raw,'points_for':as_,'points_against':hs})
    return predictions


def evaluation(rows):
    valid=[r for r in rows if r.get('completed') and r.get('home_score') is not None and r.get('away_score') is not None]
    if not valid: return {}
    mae_margin=sum(abs(r['home_margin']-(r['home_score']-r['away_score'])) for r in valid)/len(valid)
    mae_total=sum(abs(r['total']-(r['home_score']+r['away_score'])) for r in valid)/len(valid)
    brier=sum((r['home_win_prob']-(1 if r['home_score']>r['away_score'] else 0 if r['home_score']<r['away_score'] else .5))**2 for r in valid)/len(valid)
    correct=sum((r['home_margin']>0)==(r['home_score']>r['away_score']) for r in valid if r['home_score']!=r['away_score'])
    n_decided=sum(r['home_score']!=r['away_score'] for r in valid)
    return {'games':len(valid),'winner_accuracy':correct/n_decided if n_decided else None,
            'margin_mae':mae_margin,'total_mae':mae_total,'brier':brier}
