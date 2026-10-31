"""Week-scoped EDGE UI; delegates expanded details to Matchup Center renderer."""
import pandas as pd
import streamlit as st
from cfb.edge_scanner import scan_edges

def render_edge_week(forecasts, shadows, odds, now, season, week, render_matchup):
    st.subheader(f'EDGE · {season} Week {week}')
    st.caption('Only the selected season and week. Edge means model–market gap, not demonstrated betting profitability.')
    a,b,c=st.columns([1.2,1,1.4])
    minimum=a.slider('Minimum edge (points)',0.5,15.0,4.5,0.5,key='edge_threshold')
    market=b.selectbox('Market',['Both','ATS','O/U'],key='edge_market')
    agreement=c.selectbox('Agreement',['Both models agree','Either model (research)'],key='edge_agreement')=='Both models agree'
    week_games=[g for g in forecasts if int(g['season'])==int(season) and int(g['week'])==int(week)]
    rows=scan_edges(week_games,shadows,odds,now=now,min_edge=minimum,require_agreement=agreement,kind=market)
    st.metric('Qualified market discrepancies',len(rows))
    if not rows:
        st.info('No qualifying games for this specific week with eligible, recently observed sportsbook lines.')
        return
    st.dataframe(pd.DataFrame([{
        'Matchup':f'{r["away"]} @ {r["home"]}', 'Market':r['kind'], 'Side':r['side'],
        'Minimum gap':r['edge_points'], 'Elo gap':r['elo_edge'], 'Shadow gap':r['shadow_edge'],
        'Consensus line':r['market_line'],'Kickoff (UTC)':r['kickoff']}
        for r in rows]),hide_index=True,use_container_width=True)
    # A game can qualify for BOTH spread and total: show its full matchup only once.
    ids=[]
    for r in rows:
        if r['id'] not in ids: ids.append(r['id'])
    by_id={str(g['id']):g for g in week_games}
    for gid in ids:
        signals=[r for r in rows if r['id']==gid]
        st.markdown('**EDGE reason:** '+ ' · '.join(f'{r["kind"]}: {r["side"]}, {r["edge_points"]:.1f}-pt gap' for r in signals))
        # Identical rendering as Matchup Center, including ALL diagnostics and sportsbook details.
        render_matchup(by_id[gid])
