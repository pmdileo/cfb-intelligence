"""Conservative *assumed-delay* chronological replay for CFB research.

Final availability is approximated as kickoff + four hours. This is not a
verified final-whistle timestamp and is NOT a saved/immutable pregame pick.
Does not change the production model or its prediction archive.
"""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from heapq import heappush, heappop
from math import log, log1p
from . import model, shadow_ratings

DELAY_HOURS = 4.0


def _kickoff(game):
    return shadow_ratings.kickoff(game)


def _ready(game, hours):
    return _kickoff(game) + timedelta(hours=hours)


def _ordered(games):
    return sorted(games, key=lambda g: (_kickoff(g), str(g.get('id',''))))


def _eligible(g, cutoff):
    return bool(g.get('completed') and g.get('home_score') is not None
                and g.get('away_score') is not None
                and (cutoff is None or _ready(g, DELAY_HOURS) <= cutoff))


def _cutoff(as_of):
    if as_of is None: return None
    d = _kickoff({'date':as_of}) if isinstance(as_of,str) else as_of
    if d.tzinfo is None: raise ValueError('as_of must be timezone-aware')
    return d.astimezone(timezone.utc)


def replay_shadow(games, *, delay_hours=DELAY_HOURS, as_of=None):
    """Delay past results until assumed availability before updating ratings.

    For an as_of snapshot, results whose availability is after cutoff are excluded.
    Historical forecasts for games after cutoff remain hypothetical projections.
    """
    if delay_hours <= 0: raise ValueError('delay_hours must be positive')
    from itertools import groupby
    cutoff = _cutoff(as_of)
    offense, defense = defaultdict(float), defaultdict(float)
    pending = []
    output = []
    season = None
    sequence = 0
    for start, batch_it in groupby(_ordered(games), key=_kickoff):
        batch = list(batch_it)
        # Apply eligible old-season finals before the one-time season regression.
        current_season = int(batch[0]['season'])
        while pending and pending[0][0] <= start and (cutoff is None or pending[0][0] <= cutoff):
            _, _, g, p = heappop(pending)
            home, away = str(g['home_id']), str(g['away_id'])
            he = float(g['home_score']) - p['home_points']
            ae = float(g['away_score']) - p['away_points']
            lr = shadow_ratings.LEARNING_RATE / 2
            offense[home] += lr * he; defense[away] -= lr * he
            offense[away] += lr * ae; defense[home] -= lr * ae
        if season is not None and current_season != season:
            for ratings in (offense, defense):
                for team in list(ratings): ratings[team] *= shadow_ratings.SEASON_RETENTION
        season = current_season
        for g in batch:
            p = shadow_ratings.predict(g, offense, defense)
            output.append({**g, **p, 'model_version':'shadow_research_delayed_v0.6.3',
                           'availability_assumption_hours':delay_hours})
            if g.get('completed') and g.get('home_score') is not None and g.get('away_score') is not None:
                at = _ready(g, delay_hours)
                if cutoff is None or at <= cutoff:
                    sequence += 1
                    heappush(pending,(at,sequence,g,p))
    return output


def replay_baseline(games, *, boxscores=None, delay_hours=DELAY_HOURS, as_of=None):
    """Replicate production Elo formula with delayed access to final scores.

    This is for FAIR retrospective research comparison, not a replacement for
    build_predictions() or official archived picks.
    """
    if delay_hours <= 0: raise ValueError('delay_hours must be positive')
    from itertools import groupby
    cutoff = _cutoff(as_of)
    boxscores = boxscores or {}
    ratings = {}
    recent = defaultdict(lambda:deque(maxlen=8))
    pending = []
    output = []
    season = None
    sequence = 0
    for start, batch_it in groupby(_ordered(games), key=_kickoff):
        batch = list(batch_it)
        current_season = int(batch[0]['season'])
        while pending and pending[0][0] <= start and (cutoff is None or pending[0][0] <= cutoff):
            _, _, g, p = heappop(pending)
            hs, aw = float(g['home_score']), float(g['away_score'])
            h, a = str(g['home_id']), str(g['away_id'])
            raw = hs-aw
            er, ar = ratings.get(h,model.START_ELO),ratings.get(a,model.START_ELO)
            prob = model.win_prob(p['home_margin'])
            result = 1 if raw>0 else .5 if raw==0 else 0
            mult = min(2.,max(.6,log1p(abs(raw))/log(15)))
            delta = model.K*mult*(result-prob)
            ratings[h],ratings[a] = er+delta,ar-delta
            box = boxscores.get(str(g['id']), {})
            hb,ab = box.get(h,{}),box.get(a,{})
            recent[h].append({'margin':raw,'points_for':hs,'points_against':aw,'opponent_elo':ar,
                'location':'neutral' if g.get('neutral') else 'home',
                'yards_per_play':hb.get('yards_per_play'),'opp_yards_per_play':ab.get('yards_per_play')})
            recent[a].append({'margin':-raw,'points_for':aw,'points_against':hs,'opponent_elo':er,
                'location':'neutral' if g.get('neutral') else 'away',
                'yards_per_play':ab.get('yards_per_play'),'opp_yards_per_play':hb.get('yards_per_play')})
        if season is not None and current_season != season:
            ratings = {k:model.START_ELO + model.REGRESSION*(v-model.START_ELO) for k,v in ratings.items()}
            recent = defaultdict(lambda:deque(maxlen=8))
        season = current_season
        for g in batch:
            p=model.predict_from_state(g,ratings,recent)
            output.append({**g,**p,'model_version':'elo_research_delayed_v0.6.3',
                           'availability_assumption_hours':delay_hours})
            if g.get('completed') and g.get('home_score') is not None and g.get('away_score') is not None:
                at = _ready(g, delay_hours)
                if cutoff is None or at <= cutoff:
                    sequence += 1
                    heappush(pending,(at,sequence,g,p))
    return output
