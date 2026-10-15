"""Optional Streamlit UI for source-level historical market transparency."""
import pandas as pd
import streamlit as st
from .market_audit import coverage_report, market_summary, provider_rows


def render_market_providers(market, home_name, away_name):
    if not market:
        return
    rows = provider_rows(market)
    if not rows:
        return
    with st.expander('Compare individual historical sportsbook lines'):
        display = []
        for row in rows:
            margin = row['home_margin']
            if margin is None:
                spread = '—'
            elif abs(margin) < 1e-9:
                spread = 'Pick’em'
            else:
                favorite = home_name if margin > 0 else away_name
                spread = f'{favorite} -{abs(margin):g}'
            display.append({'Sportsbook': row['provider'], 'Spread': spread,
                            'Total': '—' if row['total'] is None else f"{row['total']:g}"})
        st.dataframe(pd.DataFrame(display), hide_index=True, use_container_width=True)
        summary = market_summary(market)
        if summary['spread_range'] is not None:
            st.caption(f"Difference across listed spreads: {summary['spread_range']:.1f} points")
        if summary['total_range'] is not None:
            st.caption(f"Difference across listed totals: {summary['total_range']:.1f} points")
        st.caption('Historical CFBD lines; original pregame publication times unverified. '
                   'These are retrospective research comparisons, not live offers.')


def render_market_coverage(games, markets):
    rows = coverage_report(games, markets)
    with st.expander('Historical sportsbook data coverage'):
        st.caption('Percentage of imported ESPN scoreboard games with a matched historical market record. '
                   'This is not a measure of available sportsbooks or market accuracy.')
        display = pd.DataFrame([{
            'Season': r['season'], 'Games': r['games'], 'Matched': r['matched'],
            'With spread': r['spread_games'], 'With total': r['total_games'],
            'Coverage': f"{r['coverage_pct']}%", 'Top providers': r['providers'],
        } for r in rows])
        if not display.empty:
            st.dataframe(display, hide_index=True, use_container_width=True)
