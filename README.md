# v0.6 Phase 5: Promotion Gate

Read-only model review report. **Does not modify the website or promote the shadow model.**

After phase 2 is installed, add:

- `cfb/promotion_gate.py`
- `model_gate_report.py`
- `tests/test_promotion_gate.py`

Then run `python -m pytest -q tests` and `python model_gate_report.py --test-seasons 2024 2025 --output reports/v06_gate.json`.

**Warning:** 2024–2025 are examples, not guaranteed independent held-out years; if these years were used for feature selection/tuning, choose untouched future seasons. The candidate gate requires positive paired improvements in margin MAE, total MAE, and Brier, plus minimum coverage. A candidate is only marked for *manual review*. Ratings are still experimental. No sportsbook profitability claim.
