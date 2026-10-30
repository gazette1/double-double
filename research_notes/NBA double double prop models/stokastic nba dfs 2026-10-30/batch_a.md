# Stokastic NBA DFS articles, set A (six articles)

Method note. All six pages loaded with no paywall and each appeared complete (title through footer). WebFetch passes each page through a small summarizing model that declined to reproduce the text verbatim, so I ran two extraction passes per page (a general pass and a figures-only pass) instead of reading raw text. Figures below are as relayed by that extraction and agreed across both passes. Quotes are short phrases only. Every date is as printed; every footer reads "2025" while the bylines are dated July to September 2026. None of the six cites a backtest, sample size, ROI figure or measured accuracy for any claim. Every article carries promo codes and affiliate sportsbook links, which are omitted here.

---

## 1. NBA DFS Leverage: Game Theory For Large-Field GPPs

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-leverage-game-theory
Author: Josh Engleman. Date: September 6, 2026.

- Leverage arithmetic, on a 30,000-entry contest described as "round numbers": a boom from a 40%-owned player is shared with 12,000 lineups and gains on 18,000 entries; the same boom from an 8%-owned player is shared with 2,400 and gains on 27,600. The arithmetic is correct and is an illustration, not data.
- A sharper version uses a ratio: a player's share of winning lineups divided by his ownership. Above 1 is overweight; below 1 is underweight, "not necessarily off."
- Usage is defined as the share of a team's possessions a player finishes while on the floor. Illustration: a backup guard at 16% usage can move into the low 20s when the star is out. The page says vacated usage concentrates on one or two teammates. No measured redistribution rates.
- Three checks before using an injury-created spot: minutes certainty (confirm the role, not just the inactive status; no numeric cutoff), pace (only "fast, high-total" games; no pace number), and blowout risk.
- Blowout: a double-digit spread is called the "silent killer" of a ceiling. Illustrations: a fill-in's 34-minute expectation drops to 26 in a blowout; a coach caps a fill-in at 22 minutes. No other spread threshold.
- Injury timing: use tonight's injury report, not the depth chart. Late swap is said to matter for warmup scratches and monitoring after lock. No hours-before-tip or minutes-before-lock figure.
- Boom Probability is the chance a player exceeds his salary-based expectation; Bust Probability is the chance he fails to return value. No computation method or probability cutoff is given. The one number is a Jokic example: 35% boom probability at 10% projected ownership.
- The four-box matrix (high or low boom against high or low ownership) uses only High and Low labels with no numeric thresholds. It warns against building only from players owned under 3%.
- Correlation is qualitative: stack a game environment (high total, tight spread) rather than one team's scorers; same-team players compete for possessions and usage is "zero-sum." No correlation values.
- Sims are said to run "tens of thousands of times"; multi-entry lineups should differ by "at least three players." Evidence: none. The text says "None of this is a promise of profit."

For the double-double bot. The ownership, boom-bust-versus-ownership and four-box content does not transfer; it prices a field of lineups, not a sportsbook line. What transfers is the framing that a teammate's absence lifts the next man's usage and minutes only if the role is confirmed, which matches the bot's injury-report features and gives no new magnitude (the 16% to low-20s figure is a hypothetical). The one actionable idea is the blowout and spread check. The bot's described feature list has no closing spread or game total. Test: take ten seasons of game lines (use the line available at 3 PM, not the close, to avoid leakage), bin starters by absolute spread (under 6, 6 to 9.9, 10 and above), measure minutes residual and double-double calibration in each bin, and keep a spread feature only if it improves held-out log loss. A second test from the zero-sum claim: measure the joint double-double rate of same-team pairs against the product of their marginals, since the article asserts a negative link for shared possessions and a positive link for a shared game environment but provides no numbers.

---

## 2. How To Use NBA DFS Projections To Build Better Lineups

URL: https://stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections
Author: Josh Engleman. Date: August 17, 2026.

- Read projections opportunity-first: minutes, then usage, then fantasy points, which are called the "output, not the driver." Illustration: a player at 34 minutes is a different play than the same player at 22 bench minutes. High minutes plus high usage is described as the ceiling profile (assertion).
- Usage is defined as the share of team possessions a player finishes with a shot, a free-throw trip or a turnover.
- Same-day injury news is called "the single biggest edge." A ruled-out starter spikes a teammate's minutes and usage; a backup point guard can inherit pick-and-roll work and closing minutes. Illustration: a 32-minute projection dropping to 24 on a late scratch collapses value. The author never locks until official inactives post, and says the tool updates up to tip.
- Pace: fast pace lifts every player in a game; a slower, high-efficiency team concentrates scoring in "two or three" players. No pace figures.
- Blowout: a "double-digit spread" is the "silent killer," because starters may sit the whole fourth quarter. The author fades high-minute projections in games that could get out of hand. No threshold beyond "double-digit."
- Formulas: Points per dollar = fantasy points / salary x 1,000. Value = fantasy projection minus (salary / 1,000 x 5). Examples: 55 FP at $10,000 gives 5.5 and a value of 5.0; 32 FP at $5,800 gives about 5.5 and a value of 3.0. The $5-per-1,000 baseline is not justified.
- DraftKings versus FanDuel scoring as printed: point 1 / 1; made three +0.5 / none; rebound 1.25 / 1.2; assist 1.5 / 1.5; steal 2 / 3; block 2 / 3; turnover -0.5 / -1; double-double +1.5 / none; triple-double +3 / none. Which sites benefit from multi-category bigs is the author's judgment, not tested.
- Correlation example: a point guard paired with a big man who receives his lobs; Top Stacks and the Sims "build correlation in." No numbers.
- Sims run the contest "thousands of times" and rank lineups by how often they finish near the top of the payout structure. Evidence: none; sims, injury, pace and blowout claims rest on stated experience.

For the double-double bot. Ownership, salary, value formulas and cash-versus-GPP content do not transfer. The scoring table is only a reminder that FanDuel DFS has no double-double bonus, so none of this scoring logic touches FanDuel sportsbook props. The minutes-first order of operations is what the bot already does (minutes model at 4.56 MAE against 5.15), and the article offers no accuracy number to compare against. The pace and double-digit-spread statements are the only candidate features, with the same test as article 1: add absolute spread and game total to the minutes model, check minutes MAE for starters in games with spreads of 10 or more, and check whether predicted double-double probability is biased high in those games. Also worth checking: the article's rule of waiting for official inactives before locking implies that a 3 PM post carries unresolved status risk. Count how often a top-five pick at 3 PM was later ruled out or had a changed starter flag by 6:40 PM.

---

## 3. NBA DFS Projections: How To Build Better Lineups

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-projections
Author: Sam Smith. Date: August 4, 2026.

- Minutes are called the most predictive input in basketball and the "most important column." Projections are said to estimate minutes from recent rotations, coaching tendencies and game script. No accuracy figure or backtest.
- Injury redistribution is qualitative only: a player who inherits a 32-minute role can beat a more talented teammate at 20 minutes; a 12-minute opportunity gap "rarely loses to a talent gap." An injury frees minutes and concentrates usage on the replacement. No usage percentages or redistribution rates.
- Filter mechanics: typing 40 shows players projected for 40 or more fantasy points; typing 8000 in the exclusion filter removes players above $8,000. On a six-game slate this is said to cut a list of more than 100 players to a shortlist (anecdote).
- Salary metrics repeat article 2: Pts/$ = fantasy points / salary x 1,000; Value = projection minus (salary / 1,000 x 5). Worked numbers: Jokic at $10,000 with 58.34 points gives 5.83 and +8.34; an illustrative $6,200 wing at 34.5 gives 5.56 and +3.50. The author states these are illustrative.
- Projected stat categories listed: points, rebounds, assists, steals, blocks, threes, turnovers. The page says double-double and triple-double bonuses create "hidden upside," with the example of a player projected for 9.5 rebounds and 9.0 assists. No bonus-probability calculation is shown.
- Assists are described as streakier night to night than scoring and rebounding, so category splits expose fragile projections. Assertion, no variance metrics.
- Game stacking is suggested for a projected shootout with a "tight spread" and "high implied total." No cutoffs.
- Cash lineups need to beat about half the field and should be high-floor; GPPs should be ceiling-focused. No quantified floors or ceilings.
- Not discussed: pace, blowout thresholds, correlation values, numeric ceiling or floor, any validation.

For the double-double bot. The two pieces that touch the bot are the 9.5 rebounds and 9.0 assists example and the assist-volatility claim. The example is the right intuition for a double-double (two category means near 10 matter more than one large mean), but the article never computes a probability, so there is nothing to copy. Tests: first, bin players by the second-highest projected category mean (for example 8 to 9, 9 to 10, 10 to 11) and check that predicted double-double probability is calibrated within each bin, since near-threshold players are where Platt calibration and negative-binomial dispersion matter most. Second, check whether the negative-binomial dispersion parameter should differ by category; if assists are streakier, fitting a separate dispersion for assists and testing log loss on assist-dependent double-doubles is a clean experiment. The claim that coaching tendencies drive minutes is consistent with the bot already having tested coaching fingerprints without gain; the article gives no evidence to reopen that.

---

## 4. How To Use NBA DFS Data: The Stokastic DataHub Explained

URL: https://stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-data
Author: Josh Engleman. Date: August 1, 2026.

- Site options listed are DraftKings, FanDuel, Yahoo and OwnersBox; contest type is classic or showdown; slate options are main, turbo, night and showdowns.
- Core columns: Name/Team/Opponent, Salary, Position, Minutes, FPPM (fantasy points per minute, the scoring rate while on the floor), and Projected Fantasy Points. The only explicit formula is projected fantasy points equals minutes times scoring rate, which is the same minutes-then-rate decomposition the bot uses.
- Value is fantasy points per $1,000 of salary. Projected Ownership is the share of lineups expected to roster the player. No thresholds.
- Simulation columns: Optimal is how often a player lands in the single highest-scoring simulated lineup; Leverage is the gap between projected ownership and optimal rate; Standard Deviation is how much a player's fantasy score fluctuates (low for cash, high for tournaments); Boom Score and Bust Score are how often a player posts a ceiling or floor game; Ceiling and Floor are the top and bottom of a "normal, realistic range," not the absolute extremes. None has a numeric definition, cutoff or sample size.
- Worked example: a starting point guard is ruled out about an hour before lock, the backup's projected minutes jump, value "usually spikes" because salary has not moved, and the user checks ownership against optimal rate. The page says the loop "takes just a few seconds."
- Timing: timestamps show when projections and ownership were last refreshed. The page says lineups and inactives often confirm "in the final hour before tip," and to distrust numbers read an hour earlier if the timestamp is stale near lock. No refresh frequency.
- Stated rule: do not trust a projected total until you have seen the minutes and FPPM behind it. Evidence: none; the page offers no methodology, backtest or accuracy rate.

For the double-double bot. Nothing here is new methodology; it names the fields (minutes, per-minute rate, standard deviation, a boom rate, a floor and ceiling range) without saying how they are computed, so there is no formula to adopt. The decomposition into minutes times a per-minute rate supports what the bot already does. The timing statement is the useful operational fact: the page says lineup and inactive confirmation clusters in the final hour before tip, which sits after the bot's 3 PM post and around its 6:40 PM snapshot. Test: log every top-five pick at 3 PM along with its status at 6:40 PM (out, questionable to active, starter flag changed, teammate newly out) and compute the hit rate and calibration of picks whose status changed against those whose status did not. If changed-status picks are miscalibrated, add a second post or an automatic flag at the snapshot. The Boom Score idea maps to the bot's own double-double probability, so a separate boom field adds nothing.

---

## 5. NBA DFS Tournament Strategy: How To Build Better GPP Lineups

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-tournament-strategy
Author: Stokastic Staff. Date: August 1, 2026.

- Core claim: individual ownership "barely matters" in large-field GPPs; judge ownership at the lineup level, build the best lineup first, then pivot two or three spots. Hand-built applies to three-max, five-max or 20-max entries.
- Hypothetical: the highest boom-percentage player on a slate is 60% owned, and 150 lineups with him and 150 without him could both project to positive ROI. No data.
- Strategy table verdicts: fade all chalk is "old, broken advice"; straight optimal lineup is "great for cash, too safe for GPPs"; optimal plus 2 to 3 pivots is "the tournament sweet spot"; all 2%-owned darts are "too unique to win." These verdicts are unsupported by cited data.
- Worked pivot (stated to be illustrative archetypes, not a real slate): an elite chalk center at about 50% ownership becomes a cheaper value big at about 25%, removing "roughly 25 percentage points" of ownership and freeing salary; the saved salary funds a high-ceiling wing from outside the top-owned tier. The remaining spots are untouched.
- Audit hypothetical: the top player is 70% owned across the field but appears in 80% of lineups from top 150-entry-max players. The article suggests fading the "two highest-owned guys" in some cases.
- Sims described as ranking lineups by simulated ROI against a realistic field, over "thousands of contests."
- The page never discusses minutes, usage redistribution, pace, blowouts, injury timing, variance or correlation. The only usage mention is a related-article title.

For the double-double bot. This article is about duplicating and differentiating lineups in a contest field and has no transfer to predicting double-doubles or pricing props. The one loose parallel is that the Sims rank lineups by simulated ROI instead of by raw win rate. The bot posts the five most likely double-doubles, which ranks by probability. A test the bot could run on its own data: compare the realized return, graded against closing prices, of the five highest-probability picks each day against the five with the largest edge (model probability minus price-implied probability) among players above a minimum probability. This is my suggestion, not something the article tests. No other test comes from this page.

---

## 6. NBA DFS Multi-Entry Strategy: Be Wrong On Purpose

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-multi-entry-strategy
Author: Stokastic Staff. Date: July 29, 2026.

- Multi-entry is framed as coverage across 20, 50 or 150 lineups; the main lever is the gap between a player's exposure in your pool and his projected field ownership.
- First build: cap each player at 65%, because leaving the cap at 100% puts a value guard in every lineup; then iterate two or three passes of sort, fix and rerun until changes get small.
- Worked example from a 2018 slate (the page says the salaries and exposures are dated): Alex Len 64% build exposure against 14% projected ownership, cut to 40%; Omari Spellman 64% against 17%, cut to 40%; Gary Clark 29% against about 2%, set to 12% as a deliberate exception. Cutting Len removes 24 percentage points, which spread to Cody Zeller, Clint Capela and PJ Tucker.
- Randomness: 50% randomness on a 50-point projection gives a range of 25 to 75. More randomness needs fewer uniques. Randomness should scale with player volatility, so a boom-or-bust scorer swinging from a dud to a "60-burger" gets wider randomness than a steady veteran.
- Exposure arithmetic: on FanDuel, total exposure at a two-slot position should exceed 200% (shooting guards at 204% is "too thin"). A global cap of about 3 to 4 times projected ownership, then hand-tuned. A $3,700 value guard can run near 80%; a $5,900 forward is capped around 40% to 50%. Five-max: cap favorite plays near 80%. Three-game slate: tolerate more chalk, no number.
- Late news: upload a locked full-slate pool 30 minutes before lock, then make single-player swaps for scratches. Minutes risk is qualitative: a starter scratched about an hour before tip, a blowout emptying the fourth quarter, and "full minutes" overs dying on the bench.
- Blowouts: no numeric guidance; the page says that over 150 lineups the outcomes "even out." Pace is mentioned once in passing. Correlation is not discussed beyond naming a stacks feature.
- Evidence: none; the only data is the single 2018 slate.

For the double-double bot. Exposure caps, ownership gaps and salary guidance do not transfer. Two points are loosely relevant. First, scaling randomness to a player's volatility is the same principle as giving each player or role his own negative-binomial dispersion; the test is whether a per-player or per-role dispersion beats one global value on log loss and on calibration of high-minutes versus low-minutes players. Second, the statement that blowout risk "evens out" across 150 lineups does not hold for a daily post of five picks or for a multi-leg combo, where a blowout in one game can remove several legs together if the legs share a game. A test: for same-game combos in historical data, compare simulated joint double-double probability that includes a shared game-level blowout factor against the product of the individual probabilities, and check which is better calibrated. The 30-minutes-before-lock swap practice supports comparing the bot's 6:40 PM snapshot against the lineup news that appears afterward, as noted for article 4.
