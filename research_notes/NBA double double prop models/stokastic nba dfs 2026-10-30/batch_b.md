# Stokastic NBA DFS articles: reading notes for the double-double bot

Method note. All six pages were fetched on 2026-10-30 with WebFetch. WebFetch returns a model-generated extract of each page, not raw HTML, and declined to reproduce body text verbatim, so figures below come from those extracts and short quotes. Every page loaded, looked complete (no truncation, no paywall), and needed no offset reads. All six carry a 2026 publication date (July 16 to 21, 2026) and a "© 2025" footer, which do not agree. All six are marketing pieces for paid Stokastic tools (each has a promo code). None contains a backtest, a sample size, an error metric, a regression output or a field-level data schema. Where a claim has no evidence behind it, the bullet says so.

---

## 1. NBA DFS Strategy: How Winners Build Lineups

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs
- Author: Stokastic Staff
- Date: July 21, 2026 (no update date)

Concrete claims:
- The article says NBA outcomes are predictable enough to land "within about 10 fantasy points" of a player's result, and that the edge is projection accuracy, especially minutes. No error data or method is given.
- It mentions a Boom/Bust floor-and-ceiling range per player. No distribution, percentile definition or method is given.
- Central strategy: target the backup of a ruled-out starter whose salary has not updated. It says a backup's minutes and usage rise when a starter is out, with no quantified model.
- Worked example (labeled an illustration, not a real slate): $50,000 DraftKings cap, backup priced at $4,200 and "roughly $1,500 to $2,000 below" his new-role value, studs at $11,500 (C) and $10,800 (G), a pivot guard 45% owned and a wing 10 to 12% owned. The $1,500 to $2,000 gap has no source.
- Teammate correlation: "most teammate stats are negatively correlated, with assists and points the one positive pairing." Not quantified.
- Stokastic Sims are said to run the contest "tens of thousands" of times and rank lineups by how often they finish first. No validation.
- The claim that injury-driven builds "tend to grade out ahead" in the Sims rests on "our experience" only.
- Format facts: DraftKings classic is 8 roster spots with a $50,000 cap; FanDuel is 9 spots with a $60,000 cap; scoring is points, rebounds, assists, steals, blocks, threes, minus turnovers. Showdown captain gets 1.5x points and salary.
- Not covered: pace, game script, blowouts, variance. Minutes and usage are named but not explained.

For the double-double bot. Almost all of this is DFS format and salary content and does not transfer. The one transferable idea is that the market is slowest to reprice a backup after a starter is ruled out (the article's "salary has not updated"). The bot can test the prop-market analogue directly: for player-games where a teammate's out status appears between the 3 PM post and the 6:40 PM snapshot (or between the 6:40 PM snapshot and close), compare the model's probability with the implied FanDuel probability at each snapshot and check whether closing-line movement toward the model is larger for those games than for unchanged games. Separately, test the model's calibration on the "starter newly out" subset, since that is the subset where the article says projections are most valuable. The teammate-correlation claim is the only item relevant to multi-leg combos and is tested under article 6.

---

## 2. How To Win At NBA DFS: Start With Cash Games

- URL: https://stokastic.com/articles/nba-dfs/how-to-win-at-nba-dfs
- Author: Josh Engleman
- Date: July 19, 2026 (no update date)

Concrete claims:
- Cash lineups should aim to win "roughly 51 percent of the time." Asserted, not shown.
- Lineup grading: Projection Score target "Above 90" (close to the optimal build) and Contrarian Score target "Under 10", with "a little wiggle room depending on the slate." The formulas behind both scores are not given.
- Workflow: the Single-Lineup Simulator builds the optimal lineup from Stokastic projections in one click; the author then generates the top 10 to 20 optimal lineups and compares each choice by how many projected points it costs. The claim that this is "the mathematically best build" is unsupported, and the page defers the simulator-versus-optimizer argument to another article.
- Payout facts: in head-to-heads a 25th-percentile lineup returns about 25 percent; in 50/50s and double-ups a 25th-percentile lineup returns $0.
- Single-entry contests are preferred over multi-entry (up to 150 lineups) because sharps can concentrate lineups in the latter. FanDuel single-entry 100-person 50/50s are described as offered "up to $25" and "reliably" filling; no fill data.
- "More often than not a winning cash lineup is highly projected and highly owned": no data behind it.
- Advice to avoid "two centers from the same team", with no explanation or evidence.
- Minutes, usage, pace, injuries and game script are not discussed beyond a related-article link title ("NBA DFS Usage Rate Strategy: How Injuries Create Value"). The projection inputs and method are not described.

For the double-double bot. Nothing quantitative transfers. The cash-game framing (maximize floor, beat a break-even rate) is the DFS version of what the bot already does, which is to pick the highest-probability events and grade against the price. The one testable item is the "two centers from the same team" warning: using ten seasons of box scores, compute the joint rate at which both starting centers or both bigs on one team record a double-double, and compare it with the product of their marginal rates, conditioned on game. If the joint rate is below the product, the bot should not post two same-team bigs as independent picks and should not price them as independent in a combo. The grading idea of comparing each pick with the 10th to 20th ranked alternatives is cheap to log (store the full ranked candidate list daily) but gives no accuracy gain by itself.

---

## 3. NBA DFS Post-Contest Simulator: Grade Your Lineups

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-post-contest-simulator
- Author: Josh Engleman
- Date: July 19, 2026 (no update date)

Concrete claims:
- The tool re-simulates every lineup in a completed contest "tens of thousands of times" (another passage says "thousands of outcomes", so the count is inconsistent). Inputs: sport, site, date, slate (early, main, showdown), contest, username, and an optional second username for head-to-head comparison. Leaving the username blank studies a contest the user did not play.
- Core thesis: "Sim ROI" is the honest verdict on a lineup and the number to track, rather than the single-night result. How Sim ROI is computed and validated is not explained.
- Walkthrough for one entrant on one NBA slate: Lineups Played 150; Duplicates Per Lineup about 2; Sim ROI 17.7%; Actual Lineup ROI 576.4%. Average Ownership Sum is listed as a metric without a value.
- Player-level example: Luka Doncic Sim player ROI 315.8%; the entrant's Luka lineups returned 13.6% actual ROI, at 20% ownership against 14.5% field ownership.
- The actual GPP-winning lineup had a 5.3% Sim ROI. The entrant's best Sim ROI lineup ranked third-best in the contest by expected value. Another entrant's lineup showed a 143.9% Sim ROI. A 150-lineup entrant showed -100% Sim ROI and -100% actual ROI, which the article attributes to probable dummy entries.
- Views named: Player ROI (field ownership, Sim player ROI, actual player ROI) and Lineup ROI (projected points, actual points, ownership sum, finishing place, duplicate count, Sim ROI, actual ROI).
- No simulation methodology, inputs or projection source is given. Minutes, usage, pace, injuries, correlation and game script are not discussed. General lessons about variance are drawn from single-slate, single-entrant examples.

For the double-double bot. The transferable idea is grading on expected value as well as on outcome. The 17.7% Sim ROI against 576.4% actual ROI is an illustration of how far one outcome set can sit from expectation, and the winning lineup having a 5.3% Sim ROI shows the same thing. The bot grades the five posted picks against closing prices; with five picks a day that sample is small. Tests: (1) each day compute expected hits (sum of model probabilities for the posted five) and expected ROI at the closing price, and track the cumulative gap to realized results as a z-score or a running log-loss, so luck and model error are separated; (2) grade the whole priced slate (every player with a FanDuel double-double price), not only the top five, which mirrors the tool's ability to study a contest you did not play and avoids selection bias from the top-five filter; (3) compare the model's priced-slate log loss with the closing price's log loss, which is the bot's existing closing-line comparison extended to all candidates.

---

## 4. NBA DFS Research: How To Project Minutes, Usage & Pace

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-research
- Author: Stokastic Staff
- Date: July 19, 2026 (no update date)

Section headings (from a second pass): TL;DR; Step 1 Project The Minutes; Step 2 Adjust The Rates When Someone Is Off The Floor; Step 3 Identify High Pace And High Total; A Worked Example; Where The Research Lives In Our Tools; In Summary. The extract reports two small tables (minutes data sources; usage, rebounding and assist rate) and no charts. The embedded video is not transcribed.

Concrete claims:
- Fixed order of work: project minutes first (the base), adjust usage and rebounding rates for the lineup (the multiplier), then assess pace and Vegas total (the environment).
- Minutes sources named: season averages (best for stable roles with full samples), recent playing time (best when a role is changing), and game logs or substitution patterns (to learn coaching rotations).
- Minutes spread example: Mitchell Robinson "might play anywhere from 14 minutes to 28" depending on foul trouble, with a raw average in the low-to-mid 20s. The point made is that one number hides the spread. No data source or time window is given.
- Rates named: usage rate (scorers and ball-handlers), rebounding rate (bigs and high-rebound wings), assist rate (lead guards and playmakers). On/off tools are recommended to measure how each rate shifts with a teammate on or off the floor. No rebounding or assist redistribution numbers are given.
- Harden and Westbrook example: Harden's usage "would skyrocket whenever Westbrook was off the floor," climbing toward nearly 50%. No season, sample or source. The worked steps are: confirm Harden's minutes are stable, treat Westbrook's inactive status as the usage trigger, then check that the game total and pace support the extra volume.
- Pace estimate: (one team's pace x opponent's pace) divided by league-average pace, called a "workable estimate." Not validated.
- Early-season guidance: pace and total figures are "noisy"; lean on league averages with slight matchup adjustment and do not trust a five-game pace sample.
- Higher totals are said to produce more fantasy points and higher pace more possessions. Qualitative only, no effect size.
- Tools are said to show projected minutes, on/off usage, ownership and pace-aware projections (NBA DataHub, Sims). No field list.
- Explicitly absent: no studies, sample sizes, correlations, regression coefficients, tables of results or backtests. The "underpriced beneficiary of an injured usage leader" claim is asserted without evidence.

For the double-double bot. The three-step order matches the bot's pipeline (minutes model, then rates, then environment), so this article confirms structure and gives no new numbers. Tests it suggests, each checkable on the bot's ten seasons of box scores: (1) Minutes dispersion. The Robinson example is a statement that foul trouble makes minutes variance player-specific. Add per-player rolling minutes standard deviation, the share of recent games with 5 or more fouls, and 10th and 90th percentile minutes as features, or move the minutes model to quantile outputs so the simulation draws from a player-specific spread instead of a common error term. Compare the interval coverage of simulated minutes with realized minutes, and the effect on double-double log loss for centers and other foul-prone bigs. (2) Pace. The bot lists opponent rates but not an explicit matchup pace term; add (team pace x opponent pace) / league pace from trailing games with shrinkage toward league average early in the season (the article's own caution about five-game samples), and test whether it adds anything over the 155 existing features. The prior null results on tracking data do not cover this term. (3) Game total and spread. The article names Vegas total as the environment input; the bot's feature list does not mention a game total or spread, so check whether either is present and, if not, test both, since they also drive blowout minutes. (4) On/off redistribution. The bot has teammate-absence flags from the injury report; test replacing binary flags with the absent player's trailing per-minute usage, rebound and assist shares, interacted with the specific player's own with/without-teammate lift computed over past games, and compare with the flags. The article gives no coefficients, so the bot must estimate the lift itself. Usage-rate numbers like Harden's "nearly 50%" should not be used as a prior; they are unsourced and come from a former roster.

---

## 5. NBA DFS Sims Vs. Optimizers: Why the GPP Edge Wins

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-sims-vs-optimizers
- Author: Jake Hari
- Date: July 16, 2026 (no update date)

Section headings: TL;DR; What An NBA DFS Optimizer Actually Does (And Where It Falls Short); How NBA DFS Sims Model The Full Range Of Outcomes; A Worked Example: Using Ownership Leverage For GPP Edge; Correlation And Stacking The Sims Build In; Adapting To NBA Game Flow And Variance; Customization That Goes Beyond Lock, Exclude, And Cap; More Accurate For Large Tournaments; Handling Breaking News And Late Swap; The Honest Verdict; Try It On Your Next Slate.

Concrete claims:
- Thesis: an optimizer builds lineups from one fixed projection per player and therefore targets the median outcome; large-field GPPs pay for ceiling, so a simulation that models the spread of outcomes is better suited. Cash games are said to need a separate projection-based, highest-floor workflow.
- Simulated in-game events: foul trouble, rotation changes, game tempo or pace, blowouts that empty benches, and backup minutes. Run counts are given as "thousands of simulations" in one place and "hundreds to thousands of scenarios" in another.
- Output is a simulated ROI against a GPP payout structure with ownership folded in. "Percentage to first" is a user setting; the example is $100,000 to first from a $400,000 pool, or 25%.
- Correlation is said to emerge from simulated game scripts, not manual stack toggles. Examples: a primary playmaker with the big man who finishes his assists, and players from the two teams in a fast-paced game (the two extracts worded this slightly differently). No correlation values are given.
- Injury handling: when a starter is ruled out the model shifts usage to the next man up, and the user can override the minutes input. Example: a fill-in guard whose salary implies about 22 minutes but who is expected to play 34. Boom/Bust outputs estimate the chance a player beats or misses projection.
- Late news: feed in inactives or lineup changes and re-run; re-ranking is said to take "seconds," and the late swap is called "one of the highest-value in-slate moves." Unquantified.
- Comparison table: core input (one projection vs thousands of outcomes), objective (median vs simulated ROI), variance (ignored vs modeled), ownership (not considered vs included), correlation (manual vs emergent), late news (manual rebuild vs re-run).
- Ownership example: 10% exposure to a player the field owns at about 3%, "roughly a 7% edge." Illustrative only and not relevant to the bot.
- Evidence: none. No backtests, ROI history, win rates or sample sizes. "More accurate for large tournaments" and "tilt the odds over a season" are unsupported. The statistical method is not explained: no distribution family, injury probabilities, correlation estimation or validation. The "fourth-best vs. best lineup" variance illustration is hypothetical.

For the double-double bot. This is the closest article to the bot's own design (minutes drawn first, then negative-binomial stats), and it adds a list of what the simulation should vary, with no numbers. Of that list, the bot should check whether its simulation has a shared game-level state; the article says correlation and blowouts arise because players in one game share a script. Tests: (1) Blowout. Draw a final margin from the pre-game spread (or a team-strength proxy), make starter minutes depend on margin using a curve fitted to the bot's own ten seasons of box scores (starter minutes versus final margin), and compare double-double log loss and reliability against the current minutes draw, with results split by spread bucket and by minutes bucket. (2) Dispersion check. Compare the simulated minutes and stat distributions with realized values (coverage of 10-90 and 5-95 intervals) to confirm the negative-binomial draws are not too narrow. (3) Model comparison. On a held-out season, compare log loss and reliability curves for simulation-derived P(DD), LightGBM + Platt P(DD) and a simple blend; if the simulation adds nothing over the calibrated model, the shared-state work should be judged on joint probabilities for combos instead. (4) Joint probability. For same-team and same-game pairs, compare the simulation's joint P(both DD) against the independent product and against empirical pair frequencies; a shared game state should be adopted only if it improves pair Brier score. (5) Minutes override sensitivity: the 22 versus 34 minutes example is a sensitivity test the bot can run by re-running the sim for a starter-out replacement under several minutes inputs, to see how steeply P(DD) responds and therefore how much minutes error (the bot's 4.56 MAE) costs in probability. (6) Late news: log how often the posted five at 3 PM change if the sim is re-run at the 6:40 PM snapshot with updated inactives, and whether the changed picks beat the original ones; the article asserts the value of re-running but gives no figure.

---

## 6. NBA DFS Strategy Guide: How I Win On DraftKings And FanDuel

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-strategy-guide
- Author: Alex Baker
- Date: July 16, 2026 (no update date). The page title tag reads "DFS NBA Strategy: Win Bigger On DraftKings & FanDuel"; the on-page H1 is "NBA DFS Strategy Guide: How I Win On DraftKings And FanDuel".

Concrete claims:
- Projection accuracy: players can usually be guessed "within about 10 fantasy points" on a given night; being "a minute or a couple of points off" a true projection can cause over-committing; projections sharpen as inactives are confirmed. No methodology or sample.
- Teammate correlation: assists-to-points is the only meaningfully positive teammate pairing; most other teammate stats are negatively correlated. No data cited.
- Game script: loading only the favored team's players cuts ceiling because the underdog should keep its starters in and producing. Overtime is said to roughly offset game stacks ("roughly a wash"). A deep-bench player outscoring a starter is described as minimal odds. All three are asserted without evidence.
- Injury-driven build example: $50,000 cap, 8 roster spots, LaMelo Ball ruled out, the backup guard priced at $4,200 with an estimated true value $1,500 to $2,000 higher, whose role rises from 22 to 32-plus minutes; studs Jokic at $11,500 (38% owned) and SGA at $10,800 (31%); the backup 45% owned; a suggested low-owned wing at 10 to 12%. A ruled-out starter's usage is said to redistribute to teammates, with no usage-rate figures.
- Duplication is estimated by multiplying each player's ownership; the author admits this assumes independence and is not a measure of contrarianism.
- Cash targets the highest floor from straight projections and ownership "barely matters"; tournaments target ceiling, leverage and low ownership. Best GPP lineups are said to look "fairly similar regardless of field size" (no data).
- Showdown: the captain slot applies a 1.5x multiplier to points and salary. Late swap: only unstarted games can be swapped; the article recommends 2-for-2 or 3-for-3 swaps.
- Sims are said to simulate "tens of thousands" of contests; the page describes ranking both by win rate and by simulated ROI, which is inconsistent. Pace and variance are not analyzed.

For the double-double bot. Most of this is lineup construction, showdown and late-swap content that does not apply. Three claims are testable with the bot's data. (1) Teammate correlation: for same-team pairs, compute the correlation of residuals (actual minus predicted) in rebounds, assists and points, and of double-double indicators after conditioning on each player's predicted probability. If rebounds are negatively correlated between teammates, as the article implies, multi-leg combos of two same-team rebounders should be priced below the independent product, and a scorer plus the playmaker who feeds him is the pair most likely to be positive. (2) Game script: bucket starters by pre-game spread and test whether double-double residuals (outcome minus model probability) differ between favorites and underdogs, with minutes and blowout flags held fixed; this checks the article's claim that favorite-side starters lose ceiling. (3) Overtime: from ten seasons of box scores compute the share of player-game double-doubles that occurred in overtime games and the minutes uplift in those games, to see whether the overtime tail needs an explicit term in the minutes simulation. Also run the starter-out subset check: minutes MAE for backups whose starter is out, against the overall 4.56, since the article's 22-to-32-plus example implies these are the largest minutes shifts.

---

## Overall assessment

- All six articles are product marketing. Only articles 4 and 5 touch minutes, usage, pace and simulation structure, and they contain no data. Treat every figure above (10 fantasy points, 50% Harden usage, 14 to 28 minutes for Robinson, 22 to 34 minutes, $1,500 to $2,000, 51 percent) as illustrative or unsourced, not as priors.
- What the articles give the bot is a list of hypotheses to test with its own ten seasons of box scores: player-specific minutes dispersion, an explicit matchup pace term, game total and spread as inputs, a shared game-level blowout state in the simulation, on/off-based redistribution of usage and rebounds, teammate correlation for combos, and a rerun of the sim after late news.
- Content with no transfer: ownership, leverage, salary, contest-structure, showdown, late-swap and lineup-duplication material (most of articles 1, 2, 3 and 6).
