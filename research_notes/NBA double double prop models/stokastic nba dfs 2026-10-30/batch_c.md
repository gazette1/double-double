# Stokastic NBA DFS articles: read for the double-double bot

Scope: five Stokastic articles, fetched 2026-10-30. All five loaded; none was paywalled.

Method note. WebFetch returns a condensed rendering of each page, not verbatim text. Each article was fetched once for a full pass and then queried again for numbers and injury content. The quoted phrases and figures below are as the tool relayed them and could not be checked character by character against the live page. Article 4 was also re-queried with a second offset and the page ended inside the first window, so nothing was missed past the article body.

Source-quality note, applies to all five. These are vendor marketing pages for Stokastic Sims. None names a data source, sample size, backtest or error metric. All five carry the date July 15, 2026, but each footer reads "© 2025" and each sponsored card cites a ranking "as of July 16", so the date stamp is probably a page refresh date and not the writing date. The player examples in article 1 (Wiggins, Looney, Nurkic) look older than 2026; that is an inference, not something the page says.

---

## 1. How To Use NBA DFS Ownership Projections On DraftKings

URL: https://stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-ownership-projections
Author: Stokastic Staff. Date: July 15, 2026 (see note on date reliability above).

- Ownership is defined as the share of lineups in the night's largest-field contest that roster a player. Example given: Andrew Wiggins at 73.4%, read as roughly 73% of entries.
- The article states that ownership measures what the field will do, not how many fantasy points a player will score. It says the number reads the same on DraftKings and FanDuel.
- Cash games (50/50s, double-ups): payouts are flat above roughly the top half of the field, so uniqueness adds risk without reward. Advice is to funnel toward the highest-owned, best plays. Example contest is a 100-entry 50/50.
- Tournaments: advice is to keep chalk you like and pivot part of the exposure to lower-owned upside. Worked center swap: Kevon Looney at 72% versus Jusuf Nurkic at 19%. In a GPP move down to Nurkic; in cash move up to Looney. The example reads this as roughly seven in ten opponents sharing Looney and about four in five having passed on Nurkic.
- The article says the highest-owned NBA players are often among the best plays on the board, and advises against reflexively fading chalk.
- Ownership projections are described as updating through the day as injury and rest news arrives, and as feeding the Sims. No method, input list, lag or accuracy figure is given.
- The page contains a FAQ that restates the above. Most remaining text is product promotion (code NBASIMS10, a sponsored picks card).

For the double-double bot: Almost nothing transfers. Ownership is a statement about other entrants' lineups, and a prop price has no equivalent; the bot grades against a closing price that already embeds the market's view of the player. The only loose parallel is that a public number moves as injury news arrives, which the bot already handles through its 3 PM post and 6:40 PM snapshot. No test is suggested from this article.

---

## 2. NBA DFS Contrarian Strategy: Fade Chalk, Beat the Field

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-contrarian-strategy
Author: Alex Baker. Date: July 15, 2026 (see note on date reliability above).

- Tournament payouts are top-heavy. The article's illustration: in a 100,000-entry field, finishing 5th can pay for a month while finishing 5,000th barely matters. A player at 35% ownership means over a third of the field shares that exposure.
- The key metric is exposure minus ownership. Example: 20% exposure against 8% field ownership is leverage.
- Illustrative table, labelled illustrative by the article: Chalk Wing A at $6,800, projection 34.1, field ownership 30%, exposure 8%; Similar Wing B at $6,700, projection 33.4, field ownership 9%, exposure 26%.
- Rule of thumb: if two players project within 1 to 2 points and the ownership gap is about 20 percentage points, the lower-owned player needs only a comparable ceiling and "a clean minutes path". The article warns that some gaps are justified by role, position eligibility or late news and should be left alone.
- Four-step pre-lock process: (1) read ownership projections and mark players above 25% ownership; (2) find mispriced pairs; (3) check ceiling and not only floor with Boom/Bust; (4) run contest sims ("tens of thousands" of simulations) to estimate win equity and move exposure.
- Late news: when a star is ruled out about 15 minutes before lock, the article says the field crowds onto the obvious replacement. It suggests targeting the secondary beneficiary, such as a ball-handler absorbing playmaking or a wing moving into the starting five, who gets the vacated usage at much lower ownership. No usage or minutes numbers are given.
- Contrarian building is for GPPs only. Cash games call for the highest-floor lineup.
- None of these claims has data behind it. The 25% and 20-point thresholds are presented as rules of thumb with no test.

For the double-double bot: Ownership, salary and payout content does not transfer. Two ideas do. First, "a clean minutes path" as the condition that makes a low-priced player live matches the bot's minutes model; the useful reading is that ceiling and minutes security are separate questions. Second, the late-news claim says the obvious replacement is crowded while the secondary beneficiary is under-owned. For props the analogue is price: after a late absence, the book may reprice the obvious replacement quickly and the secondary beneficiary slowly. Test: take games with a rotation player or starter newly out between the 3 PM post and the 6:40 PM snapshot, split affected teammates into the obvious replacement (the player who takes the absent player's starting slot) and secondary beneficiaries, and compare model probability against the 6:40 PM price and against the close for each group. Also check whether the bot's absence features carry the absent player's role (starter versus bench, position) or only a count of missing minutes.

---

## 3. NBA DFS Late Swap: How To Win With Late Swap Tools

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-late-swap
Author: Stokastic Staff. Date: July 15, 2026 (see note on date reliability above).

- Thesis: after lock, news (injuries, role changes, final scores) makes submitted lineups stale; the Stokastic tool re-simulates submitted lineups and ranks swaps by projected ROI. The article says doing this by hand across roughly 20 lineups against a live field is impractical.
- Staggered tip times mean much of a lineup's outcome is settled before the slate ends. The article's line: "By the time your last game tips, large chunks of your lineups' fates are already decided." Once a game ends the scores "aren't projections anymore."
- Tool settings: live contest pool (current ownership for locked players), percentage payout to first (first prize divided by prize pool, pick the nearest option), pool size set close to actual entries, swappable lineup profile of Chalky, Balanced (default) or Contrarian.
- Worked example: a $750,000 prize pool with $200,000 to first is about 26%, so the 25% option is chosen; pool size set to 50,000.
- Variance: each player has a "standard variance of 1". For players whose games are over, set variance to 0 and set the projection to the final score. Example: Shai Gilgeous-Alexander at a final 58 fantasy points. The author calls this the cheapest accuracy gain mid-slate.
- Controls: ROI Boost (example: a player at 65% exposure given a -20% boost drops to 40%) and Exposure Caps (example: a 45% player capped at 35%). In the video example 20 lineups were uploaded and 12 were swapped.
- Injury news and minutes or usage: the page gives nothing quantitative. It says only that a player can be ruled out, "a starter's role" can shift, and "a rotation change or a surprise rest decision can crater a player you're stuck with." The words minutes and usage do not appear in the article text as the tool reported it. It does not say how the tool models injury-driven changes. A video walkthrough is referenced but not transcribed.

For the double-double bot: This article does not transfer. It is about editing submitted lineups against a contest field. The one transferable idea is conditioning: once a game is final its legs are known, so a multi-leg combo that spans games with staggered tips should be priced conditionally on the legs already settled. That matters only if the bot ever prices or tracks combos live, which the description does not say. No test is suggested. For late injury news the article offers no mechanism at all, so nothing here should be used to set minutes or usage redistribution.

---

## 4. NBA DFS Stacking: The Correlation Edge That Wins GPPs

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-stacking-strategy
Author: Stokastic Staff. Date: July 15, 2026 (see note on date reliability above). Body is roughly 2,500 words (tool estimate).

- The article states no correlation coefficient, for teammates or opponents. The tool was asked directly and reported none. All correlation claims are qualitative.
- Positive teammate link: assist-to-basket. "The passer books an assist and the finisher books the points on the exact same possession"; "a guard's assist total and the wing's made threes climb together." No figure.
- Negative teammate link: same-team usage is "close to zero-sum"; "There is one ball, and every shot a teammate takes is a shot the star did not." Two high-usage scorers can "pit their ceilings against each other", so pairing them can cancel ceilings. The article does not discuss rebounds between teammates.
- Opponent link: add a run-back from the opposing team because the opponent "has to keep scoring to stay in the game." This is stated as positive correlation in a tight, fast game. No figure.
- Correlation changes the shape of outcomes and not the mean: more duds and more monster nights, which widens the right tail. The article says this helps in top-heavy GPPs and hurts in cash games.
- Game environment thresholds: "high 90s to around 100 possessions" per team is roughly league average; "low 90s" is a grind to avoid; both teams near "105 or more" is the "track meet." A "double-digit spread" is named as blowout risk because large spreads can empty benches in the fourth quarter. The article prefers a tight game with a high total over a lopsided one. Data fields it names include pace, possessions, game total, projected spread, implied team totals and usage.
- Injury and minutes: a ruled-out starter's possessions and minutes are redistributed, and a backup "priced for last week's ten minutes" can end up "playing 30". Injury news is described as arriving "about an hour before lock", and the article tells readers to check the injury report and not the depth chart. These are illustrations, not measured redistribution rates.
- Stack types in its comparison table: game stack plus run-back (fast pace, high total, tight spread; risk is a blowout), mini-stack (any pace; risk is pairing ball-dominant scorers), injury-value stack (a confirmed inactive starter's usage spike; risk is that the news gets over-owned). Its guardrails: respect blowout risk, do not stack two high-usage teammates, do not overcommit to one game.
- The Sims are said to run "tens of thousands" of simulations and rank lineups by simulated ROI. The article gives no methodology, so this is a vendor claim.

For the double-double bot: The direction of each effect is useful; the size of each is not given, so every item below is a hypothesis to measure on the bot's own ten seasons, not a number to import. (a) Shared game factors: pace, game total and blowout risk move every player in a game in the same direction, which implies positive correlation between double-double outcomes for different players in the same game, including opponents. A combo priced as a product of independent single-leg probabilities would understate joint probability for same-game legs. (b) Zero-sum usage suggests negative correlation inside a team for scoring-heavy legs, and the same logic plausibly applies to a team's pool of rebounds, though the article does not say so. (c) Blowout: double-digit spread is the article's only game-script threshold. The 155-feature description does not list closing spread, total or implied team totals; if they are absent, adding them is the first test. Specific tests: 1. Compute the empirical phi correlation of double-double indicators across ten seasons for same-team pairs, opposing-team pairs and unrelated games, split by pace tercile and by absolute spread bucket (under 5, 5 to 9.5, 10 and over). 2. Compare those with the correlation implied by the simulation, which draws minutes first and then negative-binomial stats; check whether the simulation shares a game-level pace or script factor across players, and if not, add one and measure joint-probability calibration on two-leg pairs by Brier score and a reliability plot. 3. Measure starter minutes shortfall versus the minutes model by spread bucket, to see whether the model already captures the fourth-quarter bench effect. 4. Check pair types separately: big plus big on the same team, big plus guard on the same team, big versus big on opposing teams.

---

## 5. NBA DFS Without Late Swap: How To Win Before The Slate Locks

URL: https://stokastic.com/articles/nba-dfs/nba-dfs-without-late-swap
Author: Stokastic Staff. Date: July 15, 2026 (see note on date reliability above).

- Premise: some DraftKings tournaments disable late swap, so the reader must "pre-load" upside by boosting players who benefit if a questionable star sits. There is no FAQ on this page.
- Which risk matters: ignore stars questionable in games that lock at slate start, since their status resolves before lineups freeze. The real exposure is a questionable star in a game that tips after the slate locks, where a game-time decision resolves after lineups are frozen. Example slate: seven games, two locking at 7:00 p.m. ET.
- The contest sims "play" the slate 40,000 times, play by play, and rank lineups by simulated ROI. Set the field first: default ownership is calibrated to Marquee tournaments (about $15 buy-ins); a $450 Max is less chalky than a $150 Max. A player projected near 66% owned in a $15 Marquee contest settles lower in the less-sharp field. Percent to first is first prize over total pool, for example $100,000 of $400,000, or 25%.
- Trimming risk: a questionable wing in about 22% of lineups falls to about 14% with a -35% ROI boost; an exposure cap of 0% removes him. The article says there is no cap on how hard a boost can be.
- On/off data, the only quantified usage effect in the set: a high-usage backcourt partner has 1.30 fantasy points per minute "in all situations" and 1.51 when the star is off the floor, "because the star's shots have to go somewhere." Before boosting he is in about 0.67% of lineups; a 50% ROI boost takes him to about 4% and a 120% boost to roughly 19% of top lineups. By simple arithmetic 1.51 over 1.30 is about +16% per minute. The page gives no sample size, season or player name, and fantasy points per minute blends points, rebounds, assists, steals and blocks, so it is not a double-double rate.
- Two kinds of beneficiary: the team's other high-usage star, who rises to a team-best 1.35 fantasy points per minute if the star sits and is still viable (about 20% of lineups) if the star plays; and a deep-bench fill-in, who is useful only if the star sits and gives dead lineups otherwise. The article recommends the first kind. No baseline is given for 1.35, so the lift cannot be computed.
- Salary cap is $50,000; a boosted point guard that breaks the cap is offset by swapping a pricey wing for a value piece projected in the mid-30s. A $62,500 DraftKings GPP win is cited as built with this process, with no detail.
- Late-swap slates: keep roster room in early windows and pre-boost backups for questionable lead guards. Minutes redistribution is not described anywhere; no minutes figures are given.

For the double-double bot: Lineup, contest and ROI-boost content does not transfer. Three points do. First, the article separates a star's status resolving before the decision point from resolving after it, which is the bot's situation at the 3 PM post: a questionable teammate is unresolved then and usually resolved by the 6:40 PM snapshot. Test: for games where a teammate carried a questionable tag at 3 PM, compare the current point estimate against a status-weighted mixture, P(out) times the probability with him out plus P(in) times the probability with him in, scored by log loss and Brier score against outcomes and against the 6:40 PM price. Second, the on/off figures (1.30 to 1.51 per minute) show the redistribution is partly a per-minute rate change and not only a minutes change; the bot can test whether its teammate-absence features capture the rate change separately from the minutes change by splitting the effect into minutes lift (from the minutes model) and per-minute rebound and assist rate lift. Player-specific on/off deltas with shrinkage toward a role-based prior could replace or supplement aggregate absence flags. Third, the star-versus-bench-fill-in split suggests the lift differs by the absent player's role and by the beneficiary's own usage tier, so interactions between absent-player usage share and beneficiary usage rank are worth a feature test. None of this is supported by a sample in the article, so the effect sizes must come from the bot's data.

---

## Cross-article summary

- Most useful: article 4 (direction of same-game and teammate correlation, pace and spread thresholds) and article 5 (per-minute on/off rate change, status-resolution timing). Both are qualitative or thinly quantified.
- Least useful: articles 1 to 3 (ownership, contrarian leverage, late-swap tooling), which are about contest-field behavior.
- No article gives a correlation coefficient, a minutes redistribution rate, a sample size or an out-of-sample accuracy figure.
- Thresholds stated that are concrete: pace of high 90s to 100 (average), low 90s (slow), 105 or more (fast); double-digit spread as blowout risk; 25% ownership as the chalk marker (not relevant to props); 1.30, 1.51 and 1.35 fantasy points per minute in the on/off example.
