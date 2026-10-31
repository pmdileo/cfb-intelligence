"""Selected-model EDGE dashboard; Apex appears after real validated predictions exist."""
import streamlit as st
import pandas as pd
from .edge_multi import scan_selected


def render_edge_selected(forecasts, shadows, odds, now, season, week, render_matchup):
    st.subheader(f'EDGE · {season} Week {week}')
    st.caption('Select which available forecasts participate; no unsourced Apex values or retrospective betting confidence.')
    cols=st.columns(3)
    use_elo=cols[0].checkbox('Elo',value=True,key='edge_elo')
    use_shadow=cols[1].checkbox('Shadow',value=True,key='edge_shadow')
    cols[2].caption('Apex · coming after data validation')
    selected=[name for name,enabled in [('Elo',use_elo),('Shadow',use_shadow)] if enabled]
    a,b,c=st.columns(3)
    threshold=a.slider('Minimum gap (points)',0.5,15.0,4.5,0.5,key='edge_threshold')
    kind=b.selectbox('Market',['Both','ATS','O/U'],key='edge_market')
    mode=c.selectbox('Model rule',['All selected agree','Any selected model'],key='edge_agreement')
    lookup={'Elo':{str(g['id']):g for g in forecasts}, 'Shadow':shadows}
    signals=scan_selected(forecasts,lookup,odds,season=season,week=week,models=selected,
                          threshold=threshold,agreement='all' if mode.startswith('All') else 'any',
                          market_kind=kind,now=now)
    st.metric('Eligible signals',len(signals))
    if not signals:
        st.info('No eligible games for these filters with recent, pregame sportsbook lines.')
        return
    st.dataframe(pd.DataFrame([{'Matchup':f"{x['game']['away']} @ {x['game']['home']}",
                                'Market':x['kind'],'Side':x['side'],'Gap':x['gap'],
                                'Models':', '.join(f'{n} {v:+.1f}' for n,v in x['differences'].items()),
                                'Kickoff':x['game']['date']} for x in signals]),
                 hide_index=True,use_container_width=True)
    ids=[]
    for x in signals:
        if x['id'] not in ids:ids.append(x['id'])
    for gid in ids:
        relevant=[x for x in signals if x['id']==gid]
        st.caption(' · '.join(f"{x['kind']}: {x['side']} ({x['gap']:.1f}-pt gap)" for x in relevant))
        render_matchup(relevant[0]['game'])
