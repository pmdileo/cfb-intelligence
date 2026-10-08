"""CFB Intelligence v0.2: free historical score-powered dashboard."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from cfb.data import load_games
from cfb.model import build_predictions, evaluation

st.set_page_config(page_title='CFB Intelligence', page_icon='🏈', layout='wide')
st.markdown('<style>.block-container{padding-top:1.5rem;max-width:1450px}</style>', unsafe_allow_html=True)
st.title('🏈 CFB Intelligence')
st.caption('v0.2 · Free, automated score-based predictions · All kickoff timestamps UTC')
raw = load_games()
if not raw:
    st.warning('No games yet. Run the GitHub Actions refresh workflow to download data.')
    st.stop()
meta_path = Path(__file__).parent / 'data' / 'metadata.json'
meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
with st.spinner('Computing chronological predictions…'):
    forecasts = build_predictions(raw)
df = pd.DataFrame(forecasts)
now = datetime.now(timezone.utc)
with st.sidebar:
    st.header('View options')
    seasons = sorted(df.season.unique().tolist(), reverse=True)
    season = st.selectbox('Season', seasons)
    weeks = sorted(df.loc[df.season == season, 'week'].unique().tolist())
    upcoming = df[(df.season == season) & (df.date >= now.isoformat())]['week']
    default_week = int(upcoming.iloc[0]) if not upcoming.empty else max(weeks)
    week = st.selectbox('Week', weeks, index=weeks.index(default_week) if default_week in weeks else len(weeks)-1)
    ranked_only = st.toggle('Only games involving Top 25 teams', value=True)
    show_completed = st.toggle('Include completed games', value=True)
    st.divider()
    st.caption('Top 25 event ranks come from the ESPN feed; they are not verified historical AP poll snapshots.')
    st.caption(f"Last successful refresh: {meta.get('refreshed_utc', 'unknown')}")
    if meta.get('week_errors'):
        st.warning(f"{len(meta['week_errors'])} weekly feed requests reported errors.")
subset = df[(df.season == season) & (df.week == week)].copy()
if ranked_only:
    subset = subset[subset.home_rank.notna() | subset.away_rank.notna()]
if not show_completed:
    subset = subset[~subset.completed]
subset = subset.sort_values('date')
a, b, c = st.columns(3)
a.metric('Matchups', len(subset)); b.metric('Season', season); c.metric('Week', week)
st.subheader('Matchup center')
if subset.empty:
    st.info('No qualifying matchups for this week. Try a different filter.')
for g in subset.itertuples():
    title = f"{'#'+str(int(g.away_rank))+' ' if pd.notna(g.away_rank) else ''}{g.away} @ {'#'+str(int(g.home_rank))+' ' if pd.notna(g.home_rank) else ''}{g.home}"
    with st.expander(title + (' · FINAL' if g.completed else '')):
        favorite = g.home if g.home_margin >= 0 else g.away
        short_favorite = favorite.replace(' Ducks','').replace(' Bruins','').replace(' Crimson Tide','')
        left, right = st.columns([2.35, 1])
        with left:
            x, y, z = st.columns(3)
            x.metric('Projected score (away – home)', f'{g.away_points:.0f} – {g.home_points:.0f}')
            y.metric('Model spread', f'{short_favorite} -{abs(g.home_margin):.1f}', help='Model point-margin forecast, not a sportsbook line')
            z.metric('Model total', f'{g.total:.1f}')
            st.progress(float(g.home_win_prob), text=f'{g.home}: {g.home_win_prob:.1%} win probability')
            if g.completed:
                st.info(f'Final: {g.away} {g.away_score} – {g.home} {g.home_score}')
            st.markdown('**What drives the predicted home margin?**')
            explanation = pd.DataFrame({'Factor':['Elo rating difference','Home field','Recent scoring form','Recent opponent strength'],
                'Points toward home margin':[g.elo_contribution,g.venue_contribution,g.form_contribution,g.sos_contribution]})
            st.bar_chart(explanation.set_index('Factor'))
            st.caption('Positive = favors home team; negative = favors away team. Contributions are rounded; calculations are heuristic, not calibrated effect estimates.')
            st.markdown('**Score-based team comparison**')
            def fmt(value): return '—' if value is None or pd.isna(value) else f'{value:+.1f}'
            comparison = pd.DataFrame({
                'Statistic':['Pregame Elo','Recent points/game*','Recent points allowed/game*','Prior opponent avg Elo – 1500','Venue-specific prior margin','Same-season games'],
                g.away:[g.away_elo,g.away_ppg,g.away_allowed,g.away_sos_elo,fmt(g.away_away_margin),g.away_games],
                g.home:[g.home_elo,g.home_ppg,g.home_allowed,g.home_sos_elo,fmt(g.home_home_margin),g.home_games],
            })
            st.dataframe(comparison, hide_index=True, use_container_width=True)
            st.caption('*Prior-shrunk recent scoring statistics, not raw season averages. Venue samples exclude neutral games. Strength of schedule is based on opponents’ pregame Elo ratings.')
        with right:
            st.markdown('**Markets and external intelligence**')
            st.write('ESPN expert pick: **not integrated**')
            st.write('CBS expert pick: **not integrated**')
            st.write('DraftKings: **not available**')
            st.write('FanDuel: **not available**')
            st.write('NIL estimated spending: **not available**')
            st.write('Coach / player injuries: **not integrated**')
            st.caption('Missing information is never treated as a zero or fabricated estimate.')
            st.link_button('Open ESPN matchup', g.source_url)
        st.caption(f'Model: {g.model_version} · Kickoff {g.date} · {g.venue}')
        data = pd.Series(g._asdict()).replace({float('nan'): None}).to_dict()
        st.download_button('Export matchup JSON', json.dumps(data, default=str, indent=2), file_name=f'game-{g.id}.json', key=f'dl-{g.id}')
st.divider()
st.subheader('Historical scorecard')
st.caption('Chronological walk-forward simulations: each game is predicted before that game updates ratings. This is not a independently held-out betting validation or archive of predictions made live before kickoff.')
report = evaluation(df[(df.season == season) & df.completed].to_dict('records'))
if report:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Games evaluated', report['games'])
    m2.metric('Winner accuracy', f"{report['winner_accuracy']:.1%}" if report['winner_accuracy'] is not None else '—')
    m3.metric('Margin MAE', f"{report['margin_mae']:.1f} pts")
    m4.metric('Total MAE', f"{report['total_mae']:.1f} pts")
st.subheader('Export')
st.download_button('Download weekly predictions (CSV)', subset.to_csv(index=False), file_name=f'cfb-{season}-week-{week}-v02.csv', mime='text/csv')
with st.expander('Methodology and roadmap'):
    st.markdown('''**Implemented v0.2:** Elo, home advantage, recent points for/against, recent opponent-Elo strength, home/away historical margins, spread/total/winner predictions, factor decomposition, historic scorecard, automated collection. Features use only preceding scores.

**Not implemented:** yards per play, EPA, injuries, recruiting, transfers, coaching-value-added, verified NIL dollars, ESPN/CBS picks, or current DraftKings/FanDuel odds. These require separately sourced, validated data. Do not interpret this model as proven to beat sportsbooks.

**Data caveats:** Unofficial, undocumented ESPN feed; scoreboard event ranks may differ from historical AP polls. Historic walk-forward calculations aren't immutable predictions published before kickoff. Predictions update when new results arrive; next development priority is archiving pregame snapshots and obtaining reliable advanced-stat datasets.''')
