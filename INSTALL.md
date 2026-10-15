# CFB Intelligence — v0.6 next phase: Context Intelligence Foundation (STAGED)

**This package does not modify the live model, `app.py`, existing snapshots, GitHub workflows, or production data.** No information is fabricated, and the CSV is deliberately empty.

## Prepare later
1. First integrate/verify the three previously prepared packages: Phase 1 efficiency repair, Phase 2 shadow rating model, Research Toolkit. Verify the latest `main` branch before doing so.
2. Create a **new test branch** from the updated `main` named `v0.6-context-foundation`.
3. Upload `cfb/context_features.py` to `cfb/context_features.py`, `context_audit.py` to root, and `tests/test_context_features.py` to `tests/test_context_features.py`. Optionally put `templates/context_records_template.csv` at `data/context_records.csv` for future manual collection.
4. Run `python -m pytest -q tests/test_context_features.py` followed by `python context_audit.py --records data/context_records.csv` in a working checkout (or as manual Actions step). No credentials are required.
5. Only merge after all tests pass. **No predictive coefficients are enabled** by this package.

## Timing and validation policy
Each input requires ESPN team ID, season, `known_at` with timezone, `source_url`, and a unique record ID. A record is available only if published **strictly before** the game analysis cutoff, with effective date on or before cutoff. No statistics are interpreted as zero if absent. The system cannot verify publication claims from arbitrary source URLs; manual evidence review remains necessary. Fields are **user/source-supplied** and are not standardized across providers automatically. In particular, `coach_value_added` is a placeholder, **not estimated by this code**.

## Next research stage
Gather trustworthy team/season snapshots, team ID mappings, coaching changes, recruiting/transfer records, and returning production; build immutable daily historical snapshots to verify real availability. Evaluate context features with season held-out testing only after coverage and license constraints are understood. Avoid using EA Sports game ratings until legal/quality/provenance issues have been checked.
