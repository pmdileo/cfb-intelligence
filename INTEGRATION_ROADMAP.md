# Integration order — four staged CFB Intelligence upgrades

**Current status:** Nothing in this package was deployed or merged.

| Order | Package | Goal | Verification gate |
|---|---|---|---|
| 1 | `CFB-Intelligence-v0.6-Phase1-Efficiency-Repair.zip` | Repair missing box-score offensive plays/YPP | Workflow green; number of usable YPP team records actually increases |
| 2 | `CFB-Intelligence-v0.6-Phase2-Shadow-Model.zip` | Experimental opponent-adjusted scoring ratings | Green tests, chronology verified, compare same games with baseline; keep live forecasts unchanged |
| 3 | `CFB-Intelligence-v0.6-Research-Toolkit.zip` | Data/provenance audits, common-game validation, coach registry | All tests green; inspect coverage/missing-data report |
| 4 | `CFB-Intelligence-v0.6-Phase4-Context-Foundation.zip` | Time-aware recruiting/transfer/coach/returning-production feature store | 9 tests green; empty data is acceptable, source/timestamp checks verified |

Start each branch from the **current** `main` after merging the previous tested phase, not from an old branch. Don't blindly overwrite shared application or workflow files. Run the entire test suite on each phase. Take a baseline accuracy/data completeness snapshot before/after phases 1–3. Phase 4 creates no model outputs until real audited data are collected and validated. Use full historical chronological reconstruction and held-out later seasons before considering new coefficients or production promotion.

When user is back at a computer, begin by verifying GitHub `main` and reviewing any intervening changes; integrate one phase at a time, not all four in one push.
