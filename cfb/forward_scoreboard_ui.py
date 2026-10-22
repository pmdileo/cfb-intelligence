"""Compact paired pregame Elo vs Shadow results for main Streamlit dashboard."""
import pandas as pd
import streamlit as st
from .forward_scoreboard import build_scoreboard


def render_forward_scoreboard(games):
    r = build_scoreboard(games)
    st.subheader('Forward Model Scoreboard · Actual Pregame Captures')
    st.caption('First saved pre-kickoff Elo and Shadow forecasts, compared only on the same completed games. Research-only Shadow is not the official pick.')
    a, b, c = st.columns(3)
    a.metric('Archived Elo games', r['archived_elo_games'])
    b.metric('Archived Shadow games', r['archived_shadow_games'])
    c.metric('Completed paired games', r['graded_paired_games'])
    if not r['graded_paired_games']:
        st.info('Both models have pregame archives, but no matching completed games have been graded yet. The scoreboard will populate as those games finish.')
        return
    cols = st.columns(2)
    for col, model, name in zip(cols, ('elo', 'shadow'), ('Official Elo', 'Shadow Research')):
        m = r['overall'][model]
        with col:
            st.markdown('**' + name + '**')
            st.metric('Winner accuracy', f"{m['winner_accuracy']:.1%}" if m['winner_accuracy'] is not None else '—')
            st.metric('Margin MAE', f"{m['margin_mae']:.2f} pts")
            st.metric('Total MAE', f"{m['total_mae']:.2f} pts")
            st.metric('Brier score', f"{m['brier']:.4f}")
    st.markdown('**Completed head-to-head games**')
    df = pd.DataFrame(r['rows'])
    show = ['season','week','matchup','actual_margin','elo_margin','shadow_margin','margin_disagreement','models_disagree']
    st.dataframe(df[show], hide_index=True, use_container_width=True)
    st.download_button('Download paired forward picks (CSV)', df.to_csv(index=False),
                       file_name='cfb-forward-paired-picks.csv', mime='text/csv')
    st.caption(r['limitations'])
