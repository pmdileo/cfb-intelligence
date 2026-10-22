"""Compact matchup display with unclipped spreads and transparent model differences."""
from __future__ import annotations
import streamlit as st


def _side(game):
    m=float(game['home_margin'])
    if abs(m)<0.05: return 'Pick’em', 'PK'
    return (game['home'] if m>0 else game['away']), f'-{abs(m):.1f}'


def render_official_spread(game):
    side,number=_side(game)
    st.caption('Model spread · official Elo')
    st.markdown(f'**{side}**')
    st.metric('Projected line',number,help='Model projection, not a sportsbook quote.')


def render_shadow_card(official,shadow):
    st.markdown('**Shadow Research Pick**')
    if not shadow:
        st.caption('Experimental Shadow prediction unavailable for this matchup.')
        return
    side,line=_side(shadow)
    st.markdown(f'**{side}**')
    st.metric('Shadow projected line',line)
    st.caption(f"Projected score: {shadow['away']} {float(shadow['away_points']):.0f} – "
               f"{shadow['home']} {float(shadow['home_points']):.0f}")
    st.caption(f"Projected total: {float(shadow['total']):.1f} · "
               f"Home win probability: {float(shadow['home_win_prob']):.1%}")
    if official:
        delta=float(shadow['home_margin'])-float(official['home_margin'])
        st.caption(f'Shadow vs official margin: {delta:+.1f} points (home perspective)')
        if float(shadow['home_margin'])*float(official['home_margin'])<0:
            st.warning('Models disagree on the projected winner.')
    st.caption('EXPERIMENTAL · Reconstructed research projection, not the official pick. '
               'Historical state uses an assumed four-hour result delay.')
