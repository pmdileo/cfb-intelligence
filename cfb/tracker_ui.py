"""Streamlit presentation for independently graded three-part matchup strips."""
import html
import streamlit as st
from .tracker import tracker_rows, record

STYLE={'win':('#17683c','#e5f5e9','✓ WIN'),'loss':('#a72c31','#fbe8e8','✕ LOSS'),
       'push':('#666','#f0f0f0','— PUSH'),'pending':('#666','#f0f0f0','◷ PENDING'),
       'no_line':('#666','#f0f0f0','— NO LINE'),'no_pick':('#666','#f0f0f0','— NO PICK')}

def render_tracker(games, archive_path=None):
    from .snapshots import DEFAULT_PATH
    rows=tracker_rows(games, archive_path or DEFAULT_PATH)
    st.subheader('Live prediction tracker')
    st.caption('Only the first saved forecast made before kickoff counts; no retroactive picks. ATS and O/U require a pregame saved market line.')
    if not rows:
        st.info('No pregame forecasts archived yet. The scheduled collector will begin recording upcoming games.')
        return
    seasons=sorted({r['season'] for r in rows},reverse=True)
    season=st.selectbox('Tracker season',seasons,key='tracker_season')
    all_season=[r for r in rows if r['season']==season]
    weeks=sorted({r['week'] for r in all_season})
    week=st.selectbox('Tracker week',weeks,index=len(weeks)-1,key='tracker_week')
    for title,group in [('This week',[r for r in all_season if r['week']==week]),('Season to date',all_season)]:
        st.markdown('**'+title+'**')
        cols=st.columns(3)
        for c,k,label in zip(cols,['su','ats','ou'],['Winner (SU)','Against spread (ATS)','Over / Under']):
            result=record(group,k)
            value=f"{result['wins']}–{result['losses']}"
            if result['pushes']: value+=f" ({result['pushes']} pushes)"
            c.metric(label,value, f"{result['pct']:.1%} win rate" if result['pct'] is not None else 'Awaiting graded picks')
    st.markdown('**Archived matchups**')
    for r in (x for x in all_season if x['week']==week):
        game_name=html.escape(str(r['away']))+' @ '+html.escape(str(r['home']))
        title=f"{game_name} · Model {r['away_points']:.0f}–{r['home_points']:.0f}"
        if r['completed'] and r['home_score'] is not None:
            title+=f" · Final {r['away_score']}–{r['home_score']}"
        st.markdown(f'**{title}**',unsafe_allow_html=True)
        cells=[]
        for key,label in [('su','WINNER (SU)'),('ats','SPREAD (ATS)'),('ou','OVER / UNDER')]:
            state=r['status'][key]; fg,bg,status=STYLE[state]
            cells.append(f'<div style="flex:1;min-width:0;border-radius:8px;padding:12px 4px;text-align:center;background:{bg};color:{fg}"><div style="font-size:0.73em;font-weight:bold">{label}</div><div style="font-size:0.9em;font-weight:bold">{status}</div></div>')
        st.markdown('<div style="display:flex;gap:5px;margin-bottom:16px">'+''.join(cells)+'</div>',unsafe_allow_html=True)
