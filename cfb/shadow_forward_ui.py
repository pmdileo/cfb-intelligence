"""Compact genuine archived Shadow Research forward results, separate from Elo."""
import streamlit as st
from .shadow_forward import forward_results


def render_shadow_forward(games):
    report=forward_results(games)
    st.markdown('**Shadow Research · Saved pregame record**')
    if not report['graded_games']:
        st.caption(f"{report['archived_games']} future/pregame Shadow snapshots archived; no completed forward games graded yet.")
        return
    a,b=st.columns(2)
    value=report['winner_accuracy']
    a.metric('Winner accuracy',f'{value:.1%}' if value is not None else '—')
    b.metric('Margin MAE',f"{report['margin_mae']:.1f} pts")
    st.caption(f"{report['graded_games']} completed frozen forecasts. Research only; no sportsbook-grade ATS results.")
