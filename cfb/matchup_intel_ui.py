"""Compact matchup diagnostics that can be embedded in existing game cards."""
import pandas as pd
import streamlit as st
from .matchup_intel import matchup_insights, abbreviated_team


def render_spread(row):
    """Avoid truncation from large st.metric team-name values."""
    margin = float(row['home_margin'])
    favorite = row['home'] if margin >= 0 else row['away']
    st.metric('Model spread', f'{abbreviated_team(favorite)} -{abs(margin):.1f}',
              help=f'Full favorite: {favorite}. Not a sportsbook spread.')


def render_intelligence(row):
    data=matchup_insights(row)
    st.markdown('#### Matchup intelligence')
    st.caption('Pregame model factors and observed team trends; not independent ESPN or sportsbook forecasts.')
    cols=st.columns(3)
    for col, x in zip(cols, [
        ('Power-rating gap', (float(row['home_elo'])-float(row['away_elo'])), 'Elo points; positive favors home'),
        ('Home recent PPG', row['home_ppg'], 'Smoothed points scored'),
        ('Away recent PPG', row['away_ppg'], 'Smoothed points scored'),
    ]):
        label,value,help_text=x
        col.metric(label, f'{value:+.0f}' if label=='Power-rating gap' else f'{value:.1f}', help=help_text)
    if data['facts']:
        st.dataframe(pd.DataFrame(data['facts'])[['metric','home','away','leader']].rename(columns={
            'metric':'Measure','home':str(row['home']),'away':str(row['away']),'leader':'Advantage'}),
            hide_index=True, use_container_width=True)
    st.markdown('**Projected margin breakdown**')
    chart=pd.DataFrame([{'Factor':p['label'],'Points toward home':p['points']}
                        for p in data['contributions']]).set_index('Factor')
    st.bar_chart(chart)
    st.caption(f"Data availability: {data['evidence']} · Prior YPP samples: "
               f"{row['home']} {data['home_ypp_samples']}; {row['away']} {data['away_ypp_samples']}.")
    with st.expander('How to interpret these figures'):
        st.write('Positive margin contributions favor the home team; negative contributions favor the away team. '
                 'Elo and form are not independent measures. Scoring rates are smoothed. '
                 'Venue contribution is currently a fixed assumption. '
                 'An absent stat is never treated as a measured zero. '
                 'This table explains the existing prediction; it does not add new variables to the prediction model.')
