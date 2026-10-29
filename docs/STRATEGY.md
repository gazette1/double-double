# Double-double props: buy edge, not favorites

Russell Harris, October 2026. Background source for `docs/strategy.html`. Numbers come from the reports under `data/eval/` unless a source is cited; sources are listed at the end.

## The bet

FanDuel lists a Yes side on about nine players per game: will this player record a double-double tonight. There is no No side, so the house margin is invisible on FanDuel's own board. On the 2026-10-29 slate Domantas Sabonis was -700, Jalen Johnson -188, Evan Mobley +120, and the rest ran from +158 to +5000. DraftKings had Sabonis at -438, and FanDuel was shorter than DraftKings on 17 of 27 shared players. The bet stands once the player takes the court, overtime counts, and an early injury exit is a loss.

Across the 2025-26 regular season 7.3 percent of player-games ended in a double-double, about 11.6 a night, and the top 30 players produced 45.5 percent of them [1]. The rate fell from 8.7 percent the season before because starters play fewer minutes.

## What most people do

**Pick the most likely double-doubles.** Jokic, Sabonis, Giannis, Davis, Towns, Embiid. Every model I tested, including a plain season rate, lands on the same names. FanDuel prices them at -700 to -1100, which implies 87.5 to 91.7 percent. No high-volume player has delivered that over the last two seasons: the best were Sabonis at 87.1 percent in 2024-25 and Jokic at 84.6 percent in 2025-26. Paying 90 percent for an 85 percent event loses money however good the model is.

**Pick by streaks and season averages.** A season rate shrunk toward a prior is the baseline in my backtest. It ranks players well (AUC 0.87) and the model beats it in every test season, by 0.009 to 0.013 of calibrated log loss. That gap is small per bet, and it is the whole product at the prices where the model disagrees with the market.

**Buy a projection.** A peer-reviewed study of 1,658 paid fantasy projections from four providers found them inefficient and in some cases biased [2]. DARKO, the strongest public daily system, says no input is harder to forecast than minutes [3]. The public double-double record is thin: one vendor's self-reported 12-4 run over 16 picks [4], and the one blind backtest I found lost 26 percent on the 2025-26 double-double market [5]. Another open model went from +6.1 percent on 6,424 development bets to -1.8 percent on a 35-bet pre-registered holdout [6].

**Stack parlays.** Three legs priced at -5 percent each compound to about -14 percent. Favorites are also where the de-vig method alone moves the fair probability by more than the edge anyone claims: Jokic reads 86.5 percent under multiplicative de-vig and 90.2 under power de-vig from the same two-way quote.

**Defense versus position.** The most popular matchup angle, and it tested as noise here (section 7 below).

**Follow a capper.** Public leaderboards show windows of 6 to 85 picks and no closing-line record [7][8].

## What this bot does instead

**1. Calibrated probability from ten seasons of box scores.** 239,334 player-games from 2017-18 onward and 155 features computed strictly from prior games: rolling and exponentially weighted rates, minutes trend, role, teammate absences, opponent rates. Gradient boosting, walk-forward tests on four seasons, Platt calibration fitted on a holdout slice. Pooled calibrated log loss on 103,009 regular-season test rows: season-rate baseline 0.2009, model 0.1892. Calibration matters more than accuracy for betting: a backtest that selected NBA models by calibration returned +34.7 percent against -35.2 percent for accuracy-selected models [9].

**2. Minutes first.** Minutes carry the news; per-minute rates carry the skill. Rebound rate holds year to year at r 0.95 and assist rate at 0.91 [10], while role half-lives run one to three games [3]. The v2 minutes model lands at a mean absolute error of 4.56 minutes against 5.15 for a five-game average, which for a center at 0.35 rebounds a minute is two rebounds, often the whole margin. Blowouts are the measured minutes risk: over props hit 46.7 percent in games decided by 7 or fewer against 40.9 percent at 20 or more [11].

**3. Stats drawn jointly, not multiplied.** Within a player, points, rebounds and assists correlate at 0.12 to 0.27, almost entirely through shared minutes; conditional on minutes the partial correlations are 0.08, -0.05 and 0.07. Scoring is overdispersed, and a negative binomial beats Poisson on NBA scoring [12]. The v2 simulation draws minutes first, then conditionally independent negative binomial stats, and the realized points-plus-rebounds double-double rate for mid-range players runs 16 percent above the independence product.

**4. Rank by edge, not probability.** This is the part that changes the product. In the backtest the three highest-probability picks each night hit 68.6 percent at a mean implied price of 73.3 percent and return -4.7 percent per unit. The three highest-edge picks, model probability minus a proxy price, hit 42.7 percent at a mean price of 37.6 percent and return +16 percent per unit, positive in each of the four test seasons (+1.5, +24, +17, +22). The proxy price is an assumption, 1.08 times the season rate, and softer than a real book, so +16 is the ceiling of the model's information advantage, not an expected return. The direction is the finding: the model's information lives in the mid-tier, from plus money to modest minus prices, and nowhere near -700.

**5. Shrink the top of the board.** Selecting the maximum of noisy estimates biases it upward. The nightly top-3 picks carry a mean calibrated probability of 0.70 and hit 0.65 per leg; all three hit on 28 percent of nights against 34 percent from multiplying the legs. A three-card combination priced from a model's own legs needs about 5 points of shrinkage per leg. Most combo pricing skips this and overpays.

**6. Log every price and grade by closing line.** My strikeout bot ran a whole season, 492 picks at 383-95 on its safe line, and never logged a price, so its profitability is undetermined; judged at the market line it hit 54.7 percent and the market line forecast strikeouts better than the model did. This bot snapshots FanDuel, DraftKings and two-way books before and at tip, de-vigs the two-way quotes under multiplicative and power methods, and records fair closing line value on every pick. A model only earns where it disagrees with an informed price and is right [13]. The gate before any real stake: positive fair closing line value above FanDuel's one-sided margin over at least 100 picks under both de-vig methods.

**7. Test ideas before trusting them, and publish the misses.** Three ideas got the same controlled test: identical rows, hyperparameters, seed, holdout and calibration, with a block bootstrap by game date on the difference.

- Tracking and matchup data from stats.nba.com: rebound chances, potential assists, box outs, who guarded whom, and what the opponent allows to the position a player is actually defended by. Built, matched to 99.998 percent of box-score rows, and worth nothing measurable: -0.00014 of log loss against the model's 0.0118 advantage over the season rate, with the matchup group slightly negative.
- Weighting recent seasons more than old ones: a three-season half-life is indistinguishable from no decay; a one-season half-life and a three-season window are significantly worse. The recency the model needs is already in the per-player exponentially weighted features.
- Coaching staffs tracked across teams: head coach tenure and in-season changes, staff continuity, each coach's pace, rebounding, assist and rotation fingerprint carried from prior stops, and the opponent coach's defensive fingerprint. Built and tested the same way over four seasons: +0.00005 of log loss pooled, one season better and one worse, nothing measurable. The splits the model used most were the opponent coach's rotation concentration, tenure and pace. Report in `data/eval/coach/`.

## Side by side

| | Probability-ranked favorites | Season rate or streaks | Paid projections | Parlays | This bot |
|---|---|---|---|---|---|
| Ranks by | highest probability | recent hit rate | the vendor's number | the combined price | probability minus the de-vigged price |
| Where it bets | -700 to -1100 | wherever the streak is | wherever the vendor says | stacked favorites | plus money to modest minus |
| Calibration | none | none | unverified | none | Platt on a holdout, checked by season |
| Price logging | rare | rare | no | no | every pick, open and close, two books plus two-way quotes |
| Combos | multiplied | multiplied | multiplied | multiplied | legs shrunk about 5 points for selection |
| New feature ideas | adopted on story | adopted on story | opaque | not applicable | controlled test, misses published |
| Verified record | none public | none public | inefficient in peer review | compounding margin | 100-pick closing-line gate before real stakes |

## What would make me wrong

- Sample size. Proving a 2-point edge at -300 takes about 3,600 bets at 95 percent confidence and 80 percent power, seven seasons at three picks a night; a 3-point edge about 1,600. Closing line value is the faster test, which is why it is the gate.
- Limits. Massachusetts data show 0.64 percent of accounts limited, disproportionately closing-line beaters [14], and operators have defended limiting customers with a better model [15]. A real 2 to 3 point edge is worth roughly $190 to $2,100 a season at $25 to $100 stake caps.
- Prices. Historical double-double prices are not free; The Odds API archive starts in May 2023 on paid plans [16]. Until the live log accumulates, every return figure here is measured against a proxy price.
- Base-rate drift. Every model over-predicted 2025-26 by about half a point of base rate because starters' minutes compressed league-wide. Weekly retraining and the minutes model answer that; recency weighting of old seasons did not.

## Sources

1. Land of Basketball, 2025-26 regular-season double-doubles: https://www.landofbasketball.com/year_by_year_stats/2025_2026_double_doubles_rs.htm
2. Koehler, Tegtmeier and Doepke 2024, efficiency of paid fantasy projections (peer-reviewed): https://link.springer.com/article/10.1007/s12197-023-09646-7
3. DARKO, about the model: https://www.darko.app/about
4. Dimers, triple-double betting article (self-reported record): https://www.dimers.com/nba/news/2025-nba-betting-how-to-capitalize-on-the-leagues-historical-triple-double-numbers
5. KyShiesty919, NBA-Props README (self-reported backtests): https://github.com/KyShiesty919/NBA-Props
6. seantanger, nba-props-research (self-reported, pre-registered holdout): https://github.com/seantanger/nba-props-research
7. Action Network, top experts leaderboard: https://www.actionnetwork.com/nba/picks/top-experts
8. Juice Reel, NBA handicapper records: https://www.juicereel.com/best-nba-handicappers
9. Walsh and Joshi 2023, calibration against accuracy in sports betting models (preprint): https://arxiv.org/abs/2303.06021
10. Medvedovsky 2020, NBA stabilization rates: https://kmedved.com/2020/08/06/nba-stabilization-rates-and-the-padding-approach/
11. DataStreak, blowouts and fourth-quarter props: https://datastreak.com/insights/nba-blowouts-4th-quarter-props
12. Negative binomial fit to NBA team scoring (peer-reviewed): https://pmc.ncbi.nlm.nih.gov/articles/PMC8282683/
13. Hubacek, Sourek and Zelezny 2019, exploiting sports-betting markets using machine learning (peer-reviewed): https://econpapers.repec.org/RePEc:eee:intfor:v:35:y:2019:i:2:p:783-796
14. Covers, Massachusetts limiting data, September 2025: https://www.covers.com/industry/massachusetts-limiting-sports-betting-prediction-markets-exchanges-sharps-box-september-2025
15. ESPN, sportsbooks defend limiting sharp customers: https://www.espn.com/sports-betting/story/_/id/41231266/espn-sports-betting-news-sportsbooks-defend-practice-limiting-sharp-customers
16. The Odds API, v4 guide and historical data: https://the-odds-api.com/liveapi/guides/v4/

Project reports: `data/eval/v1/report_v1.md`, `data/eval/v2/report_v2.md`, `data/eval/tracking/report_tracking.md`, `data/eval/recency/report_recency.md`, `data/eval/coach/report_coach.md`. Research notes with the full citation trail: `research_notes/` and `reports/NBA double double prop models.md`.
