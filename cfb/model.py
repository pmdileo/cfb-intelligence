"""Time-ordered, score-based CFB rating model.

No yards/play, NIL, injuries or lines are inferred from scoreboard scores.
All feature calculations use only games already completed before kickoff.
"""
from __future__ import annotations
import math
from collections import defaultdict, deque
from datetime import datetime, timezone

START_ELO = 1500.0
HOME_ADV_PTS = 2.5
ELO_TO_POINTS = 25.0
K = 24.0
REGRESSION = .70
LEAGUE_PPG = 27.5


def timestamp(value):
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def expected_home_margin(home, away, neutral=False):
    return (home - away) / ELO_TO_POINTS + (0 if neutral else HOME_ADV_PTS)


def win_prob(margin):
    return 1 / (1 + math.exp(-margin / 9.0))


def _avg(values, prior=LEAGUE_PPG, prior_games=4):
    return (sum(values) + prior * prior_games) / (len(values) + prior_games)


def _features(team, recent):
    games = list(recent.get(team, []))
    last = games[-5:]
    home = [g for g in games if g['location'] == 'home'][-5:]
    away = [g for g in games if g['location'] == 'away'][-5:]
    yp = [g['yards_per_play'] for g in last if g.get('yards_per_play') is not None]
    yp_allowed = [g['opp_yards_per_play'] for g in last if g.get('opp_yards_per_play') is not None]
    return {
        'ypp': sum(yp)/len(yp) if yp else None,
        'ypp_allowed': sum(yp_allowed)/len(yp_allowed) if yp_allowed else None,
        'ypp_samples': len(yp),
        'games': len(games), 'ppg': _avg([g['points_for'] for g in last]),
        'allowed': _avg([g['points_against'] for g in last]),
        'margin': sum(g['margin'] for g in last) / max(4, len(last)),
        'sos': sum(g['opponent_elo'] - START_ELO for g in last) / max(4, len(last)),
        'home_margin': sum(g['margin'] for g in home) / len(home) if home else None,
        'away_margin': sum(g['margin'] for g in away) / len(away) if away else None,
        'home_games': len(home), 'away_games': len(away),
    }


def predict_from_state(game, ratings, recent):
    h, a = game['home_id'], game['away_id']
    er, ar = ratings.get(h, START_ELO), ratings.get(a, START_ELO)
    neutral = bool(game.get('neutral'))
    hf, af = _features(h, recent), _features(a, recent)
    elo_contribution = (er - ar) / ELO_TO_POINTS
    venue_contribution = 0 if neutral else HOME_ADV_PTS
    form_contribution = .08 * (hf['margin'] - af['margin'])
    # Differences in prior opponent strength temper the raw recent-score adjustment.
    sos_adjustment = .08 * (hf['sos'] - af['sos']) / ELO_TO_POINTS
    # Optional historical box-score data; a missing value contributes zero, not a fabricated statistic.
    # This heuristic must be evaluated on held-out seasons before trusting its weight.
    ypp_contribution = 0.0
    if hf['ypp'] is not None and af['ypp_allowed'] is not None and af['ypp'] is not None and hf['ypp_allowed'] is not None:
        ypp_contribution = max(-5., min(5., 1.2 * ((hf['ypp'] - af['ypp_allowed']) - (af['ypp'] - hf['ypp_allowed']))))
    margin = max(-50, min(50, elo_contribution + venue_contribution + form_contribution + sos_adjustment + ypp_contribution))
    total = max(30, min(85, (hf['ppg'] + af['allowed'] + af['ppg'] + hf['allowed']) / 2))
    hp, ap = (total + margin) / 2, (total - margin) / 2
    return {
        'home_margin': round(margin, 1), 'home_win_prob': round(win_prob(margin), 4),
        'total': round(total, 1), 'home_points': round(hp, 1), 'away_points': round(ap, 1),
        'home_elo': round(er), 'away_elo': round(ar),
        'home_form': round(form_contribution, 1), 'home_games': hf['games'], 'away_games': af['games'],
        'ypp_contribution': round(ypp_contribution, 2),
        'home_ypp': hf['ypp'], 'away_ypp': af['ypp'],
        'home_ypp_allowed': hf['ypp_allowed'], 'away_ypp_allowed': af['ypp_allowed'],
        'home_ypp_samples': hf['ypp_samples'], 'away_ypp_samples': af['ypp_samples'],
        'elo_contribution': round(elo_contribution, 2), 'venue_contribution': round(venue_contribution, 2),
        'form_contribution': round(form_contribution, 2), 'sos_contribution': round(sos_adjustment, 2),
        'home_ppg': round(hf['ppg'], 1), 'away_ppg': round(af['ppg'], 1),
        'home_allowed': round(hf['allowed'], 1), 'away_allowed': round(af['allowed'], 1),
        'home_sos_elo': round(hf['sos']), 'away_sos_elo': round(af['sos']),
        'home_home_margin': None if hf['home_margin'] is None else round(hf['home_margin'], 1),
        'away_away_margin': None if af['away_margin'] is None else round(af['away_margin'], 1),
        'home_home_games': hf['home_games'], 'away_away_games': af['away_games'],
        'model_version': 'elo_score_box_v0.3',
    }


def build_predictions(games, as_of=None, boxscores=None):
    """Replay chronologically; apply a finished game's result only after its kickoff.

    With as_of supplied, do not apply results for games later than the cutoff.
    Predictions beyond cutoff are simulated from the last available cutoff state.
    """
    boxscores = boxscores or {}
    ordered = sorted(games, key=lambda g: (timestamp(g.get('date')), str(g.get('id', ''))))
    as_of = timestamp(as_of) if isinstance(as_of, str) else as_of
    ratings = {}
    recent = defaultdict(lambda: deque(maxlen=8))
    forecasts = []
    season = None
    for g in ordered:
        if season is None:
            season = g['season']
        if g['season'] != season:
            ratings = {k: START_ELO + REGRESSION * (v - START_ELO) for k, v in ratings.items()}
            recent = defaultdict(lambda: deque(maxlen=8))
            season = g['season']
        p = predict_from_state(g, ratings, recent)
        forecasts.append({**g, **p})
        if not g.get('completed') or (as_of and timestamp(g.get('date')) > as_of):
            continue
        hs, aws = g.get('home_score'), g.get('away_score')
        if hs is None or aws is None:
            continue
        h, a = g['home_id'], g['away_id']
        raw = hs - aws
        er, ar = ratings.get(h, START_ELO), ratings.get(a, START_ELO)
        prob = win_prob(p['home_margin'])
        result = 1.0 if raw > 0 else .5 if raw == 0 else 0.0
        mult = min(2.0, max(.6, math.log1p(abs(raw)) / math.log(15)))
        delta = K * mult * (result - prob)
        ratings[h], ratings[a] = er + delta, ar - delta
        box = boxscores.get(str(g['id']), {})
        hbox = box.get(str(h), {})
        abox = box.get(str(a), {})
        recent[h].append({'margin': raw, 'points_for': hs, 'points_against': aws,
                          'opponent_elo': ar, 'location': 'neutral' if g.get('neutral') else 'home',
                          'yards_per_play': hbox.get('yards_per_play'),
                          'opp_yards_per_play': abox.get('yards_per_play')})
        recent[a].append({'margin': -raw, 'points_for': aws, 'points_against': hs,
                          'opponent_elo': er, 'location': 'neutral' if g.get('neutral') else 'away',
                          'yards_per_play': abox.get('yards_per_play'),
                          'opp_yards_per_play': hbox.get('yards_per_play')})
    return forecasts


def evaluation(rows):
    valid = [r for r in rows if r.get('completed') and r.get('home_score') is not None and r.get('away_score') is not None]
    if not valid:
        return {}
    n = len(valid)
    decided = [r for r in valid if r['home_score'] != r['away_score']]
    return {
        'games': n,
        'winner_accuracy': sum((r['home_margin'] > 0) == (r['home_score'] > r['away_score']) for r in decided) / len(decided) if decided else None,
        'margin_mae': sum(abs(r['home_margin'] - (r['home_score'] - r['away_score'])) for r in valid) / n,
        'total_mae': sum(abs(r['total'] - (r['home_score'] + r['away_score'])) for r in valid) / n,
        'brier': sum((r['home_win_prob'] - (1 if r['home_score'] > r['away_score'] else 0 if r['home_score'] < r['away_score'] else .5)) ** 2 for r in valid) / n,
    }

