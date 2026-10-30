# Stokastic NBA DFS articles, read for the bot (2026-10-30)

Russ asked for every article on https://www.stokastic.com/articles/nba-dfs to be read "to enhance the bot". The index listed 22 articles (June 17 to September 6, 2026 by their bylines; the footers read 2025, so the dates look like refresh dates) and no pagination. All 22 were read on 2026-10-30. The per-article notes, with the claims, figures and the test each one suggests, are in `stokastic nba dfs 2026-10-30/batch_a.md` to `batch_d.md` in this folder. This note is the synthesis and the record of what was tested the same morning.

## What the pages are

Every one is a how-to or marketing page for Stokastic's paid DFS tools (projections, Sims, DataHub, late-swap). None cites a backtest, a sample size, an error metric, a coefficient or a data schema. Every number is a definition (boom = 5 x salary/1000 + 10), an arithmetic illustration (a 40%-owned player shares a boom with 12,000 lineups), or a hypothetical the page itself labels illustrative (a backup center "up to roughly 30 minutes", a backcourt partner from 1.30 to 1.51 fantasy points per minute with the star off the floor). Ownership, salary, leverage, contest structure, showdown, late-swap tooling and lineup duplication, which is most of the content, has no analogue for a single prop priced by a sportsbook.

Articles with no transfer at all: leverage and game theory, tournament strategy, multi-entry, cash games, ownership projections, contrarian strategy, late swap tools, how to use Sims, lineup flexibility, DraftKings strategy, the post-contest simulator (except one idea below). The pages that touch the bot's problem are the minutes-usage-pace research piece, the sims-against-optimizers piece, the stacking piece, the boom-bust piece and the starting-lineups piece, and even those carry mechanism only.

## The claims worth testing, and what the bot already has

| Claim in the articles (no data behind any of them) | Bot status before today |
|---|---|
| Minutes first, then per-minute rates, then the game environment | Already the v2 design (minutes model, MAE 4.56 against 5.15 for a five-game mean; simulation draws minutes then negative-binomial stats). |
| A double-digit spread is the "silent killer": starters sit the fourth quarter | No spread, total or implied team total among the 155 features. Pace proxies exist (team and opponent trailing possessions). The daily board does log the ESPN spread and the bar rule doubles for near-locks in 10-point spreads. |
| Pace estimate = team pace x opponent pace / league pace | Team and opponent trailing possessions are features; the product term is not. |
| Same-team usage is zero-sum; a starter and his direct backup are negatively linked; a passer and his finisher move together; opponents in a tight, fast game move together | Never measured. Combos were priced as a product with the selection shrinkage from the top-3 analysis. |
| Spread of outcomes is player-specific: foul trouble, role, blowout risk | min_sd_l20, reb_sd_l20, ast_sd_l20 exist; no foul features; one dispersion per stat in the simulation. |
| Lineups and inactives confirm in the final hour before tip; "probable" players sit and "questionable" players play 34 minutes | The 3 PM board stores every player's injury tag and the 6:40 PM snapshot marks players ruled out. Two days of history so far, so a tag-reliability table and a status-weighted mixture wait for a sample. |
| A ruled-out starter frees "roughly 25 to 30 minutes" and the second domino gains 8 to 10 | The abs_ features carry absent regulars' minutes share and per-game rebounds, assists and points; no beneficiary-specific on/off lift. |
| Grade on expected value, not the single night (the Sim ROI idea) | The five-name ledger graded wins and units only. |

## Tests run on 2026-10-30

### 1. Pair correlation of double-double outcomes (`tools/pair_correlation.py`, `data/eval/pairs/report_pairs.md`)

Rows: the 103,009 v1 test rows (regular season 2022-23 to 2025-26) with the calibrated v1 probability, players at p of at least 0.10, every pair inside a game: 49,309 pairs in 4,904 games. ratio = joint hit rate / product of the two probabilities, with a 500-resample block bootstrap by game date.

| group | pairs | ratio | 95% interval |
|---|---:|---:|---|
| all pairs | 49,309 | 0.94 | 0.90 to 0.98 |
| same team | 20,915 | 0.92 | 0.86 to 0.97 |
| opponents | 28,394 | 0.95 | 0.91 to 1.00 |
| same team, both legs p at least 0.30 | 2,227 | 0.93 | 0.86 to 1.00 |
| opponents, both legs p at least 0.30 | 4,295 | 0.93 | 0.88 to 0.99 |
| same team, both starters | 15,909 | 1.00 | 0.94 to 1.06 |
| same team, starter plus bench | 4,829 | 0.55 | 0.45 to 0.65 |
| same team, both centers | 1,045 | 0.69 | 0.55 to 0.86 |
| same team, center plus guard | 2,664 | 1.05 | 0.95 to 1.16 |
| same team, final margin under 10 | 9,926 | 1.05 | 0.96 to 1.14 |
| opponents, final margin under 10 | 13,473 | 1.17 | 1.10 to 1.24 |
| same team, final margin 20 or more | 3,971 | 0.55 | 0.44 to 0.64 |
| opponents, final margin 20 or more | 5,390 | 0.50 | 0.43 to 0.58 |

Reading. Two legs in one game are worth about 7 percent less than the product of their probabilities, on either side of the ball. The articles' three directional claims hold: starter plus his own team's bench is the worst pairing (0.55), two centers on one team cancel (0.69), and the center-plus-guard pairing is the only same-team pair at or above independence (1.05, inside the noise). The blowout mechanism is large after the fact: in games decided by under 10 points, pairs hit together above the product (1.05 same team, 1.17 opponents); at 20 points or more, about half. That is the shared game-state factor the simulation does not have.

Rule adopted for combo pricing (paper only): same-game legs at p of at least 0.30 take the product times 0.93, on top of the selection shrinkage of about 5 points per leg from the top-3 analysis; never pair a starter with a bench player from the same team, never pair two centers from the same team; a center-plus-guard pair from one team is priced at the product.

### 2. Expected-margin proxy and residuals (`tools/build_gamestate_features.py`, `data/eval/pairs/residual_by_expected_margin.md`)

No historical spreads are in the data (the hoopR schedule files carry none; The Odds API history is paid). A point-in-time proxy was built from the box scores: team trailing-20 point differential minus the opponent's, plus or minus 2.5 for home court. It correlates only 0.137 with the realized final margin, so it is a weak stand-in for a market spread. Against it, the v1 model's calibration moves little: realized minus p runs between -0.022 (underdogs expected to lose by 12 or more) and +0.015 (favorites expected to win by 12 or more), and for starters alone within 0.005 in every bucket. The blowout effect on pairs is therefore mostly unpredictable from pre-game team strength; a market spread, which embeds injuries and rest, may do better, and that needs a price history.

### 3. Controlled lift tests (`tools/coach_lift.py` on the new feature files)

Same rows, hyperparameters, seed, holdout and Platt calibration as every earlier test, block bootstrap by game date on the difference against BASE.

- GAMESTATE: gs_exp_margin, gs_abs_exp_margin, gs_exp_total, gs_exp_pace (team x opponent / league pace), gs_pace_gap, gs_opp_pd_l20. Results in `data/eval/gamestate/report_coach.md`.
- FOULS: foul_pg_l10, foul_pm_l20, foul5_share_l10, minv_cv_l10, minv_q10_l10. Results in `data/eval/fouls/report_coach.md`.

Results.

- GAMESTATE: pooled calibrated log loss 0.1892 (BASE) to 0.1890, difference -0.00022 with a bootstrap interval of -0.00045 to -0.00001 and 98 percent of resamples better; by season -0.00027, -0.00027, -0.00006, -0.00027. It is the first feature group in this project to clear its interval pooled, and it does so with a proxy that correlates 0.14 with the final margin. The mid-tier slice (season rate between 0.25 and 0.65) improves in three of four seasons. The proxy-edge top-3, the product the bot would sell: hit rate 0.4375 against 0.4273, return per unit 0.184 against 0.163, better in three of four seasons (2022-23 0.054 against 0.056). The disagreement buckets go the right way in both directions: where the new model lowers a probability by more than 0.05 (589 rows) the realized rate is 0.351 against BASE's 0.388 and the new model's 0.325; where it raises one by more than 0.05 (766 rows) the realized rate is 0.389 against 0.349 and 0.413. Importance is spread across all six features, led by the absolute expected margin, the expected total and the expected pace. Nightly top-3 by probability is unchanged within noise (0.683 against 0.677).
- FOULS: -0.00015 pooled, interval -0.00039 to +0.00009; one season (2023-24) clears its interval at -0.00068, the other three are flat; the mid-tier slice improves in three of four seasons; the minutes coefficient of variation is the most used of the five. Not adopted on its own; worth re-running together with the game-state group.

Decision: adopt the six game-state features into the production feature set at the next retrain. That needs the live path (`tools/daily_run.py`, which builds the day's rows through `build_features`) to compute them for the day's games from the trailing team box scores, and the features file to be rebuilt for training; then a side-by-side of the retrained production model against the current one on the saved holdout before the swap. Replace the proxy with the market spread and total when a price history exists.

### 4. Expected hits in the five-name ledger (`tools/grade.py`)

The grading of the five names now logs expected hits (the sum of the five probabilities) against realized hits and a running z-score over the season, so a cold night (2026-10-29: 0 of 5 against 2.33 expected) is read as dice or as model bias on the record rather than on feel. The season line in the grade log: 4-6 against 5.7 expected, z -1.14 after two nights.

## Backlog from the reading, in order

1. Tag reliability and status mixture. Once the board holds 30 or more days: P(plays), P(starts) and the minutes distribution by 3 PM tag; then test P(DD) = P(out) x P(DD | out) + P(in) x P(DD | in) for picks with a questionable teammate, scored against outcomes and the 6:40 PM price. Also the share of 3 PM picks whose status changed by tip and their hit rate against unchanged picks.
2. Beneficiary-specific redistribution. Replace the aggregate abs_ flags with the absent player's trailing usage, rebound and assist shares interacted with the beneficiary's own with-and-without lift, shrunk toward a role prior; and measure the position-matched backup and the promoted starter separately (the articles' 25 to 30 and 8 to 10 minutes are illustrations to check, not priors).
3. Market spread and total as features, once a price history exists (The Odds API archive from May 2023 on a paid plan, or a free archive Russ approves). The pair test says the game state matters; the proxy test says team strength alone does not predict it.
4. Shared game state in the simulation. Draw a margin, let starter minutes depend on it with a curve fitted to the ten seasons, and judge it on pair Brier score, not on single-leg log loss.
5. Dispersion by category and by minutes volatility in the simulation, checked by tail calibration of P(stat at least 10) for players whose mean sits at 8 to 12.

## Sources

The 22 pages, by URL, with author and byline date as printed, are listed at the top of each batch file in `stokastic nba dfs 2026-10-30/`. Index page: https://www.stokastic.com/articles/nba-dfs (read 2026-10-30, 22 articles, no pagination).
