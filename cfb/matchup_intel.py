"""Transparent diagnostic layer for CFB Intelligence v0.4.3.

Uses only pregame fields already computed by the current chronological
scoreboard model. Does not manufacture EPA, coaching values or market odds.
"""
from __future__ import annotations
import math


def _num(row, field):
    value = row.get(field)
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def abbreviated_team(name):
    """Get a legible short name without an unmaintainable school lookup."""
    words = str(name or '').split()
    if not words:
        return 'Unknown'
    if len(words) == 1:
        return words[0]
    # Common mascot endings retained for a short, human-friendly display.
    return words[-1]


def factors(row):
    """Point-contribution factors with user-facing explanations."""
    names = (
        ('elo_contribution', 'Team power (Elo)', 'Existing relative Elo ratings'),
        ('venue_contribution', 'Home field', 'Fixed model venue adjustment; not venue-specific measured advantage'),
        ('form_contribution', 'Recent form', 'Last-five scoring margins'),
        ('sos_contribution', 'Opponent strength', 'Prior opponent Elo adjustment'),
        ('ypp_contribution', 'Yards/play', 'Available prior completed-game box scores only'),
    )
    return [dict(key=k, label=label, description=description, points=_num(row, k) or 0.0)
            for k, label, description in names]


def matchup_insights(row):
    """Deterministic summaries of observed model inputs; not extra forecasts."""
    h, a = row.get('home', 'Home'), row.get('away', 'Away')
    facts=[]
    for title, hk, ak, low_good in (
        ('Recent points scored/game', 'home_ppg', 'away_ppg', False),
        ('Recent points allowed/game', 'home_allowed', 'away_allowed', True),
        ('Pregame Elo', 'home_elo', 'away_elo', False),
    ):
        hv, av = _num(row, hk), _num(row, ak)
        if hv is None or av is None:
            continue
        delta = hv - av
        if abs(delta) < (0.5 if 'Elo' not in title else 5):
            leader='Even'
        elif (delta < 0) == low_good:
            leader=h
        else:
            leader=a
        facts.append(dict(metric=title, home=hv, away=av, leader=leader,
                          difference=abs(delta)))
    hs, as_ = _num(row,'home_ypp_samples') or 0, _num(row,'away_ypp_samples') or 0
    ypp_usable = min(hs, as_) > 0
    evidence = 'Limited box-score coverage' if not ypp_usable else (
        'Partial box-score coverage' if min(hs, as_) < 3 else 'Box scores available for both teams')
    return dict(facts=facts, evidence=evidence, home_ypp_samples=int(hs),
                away_ypp_samples=int(as_), ypp_usable=ypp_usable,
                contributions=factors(row))
