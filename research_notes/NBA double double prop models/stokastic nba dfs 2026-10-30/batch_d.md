# Stokastic NBA DFS articles: notes for the double-double bot

Read on 2026-10-30. Method note: all five pages loaded. WebFetch declined to return the raw article text and returned model-written summaries each time, so I could not page through the text with offset, and none of the wording below is verbatim unless it is shown in quotation marks as the "nearest wording" the tool gave. I made two to four calls per article and cross-checked the figures that matter (article 4 and article 5 were checked a second time number by number; every figure listed was confirmed on the second pass unless stated). The tool reported no truncation on any page. Article dates are as printed on the pages: they run from June 17 to July 13, 2026, and several pages carry a "© 2025" footer and cite a leaderboard "as of July 16", so the dates on the site are not fully consistent.

Overall finding: these are vendor marketing and how-to pages for DraftKings and FanDuel daily fantasy tournaments. None gives a backtest, a sample size, a calibration result or a model specification. Every number is either a definition, an arithmetic example or a hypothetical. The pages that matter most to the bot (4 and 5) are the thinnest on data. The useful content is a handful of rules of thumb to test against the bot's own ten seasons of box scores, not figures to import.

---

## 1. How To Use NBA DFS Sims To Win On DK & FanDuel

- URL: https://stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-sims
- Author: Stokastic Staff
- Date: July 13, 2026

Claims, methods and numbers:
- Three-step workflow for large-field tournaments (GPPs): build a lineup pool, run a contest simulation, then shape exposures. Cash games (double-ups, 50/50s) are said to call for the highest-floor lineup built directly from projections, not from the Sims.
- Pool sizes: Max builds up to 5,000 lineups (suited to 20,000 to 30,000-entry GPPs), Core up to 2,000, and a 1,000-lineup example for a 1,000-entry contest. Generation takes "30 to 60 seconds". Pool exposure versus projected ownership is "usually within a couple percentage points".
- Contest archetypes: low stakes (under $2), Marquee (examples: $51 150-max on DraftKings, $91 150-max on FanDuel), and high stakes ($100+).
- The payout shape is set by "percentage to first". Example: $100,000 to first on a $400,000 pool is 25%.
- Projection fields the tool exposes per player: minutes, fantasy points per minute, projected fantasy points, points per dollar, ownership, standard deviation and variance. A custom CSV upload takes three columns: player name, projection, ownership. A player who has already played (locked) can have his exact score entered and his variance set to zero.
- The simulation runs "tens of thousands" of times and ranks lineups by simulated ROI. One example lineup shows a 190.5% simulated ROI. Outputs are wins, top-10 finishes, min-cashes and dupes.
- Exposure shaping: leverage is exposure minus projected ownership. Example: a center with 45.6% projected ownership and 80% exposure has +34.4% leverage. A -20% ROI boost cut him from 80% to about 70%. An exposure cap of 50% sets a hard ceiling. A 7% player was raised to exactly 20% by boosting to 100% and then capping.
- What the page does not say: how a simulated score is generated. It names the inputs (minutes, per-minute rate, standard deviation, variance) but gives no distribution type, no player-to-player correlation, no pace or game-environment term and no blowout modeling.
- Evidence: the only performance figure is the single 190.5% example. The statements that the process "usually" beats hand-built lineups and tilts results "over a season" are assertions.

For the double-double bot: almost nothing transfers. Pool building, payout shape, ROI ranking, exposure and leverage are tournament-lineup tools. The one structural point is that the Sims split a player into minutes, a per-minute rate and a standard deviation, which is the same architecture as the bot's simulation (minutes first, then negative-binomial stats), but the page gives no information on how the spread is set. The late-swap idea of re-simulating with updated information has one possible test: re-run the bot's simulation at the 6:40 PM snapshot with whatever lineup and injury data exists by then, and compare its log loss and closing-price edge against the 3 PM version, restricted to players whose status was unresolved at 3 PM.

---

## 2. NBA DFS Lineup Flexibility: How To Build Lineups That Capitalize On Late Swap

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-lineup-flexibility
- Author: Josh Engleman
- Date: July 13, 2026

Claims, methods and numbers:
- Core claim: the NBA is the most injury-driven DFS sport and a late scratch "can spike" a teammate's usage, minutes or shot volume. No quantities are given for this effect.
- Locking: slates lock game by game, so rosters filled with early-window players are frozen before later injury news. The only timing example is hypothetical (a Utah Jazz game locking at 7:00 p.m. ET). The page says starting lineups "drop" and news often breaks after lock but gives no release times.
- Main example: the author says he won $20,000 on one DraftKings slate with a lineup completed after lock. Blake Wesley became the starting point guard after Tre Jones was ruled out, and was 11% owned with a projection similar to a popular value play at roughly a third of its ownership. The page says Memphis's starting lineup was not confirmed until after the slate had started. (One pass of the page described Jones as ruled out after lock and another as questionable at lock, so the timeline on the page is loose.)
- Method: build and simulate lineups, find the players the author is most exposed to in early games, apply a -50% ROI boost to them, then re-favorite the top lineups (about 150 in the example). Kelly Olynyk went from about 70% exposure to about 23%. Collin Sexton and Walker Kessler were also named. The stated principle is to cap early-game plays, not remove them.
- Counter-example: Nickeil Alexander-Walker finished 32.1% owned; the author had him in 12% of lineups. Lineups with him returned -51.4% ROI, and the post-contest Sims graded him at -27.3% simulated player ROI.
- Trigger: use the flexible approach when the injury report has many questionable tags and starting lineups are unknown. On clean slates with healthy players and set starting fives, build closer to optimal. No numeric definition of "many questionable tags" is given.
- Evidence: one slate and one author's experience. The grader (the post-contest simulator) is the vendor's own tool. No sample size.

For the double-double bot: the useful idea is a slate-level uncertainty state, which the bot can quantify where the article does not. A concrete test: at 3 PM, count questionable, probable or game-time-decision players among each candidate's team's top eight in minutes, bucket the daily top-five picks by that count, and compare hit rate, Brier score and calibration across buckets. If calibration degrades as the count rises, replace the single-scenario probability with a mixture, P(DD) = P(teammate out) x P(DD | out) + P(teammate in) x P(DD | in), with the tag-resolution probabilities taken from the bot's own injury-report history (for example, how often a questionable player plays and how often a bench player is promoted to the starting five). Also log the fraction of 3 PM picks whose status changed before tip. The ROI boost and exposure caps have no analogue for single props, and the 70%-to-23% numbers are just one slate.

---

## 3. NBA DraftKings DFS Strategy: Build Winning Lineups Fast

- URL: https://stokastic.com/articles/nba-dfs/nba-draftkings-dfs-strategy
- Author: Josh Engleman (the page attributes its framework in part to Alex Baker, founder of Awesemo.com)
- Date: July 7, 2026

Claims, methods and numbers:
- DraftKings has eight slots (PG, SG, SF, PF, C, G, F, UTIL) and most players are eligible at several, which the page says makes lineup building a different problem from FanDuel's fixed positions. Not relevant to props.
- Value benchmark: about 5 points per $1,000 of salary, plus a constant of +5 to +10 (the author uses +10). Examples (5x to 5x plus 10): $3,000 is 15 to 25 points; $4,900 is about 25 to 35; $9,600 is 48 to 58; $10,000 is 50 to 60. A $3,000 player scoring 20 is 6.7x and a $10,000 player scoring 55 is 5.5x. The constant is asserted to "work well" with no backtest.
- "Value comes from opportunity before efficiency": read minutes and usage before price.
- Injuries: a ruled-out starter frees "roughly 25 to 30 minutes" and a block of shot attempts for backups. The page says to check the live injury report, not the season depth chart, to track the specific teammate whose usage rises, and to rebuild the player pool every time the injury report changes. No usage-redistribution rate is given. This is assertion and anecdote.
- Correlation: stacking is said to matter less in the NBA because points are spread across possessions and the total is roughly fixed. The page says to mostly ignore positive correlation, never to pair a starter with his direct backup, and that game stacks are "optional at best" and not "reliably profitable". No data is cited.
- Ownership: build around about six strong values and one or two low-owned sleepers; a value at 8% ownership has more win equity than the same projection at 40%. No ownership cutoff is defined.
- Multi-entry settings: lighter randomness than other sports (more on cheap players, less on stars), a uniqueness constraint on larger slates (no number given), a cap of four players per team (five on small slates, six "questionable"), and starter/backup pairs grouped so no lineup holds both.
- Not addressed: pace, game total, blowout risk and game-script risk.

For the double-double bot: two items are worth testing and the rest does not transfer (salary, cap, ownership, positions and lineup caps are DFS construction). First, the "25 to 30 minutes freed" figure is a prior the bot can check directly: from ten seasons of box scores, compute minutes and rebound, assist and double-double rate changes for the top one and two beneficiaries when a starter is absent, and compare with 25 to 30 minutes in total and the bot's current teammate-absence features. Second, the starter-versus-direct-backup negative correlation is the only correlation claim with a stated mechanism (they share minutes, and in a blowout the starter loses minutes while the backup gains). For multi-leg combos the bot can measure it: compute residual correlation of double-double outcomes between same-team pairs (and starter-backup pairs specifically) after conditioning on model probabilities, and compare joint hit rates with the product of marginals. The claim that correlation can be ignored is unsupported here and should not be adopted without that test. The "rebuild whenever the report changes" habit points to refresh cadence for the bot's injury inputs.

---

## 4. NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy
- Author: Alex Baker
- Date: June 17, 2026

Claims, methods and numbers:
- Definitions: "Success ('boom') is reaching about 5 x (salary/1000) + 10 fantasy points; failure ('bust') is falling short of 5 x (salary/1000)." Examples from the page: a $9,000 player needs about 45 to clear value and about 55 to boom; a $4,000 player needs about 20 and about 30. For $6,800 the thresholds are 34 and 44.
- The tool reports median projection, standard deviation, ceiling ("the 75th-percentile outcome"), floor ("the 25th-percentile outcome"), Boom%, Bust% and projected ownership.
- The page says standard deviations are built "from a range of factors (role, usage, blowout and pace risk, minutes volatility, matchup) rather than one static number". No formula, weights, distribution shape or data source is given. The page does not explain how Boom% or Bust% are computed from the distribution.
- Illustration of why spread matters at equal projection: a 38-point projection can be a "steady veteran who scores 34 to 42 almost every time out" or a "high-usage gunner who drops 14 on you one night and 55 the next". The page also asserts that "in basketball, player-to-player correlation barely matters", with no source.
- Cash versus tournament use: cash favors high floor and low Bust%. Example: a $7,200 wing projected at 36 with 22% Bust% is preferred to a same-salary, same-projection wing at 38% Bust%. Tournaments favor ceiling and Boom%, accepting more Bust%, and pair Boom% with ownership to find low-owned players with similar upside. Cash lineups are built by hand from the boom/bust sheet, not with the Contest Sims.
- Worked example, two $6,800 players with a 34-point median. Player 1: floor 28, ceiling 40, Boom% 30%, Bust% 25%, ownership 24% (cash pick). Player 2: floor 18, ceiling 52, Boom% 44%, Bust% 41%, ownership 9% (tournament pick). The page presents these as hypothetical.
- Internal consistency check (my arithmetic, not the article's): the example does not follow from the page's own definitions. With a median of 34 and a bust line of 34, Bust% should be about 50% for both players, not 25% and 41%. And if Player 1's ceiling (75th percentile) is 40, no more than 25% of outcomes can reach the 44-point boom line, yet Boom% is given as 30%. The figures are illustrations and cannot be used as a calibration reference.
- Listed mistakes: using identical lineups for cash and tournaments, chasing Boom% without checking ownership, treating projections as guarantees, and running the Sims for cash.
- Evidence: none. No backtest, sample size or calibration of Boom% and Bust% against results appears anywhere on the page.

For the double-double bot: the transferable idea is that two players with the same mean can have very different threshold probabilities, and that the spread should be player-specific and built from minutes volatility, role, usage, blowout risk, pace and matchup. A double-double needs two stats at 10 or more, so the effect is larger for players whose mean in a category sits near 10: extra variance raises the chance for a player averaging 8 and lowers it for a player averaging 12. The page supplies the list of spread inputs but no weights, so the bot has to estimate them. Specific tests: (1) add minutes-volatility features (rolling standard deviation of minutes over the last 10 games, share of recent games under a chosen minutes cutoff, share of games decided by a large margin) and check log loss and calibration within groups of equal predicted probability; (2) bin players by historical minutes standard deviation and check whether the negative-binomial simulation's tail probabilities (P(points >= 10), P(rebounds >= 10), joint) are calibrated in each bin, and if not, let the dispersion parameter depend on minutes volatility and game spread; (3) compare the simulated P(DD) with the realized rate for players near the 10 line in a category. The salary-based boom and bust thresholds, cash versus tournament framing, ownership leverage and Contest Sims do not transfer, and the "correlation barely matters" claim is an unsupported assertion.

---

## 5. NBA DFS Starting Lineups: How to Leverage Them

- URL: https://stokastic.com/articles/nba-dfs/nba-dfs-starting-lineups-leverage
- Author: Josh Engleman
- Date: June 17, 2026

Claims, methods and numbers:
- Premise: lineup news drives ownership, and ownership drives tournament leverage; the winning players are said to react faster than the field.
- Mechanism example: a starting point guard is ruled out "40 minutes before tip", his backup (a "$4,000 afterthought on DraftKings") moves into starter minutes, and the page says about 30 minutes of run is redistributed.
- "Second domino": a wing or power forward who slides into the starting five and "absorbs an extra 8 to 10 minutes of run", often underowned. In the worked example a backup center priced $4,200 (center ruled out "an hour before lock") projects for "up to roughly 30 minutes" at "about 45% projected ownership", while the forward who gains 8 to 10 minutes sits at "maybe 12% ownership". The page suggests 15 to 20% exposure on the underowned beneficiary. The page states these prices and percentages are "illustrative of the mechanic, not a measured result".
- Confirmation workflow: build early from projected starters ("hours before lock"), then re-check against official starters before lock. Sources named are the Stokastic NBA DataHub and team social accounts (the page mentions checking five team accounts by hand). A "5pm" reference appears in connection with projections but its meaning is not clear from the text. No official lineup release time is given.
- Injury tags: "probable" players can sit and "questionable" players can start and play 34 minutes. No statistics on how often any tag is right.
- Four things move together when news breaks: minutes, usage, ownership and correlation. The page says to re-run the simulation instead of adjusting by hand.
- Stacking: a starter's absence can make a mini-stack of two high-usage teammates more attractive, and a returning starter can dilute one. The page says the Sims handle the math and gives no correlation values.
- Late swap: slates lock per game, so re-check players in later games before each lock; position eligibility limits swaps; in tournaments swap toward ceiling.
- Cash versus tournament: cash favors the safe, high-minutes replacement even if he is chalk ("you only have to beat about half the field"); tournaments favor lower-owned beneficiaries or pivots off chalk.
- Evidence: none. No sample sizes, backtests or measured redistribution. The claims about winning "over a season" are assertions.

For the double-double bot: this is the article closest to the bot's problem, but it supplies mechanism rather than data. The mechanism (a scratch moves minutes first to the direct backup and then to a promoted starter, and usage follows) matches the bot's minutes-first design. Tests the bot can run with its own data: (1) build a tag-reliability table from the injury-report history, covering P(plays), P(starts) and the minutes distribution given probable, questionable and doubtful at 3 PM, since the article gives none; (2) for games where a starter is out, measure the minutes, rebound, assist and double-double change for the position-matched backup and for the player promoted into the starting five, and check that the bot's minutes model reproduces the second-order gain (the article's 8 to 10 minutes is only an illustration); (3) check for leakage if the starter-role feature in training is the observed tip-off starter while at 3 PM only a projected starter is known; (4) save a 3 PM price as well as the 6:40 PM snapshot, then test whether closing-price movement and double-double hit rate are concentrated in players whose status was unresolved at 3 PM, which would measure the cost of posting before lineups are known. Ownership, leverage, cash versus tournament and stacking advice do not transfer, and the late-swap tool has no direct analogue for a single prop except the option to wait until lineups are confirmed and trade price decay against information.
