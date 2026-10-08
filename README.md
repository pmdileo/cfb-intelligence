# CFB Intelligence — first functional build

A private Streamlit CFB weekly prediction dashboard using free ESPN scoreboard data, a simple historical Elo model, and GitHub Actions weekly refreshes. **Version 0.1: educational baseline, not a validated betting model.**

## Fast setup (no coding)

1. Create a **private** GitHub repository named `cfb-intelligence`.
2. Upload the unzipped contents of this folder **including `.github/` and `.streamlit/`**. You can use GitHub's upload files page, but hidden folders may require uploading via desktop/GitHub Desktop or the provided `upload_to_github.sh`.
3. In the repo, open **Actions**, enable workflows if prompted, and select **Refresh college football data → Run workflow** for the first data collection. The initial collector needs Internet access. No API key is needed for this baseline.
4. Open [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, choose **Create app**, select this repo, branch `main`, and entrypoint `app.py`.
5. Set the app to **private** in Streamlit's Sharing settings. Invite your father-in-law by email as a viewer. Community Cloud has a limit of one private app per workspace, subject to current service rules.
6. Check the dashboard. The refresh workflow is scheduled on Tuesdays and Fridays; use **Run workflow** for an extra on-demand update.

**Alternative Mac local launch:** install Python 3.12+, unzip, open Terminal in folder, run `python3 -m pip install -r requirements.txt && python3 refresh.py && python3 -m streamlit run app.py`.

## What's real in v0.1

- Uses a free public ESPN *unofficial/undocumented* scoreboard feed for 2021–present game results and fixture schedule. Data freshness depends on access to this endpoint.
- Selects all games where either opponent has event-level rank 1–25. The event-level ranking can be missing or differ from the weekly official AP poll.
- Elo rating with home advantage, year-to-year regression, last-four-game scoring-margin correction, last-five-game scoring averages to estimate total; estimated score, spread, winner probability.
- Walk-forward metrics for all completed games and matchup-by-matchup export.
- GitHub Actions pull/commit twice weekly, on Tuesday and Friday. Scheduling is best effort, not guaranteed to run on time; data updates as long as Actions run and commits succeed.

## What's not implemented yet

- Real DraftKings/FanDuel prices or ESPN/CBS forecast feeds. Scraping odds and media sites may violate terms or break frequently; this version **does not** fake prices. Historical betting lines may later be imported from permitted sources.
- True NIL dollar spending (generally not public and reliably comparable), injuries, returning starters, transfer rankings, coaching value-add or a 0–100 composite score.
- Team yards per game, adjusted efficiency, advanced metrics, or validated probabilistic calibration.
- Publishing timestamped immutable predictions. Backtesting is chronological in-code but assumes historical data as fetched; current-season injury/news information is absent.

## Roadmap

1. Add freely available per-team season/game stats, actual YPG, opponent-adjusted offense/defense, and feature coverage reporting.
2. Save weekly pregame snapshots + a strict time-split holdout test; calibrate totals and probabilities.
3. Add coaches/transfers/recruiting through documented sources, monetary NIL data only where verified, with source and quality labels.
4. Add legal/allowed odds inputs and time-stamped line movement if feasible for free.

## Notes

- This project is independent of ESPN, CBS, DraftKings and FanDuel and not affiliated with or endorsed by them.
- Sportsbook odds sources and NIL reports are optional; the free-only commitment is maintained.
- Do not commit credentials or secrets.
