# NBA double-double prediction models: inventory, reported results, and what the better approaches share

Tags: [PR] peer-reviewed. [PP] preprint, thesis, or student report. [SR] self-reported by the author or vendor, not independently verified. [BT] backtest. [LIVE] forward or live record. [EXC] detail taken from a search-result excerpt because the page could not be fetched or was not opened; treat as lower confidence. Numbers marked "computed" are my arithmetic, not the source's. Research date 2026-10-29.

## 1. Which public models or papers predict double-doubles (or jointly predict points, rebounds, assists), and what did they report out of sample?

### Takeaway
I found no peer-reviewed paper that predicts NBA double-doubles (DD). Public DD-specific work is thin: a single-player logistic regression tutorial, a triple-double student capstone, a vendor flag with a 16-bet self-reported record, and one open-source backtest in which DD bets lost 26% on a blind season. The more rigorous public prop models target single stats; those with honest holdouts report roughly break-even results, and in the one that measured it, the de-vigged market was more accurate than the model alone.

### Cited Findings

A. Double-double specific
- Towards Data Science, "How to predict NBA double-doubles": direct binary classifier, logistic regression in R for one player (Nikola Vucevic); DD defined as 10+ in two of points, rebounds, assists, steals, blocks; the author removes those five stats from the predictors to avoid leakage. No accuracy figures retrievable (page returned HTTP 403 to fetch) [EXC] ([TDS](https://towardsdatascience.com/how-to-predict-nba-double-doubles-f4c30be08ca0/))
- Russell Westbrook triple-double capstone: playing time and plus/minus described as "effective" predictors, game result and opponent conference useful, playing side not; data were Westbrook's last 3 OKC seasons; no accuracy metrics reported; authors say the sample is not random and model selection was unfinished [PP] ([bookdown capstone](https://bookdown.org/theqdata/data_science_capstone_project_report/conclusion-and-future-work.html))
- Dimers (Player Projections Hub, formerly NBA Cheat Sheet): players "projected close to a double double" are tagged "Double Double Threat"; the cheat sheets were discontinued in March 2025; a Dimers tweet of Feb 1, 2025 claimed its "double-double predictor" went "12-4 for a return of +5.55u based upon a 1u flat bet on each" [SR] ([Dimers, Feb 2025](https://www.dimers.com/nba/news/2025-nba-betting-how-to-capitalize-on-the-leagues-historical-triple-double-numbers))
- Dimers says its projections are averages of simulations and that it does not publish a direct DD probability; one excerpt says the old cheat sheet flagged players within 2 points, rebounds, or assists of a DD, but the fetched Dimers article gives no numeric cutoff [EXC] ([Dimers projections hub article](https://www.dimers.com/nba/news/nba-prop-bets-three-plus-money-plays-identified-by-dimers-projections-hub-on-wednesday-november-12))
- KyShiesty919/NBA-Props tested DD bets in a second-round angle backtest: "Double-doubles | - | -26% | Same." where the row above reads "Alt points ladders | - | -40% | Longshot bias. Not offered." Blind season 2025-26, no sample size given [BT][SR] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md))
- FantasyLabs says its projections come from NBA simulations and uses them for double-double lines in its Underdog picks; no accuracy reported [EXC] ([FantasyLabs](https://www.fantasylabs.com/?p=214229))

B. Open-source prop models with documented backtests (single stats; they produce the inputs a DD model needs)
- KyShiesty919/NBA-Props method: minutes = exponentially weighted mean of last 10 games with a 3% haircut on back-to-backs; this season's per-minute rate shrunk toward last season's with weight games/(games+15); players listed Out removed and their production redistributed; opponent adjustment half team-level and half position-level at half strength; half-strength pace adjustment; +1.5% home; negative binomial for counts, normal for PRA, each player's own game-to-game variance; multiplicative de-vig per book, median fair probability across at least 2 books; final = w x market + (1 - w) x model, w from 0.70 (no games this season) decaying to 0.35 by about 15 games [BT][SR] ([KyShiesty repo](https://github.com/KyShiesty919/NBA-Props))
- KyShiesty results, fit 2023-25 vs blind 2025-26: original settings -2.1% (z -2.0) vs -1.8%; current config (no usage-model bets, 10+ games) +5.6% (930 bets) vs +1.9% (247 bets, z 0.3); unders in 10+ point spread games +14.9% (199) vs +20.9% (190, z 2.9), note "Starters sit in blowouts"; unders only +8.8% (494) vs +8.3% (150); back-to-back unders +5.4% vs -3.4% ("Didn't hold"); a gradient-boosted overs model +18% in-sample vs -6% blind; first 5 games of the season ran -28%; author: "Nothing tested is profitable with statistical confidence" [BT][SR] ([KyShiesty repo](https://github.com/KyShiesty919/NBA-Props))
- KyShiesty calibration: "The original settings were overconfident by 5-11 points in every probability bucket. Actual hit rates landed ~1 point above the market's fair price: a real edge, smaller than the vig." Brier scores: raw model 0.248, market 0.244, blend 0.241 [BT][SR] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md))
- seantanger/nba-props-research: LightGBM predicts mean and dispersion of points, rebounds, assists, threes, PRA from prior games only, with injury features from NBA official injury reports; historical prices from BettingPros; a rule anchored on FanDuel's line that bets DraftKings, BetMGM, or BetRivers when they disagree by at least 3 percentage points returned +6.1% ROI on 6,424 bets (2020-21 to 2024-25) but -1.8% on a 35-bet pre-registered holdout; model variants with edge >= 0.08 were break-even on development data; status "no proven edge"; forward ledger started 2026-10-25 [BT][SR] ([seantanger repo](https://github.com/seantanger/nba-props-research))
- hacksumn/NBA-Prop-Maker: five layers (play-by-play base, Ridge points-per-possession engine separating talent from opponent, usage and injury, luck regression of opponent FT% and 3P%, blowout discount that drops garbage time at 25+ point Q3 leads, 15+ in Q4, 10+ in the final 3 minutes); GradientBoosting, RandomForest, Ridge, XGBoost with isotonic calibration; 77,890 player-game rows, 800 players, 3 seasons; graded against PrizePicks lines; live pick record 54.1% (693-588) while the headline claims "54.4% win rate and +3.88% ROI"; regression MAE PTS 4.08, TRB 1.75, AST 1.31; README lists the lack of a real-time injury feed as its top gap [LIVE][SR] ([hacksumn repo](https://github.com/hacksumn/NBA-Prop-Maker))
- Zhang Haipeng minutes model: LightGBM on 151,493 player-games (2012-2018) predicts next-game minutes with test MSE 38.24 and R^2 0.65 vs a 5-game average at MSE 50.24 and R^2 0.55 [SR] ([Zhang](https://zhang-haipeng.github.io/2020/02/10/project-NBA-minutes.html))
- Sciberras (2023), University of Malta B.Sc.: RNN, LSTM, transformer trained on each player's prior games for player props; the transformer was most accurate of the three but did not match the accuracy of bookmakers' models and was not profitable overall [PP] ([OAR@UM](https://www.um.edu.mt/library/oar/handle/123456789/115275))

C. Vendors and tools (methods and claims)
- Action Network / FantasyLabs props tool: compares its projections to props at several books and grades each bet 1-10 "Bet Quality"; claims Bet Quality 10 won 60.31% and 9 won 58.82% "last season," unders at 10 went 341-172 (66.47%); no sample size, prices, or dates for the overall figures; page timestamp Sep 23, 2021 [SR] ([Action Network](https://www.actionnetwork.com/nba/tuesday-nba-player-props-betting-picks-january-28-trae-young))
- BettingPros: star rating "determined by our projections, expected value and advanced modeling," built on a consensus of projection sources; hit rates shown over short windows (last 5, last 15); one Nov 2023 article lists a sleeper-pick season record of 32-16 that included DD props; no aggregate NBA record or audit found [SR][EXC] ([BettingPros](https://www.bettingpros.com/articles/nba-sleeper-picks-player-predictions-11-16/))
- SaberSim: lineups come from thousands of play-by-play simulations, each producing a full game script with correlations [EXC] ([SaberSim support](https://support.sabersim.com/en/articles/12079141-building-lineups))
- Stokastic publishes boom/bust probabilities from its projections and a props "Bet Pro" model; methodology not disclosed [EXC] ([Stokastic boom-bust](https://www.stokastic.com/nba/boom-bust-probability/))
- Props.cash: shows how often a player cleared a line over a user-chosen window and added a section with "5 pieces of correlation" per prop; no method published [EXC] ([Props.cash newsletter](https://propsdotcash.beehiiv.com/p/a-new-props-cash-feature))
- Outlier: research tool to compare lines, flag EV, and show trends; an automated review summary (49 reviews) cites complaints of incorrect hit rates [EXC] ([magica summary](https://magica.com/youtube-summarizer/this-is-why-your-nba-player-props-keep-losing-and-how-to-research-them-using-outlier-EryMnSQ6gFE)); ([marlvel](https://marlvel.ai/apps/st-colorcast-betslurp))
- OddsJam: pulls real-time odds from dozens of books, computes no-vig fair value, flags positive-EV lines; a market-consensus method, not a stat model [EXC] ([RotoWire OddsJam review](https://www.rotowire.com/betting/oddsjam-review))
- Unabated: odds screens, a premium "Unabated Line," and a conditional projections tool based on day-to-day starting lineups and benches [EXC] ([SBC Americas, Oct 2024](https://sbcamericas.com/2024/10/21/nba-season-unabated-sports-platform/))
- PropsBot (vendor): "NBA High ROI 25.9% ROI, 47.1% win rate, 81,410 picks (as of Sep 29, 2026)" [SR][EXC] ([PropsBot](https://propsbot.ai/best-ai-sports-betting-app/))
- Sportsbook pricing supplier Huddle: a simulation recalculates prices, then operator hold and limits are applied, with prices typically generated at least 24 hours before the event [EXC] ([Huddle PDF](https://huddle.tech/wp-content/uploads/2024/03/NBA-Player-Proposition-Micro-Markets-From-Creation-to-Resulting.pdf))
- Covers runs an NBA player props page; no methodology found ([Covers](https://www.covers.com/sport/basketball/nba/player-props))

D. Academic and foundational work relevant to the joint problem
- Hubacek, Sourek, Zelezny (2019), International Journal of Forecasting 35(2): CNN over player-level statistics for NBA game outcomes, trained with a loss that penalizes correlation with bookmaker-implied probabilities, plus portfolio-theory bet sizing; positive cumulative profit on NBA 2007-2014, no figure in the abstract [PR] ([EconPapers](https://econpapers.repec.org/RePEc:eee:intfor:v:35:y:2019:i:2:p:783-796))
- Hubacek and Sir (2023), IJF: adding a decorrelation term to MSE generally increased profits, with a tuning sweet spot [PR][EXC] ([arXiv 2010.12508](https://arxiv.org/abs/2010.12508v1))
- Walsh and Joshi (2023, rev. 2024): on NBA game betting, selecting models by calibration returned +34.69% ROI on average vs -35.17% for accuracy-based selection; best case +36.93% vs +5.56% [PP] ([arXiv 2303.06021](https://arxiv.org/abs/2303.06021))
- Dare, Dennis, Paul (2015), Finance Research Letters 13: lines move away from teams with absences; opening lines contain "significant errors in games when a player is absent"; no profitable strategy at the closing line [PR] ([IDEAS](https://ideas.repec.org/a/eee/finlet/v13y2015icp130-136.html))
- Kaunitz, Zhong, Kreiner (2017): betting where a book's odds diverge from the market consensus was profitable in three settings for football, and bookmakers applied discriminatory practices to successful clients [PP] ([arXiv 1710.02824](https://arxiv.org/abs/1710.02824))
- Franks, D'Amour, Cervone, Bornn (2016), "Meta-Analytics": rebounds, blocks, assists are highly discriminative and stable; 3P% least stable ("over 50% of the variation ... is due to chance"); per-minute metrics more stable than totals because injuries reduce minutes; dependence modeled with a Gaussian copula X = F^-1(Phi(Z)) fit by rank likelihood (sbgcop) [PP] ([ar5iv 1609.09830](https://ar5iv.labs.arxiv.org/html/1609.09830))

### Inferences
- The public record contains no DD model with a disclosed, independently verified out-of-sample hit rate, calibration curve, or ROI. Everything DD-specific is either a tutorial, a 16-bet vendor claim, or one negative backtest.
- Dimers' 12-4 for +5.55u implies an average winning return of about 0.80u, roughly -126 average odds (computed), so those picks were near even money, not the -400 to -700 favorites the bot targets.
- KyShiesty's DD row is noted "Same." under the alt-ladder "Longshot bias" row, which reads as the author attributing the -26% to longshot pricing; that suggests the bets were plus-money DD legs (my reading, not stated).
- The two honest GitHub projects (KyShiesty, seantanger) both found apparent development edges that shrank or vanished on held-out data; this pattern is the main warning for any DD backtest.

### Gaps
- No peer-reviewed or SSAC paper on DD prediction found. I did not reach Google Scholar or SSRN directly; MIT Sloan and JQAS searches returned nothing DD-specific.
- No Kaggle notebook targeting DDs found; no GitHub repo built around DDs found.
- No methodology found for Hashtag Basketball, PropsHQ, Juice Reel, Covers, RotoWire props tools, or Dunks and Threes; FantasyLabs and Unabated support pages blocked fetches.
- The TDS DD article's metrics could not be retrieved (403).

## 2. Do the better approaches classify the double-double directly or simulate the stat lines and read off the probability?

### Takeaway
No public head-to-head comparison on DDs exists. Vendors and sportsbook suppliers simulate (Dimers, SaberSim, FantasyLabs, Huddle), and the documented open-source prop models build count distributions on top of a minutes projection; the only direct DD classifiers found are single-player or single-season exercises with no out-of-sample metrics. The betting evidence points to calibration and independence from the market price mattering more than the classifier-versus-simulation choice.

### Cited Findings
- Direct classification examples are limited to one-player logistic regression (Vucevic) [EXC] ([TDS](https://towardsdatascience.com/how-to-predict-nba-double-doubles-f4c30be08ca0/)) and a Westbrook capstone using same-game playing time and plus/minus as predictors ([bookdown](https://bookdown.org/theqdata/data_science_capstone_project_report/conclusion-and-future-work.html))
- Simulation users: Dimers ("projections are averages of all simulations") [EXC] ([Dimers](https://www.dimers.com/nba/news/nba-prop-bets-three-plus-money-plays-identified-by-dimers-projections-hub-on-wednesday-november-12)); SaberSim play-by-play sims [EXC] ([SaberSim](https://support.sabersim.com/en/articles/12079141-building-lineups)); FantasyLabs NBA simulations [EXC] ([FantasyLabs](https://www.fantasylabs.com/?p=214229)); sportsbook supplier simulation pricing [EXC] ([Huddle](https://huddle.tech/wp-content/uploads/2024/03/NBA-Player-Proposition-Micro-Markets-From-Creation-to-Resulting.pdf))
- DARKO's structure is rate times minutes: box-score stats are projected "per 100 possessions and as shooting percentages," and per-game numbers multiply those rates by projected minutes and pace ([DARKO about](https://www.darko.app/about))
- Distributional prop models: KyShiesty uses negative binomial marginals per stat and a normal for PRA ([KyShiesty](https://github.com/KyShiesty919/NBA-Props)); seantanger's LightGBM outputs mean and dispersion ([seantanger](https://github.com/seantanger/nba-props-research))
- Calibration evidence: calibration-based model selection +34.69% vs -35.17% ROI for accuracy-based on NBA game bets [PP] ([Walsh and Joshi](https://arxiv.org/abs/2303.06021)); an uncalibrated prop model was overconfident by 5 to 11 points per bucket and the market had a lower Brier score than the model (0.244 vs 0.248), with the blend lowest (0.241) [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); hacksumn applies isotonic calibration ([hacksumn](https://github.com/hacksumn/NBA-Prop-Maker))
- Decorrelation from the bookmaker improved profit in NBA game models [PR] ([Hubacek et al. 2019](https://econpapers.repec.org/RePEc:eee:intfor:v:35:y:2019:i:2:p:783-796))

### Inferences
- The Westbrook capstone's predictors (same-game minutes and plus/minus) are not known before tip, so it explains triple-doubles after the fact; it is not a pregame forecaster.
- Simulation from minutes produces P(DD) for every player from one set of components and carries the shared-minutes dependence automatically; a direct classifier needs many DD events per player and, for elite players at 80% to 87% DD rates, mostly relearns the season rate unless it is given minutes-risk features (spread, rest, foul-proneness, teammate absences).
- A defensible design for the bot is hybrid: simulate minutes then stats to get a raw P(DD), recalibrate with isotonic regression on past predictions in the 0.6 to 0.95 band, then compare with the de-vigged market; a direct classifier can serve as a stacking check. This is my recommendation, not a tested result from any source.
- The -26% DD result in a model that used independent per-stat marginals is consistent with, but does not prove, that independent marginals misprice DDs; the author's own note points to longshot pricing.

### Gaps
- No study compares log loss or Brier of a direct DD classifier vs a simulated joint model on the same games.
- Dimers, SaberSim, FantasyLabs, and sportsbook suppliers do not disclose simulation counts, distributions, or DD calibration.

## 3. How important is the minutes projection relative to per-minute rates, and what do projection systems say about minutes, injuries, blowouts, and back-to-backs?

### Takeaway
Every documented system treats minutes as a separate and harder forecast than per-minute rates. DARKO reports beating two DFS projection sites on every stat except minutes, and a public LightGBM minutes model explained 65% of next-game minutes variance vs 55% for a 5-game average. Injuries, blowouts, foul trouble, and rest are handled mainly as minutes adjustments that update through the day.

### Cited Findings
- DARKO calls minutes "the hardest thing any projection system forecasts"; minutes are projected "from his recent playing time and role"; rates use exponential decay beta^t (t in days) with beta tuned per stat by differential evolution, a modified Kalman filter, and a gradient boosted tree combining the two; adjustments for rest, travel, home court, opponent, aging, seasonality; a player ruled out still shows a healthy-minutes projection; "With one exception, DARKO beat both sites in every stat tested," the exception being minutes [SR] ([DARKO about](https://www.darko.app/about))
- A fan write-up says DARKO beat two paid DFS sites in every stat over three years of data [EXC] ([Liberty Ballers](https://www.libertyballers.com/2019/12/8/20997234/the-sixers-past-present-and-future)); DARKO used Basketball Monster preseason minutes in a 2021-22 team-win contest [EXC] ([APBR forum](https://apbr.org/metrics/viewtopic.php?p=38511))
- LightGBM minutes: MSE 38.24, R^2 0.65 vs 5-game average MSE 50.24, R^2 0.55 [SR] ([Zhang](https://zhang-haipeng.github.io/2020/02/10/project-NBA-minutes.html))
- KyShiesty: an EWMA of the last 10 games had the lowest error of the rules tested (MAE 4.6 minutes); a per-team-game average was biased 4 minutes low; rotations anchored to 240 team minutes, absent players' minutes redistributed with a position preference, capped at 36 per player, only 40% to the tracked rotation [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md))
- Basketball-Reference's Simple Projection System projects per-36 rates only, weighting the last three seasons 6/3/1 and adding 1000 minutes of league-average production ([BBRef SPS](https://www.basketball-reference.com/about/projections.html)); a Basketball-Reference blog post says playing time is too hard to forecast and leaves it to the user [EXC] ([BBRef blog](https://aws.basketball-reference.com/blog/index4ee6.html?p=3383))
- FiveThirtyEight's 2022-23 forecast blended a rolling average of recent minutes adjusted for availability (60%) with a depth-chart projection (40%) for games in the next two weeks [EXC; original page now redirects] ([FiveThirtyEight](https://fivethirtyeight.com/features/how-were-improving-our-nba-forecast-for-2022-23))
- RotoWire (Mark Strotman, Dec 10, 2025): minutes inputs are matchups, rest schedules, back-to-backs, travel, historical lineup patterns, usage history, teammate injuries, opponent strength and "potential blowout scenarios"; projections update "constantly throughout each day"; no accuracy figures ([RotoWire](https://www.rotowire.com/basketball/article/nba-projected-minutes-explained-fantasy-basketball-97473))
- Stokastic (July 19, 2026): season averages "flatten out the games at the extremes," e.g., Mitchell Robinson ranging 14 to 28 minutes from foul trouble; usage and rebound rates adjusted with on/off data, "not a perfectly scientific process"; James Harden's usage near 50% with Russell Westbrook off the floor ([Stokastic](https://www.stokastic.com/articles/nba-dfs/nba-dfs-research))
- An ETR job posting frames the core problem as how projected playing time shifts with injuries, Q-tags, and minutes restrictions [EXC] ([ETR job posting](https://establishtherun.com/etr-job-posting-nba-data-scientist/)); RotoGrinders treats injuries, role changes, and blowouts as the main drivers of rotation change [EXC] ([RotoGrinders](https://rotogrinders.com/fantasy/lessons/accurately-predicting-minutes-nba-dfs))
- Blowouts: unders in games with 10+ point spreads returned +20.9% blind (190 bets, z 2.9), note "Starters sit in blowouts" [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); hacksumn removes garbage time by score-margin thresholds ([hacksumn](https://github.com/hacksumn/NBA-Prop-Maker))
- Back-to-backs: KyShiesty applies a 3% minutes haircut; back-to-back unders did not hold blind (-3.4%) [BT] ([KyShiesty](https://github.com/KyShiesty919/NBA-Props)); team-level studies find win chances rise with one rest day vs back-to-backs (Esteves et al. 2020; Yang et al. 2021, 1,230 games of 2016-17) [EXC] ([Crossref EJSS](https://api.crossref.org/works/10.1080/17461391.2020.1736179)); ([Frontiers 2021](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.630769/pdf)); a 2026 preprint reports a 44% back-to-back win rate vs 50% expected and notes teams rest stars on the second night [EXC] ([arXiv 2606.27957](https://arxiv.org/pdf/2606.27957))
- Minutes and fantasy output: one analyst reported r = 0.84 for one player; another found r = .672 between minutes and player-rater score per game [EXC] ([NBC Sports](https://www.nbcsports.com/fantasy/basketball/news/article-numbers-game-advanced-stats-correlations)); ([davidgonos](https://davidgonos.com/highest-correlation-player-rater-score/amp))
- Per-minute metrics are more stable season to season than totals because injuries reduce minutes [PP] ([Franks et al.](https://ar5iv.labs.arxiv.org/html/1609.09830))

### Inferences
- The LightGBM minutes model's error is about 6.2 minutes RMSE vs 7.1 for the 5-game average (computed from the MSEs). For a big who gets 12 rebounds in 34 minutes (about 0.35 per minute, illustrative), a 6-minute shortfall costs about 2 rebounds, which is the gap between a DD and a miss for many candidates.
- For DD favorites, misses come from the left tail of minutes (blowout, foul trouble, in-game injury) more than from the mean, so the bot should simulate a minutes distribution with blowout risk tied to the spread, not a point estimate.
- Rates are the stable part (Franks et al.); minutes carry the news. A bot without a fast injury and lineup feed will lose most of the value a minutes model can add.

### Gaps
- No public methodology found for Hashtag Basketball, Basketball Monster (beyond producing full-season and daily projections since 2002 [EXC] ([Basketball Monster](https://basketballmonster.com/Projections.aspx))), Dunks and Threes, or FantasyPros minutes.
- No published variance decomposition of player stat lines into minutes vs per-minute rate.
- No player-level study quantifying back-to-back effects on minutes or rebounds; available studies are team-level.

## 4. How correlated are points, rebounds, and assists within a game, and how do models handle the correlation when computing P(two categories >= 10)?

### Takeaway
I found no published within-player correlation coefficients for points, rebounds, and assists. Sources agree qualitatively that the three co-move through minutes, and SaberSim says cross-player correlations in the NBA are weak. Methods exist (Gaussian copula with count marginals; simulation conditional on minutes), but no public DD tool discloses which it uses, and the one open-source model that tested DDs used independent per-stat marginals.

### Cited Findings
- SaberSim: "not a whole lot of strong correlations between players"; starters on the same team tend to be positively correlated; point guards tied to teammates through assists; simulation is useful because NBA correlations are "not always completely intuitive" [EXC] ([SaberSim guide](https://www.sabersim.com/dfs/strategy/ultimate-nba-guide/))
- Props.cash shows correlations between props on player pages; no numbers or method published [EXC] ([Props.cash](https://propsdotcash.beehiiv.com/p/a-new-props-cash-feature))
- A betting guide calls points and rebounds "moderately correlated" for bigs and rebounding wings, more so in high-usage games; no coefficients [EXC] ([oddsindex](https://oddsindex.com/guides/nba-same-game-parlay-tips))
- A projections thread says more minutes mean more chances "to score, rebound, and assist," with no data ([xEP Network](https://typefully.com/xEP_Network/correlation-between-nba-player-performance-uYlZTBU))
- Gaussian copula approach for box-score metrics, handling discrete values via rank likelihood (Hoff 2007, sbgcop) [PP] ([Franks et al.](https://ar5iv.labs.arxiv.org/html/1609.09830)); Bayesian network with Gaussian copula for basketball performance data (De Giovanni, D'Urso, Vitale, Annals of Operations Research) [PR][EXC] ([Sapienza IRIS](https://iris.uniroma1.it/handle/11573/1661208)); a Poisson graphical model test applied to 2016-17 NBA player count statistics [PP][EXC] ([arXiv 2506.18778](https://arxiv.org/pdf/2506.18778))
- KyShiesty models each stat with its own negative binomial and PRA with a normal; no joint model is described, and its DD test lost 26% blind [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md))
- DD rules: 10+ in two of points, rebounds, assists, steals, blocks ([Wikipedia](https://en.wikipedia.org/wiki/Double-double)); a DD bet wins on a triple-double and overtime counts at books reviewed by StatsBench (not FanDuel-specific) [EXC] ([StatsBench](https://blog.statsbench.com/?p=393))

### Inferences
- Math that bounds the problem (Frechet bounds, computed): P(A and B) lies between max(0, P(A) + P(B) - 1) and min(P(A), P(B)). For an elite big with P(points >= 10) = 0.97 and P(rebounds >= 10) = 0.85, independence gives 0.82 and any correlation keeps it in 0.82 to 0.85. For a fringe candidate at 0.70 and 0.60, independence gives 0.42 but the true value can be anywhere from 0.30 to 0.60.
- So for the Jokic or Sabonis tier, correlation handling moves P(DD) by at most a few points and the job is estimating the second category's marginal (mostly rebounds, driven by minutes). For plus-money candidates the joint structure matters a lot, which is where the one tested DD strategy lost money.
- Players with three paths (points, rebounds, assists all near 10, as with Jokic) have P(DD) above any single pair; a model must count all pairs, not only points plus rebounds.
- Practical joint method: simulate minutes first (this carries most positive dependence), then draw per-minute stat vectors jointly, either from a Gaussian copula fit to the player's residuals or by resampling the player's own recent per-minute stat lines, which preserves his empirical correlation. This is my recommendation; no source tested it on DDs.

### Gaps
- No published Pearson or rank correlations of same-game points, rebounds, assists for a player, raw or conditional on minutes. These need to be computed from game logs.
- No source states whether FanDuel, Dimers, or other books price DDs from joint simulations or from marginals.

## 5. Which features repeatedly show up as most predictive?

### Takeaway
The inputs that recur across systems are projected minutes with recency weighting, per-minute or per-possession rates shrunk toward prior seasons, teammate absences with usage redistribution, pace and game total, opponent adjustments, point spread as blowout risk, rest and back-to-backs, and home court. In the one model that measured it, the market price outperformed the model on its own, and the usage-redistribution bets lost money.

### Cited Findings
- KyShiesty's 31 as-of-date overs features include spread, rest, minutes trend, recent form, L10 hit rate, pace, opponent defense, history vs opponent, and market shape; usage bumps of 30% for PTS/AST/3PM and 17.5% for REB (stronger at the same position) calibrated on 900+ absences; boosted players still came out about 0.9 PTS high; usage-model bets returned -3.2% vs +0.7% without them [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); ([KyShiesty repo](https://github.com/KyShiesty919/NBA-Props))
- KyShiesty: model leans in morning lines moved toward the model 56% to 59% of the time, +0.6 points average CLV [BT] ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md))
- DARKO adjusts for rest, travel, home court, opponent, aging, seasonality, interaction effects [SR] ([DARKO about](https://www.darko.app/about))
- RotoWire minutes inputs include teammate injuries, opponent strength, blowout risk, back-to-backs, travel ([RotoWire](https://www.rotowire.com/basketball/article/nba-projected-minutes-explained-fantasy-basketball-97473))
- Stokastic matchup pace estimate: (team pace x opponent pace) / league pace; higher Vegas totals mean more fantasy output; early in the season lean on league averages with a slight matchup bump ([Stokastic](https://www.stokastic.com/articles/nba-dfs/nba-dfs-research))
- Rebounds, blocks, assists are stable, discriminative skills; 3P% is mostly noise within a season [PP] ([Franks et al.](https://ar5iv.labs.arxiv.org/html/1609.09830))
- Player absences move game lines, and opening lines err when a player is absent; closing lines are efficient [PR] ([Dare, Dennis, Paul](https://ideas.repec.org/a/eee/finlet/v13y2015icp130-136.html))
- hacksumn's features include opponent-adjusted points per possession, usage and injury, regression of opponent FT% and 3P% luck, and a blowout discount ([hacksumn](https://github.com/hacksumn/NBA-Prop-Maker))
- Leakage rule for DD classifiers: exclude the five component stats from predictors [EXC] ([TDS](https://towardsdatascience.com/how-to-predict-nba-double-doubles-f4c30be08ca0/))

### Inferences
- For a big-man DD the likely order of importance is: minutes distribution (including spread and foul risk), rebound rate (stable), teammate frontcourt absences, opponent shot volume and miss rate (pace and opponent FG%), then home and rest. This ordering is my synthesis; no DD-specific feature-importance ranking was found.
- Because the market absorbs injury news (Dare et al.; KyShiesty usage bets losing), a feature that only restates widely known absences is unlikely to create an edge by itself; timing (betting before the line moves) is where absence information can pay.

### Gaps
- No source quantifies opponent defensive rebound rate or opponent missed-shot volume as a predictor of individual rebounds or DDs.
- No feature-importance results from a DD classifier found.

## 6. What hit rates do public double-double pick services report, are records independently tracked, and how concentrated are the obvious picks?

### Takeaway
No DD-specific, independently tracked pick record was found; the only DD record located is Dimers' self-reported 12-4 (+5.55u). Elite DD rates per game played were 80% to 87% in 2024-25, but in 2025-26 only Nikola Jokic (84.6%) cleared 80% among high-volume players, and injuries cut Sabonis, Giannis, and Davis to 19 to 36 games. Example DraftKings prices for the top tier (-455 to -650) imply 82% to 87%, close to season rates, which leaves little room for a season-rate screen to find value.

### Cited Findings
- 2024-25 DD per games (rate computed): Sabonis 61/70 (87.1%), Jokic 59/70 (84.3%), Zubac 59/80 (73.8%), Towns 58/72 (80.6%), Giannis 55/67 (82.1%), Trae Young 51/76 (67.1%), Sengun 45/76 (59.2%), Vucevic 45/73 (61.6%), Duren 41/78 (52.6%), Allen 40/82 (48.8%), Davis 36/51 (70.6%), Gobert 36/72 (50.0%) ([Land of Basketball 2024-25](https://www.landofbasketball.com/year_by_year_stats/2024_2025_double_doubles_rs.htm))
- 2025-26 DD per games (rate computed): Towns 56/75 (74.7%), Jokic 55/65 (84.6%), Jalen Johnson 49/72 (68.1%), Wembanyama 42/64 (65.6%), Duren 41/70 (58.6%), Cunningham 38/64 (59.4%), Clingan 37/77 (48.1%), Adebayo 35/73 (47.9%), Doncic 34/64 (53.1%), Sengun 34/72 (47.2%), Gobert 33/76 (43.4%), Zubac 24/48 (50.0%), Sabonis 12/19 (63.2%), Giannis 19/36 (52.8%), Davis 13/20 (65.0%); the list covers about 282 players; the page carries no season-complete note ([Land of Basketball 2025-26](https://www.landofbasketball.com/year_by_year_stats/2025_2026_double_doubles_rs.htm))
- Jan 2024 snapshots: Jokic 32 DDs in 38 games (84.2%), Sabonis 33 in 37 (89.1%) [EXC] ([FantasyPros](https://www.fantasypros.com/2024/01/fridays-nba-sleeper-picks-player-predictions-nikola-jokic-domantas-sabonis-immanuel-quickley-1-12))
- Example DD prices (implied probability computed): Sabonis -525 at DraftKings, Oct 29, 2024 (84.0%) [EXC] ([DK Network](https://dknetwork.draftkings.com/2024/10/29/domantas-sabonis-best-prop-bets-for-kings-at-jazz/)); Sabonis -650 (86.7%) and -285 (74.0%), undated [EXC] ([DK Network](https://dknetwork.draftkings.com/?p=149309)); Jokic -455 at DraftKings, undated (82.0%) [EXC] ([RotoWire](https://www.rotowire.com/basketball/article.php?id=57004))
- FanDuel examples: Jalen Duren to record a DD -170 (Jan 2026, 63.0%), Jarrett Allen +140 (late Feb 2026, 41.7%), Wendell Carter Jr. +190 (Jan 2026, 34.5%) [EXC] ([FanDuel Research Jan 2026](https://www.fanduel.com/research/2-nba-best-bets-player-props-and-predictions-for-tuesday-1-6-26)); ([FanDuel Research Feb 2026](https://fanduel.com/research/2-best-nba-player-prop-bets-for-friday-2-27-26))
- FanDuel settlement: a prop stands "once the player takes the court no matter how long they play"; "If a player doesn't participate at all, bets are void" (July 31, 2024) ([Action Network](https://www.actionnetwork.com/education/does-fanduel-void-injured-player-props))
- Tracked records found are not DD-specific: SportsLine lists Larry Hartstein at 87-56 over his last 143 NBA prop picks and PropBetGuy at 29-13 over 42 (snapshots, all prop types) [EXC] ([SportsLine](https://www.sportsline.com/experts/13773/larry-hartstein?league=NBA)); BettingPros 32-16 sleeper picks including DD props (Nov 2023) [SR][EXC] ([BettingPros](https://www.bettingpros.com/articles/nba-sleeper-picks-player-predictions-11-16/)); Action Network Bet Quality 10 at 60.31% [SR] ([Action Network](https://www.actionnetwork.com/nba/tuesday-nba-player-props-betting-picks-january-28-trae-young))
- Small-sample caution: a 60% hit rate over 50 entries fits both a 55% and a 65% true rate [EXC] ([oddsreference](https://oddsreference.pages.dev/dfs/pickem/pickem-expected-value))
- Rufus Peabody often bets unders on popular players near kickoff after public money pushes prices, and says props grew more efficient as books added player markets (NFL context) [EXC] ([Fox Sports](https://amp.foxsports.com/stories/nfl/super-bowl-2022-odds-pro-bet))
- Prop limits are low and winning prop bettors get limited, per r/algobetting threads [EXC] ([r/algobetting mirror](https://lr.eu.psf.lt/r/algobetting)); bookmakers discriminate against successful clients [PP] ([Kaunitz et al.](https://arxiv.org/abs/1710.02824))

### Inferences
- Break-even at -500 is 83.3% and at -525 is 84.0% (computed). Sabonis's 87.1% in 2024-25 sits 3 points above the -525 break-even, but the standard error of a 70-game rate near 87% is about 4 points (computed), so a season rate alone cannot show an edge for the elite tier.
- At -525 each point of probability error moves expected ROI by about 1.2 points (computed); KyShiesty's measured 5 to 11 point overconfidence would turn a break-even bet into an apparent 6% to 13% edge. Calibration in the 0.75 to 0.95 band is the crux for a favorites-only DD bot.
- Nightly expectation for three independent picks (computed): at 85% each, 2.55 hits on average and a 61% chance all three hit; at 80% each, 51%; using the three highest 2025-26 rates (Jokic 84.6%, Towns 74.7%, Jalen Johnson 68.1%), 43%. Parlaying the picks compounds the hold on each leg.
- Concentration risk: 2025-26 showed the obvious tier can collapse to one or two players when stars miss time; on nights Jokic sits, the third pick may be a 60% to 70% player, where joint modeling matters more (Question 4).
- Gobert's 43% to 50% DD rates in the last two seasons put him outside the "obvious" tier the bot spec assumes.
- "Yes" DD bets on stars are the popular side; if books shade the popular side, as Peabody describes for NFL props, value is less likely on heavy "Yes" favorites. This is a hypothesis to test, not a finding.
- seantanger anchors on FanDuel's prop line and bets other books when they differ, which suggests that author treats FanDuel props as a reference price; a bot betting only at FanDuel gives up line shopping.

### Gaps
- No independently audited DD pick record found for any service, and no public record of a "top 2 or 3 DDs per night" strategy.
- No FanDuel DD price history found; I could not confirm whether FanDuel offers a "No" side (needed to de-vig), whether overtime counts in its DD market, or its exact hold.
- 2025-26 games-played figures come from one site via an automated summarizer; cross-check against Basketball-Reference before use.

## 7. What do the better-performing approaches have in common, and why?

### Takeaway
The approaches with the most defensible out-of-sample evidence (DARKO for projections, the two honest GitHub backtests, and the calibration and decorrelation papers) share a separate minutes model, recency-weighted rates shrunk toward priors, explicit absence handling, calibration checked against outcomes, and a blend with or benchmark against the de-vigged market. None shows a statistically significant betting edge on DD props.

### Cited Findings
- Minutes modeled separately and treated as the hardest input ([DARKO about](https://www.darko.app/about)); minutes EWMA and 240-minute team anchoring ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); a minutes model beats a 5-game average (R^2 0.65 vs 0.55) ([Zhang](https://zhang-haipeng.github.io/2020/02/10/project-NBA-minutes.html))
- Recency weighting plus shrinkage: DARKO exponential decay and Kalman filter ([DARKO about](https://www.darko.app/about)); games/(games+15) shrinkage ([KyShiesty](https://github.com/KyShiesty919/NBA-Props)); 6/3/1 weights plus 1000 average minutes ([BBRef SPS](https://www.basketball-reference.com/about/projections.html))
- Market as benchmark or input: market Brier 0.244 beat model 0.248, blend 0.241 ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); decorrelation from odds raised profit [PR] ([Hubacek et al.](https://econpapers.repec.org/RePEc:eee:intfor:v:35:y:2019:i:2:p:783-796))
- Calibration over accuracy [PP] ([Walsh and Joshi](https://arxiv.org/abs/2303.06021))
- Honest evaluation: leak-free features, grading at prices actually offered, pre-registered holdout; development +6.1% fell to -1.8% on holdout ([seantanger](https://github.com/seantanger/nba-props-research)); an in-sample +18% overs model went -6% blind ([KyShiesty](https://github.com/KyShiesty919/NBA-Props))
- Blowout and game-script awareness: 10+ point spread unders +20.9% blind ([KyShiesty README](https://raw.githubusercontent.com/KyShiesty919/NBA-Props/main/README.md)); garbage-time removal ([hacksumn](https://github.com/hacksumn/NBA-Prop-Maker))

### Inferences
- Why minutes-first works: rates are stable skills (Franks et al.), while minutes carry nearly all game-specific news (injuries, rest, blowouts, fouls), so separating them lets fast-changing information update one component without re-estimating skill.
- Why market blending works: the book's price already aggregates injury news and sharp action; a model adds value only where it is right and the market is wrong, which is a decorrelation problem, not an accuracy problem.
- Implications for the DD bot (my recommendations, untested): (1) simulate minutes as a distribution tied to spread, rest, foul rate, and injury news; (2) draw stats jointly given minutes; (3) recalibrate P(DD) in the 0.6 to 0.95 band; (4) compare with a de-vigged price, using a two-way market from another book if FanDuel lists only "Yes"; (5) skip or require extra edge for DD favorites in 10+ point spread games; (6) be cautious in the first weeks of 2026-27 (the first 5 games ran -28% in one backtest); (7) log closing-line value from day one, since win rate on -500 favorites says little in small samples.

### Gaps
- No public DD model reports CLV, calibration curves, or holdout ROI, so "better-performing" here rests on single-stat prop evidence and projection accuracy, not on DD results.
