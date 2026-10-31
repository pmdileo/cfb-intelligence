"""Short factual game overview, explicitly not live injuries/news."""
import streamlit as st
from .nil_comparison import compare, load


def render_quick_brief(game, shadows):
    st.markdown('**Game snapshot**')
    st.write(f"{game['away']} at {game['home']} · Week {game['week']} · {game['date']} (UTC)")
    st.write(f"Elo model: {game['away_points']:.1f}–{game['home_points']:.1f} (away–home); total {game['total']:.1f}.")
    shadow=shadows.get(str(game['id']))
    if shadow:
        st.write(f"Shadow: {shadow['away_points']:.1f}–{shadow['home_points']:.1f} (away–home).")
    st.caption('Generated exclusively from stored matchup data. Live injuries, coaching changes and news are not verified here.')


def render_nil_panel(game, team_estimates=None):
    values=compare(game['away'],game['home'],team_estimates if team_estimates is not None else load())
    st.markdown('**NIL / roster investment comparison**')
    for team,key in [(game['away'],'away'),(game['home'],'home')]:
        item=values[key]
        if item:
            st.write(f"{team}: ${item['low_millions']:.1f}M–${item['high_millions']:.1f}M · {item['metric']}")
            st.caption(f"As of {item['as_of']} · Source: {item['source_url']} · {item.get('method','Estimate')}")
        else:
            st.write(f'{team}: Not verified')
    if values['comparable']:
        gap=values['gap']
        st.caption(f'Estimated midpoint differential (away minus home): {gap:+.1f}M USD')
        if abs(gap)>=10:
            st.warning('Large estimated investment gap (≥$10M): descriptive only; not a validated prediction factor.')
    else:
        st.caption('Differential unavailable: both teams need comparable, sourced estimates from the same year and metric.')
