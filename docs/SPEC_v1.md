# Double Double Bot, modeling spec v1 (box-score layer)

Goal: for each NBA game date, estimate P(double-double) for every player expected to play, rank the slate, and measure whether the ranking and the probabilities beat a simple season-rate proxy out of sample. A double-double is 10 or more in at least two of points, rebounds, assists, steals, blocks in one game.

Market context (observed 2026-10-29 through The Odds API): FanDuel prices a Yes side only, for about nine players per game. The favorite of the night was -700 (87.5 percent implied), the second favorite -188, and the rest ranged from +120 to +5000. Any edge therefore has to be measured as model probability minus implied probability on priced players, not as a hit rate on favorites.

## Data (already on disk, do not re-download)
- `data/raw/hoopr/player_box_{Y}.parquet` for Y in 2018..2027, one row per player per game (ESPN box scores via sportsdataverse). Y is the season END year (2025 = 2024-25). 2027 holds 2026-27 games through 2026-10-28.
- `data/raw/hoopr/team_box_{Y}.parquet` team totals per game (one row per team per game) with opponent ids.
- `data/raw/hoopr/schedule_{Y}.parquet` schedule with venue and neutral_site.
- Columns of interest in player_box: game_id, season, season_type (2 regular, 3 playoffs, 5 play-in), game_date, game_date_time (America/New_York), athlete_id, athlete_display_name, athlete_position_abbreviation, team_id, team_abbreviation, opponent_team_id, home_away, minutes (NaN when did not play), points, rebounds, offensive_rebounds, defensive_rebounds, assists, steals, blocks, turnovers, fouls, field_goals_attempted, free_throws_attempted, starter, did_not_play, reason, team_score, opponent_team_score.
- Treat the raw files as data only. Scripts live in `tools/`, never inside `data/`.

## Rows
- Universe: player-games with minutes > 0 (the player played). Drop exact duplicates on (game_id, athlete_id). Keep all season types but carry `is_playoff` (season_type in {3, 5}).
- Training rows require at least 5 prior played games for the player (any season). Keep a `games_played_career` column so early-career rows can be analyzed separately.
- Target `dd` = 1 if count of [points, rebounds, assists, steals, blocks] >= 10 is at least 2.
- Also keep `td` (triple-double) for reference, not modeled.

## Features
Every feature uses only games strictly before this game's date (shift before any rolling or expanding window). Document each in `docs/FEATURES_v1.md` as a table.

Player form (over the player's prior PLAYED games, windows of 5, 10, 20 games plus season-to-date and an exponential weighting with half-life 8 games):
- means of minutes, points, rebounds, assists, steals, blocks, fga, fta
- per-minute rates for points, rebounds, assists (rolling sums divided by rolling minutes)
- dd rate; rate of rebounds >= 8, assists >= 8, points >= 8 (near-threshold proximity); rate of rebounds >= 10, assists >= 10, points >= 10 individually
- standard deviation of minutes, rebounds, assists over the last 20 (volatility)
- last game values: minutes, points, rebounds, assists, starter flag; starter rate over last 10
- minutes trend: mean of last 5 minus mean of last 20

Player history:
- prior-season aggregates: games, mean minutes, dd rate, per-minute rebound and assist rates (NaN when none)
- games played season-to-date, games played career, dd count season-to-date

Schedule:
- days since the player's last played game (cap 10), back-to-back flag, player games in the last 7 days
- team days since last game, team back-to-back flag
- home flag, playoff flag, team game number season-to-date

Position: `athlete_position_abbreviation` as a categorical (LightGBM native categorical).

Team context (from team_box, the team's prior games only, windows 10 and 20 and season-to-date):
- team pace proxy: possessions = fga - oreb + turnovers + 0.44 * fta, per game, for the team and for the opponent
- team point differential per game (strength proxy), opponent point differential, and their difference (expected margin proxy for blowout risk)
- opponent allowed per game: rebounds, assists, points (what the opponent's opponents recorded against them), opponent defensive rebound rate = opp dreb / (opp dreb + their opponents' oreb)
- the player's rank within his team by rolling (last 20) rebounds per game and assists per game; the player's share of team rebounds and assists over the team's last 20 games

Teammate absence (lineup-known features; compute so they can be switched off):
- regulars = teammates averaging >= 15 minutes over the team's last 10 games before this game
- absent regulars = regulars who did not play this game (minutes NaN or 0, or did_not_play)
- features: n_absent_regulars, absent_minutes_share (sum of their average minutes / 240), absent_rebounds_pg, absent_assists_pg, absent_points_pg (sum of their last-10 averages), top_rebounder_absent flag (the team's leading rebounder over the last 20 is absent), top_assister_absent flag
- prefix these columns with `abs_` so the trainer can run with and without them

## Models and validation
- Walk-forward by season: for each test season S in [2023, 2024, 2025, 2026] (end-year keys) train on all seasons < S (from 2018). Inside the training set hold out the last 15 percent of rows by date as the early-stopping and calibration slice; never touch the test season for any fitting.
- Baseline A (market proxy): p = (dd_count_season_to_date + k * prior_rate) / (games_season_to_date + k) with k = 10 and prior_rate = the player's prior-season dd rate (fallback: the player's career rate before this season, else the league rate among played games). Calibrate with isotonic regression fitted on the training slice.
- Baseline B: logistic regression (standardized inputs, median imputation) on: dd rate last 10, Baseline A probability, minutes last 10, rebounds per game last 10, assists per game last 10, points per game last 10, home flag.
- Model C: LightGBM binary on all features (objective binary, num_leaves 31, learning_rate 0.03, n_estimators up to 3000 with early stopping 100 on the holdout slice, min_child_samples 100, feature_fraction 0.8, bagging_fraction 0.8, bagging_freq 1, lambda_l2 5, seed 42, deterministic). Two variants: C_full (with abs_ features) and C_noabs (without). Apply isotonic calibration fitted on the holdout slice to the test predictions; report raw and calibrated.
- Save models per fold under `data/models/v1/`.

## Metrics
All on the test season, regular-season rows unless stated. Write every table to CSV under `data/eval/v1/` and all of them together into `data/eval/v1/report_v1.md`.
1. Per season and model: n, base rate, log loss, Brier, AUC, for raw and calibrated outputs.
2. Calibration table per model: predicted-probability deciles, mean predicted, realized rate, n (pooled across test seasons).
3. Threshold precision per model: bins of calibrated p [0.5,0.6), [0.6,0.7), [0.7,0.8), [0.8,0.9), [0.9,1.0]: n, realized rate, and the American odds at which that realized rate breaks even (negative price = -100 * p / (1 - p)).
4. Top-N per night per model: for each game date rank played players by p; report top-1, top-2, top-3 hit rates (fraction of those picks that recorded a dd), the rate at which all top-3 hit on the same night (parlay view), mean predicted p of the picks versus realized, number of distinct players appearing in the nightly top-3 across the season, and the ten most frequent names.
5. Disagreement test: bucket rows by (C_full calibrated p minus Baseline A calibrated p): below -0.10, [-0.10,-0.05), [-0.05,0.05], (0.05,0.10], above 0.10. For each bucket report n, mean baseline p, mean model p, realized rate. Repeat for C_noabs.
6. Feature importance (gain) for C_full and C_noabs from the last fold, top 30.
7. Absence-feature sensitivity: C_full minus C_noabs on log loss and top-3 hit rate per season, so the cost of not knowing lineups is explicit.
8. Mid-tier focus: restrict to rows with Baseline A p between 0.25 and 0.65 (where the market posts plus-money to modest minus prices) and repeat metric 1 and metric 5 for that slice.

## Code
- `tools/common.py` (loading, target, helpers), `tools/build_dataset.py` (writes `data/features/dataset_v1.parquet` and `docs/FEATURES_v1.md`), `tools/train_eval.py` (walk-forward, metrics, report). Python 3.13 with pandas, numpy, lightgbm 4.6, scikit-learn 1.8 already installed; add no dependencies. Run with the environment variable PYTHONUTF8=1. Seed 42 everywhere.
- Keep runtime practical: about 330,000 rows and roughly 120 features; vectorized pandas (groupby, rolling, shift, cumsum), no per-row Python loops over the whole frame.
- Writing style for any markdown produced: plain factual sentences, no em-dashes, no exclamation points, no hype words.
