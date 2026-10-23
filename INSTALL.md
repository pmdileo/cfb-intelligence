# Install EDGE view (v0.7.3)

Create branch `v0.7.3-edge-tab` from `main`.

Upload:
- `cfb/edge_scanner.py`
- `cfb/edge_tab_ui.py`
- `tests/test_edge_scanner_v073.py`

In `app.py`, add this import near existing Streamlit UI imports:

```python
from cfb.edge_tab_ui import render_edge_tab
```

Find the following **existing** line (right above `st.subheader('Matchup center')`):

```python
render_records(archived_rows, historical_scope.to_dict('records'), season, week, market_lines)
```

Immediately **after** that line, insert:

```python
st.divider()
view = st.radio("Navigate", ["Matchup center", "EDGE"], horizontal=True, key="main_view")
if view == "EDGE":
    render_edge_tab(forecasts, shadow_research_by_id, current_odds, now)
    st.stop()
```

This provides a two-choice tab-like switch. EDGE shows the full national upcoming schedule regardless of the Matchup Center's Top 25/week filters, intentionally.

No changes to forecasting math, archived predictions, or odds-collection workflow.

Commit on the feature branch. Run `Refresh college football data` on that branch and check all tests pass. Open a PR into `main` after verification.

**Important:** The default 4.5-point gap is a proposed screening threshold, not a calibrated wagering edge. Betting performance must be evaluated with immutable before-kickoff line snapshots and prices including vig. The scanner uses recently observed consensus and rejects games kicked off / quoted after kickoff. It does not generate bets or place wagers.
