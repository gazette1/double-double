# Double Double Bot

NBA double-double prop research and backtest. Vault master note: `Obsidian Vault/Double Double Bot/Double Double Bot.md` (start there). Started 2026-10-29.

## Layout
- `tools/pull_hoopr.py` downloads ESPN box scores, team box scores and schedules (sportsdataverse hoopR-nba-data) into `data/raw/hoopr/`. Season key is the season end year.
- `tools/check_sources.py` checks which public data sources respond.
- `tools/odds_snapshot.py` logs The Odds API `player_double_double` prices (FanDuel, DraftKings by default) to `data/odds/dd_prices.csv` and `data/odds/snapshots/`. One credit per game per call.
- `tools/market_check.py` compares the latest logged prices with realized double-double rates.
- `tools/stat_structure_check.py` measures within-player stat correlations, dispersion and the arena assist effect from the game logs.
- `tools/build_dataset.py` builds `data/features/dataset_v1.parquet` (point-in-time features, spec in `docs/SPEC_v1.md`, catalog in `docs/FEATURES_v1.md`).
- `tools/train_eval.py` runs the v1 walk-forward backtest to `data/eval/v1/`.
- `tools/train_eval_v2.py` runs the v2 models (minutes model, simulation probability, stack, blends, calibration study) to `data/eval/v2/`, spec in `docs/SPEC_v2.md`.
- `tools/edge_bands.py` assumption-based edge view by price band from the v2 predictions.
- `tools/pull_tracking.py` pulls per-game tracking and hustle box scores (rebound chances, potential assists, box outs) from stats.nba.com through `nba_api`, one request per game date per measure, into `data/raw/tracking/`. Resumable, and it waits out the site's throttling blocks (hung requests) with long pauses and re-passes instead of retrying quickly.
- `tools/pull_matchups.py` pulls season-level defender versus offensive-player matchup totals (who guarded whom, partial possessions, points and assists allowed) per defensive team into `data/raw/matchups/`.
- `tools/build_tracking.py` matches NBA player ids to ESPN ids (`data/raw/tracking/crosswalk.csv`) and writes `data/features/tracking_games.parquet`, `tracking_team_games.parquet` and the point-in-time player features `tracking_features.parquet` (prefix `trk_`).
- `tools/build_opponent_features.py` writes `data/features/opponent_features.parquet`: opponent position-allowed (`oppx_`), opponent tracking profile (`oppt_`) and prior-season matchup features (`mu_`), all point-in-time.
- `tools/tracking_lift.py` controlled walk-forward test of those feature groups against the v1 feature set, including residual boosting from the saved v1 prediction (zero trees equals v1), output in `data/eval/tracking/report_tracking.md`. Result 2026-10-29: no measurable lift; the layer is not part of the production model.
- `research_notes/` five cited research notes; `reports/NBA double double prop models.md` the synthesis.

## Running
All scripts run from the project root with `PYTHONUTF8=1 python tools/<script>.py`. Python 3.13 with pandas, numpy, scipy, lightgbm, scikit-learn, pyarrow, requests, plus `nba_api` 1.12 (installed 2026-10-29 with Russ's go-ahead) for the tracking and matchup pulls. `.env` (optional) holds `ODDS_API_KEY`; otherwise the StrikeOut Bot `.env` is read.
