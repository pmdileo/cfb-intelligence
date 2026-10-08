"""CFB Intelligence v0.1: ranked matchup dashboard using free ESPN scoreboard data."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from cfb.data import load_games
from cfb.model import build_predictions,evaluation

st.set_page_config(page_title='CFB Intelligence',page_icon='🏈',layout='wide')
st.markdown('''<style>.block-container{padding-top:1.5rem;max-width:1300px}.small{color:#888;font-size:12px}</style>''',unsafe_allow_html=True)
st.title('🏈 CFB Intelligence')
st.caption('Private college football prediction dashboard · Independent statistical baseline · All times UTC')
raw=load_games()
if not raw:
    st.warning('No game data bundled yet. Run `python refresh.py` once (internet required), then reopen this page. Weekly updates run automatically after deployment.')
    st.stop()
meta_file=Path(__file__).parent/'data'/'metadata.json'
meta=json.loads(meta_file.read_text()) if meta_file.exists() else {}
forecasts=build_predictions(raw)
df=pd.DataFrame(forecasts)
seasons=sorted(df.season.unique().tolist(),reverse=True)
now=datetime.now(timezone.utc)
with st.sidebar:
    st.header('View options')
    season=st.selectbox('Season',seasons,index=0)
    available=sorted(df.loc[df.season==season,'week'].unique().tolist())
    cur=df[(df.season==season)&(df.date>=now.isoformat())]['week']
    default_week=int(cur.iloc[0]) if not cur.empty else max(available)
    week=st.selectbox('Week',available,index=available.index(default_week) if default_week in available else len(available)-1)
    ranked_only=st.toggle('Only games involving Top 25 teams',value=True)
    show_completed=st.toggle('Include completed games',value=True)
    st.divider()
    st.caption('Rankings are ESPN scoreboard event rankings, not independently reconstructed weekly AP poll snapshots.')
    st.caption(f"Last update: {meta.get('refreshed_utc','unknown')}")
    if meta.get('week_errors'): st.warning(f"{len(meta['week_errors'])} feed requests failed at refresh; data may be incomplete.")
subset=df[(df.season==season)&(df.week==week)].copy()
if ranked_only: subset=subset[subset.home_rank.notna()|subset.away_rank.notna()]
if not show_completed: subset=subset[~subset.completed]
subset=subset.sort_values('date')
a,b,c=st.columns(3)
a.metric('Games displayed',len(subset));b.metric('Season',season);c.metric('Week',week)
if subset.empty:
    st.info('No qualifying games in this week with the current data. Try another week or disable the Top 25 filter.')
else:
    st.subheader('Matchup center')
    names={str(r.id):f"{('#'+str(int(r.away_rank))+' ' if pd.notna(r.away_rank) else '')}{r.away} @ {('#'+str(int(r.home_rank))+' ' if pd.notna(r.home_rank) else '')}{r.home}" for r in subset.itertuples()}
    for g in subset.itertuples():
        key=str(g.id)
        with st.expander(names[key] + (' · FINAL' if g.completed else ''),expanded=False):
            lhs,rhs=st.columns([2,1])
            with lhs:
                x,y,z=st.columns(3)
                x.metric('Predicted score',f'{g.away_points:.0f} – {g.home_points:.0f}',help='Away – Home; decimals rounded for display')
                favorite=g.home if g.home_margin>0 else g.away
                y.metric('Predicted spread',f'{favorite} -{abs(g.home_margin):.1f}')
                z.metric('Predicted total',f'{g.total:.1f}')
                st.progress(float(g.home_win_prob),text=f'{g.home}: {g.home_win_prob:.1%} win probability')
                if g.completed: st.info(f'Final score: {g.away} {g.away_score} – {g.home} {g.home_score}')
                st.markdown('**How the model arrived here**')
                st.write(f'Pregame Elo: {g.away} **{g.away_elo}**, {g.home} **{g.home_elo}**. Recent-form contribution to home margin: **{g.home_form:+.1f} points**. Home field: **{"neutral" if g.neutral else "home advantage applied"}**.')
                st.caption(f'Previous same-season game samples: {g.away} {g.away_games}, {g.home} {g.home_games}. Early-season predictions rely more heavily on historical Elo and league-average scoring.')
            with rhs:
                st.markdown('**Market & expert comparisons**')
                st.write('ESPN pick: **not integrated**')
                st.write('CBS pick: **not integrated**')
                st.write('DraftKings: **unavailable**')
                st.write('FanDuel: **unavailable**')
                st.write('NIL spending difference: **unavailable**')
                st.write('Injuries / transfers: **not integrated**')
                st.caption('No invented market lines, expert predictions, or dollar estimates.')
            st.caption(f'Data: ESPN unofficial scoreboard · Model elo_form_v0.1 · {g.date} · {g.venue}')
            st.link_button('View ESPN game page',g.source_url)
            st.download_button('Export matchup JSON',json.dumps(pd.Series(g._asdict()).replace({float('nan'):None}).to_dict(),default=str,indent=2),file_name=f'game-{g.id}.json',key=f'dl{g.id}')
st.divider()
st.subheader('Model scorecard')
st.caption('Historical walk-forward scoring: each forecast is calculated before that game result updates ratings. These are in-sample design diagnostics, not independent out-of-sample betting results.')
completed=df[(df.season==season)&df.completed]
report=evaluation(completed.to_dict('records'))
if report:
    z1,z2,z3,z4=st.columns(4)
    z1.metric('Evaluated games',report['games'])
    z2.metric('Winner accuracy',f"{report['winner_accuracy']:.1%}" if report['winner_accuracy'] is not None else '—')
    z3.metric('Margin MAE',f"{report['margin_mae']:.1f} pts")
    z4.metric('Total MAE',f"{report['total_mae']:.1f} pts")
st.subheader('Download predictions')
cols=['season','week','date','away','home','away_rank','home_rank','home_margin','home_win_prob','total','away_points','home_points','completed','away_score','home_score','model_version']
st.download_button('Download this week as CSV',subset[cols].to_csv(index=False),file_name=f'cfb-{season}-week-{week}.csv',mime='text/csv')
with st.expander('Methodology, data limitations, and next upgrades'):
    st.markdown('''**Implemented:** historical/game-score ingestion, weekly ranked schedule, chronological Elo with offseason regression, modest recent form, rudimentary point totals, predicted score/spread/winner, one-click CSV/JSON export, model error tracking, and automation workflow.\n\n**Not yet implemented:** adjusted yards per game, EPA, strength of schedule explicitly, true AP poll archival rankings, verified injuries, coaching value added, recruiting, NIL investment, ESPN/CBS picks, sportsbook lines, or calibrated probability/total models. The 0–100 composite described in the product plan is not claimed to exist yet.\n\n**Important:** game score predictions are heuristic. Historical scorecard includes games already used for tuning assumptions and is not evidence of a profitable strategy. Data are obtained from an undocumented third-party scoreboard feed; refreshes may fail or rankings may be inconsistent. Ranking display is event-feed ranking and may not perfectly match official AP Top 25. Past picks are generated by walk-forward simulation; no pregame publication-time snapshots are archived yet.''')
