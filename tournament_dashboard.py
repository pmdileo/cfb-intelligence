"""Experimental CFB model tournament; run: streamlit run tournament_dashboard.py."""
import pandas as pd
import streamlit as st
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.market_lines import load_lines
from cfb.model import build_predictions
from cfb.shadow_ratings import replay
from cfb.tournament import tournament, calibration_rows, picks_record

st.set_page_config(page_title='CFB Model Tournament',page_icon='🏈',layout='wide')
st.title('🏈 CFB Model Tournament · Experimental')
st.warning('RESEARCH ONLY — chronological retrospective replay, not saved pregame forecasts. Historical market lines have UNVERIFIED timing; ATS/O-U records are illustrative, not verified betting results.')
games=load_games()
if not games:
    st.error('No games data. Run the usual data refresh first.');st.stop()
all_seasons=sorted({int(g['season']) for g in games if g.get('completed')})
seasons=st.multiselect('Evaluation seasons',all_seasons,default=[s for s in all_seasons if s>=2023])
if not seasons:
    st.info('Select at least one season.');st.stop()

@st.cache_data(show_spinner='Computing both chronological models…')
def predictions():
    games=load_games()
    return build_predictions(games,boxscores=load_boxscores()), replay(games)

baseline,shadow=predictions()
r=tournament(baseline,shadow,load_lines(),seasons)
st.caption(f"{r['paired_games']:,} paired completed games. Same game IDs for both models; no new production forecasts are published.")
if not r['paired_games']:
    st.warning('No completed paired games in the selected seasons.');st.stop()
a,b=r['overall']['baseline'],r['overall']['shadow']
cols=st.columns(4)
for col,name,key,fmt in zip(cols,['Winner accuracy','Margin MAE','Total MAE','Brier score'],['winner_accuracy','margin_mae','total_mae','brier'],['.1%','.2f','.2f','.4f']):
    av=a[key];bv=b[key]
    col.metric(name,'—' if bv is None else format(bv,fmt),delta=None if av is None or bv is None else f'Baseline: {format(av,fmt)}')
st.subheader('Season-by-season head-to-head')
rows=[]
for x in r['summary']:
    rows.append({'Season':x['season'],'Games':x['baseline']['games'],
                 'Elo winner %':x['baseline']['winner_accuracy'], 'Shadow winner %':x['shadow']['winner_accuracy'],
                 'Elo margin MAE':x['baseline']['margin_mae'],'Shadow margin MAE':x['shadow']['margin_mae'],
                 'Elo total MAE':x['baseline']['total_mae'],'Shadow total MAE':x['shadow']['total_mae'],
                 'Elo Brier':x['baseline']['brier'],'Shadow Brier':x['shadow']['brier']})
st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
st.subheader('Historical market grading · timing unverified')
for kind,label in [('ats','Against spread'),('ou','Over / under')]:
    cols=st.columns(2)
    for col,model in zip(cols,('baseline','shadow')):
        record=picks_record(r['details'],model,kind)
        col.metric(f'{model.title()} · {label}',f"{record['win']}–{record['loss']}",f"{record['no_line']} without lines · {record['push']} pushes · {record['no_pick']} no pick")
st.caption('A win/loss here compares predictions to the currently stored historical consensus; it is NOT verified pregame betting performance.')
st.subheader('Largest model disagreements')
df=pd.DataFrame(r['details']).sort_values('model_disagreement',ascending=False)
st.dataframe(df[['season','week','matchup','actual_margin','baseline_margin','shadow_margin','model_disagreement','historical_market_home_margin','historical_market_total']],hide_index=True,use_container_width=True)
st.download_button('Download paired game diagnostics (CSV)',df.to_csv(index=False),file_name='cfb-model-tournament.csv',mime='text/csv')
st.subheader('Probability calibration')
choice=st.radio('Model',('baseline','shadow'),horizontal=True)
calibration=pd.DataFrame(calibration_rows(r['details'],choice))
if not calibration.empty:
    st.line_chart(calibration.set_index('bin')[['mean_probability','observed_home_win_rate']])
    st.dataframe(calibration,hide_index=True,use_container_width=True)
st.info('Held-out validity requires predeclared parameters and previously untouched test seasons. These diagnostics do not establish a wagering advantage or automatically promote a model.')
