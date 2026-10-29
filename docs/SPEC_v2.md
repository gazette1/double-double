# Double Double Bot, modeling spec v2 (research-informed additions)

Builds on v1 (`docs/SPEC_v1.md`, `tools/build_dataset.py`, `tools/train_eval.py`, `data/features/dataset_v1.parquet`, results in `data/eval/v1/report_v1.md`). Do not modify the v1 scripts or overwrite v1 outputs. New code goes in `tools/train_eval_v2.py` (plus `tools/features_v2.py` if extra features are needed), outputs under `data/eval/v2/` and `data/models/v2/`.

## Why these additions (from the research notes in `research_notes/NBA double double prop models/`)
- Minutes are the largest error source; role half-lives are 1 to 3 games while rate half-lives are 17 to 54 games (DARKO). A minutes model should be separate from the rate model.
- Within a player, points, rebounds and assists are close to conditionally independent given minutes (partial correlations 0.08, -0.05, 0.07 measured on 2021-22 to 2025-26 game logs by `tools/stat_structure_check.py`); the raw correlations of 0.12 to 0.27 come from shared minutes. Dispersion: variance-to-mean about 1.29 for rebounds, 1.17 for assists, 2.78 for points. So P(double-double) can be computed as a mixture over minutes with conditionally independent negative binomial stats.
- Honest prop backtests found a blend of model and market beat both (KyShiesty, Brier 0.241 vs 0.244 market vs 0.248 model). With no historical prices, Baseline A stands in for the market.
- Calibration decides profit more than accuracy. v1's top probability bin is overconfident (C_full 0.961 predicted vs 0.840 realized, n 119).
- Home-arena scorekeeping shifts assists (Utah about +2 per game, Indiana about -1.4 in 2025-26; year-over-year correlation 0.5 to 0.6 recently).

## Walk-forward and rows
Same folds as v1: test seasons 2023, 2024, 2025, 2026 (end-year keys), train on earlier seasons, last 15 percent of training rows by date as the holdout slice for early stopping, calibration and blend weights. Same regular-season evaluation rows. Load v1 predictions from `data/eval/v1/predictions_v1.parquet` so A, B, C_full and C_noabs can be compared on identical rows; recompute them only if the saved file lacks what you need.

## New models
1. MIN: minutes model. LightGBM regression (objective regression_l1 or huber, same hyperparameters as v1 otherwise) on the v1 feature set without abs_ features (MIN_noabs) and with them (MIN_full). Also fit quantile models at 0.1 and 0.9 on the same features to describe the spread. Report MAE and RMSE against the actual minutes on the test season versus two baselines: the last-5 mean and the v1 min_ewm feature. Report MAE separately for starters (last_starter = 1) and non-starters.
2. SIM: structured probability. For each row take a minutes grid of 15 quantiles from the MIN predictive distribution (use q10, q50, q90 and a normal approximation between them, truncated to [0, 48]). Per-minute rates for points, rebounds, assists, steals, blocks: shrink the player's EWM per-minute rate toward a position prior with k = 300 minutes of prior weight (rate = (ewm_rate * ewm_minutes_weight + prior_rate * 300) / (ewm_minutes_weight + 300); if the v1 features do not store the EWM minutes weight, use the l20 per-minute rate with min(games_l20, 20) * mean minutes as the weight). Position priors are per-minute league means by athlete_position_abbreviation on the training rows. Given minutes m, each stat is negative binomial with mean rate * m and dispersion set from the measured variance-to-mean ratios (points 2.78, rebounds 1.29, assists 1.17; steals and blocks Poisson). The stats are conditionally independent given m, so P(at least 2 of 5 reach 10 | m) is 1 minus P(0 reach) minus P(exactly 1 reaches), computed from the five tail probabilities. Average over the minutes grid with equal weights. Vectorize with numpy and scipy.stats.nbinom.sf; no per-row Python loops. Report SIM raw and SIM isotonic-calibrated.
3. C_stack: v1 C_full features plus two added columns, sim_p and min_pred (MIN_full q50), trained like C_full. Also C_stack_noabs with the noabs versions.
4. BLEND_A: logit-space average of calibrated C_full and calibrated Baseline A, weight w chosen on the holdout slice from a grid of 0.0 to 1.0 in steps of 0.05 by log loss. Report the chosen w per fold. Also BLEND_SIM: same between calibrated C_full and calibrated SIM.
5. Calibration study on C_full raw outputs (then apply the best method to C_stack): isotonic (v1), Platt (logistic on logit p), and beta calibration (logistic regression on log p and -log(1 - p)). Fit on the holdout slice, apply to the test season, report pooled log loss and the calibration table with special attention to the [0.8, 0.9) and [0.9, 1.0] bins.

## New features (small, optional; add only if the build stays under 15 minutes)
- arena_ast_excess_prev: prior-season home-arena assist-rate excess for the game's arena (home team), as computed in `tools/stat_structure_check.py` section 5 (team AST/FGM at the arena minus the teams' own road rate, excluding All-Star rosters). NaN when the arena has no prior season.
- abs_ fix: reset the regulars window at the season boundary (use the current season's team games when at least 3 exist, otherwise the prior season's last 10). Report whether this changes metric 7.

## Evaluation (write CSVs under `data/eval/v2/` and `data/eval/v2/report_v2.md`)
- Metric 1 (log loss, Brier, AUC per season, calibrated) for A, C_full, SIM, C_stack, BLEND_A, BLEND_SIM, with C_noabs and C_stack_noabs included.
- Metric 4 nightly top-1, top-2, top-3 hit rates and all-three rate for the same models.
- Metric 5 disagreement buckets of C_stack and BLEND_A against A.
- Metric 8 mid-tier slice (A calibrated p between 0.25 and 0.65): metric 1 and metric 5 for the new models.
- Minutes table from model 1.
- Calibration study table from model 5.
- Proxy-edge rule (clearly labeled as an assumption, not a price backtest): define a stand-in implied probability q = min(0.97, 1.08 * A_cal) to mimic a Yes-only price with about 8 percent margin. For each model, bet Yes on rows where model p minus q is at least 0.03, 0.05, 0.08, 0.10. Report n bets per season, realized hit rate, mean q, mean p, and the flat-stake return assuming a fair price at implied q (return per bet = hit * (1 - q) / q - (1 - hit)). State in the report that this is a proxy and that forward prices are logged in `data/odds/dd_prices.csv` for the real test.
- Feature importance for C_stack (top 30).

## Code and style
- Python 3.13, pandas, numpy, scipy, lightgbm 4.6, scikit-learn 1.8; add no dependencies. PYTHONUTF8=1. Seed 42. Keep total runtime under 30 minutes; if the SIM grid is slow, reduce to 9 minutes quantiles and say so.
- Markdown: plain factual sentences, no em-dashes, no exclamation points, no hype words. Label every proxy assumption as such.
