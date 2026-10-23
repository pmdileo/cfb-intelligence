# v0.7.4 — week-correct EDGE, conference-filtered Matchup Center, shared full matchup details

## What changes
- EDGE uses **only** the selected season + week, independent of Top-25 and conference filters.
- Matchup Center adds its own conference filter. A game qualifies when either participating team belongs to the selected conference. "All conferences" keeps the full list. Unmapped teams remain visible as "Other / Unmapped".
- EDGE displays one **identical full Matchup Center dropdown per qualifying game**, even if both ATS and O/U qualify. Reasons appear above the dropdown. Existing graphs, archived results, sportsbook observations, and JSON export remain intact.

## Install on `v0.7.4-week-and-matchup` (from main)

This archive includes an *idempotent app patcher* because the full Matchup Center is a long block of code. Moving it into a reusable function requires coordinated edits; do **not** manually paste another copy of the matchup block.

1. Upload **three root-level files** to that branch: `conferences.py`, `edge_week_ui.py`, `apply_patch.py`.
2. On the same branch edit `.github/workflows/weekly.yml`. Immediately **before** `- name: Run regression tests`, add:

   ```yaml
      - name: Install v0.7.4 UI integration
        run: python apply_patch.py
   ```

3. In the existing final `Commit updated datasets` step change:

   `git add -A data/`

   to:

   `git add -A data/ app.py cfb/conferences.py cfb/edge_week_ui.py`

4. Run **Refresh college football data** on this branch. The patching step generates the final app and moves the helper files into `cfb/`. The subsequent tests and commit happen in the same run. **Do not merge if the patch step fails.**
5. After successful run, open `app.py` on the branch: verify imports `game_in_conference`, `render_edge_week`, and a `render_matchup` function. Check `cfb/conferences.py` and `cfb/edge_week_ui.py` exist.
6. Remove the one-time `Install v0.7.4 UI integration` step from `weekly.yml` before merging. The already-patched `app.py` stays patched. You may also remove the root-level install files `apply_patch.py`, `conferences.py`, `edge_week_ui.py` once their `cfb/` copies exist; no need to retain patcher in deployed code.
7. Rerun the refresh on the cleaned branch, confirm tests, then merge to `main`.

## Warnings
- This patch targets the verified v0.7.3 `app.py` layout. Its safety assertions will abort if the app has changed unexpectedly.
- Conference mappings are curated 2026 display-only data. Realignment or ambiguous ESPN school names can cause some games to be marked Other / Unmapped. They are never silently assigned by inference.
- EDGE is an exploratory model–market discrepancy screen, not a calibrated wagering signal.
- Original matchup presentation is reused verbatim rather than restated in a separate UI.
