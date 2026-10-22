"""CFB Intelligence v0.5.1: retrospective historical market grades."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.backtest import seasons_report
from cfb.model import build_predictions, evaluation
from cfb.tracker import tracker_rows, grade_game
from cfb.tracker_ui import render_result_strip, render_records
from cfb.matchup_intel_ui import render_spread, render_intelligence
from cfb.market_lines import load_lines
from cfb.current_odds import load as load_current_odds
from cfb.current_odds_ui import render_current_odds
from cfb.market_audit_ui import render_market_providers, render_market_coverage
from cfb.historical_markets import retrospective_grade

st.set_page_config(page_title='CFB Intelligence', page_icon='🏈', layout='wide')
st.markdown('<style>.block-container{padding-top:1.5rem;max-width:1450px}</style>', unsafe_allow_html=True)
st.title('🏈 CFB Intelligence')
st.caption('v0.5.1 · Historical sportsbook analysis + archived live picks · Kickoff times UTC')
raw = load_games()
market_lines = load_lines()
current_odds = load_current_odds()
if not raw:
    st.warning('No games yet. Run the GitHub Actions refresh workflow to download data.')
    st.stop()
meta_path = Path(__file__).parent / 'data' / 'metadata.json'
meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
with st.spinner('Computing chronological predictions…'):
    forecasts = build_predictions(raw, boxscores=load_boxscores())
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
# First recorded before kickoff is the official prediction. For earlier games,
# a historical walk-forward forecast can be displayed, but not counted as live.
archived_rows = tracker_rows(raw)
archived_by_id = {str(r['id']): r for r in archived_rows}
render_market_coverage(raw, market_lines)
st.subheader('Weekly record')
# Retrospective estimates are calculated from chronological historical replay.
# Apply the same top-25 filter as the matchup center for a coherent scorecard.
historical_scope = df[df.season == season].copy()
if ranked_only:
    historical_scope = historical_scope[historical_scope.home_rank.notna() | historical_scope.away_rank.notna()]
if not show_completed:
    historical_scope = historical_scope[~historical_scope.completed]
render_records(archived_rows, historical_scope.to_dict('records'), season, week, market_lines)

st.subheader('Matchup center')
if subset.empty:
    st.info('No qualifying matchups for this week. Try a different filter.')
for g in subset.itertuples():
    title = f"{'#'+str(int(g.away_rank))+' ' if pd.notna(g.away_rank) else ''}{g.away} @ {'#'+str(int(g.home_rank))+' ' if pd.notna(g.home_rank) else ''}{g.home}"
    archived = archived_by_id.get(str(g.id))
    if archived is not None:
        status = archived['status']
        provenance = 'archived'
    elif g.completed and pd.notna(g.home_score) and pd.notna(g.away_score):
        # Backtest only: NOT a prediction saved before the actual game.
        status = retrospective_grade(g._asdict(), market_lines.get(str(g.id)))
        provenance = 'retrospective'
    else:
        status = {'su': 'pending', 'ats': 'pending', 'ou': 'pending'}
        provenance = 'pending'
    with st.expander(title + (' · FINAL' if g.completed else '')):
        render_result_strip(status, provenance)
        if archived is not None:
            st.caption(f"Archived model score: {archived['away_points']:.0f}–{archived['home_points']:.0f}; "
                       "results graded against the archived forecast, not today's recalculation.")
        historical_market = market_lines.get(str(g.id))
        left, right = st.columns([2.35, 1])
        with left:
            x, y, z = st.columns(3)
            x.metric('Projected score (away – home)', f'{g.away_points:.0f} – {g.home_points:.0f}')
            with y:
                render_spread(g._asdict())
            z.metric('Model total', f'{g.total:.1f}')
            st.progress(float(g.home_win_prob), text=f'{g.home}: {g.home_win_prob:.1%} win probability')
            if g.completed:
                st.info(f'Final: {g.away} {g.away_score} – {g.home} {g.home_score}')
            st.markdown('**What drives the predicted home margin?**')
            explanation = pd.DataFrame({'Factor':['Elo rating difference','Home field','Recent scoring form','Recent opponent strength', 'Yards/play advantage (when available)'],
                'Points toward home margin':[g.elo_contribution,g.venue_contribution,g.form_contribution,g.sos_contribution,g.ypp_contribution]})
            st.bar_chart(explanation.set_index('Factor'))
            st.caption('Positive = favors home team; negative = favors away team. Contributions are rounded; calculations are heuristic, not calibrated effect estimates.')
            st.markdown('**Recent performance comparison**')
            def fmt(value): return '—' if value is None or pd.isna(value) else f'{value:+.1f}'
            comparison = pd.DataFrame({
                'Statistic':['Pregame Elo','Recent points/game*','Recent points allowed/game*','Prior opponent avg Elo – 1500','Venue-specific prior margin','Same-season games','Yards per play (available previous games)','Opponent yards per play (previous games)','Box-score samples'],
                g.away:[g.away_elo,g.away_ppg,g.away_allowed,g.away_sos_elo,fmt(g.away_away_margin),g.away_games,fmt(g.away_ypp),fmt(g.away_ypp_allowed),g.away_ypp_samples],
                g.home:[g.home_elo,g.home_ppg,g.home_allowed,g.home_sos_elo,fmt(g.home_home_margin),g.home_games,fmt(g.home_ypp),fmt(g.home_ypp_allowed),g.home_ypp_samples],
            })
            st.dataframe(comparison, hide_index=True, use_container_width=True)
            render_intelligence(g._asdict())
            st.caption('*Scoring rates are shrunk toward a league prior; yards/play appears only for previous games with usable box scores. No yards/play estimates are fabricated. Historical completeness varies.')
        with right:
            render_current_odds(
                current_odds.get(str(g.id)),
                g.home,
                g.away,
                g.date
            )
            st.divider()
            st.markdown('**Markets and external intelligence**')
            if historical_market:
                st.markdown('**Historical sportsbook consensus (NOT LIVE)**')
                mm = historical_market.get('market_home_margin')
                mt = historical_market.get('market_total')
                if mm is not None:
                    st.write(f"Market spread: **{g.home if mm > 0 else g.away if mm < 0 else 'Pick em'}** " +
                             (f"-{abs(mm):.1f}" if mm else "(even)"))
                    st.write(f"Model vs market margin: **{g.home_margin - mm:+.1f} points** (home-team view)")
                if mt is not None:
                    st.write(f"Market total: **{mt:.1f}** · Model difference: **{g.total - mt:+.1f}**")
                st.caption(f"{historical_market.get('provider_count', 0)} provider(s). Historical line timing UNVERIFIED; not a live pregame quote.")
                render_market_providers(historical_market, g.home, g.away)
            else:
                st.caption('No historical sportsbook consensus matched for this game.')
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
st.caption('Historical chronological replay, not a record of predictions actually saved before kickoff. Live archived picks are reported separately above.')
report = evaluation(df[(df.season == season) & df.completed].to_dict('records'))
if report:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Games evaluated', report['games'])
    m2.metric('Winner accuracy', f"{report['winner_accuracy']:.1%}" if report['winner_accuracy'] is not None else '—')
    m3.metric('Margin MAE', f"{report['margin_mae']:.1f} pts")
    m4.metric('Total MAE', f"{report['total_mae']:.1f} pts")
st.subheader('Season-by-season backtest')
st.caption('Retrospective chronological replay, not archived real-time picks. Ratings use no future results. The box-score adjustment is heuristic and not held-out validated.')
season_rows = seasons_report(forecasts)
if season_rows:
    st.dataframe(pd.DataFrame(season_rows).rename(columns={'season':'Season','games':'Games','winner_accuracy':'Winner accuracy','margin_mae':'Margin MAE','total_mae':'Total MAE','brier':'Brier score'}), hide_index=True, use_container_width=True)
st.subheader('Export')
st.download_button('Download weekly predictions (CSV)', subset.to_csv(index=False), file_name=f'cfb-{season}-week-{week}-v03.csv', mime='text/csv')
with st.expander('Methodology and roadmap'):
    st.markdown('''**Implemented v0.3:** Elo, home advantage, recent points for/against, recent opponent-Elo strength, home/away historical margins, spread/total/winner predictions, factor decomposition, historic scorecard, automated collection. Features use only preceding scores.

**Not implemented:** complete yards/play coverage, EPA, injuries, recruiting, transfers, coaching-value-added, verified NIL dollars, ESPN/CBS picks, or current DraftKings/FanDuel odds. These require separately sourced, validated data. Do not interpret this model as proven to beat sportsbooks.

**Data caveats:** Unofficial, undocumented ESPN feed; scoreboard event ranks may differ from historical AP polls. Historic walk-forward calculations aren't immutable predictions published before kickoff. Predictions update when new results arrive; next development priority is archiving pregame snapshots and obtaining reliable advanced-stat datasets.''')
