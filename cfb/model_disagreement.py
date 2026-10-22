"""Explain current Elo-versus-Shadow forecasts using recorded model components.

Read-only analysis. Never claim a causal football explanation beyond model inputs.
"""
from __future__ import annotations


def describe(official, shadow):
    """Return auditable breakdown of each model's home minus away margin."""
    if not official or not shadow:
        return None
    e = float(official['home_margin'])
    s = float(shadow['home_margin'])
    keys = (
        ('Elo rating difference', 'elo_contribution'),
        ('Home field', 'venue_contribution'),
        ('Recent scoring form', 'form_contribution'),
        ('Recent opponent strength', 'sos_contribution'),
        ('Yards per play', 'ypp_contribution'),
    )
    elo_parts = [{'factor': label, 'points_to_home': float(official.get(k) or 0)} for label,k in keys]
    elo_parts.append({'factor': 'Rounding / caps', 'points_to_home': round(e - sum(r['points_to_home'] for r in elo_parts), 4)})
    required = ('shadow_home_offense_offset','shadow_away_offense_offset',
                'shadow_home_defense_offset','shadow_away_defense_offset',
                'shadow_home_field_per_team')
    available = all(shadow.get(k) is not None for k in required)
    shadow_parts = []
    if available:
        # Shadow margin = home points - away points. Positive values favor home.
        shadow_parts = [
            {'factor': 'Home offensive rating', 'points_to_home': float(shadow['shadow_home_offense_offset'])},
            {'factor': 'Away defensive resistance', 'points_to_home': -float(shadow['shadow_away_defense_offset'])},
            {'factor': 'Away offensive rating', 'points_to_home': -float(shadow['shadow_away_offense_offset'])},
            {'factor': 'Home defensive resistance', 'points_to_home': float(shadow['shadow_home_defense_offset'])},
            {'factor': 'Home field', 'points_to_home': 2*float(shadow['shadow_home_field_per_team'])},
        ]
        shadow_parts.append({'factor': 'Score floor / rounding',
                             'points_to_home': round(s - sum(r['points_to_home'] for r in shadow_parts),4)})
    sign_disagree = (e > 0 > s) or (s > 0 > e)
    return {
        'elo_margin': e, 'shadow_margin': s, 'shadow_minus_elo': s-e,
        'opposite_winners': sign_disagree,
        'elo_parts': elo_parts, 'shadow_parts': shadow_parts,
        'has_exact_shadow_parts': available,
        'elo_total': float(official['total']), 'shadow_total': float(shadow['total']),
    }
