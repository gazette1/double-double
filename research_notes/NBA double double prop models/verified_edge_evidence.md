# NBA player prop markets: evidence on durable retail edge, verified track records, and failure modes

Research date: 2026-10-29. Labels used below: [VERIFIED-SYNC] = bets proven placed via sportsbook account sync by a third-party app; [PRICE-VERIFIED] = app confirmed the price was available when logged, not that a bet was placed; [PLATFORM-TRACKED] = tracked by the expert's own employer or platform; [SELF-REPORTED] = vendor or individual claim with no outside check; [COMPUTED] = my arithmetic from the stated formula; [UNVERIFIED EXTRACT] = figure taken from a search-engine extract because the page itself could not be retrieved.

## Q1. What peer-reviewed or rigorously analyzed evidence exists on the efficiency or inefficiency of NBA player prop markets, with numbers?

### Takeaway
I found no peer-reviewed study that tests NBA player prop pricing directly (closing-line calibration, over bias, star bias) as of 2026-10-29. The rigorous evidence is adjacent: NBA game-line research shows opening lines misprice star absences but closing lines absorb the news. Industry datasets show props carry higher margins (about 7.9% vs 4.8% on main lines). They also show overs underperforming unders, with both sides losing money at closing prices.

### Cited Findings

#### Peer-reviewed and academic work (game lines and adjacent markets)
- Dare, Dennis and Paul (2015, Finance Research Letters 13: 130-136) tested NBA betting lines when players are absent. Opening lines carried significant errors when a high-quality player was out, the biases were removed by game time (by book response to news or to bettor action), and no profitable strategy existed when betting at the closing line. ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1544612315000227); [IDEAS/RePEc](https://ideas.repec.org/a/eee/finlet/v13y2015icp130-136.html))
- Levitt (2004, Economic Journal 114(495): 223-246) used about 20,000 NFL wagers by 285 bettors. Bookmakers did not act as market makers balancing action. They set a price, took large positions, and shaded lines toward bettor biases. One summary reports that exploiting biases raised gross profit from 5.0% to 6.16%. The data showed little evidence that any bettors systematically beat the book. ([Berkeley PDF](https://www.stat.berkeley.edu/users/aldous/157/Papers/Levitt_Gambling_2004.pdf); [IDEAS/RePEc](https://ideas.repec.org/a/ecj/econjl/v114y2004i495p223-246.html); [NBER w9422](https://www.nber.org/papers/w9422); [AcaWiki summary](https://acawiki.org/Why_are_Gambling_Markets_Organised_So_Differently_from_Financial_Markets%3F))
- Paul and Weinbach (2002, Journal of Sports Economics) found that in NFL game totals the over is overbet at the highest totals, and unders win more often than efficiency implies in that subset. This covers game totals, not props. ([ResearchGate](https://www.researchgate.net/publication/227358040_Market_Efficiency_and_a_Profitable_Betting_Rule_Evidence_From_Totals_on_Professional_Football))
- One study covered NBA regular seasons 1999-00 through 2003-04 (5,671 games, covers.com closing lines). It found some predictive power beyond the line but could not turn it into consistent profit. ([ResearchGate](https://www.researchgate.net/publication/24131329_Is_the_NBA_betting_market_efficient))
- A working paper on real-time pre-game moneyline movement (NBA, NFL, NHL, 2019-2023, three sportsbooks) cites Moskowitz (2021) as finding that closing lines generally overreact. I did not retrieve that paper's own results. ([ResearchGate](https://www.researchgate.net/publication/372441761_Inefficient_Forecasts_at_the_Sportsbook_An_Analysis_of_Real-Time_Betting_Line_Movement))
- Kaunitz, Zhong and Kreiner (2017, arXiv 1710.02824) studied soccer, not the NBA. They bet whenever a bookmaker's odds exceeded the fair price implied by the consensus of other books. Results:
  - +3.5% over 56,435 simulated bets at closing odds (Jan 2005 to Jun 2015).
  - +9.9% over 6,994 simulated bets on minute-by-minute odds (Sep 2015 to Feb 2016).
  - +5.5% over 407 paper-traded bets.
  - +8.5% over 265 real-money $50 bets in 5 months.
  - The 672 live and paper bets combined returned 6.2% ($2,086), with p = 0.089 versus a random-bet benchmark, so not significant at 0.05.
  ([arXiv](https://arxiv.org/abs/1710.02824))
- arXiv "Beating the House" (1910.08858) reports a mean NBA ROI of about -4.39% in its own table while claiming above-market returns across leagues. [UNVERIFIED EXTRACT: table not checked directly] ([arXiv PDF](https://arxiv.org/pdf/1910.08858))
- arXiv "Penalized Regression Models for the NBA" (1301.3523) reported 57.24% on 290 game-spread bets, a small sample. ([arXiv PDF](https://arxiv.org/pdf/1301.3523))
- A 2026 MDPI paper reports steady bankroll growth for moneyline and "synthetic player-prop" strategies. The results come from a simulated protocol, not from executed prices. ([MDPI Information 17(1):56](https://www.mdpi.com/2078-2489/17/1/56))
- A Claremont student thesis on NFL moneylines (2020-2024 data) asserts that mispricing is more common in player prop and alternative-line markets with less volume. It does not test props. ([Claremont thesis](https://scholarship.claremont.edu/cgi/viewcontent.cgi?article=5145&context=cmc_theses))

#### Industry datasets on prop pricing (not peer reviewed)
- **Margins.** A 2026 Mendeley margin panel covers more than 4 million odds from 52 bookmakers in 22 leagues. It reports an average margin of 7.93% on player props, 4.77% on head-to-head main lines and 5.45% on totals. NBA/WNBA assists props show higher median margins that can exceed 7%. ([LowJuiceSportsbooks summary](https://lowjuicesportsbooks.com/prop-market-margins-in-mlb-and-nba/); [Mendeley dataset](https://data.mendeley.com/datasets/yt3xsvk7zn/1))
- **Over vs under at close.** Sickfade reports a study of over 1 million props graded at closing prices. Across sports, unders won 56.7% and overs 43.2%. The NBA slice (375,339 props) shows ROI of about -8.7% on overs and -3.8% on unders. Sickfade is a commercial site, and the page returned HTTP 429 to direct retrieval. [UNVERIFIED EXTRACT] ([Sickfade](https://sickfade.com/overs-vs-unders))
- **Blowouts.** DataStreak (2026-08-08) graded 40,856 NBA over props (points, rebounds, assists, threes, PRA) at posted lines. Seasons, books and open vs close are not stated. Over hit rate by final margin:

  | Final margin | Over hit rate | Props |
  |---|---|---|
  | 7 or fewer | 46.7% | 12,182 |
  | 8 to 14 | 44.9% | not stated |
  | 15 to 19 | 43.8% | not stated |
  | 20 or more | 40.9% | 10,986 |

  ([DataStreak](https://datastreak.com/insights/nba-blowouts-4th-quarter-props))
- **Book sharpness on NBA props.** Pikkit (2024-06-10, author PromoGuy) built lead-lag weights for NBA player props. No date range or sample count is given, and the top five books showed little separation.
  - Circa 1.094 (on about 1/20th as many markets as the others)
  - DraftKings 1.046
  - Propbuilder 1.014
  - FanDuel 1.007
  - Caesars 0.995
  - Kambi 0.627

  ([Pikkit](https://pikkit.com/blog/which-sportsbooks-are-sharp))
- **Book sharpness on MLB props (no NBA equivalent found).** SmartStake (2026-07-07) scored devigged closing lines with the Brier score. The data covered over 600 million MLB prop line movements and 1.3 million closing lines across 75 books and exchanges.
  - Ranking: Kalshi and ProphetX ranked first, Novig next, DraftKings and FanDuel in the middle, and Pinnacle and Bookmaker last.
  - Gap between books on high-volume props: RBIs 0.002 Brier, strikeouts 0.003, hits 0.005.
  - Soft books are described as slow to react to lineup and injury news. Its example is a couple-minute window in which ProphetX repriced in seconds and Fanatics lagged; this is an illustration, not a measurement.
  - It says FanDuel's NBA prop reputation was not tested.

  ([SmartStake](https://www.smartstake.app/learn/sharpest-sportsbooks-mlb-player-props))

#### Speed of adjustment to injury and lineup news
- I found no measured study of how fast NBA props reprice after injury news. One blog claims regional or square books lag sharp offshore markets by 60 to 120 seconds on individual props. That is a single unsourced claim. ([Tony's Picks, 2026-05-20](https://www.tonyspicks.com/2026/05/20/reading-the-nba-injury-report-probable-questionable-and-doubtful-decoded/))
- Books do react to concentrated prop flow. ESPN (2025-10-30) reported on a March 2023 game in which books saw heavy under interest on Terry Rozier's stats and pulled his props hours early.
  - The indictment alleges $257,700 was wagered on the under across books.
  - One Mississippi book took 30 under bets totaling $13,759 that morning.

  ([ESPN](https://www.espn.com/nba/story/_/id/46785871/nba-books-review-most-vulnerable-bets-wager-limits))

#### Practitioner views on where residual edge lives
- Unabated (undated video page, footer 2026) makes four points:
  - Props have more surface area than sharp books can defend.
  - Limits are too low for leading sharps to make props a large share of their action.
  - Books move props mostly to protect liability, so a prop line move can reflect square action.
  - CLV means much only when a sharp book such as Pinnacle or Circa also lists the market.

  ([Unabated](https://unabated.com/content/videos/you-re-using-closing-line-value-wrong))
- Miller and Davidow, "The Logic of Sports Betting", per secondary summaries, not the book itself:
  - Retail books copy a few market makers.
  - Props and derivatives are added faster than anyone can price them.
  - Many markets have limits too small for proven winners to bother with.
  - NBA player props are named as a weaker market that no market-making book lists.
  - Market makers open with low limits and raise them as they take action.

  ([SoBrief summary](https://sobrief.com/books/the-logic-of-sports-betting); [review](https://philoonbooks.wordpress.com/2025/08/28/the-logic-of-sports-betting-by-ed-miller-and-matthew-davidow/))
- Rufus Peabody:
  - A Circles Off episode description says he projects minutes and rotations from preseason information and uses matchups and defensive schemes to find mispriced props. ([Podtail episode page](https://podtail.com/en/podcast/circles-off-sports-betting-podcast/20-rufus-peabody-joins-for-a-discussion/))
  - VSiN reports he now waits for markets to develop and then targets mispriced props, alt lines and game-script scenarios, rather than hitting openers. ([VSiN](https://vsin.com/the-vsin-daily/inside-the-mind-of-sharpest-of-the-super-bowl-prop-sharps/))
  - Adam Levitan posted on X (2025-11-13) about a Peabody podcast interview with a group that bets NBA player props at large scale. The episode content was not retrieved. ([X](https://x.com/adamlevitan/status/1989012864074674551))
- Minutes are the dominant input. A hobbyist NBA prop model (GitHub PR, 2026-10-14; rolling-origin 2022-2025; about 103k player-games per stat) improved MAE over a naive baseline by only 0.5% to 2.7%: points 4.547 vs 4.634, PRA 5.981 vs 6.146. The author states that giving the model actual minutes would cut MAE by 9% to 28%. ([GitHub PR #49](https://github.com/lmaynor/mlb-betting/pull/49))
- Wizard of Odds (explanatory article, no data):
  - Closing lines on major games are good probability estimates.
  - Exotic props on secondary players are less efficient.
  - Books may shade star overs when they expect public action.

  ([Wizard of Odds](https://wizardofodds.com/article/player-props-understanding-the-math-behind-the-lines/))

### Inferences
- **Information timing.** The best-supported route to a retail prop edge is acting on news (absences, rotation changes) before the book reprices. This matches Dare et al. at the game-line level. The same study shows the edge is gone by the close, so it can only be captured at openers or right after news, where limits are lowest.
- **"Bet unders" is not a rule.** If the Sickfade NBA figures hold, both overs and unders lose at closing prices. Unders simply lose less, so a blanket unders rule would not be profitable after margin.
- **Overs under 50%.** Overs hit under 50% in every margin bucket in the DataStreak sample. That fits lines set above the median for right-skewed stats, plus minutes risk. Blowout minutes loss works against any "yes" or over-type bet, including double-doubles.
- **Soft but defended.** Practitioners (Unabated, Miller and Davidow) describe props as softer than main lines but defended with low limits, not as efficient. The edge is therefore capped more by limits than by pricing.

### Gaps
- **No direct test.** Searches of SSRN, arXiv, Journal of Sports Economics and Journal of Prediction Markets found no peer-reviewed test of NBA player prop efficiency.
- **No repricing study.** There is no measured median time-to-reprice for NBA props after injury or lineup news.
- **No star-bias data.** I found nothing on star vs role-player bias in prop pricing; the Wizard of Odds point is explanatory only.
- **Sickfade unverified.** The Sickfade methodology (books, seasons, push handling) could not be checked.
- **Leads not retrieved.** Girdner et al. (2013, Journal of Prediction Markets) on early-season NBA over/under bias, and Davis and Krieger (2017, Applied Economics) on preseason bias in NFL and NBA markets. Both are game totals, not props, and were seen only as citations in search results.

## Q2. Which NBA prop models or cappers have verified multi-season records (ROI, CLV, sample size), and what do those numbers look like?

### Takeaway
I found no NBA prop model or capper with a public, third-party-verified, multi-season record that is prop-only and includes CLV. The verifiable records that exist are of two kinds:
- One-year, all-NBA (not prop-only) sportsbook-synced leaderboards, showing ROIs of about -0.2% to +20.8% with no settled sample sizes and no CLV.
- Employer-tracked 30-day records of 6 to 85 picks.

The "hit rates" shown by Outlier and Props.cash are historical frequencies of a line clearing, not forecasts or track records.

### Cited Findings

#### How each platform verifies
- **Pikkit [VERIFIED-SYNC]**
  - Profiles sync to sportsbook accounts, and Pikkit says each bettor's full history is public (wins, losses, ROI, sample size). It offers a CLV tracker.
  - Its ROI guide calls 3% to 7% ROI very strong and hard to sustain. It also says 15% over 200 prop bets is not comparable to 15% over 5,000 spread bets.
  - I found no published platform-wide statistic on prop profitability.

  ([Pikkit ROI guide](https://pikkit.com/blog/how-to-track-sports-betting-roi); [Pikkit on finding bettors](https://pikkit.com/blog/how-to-find-profitable-bettors-to-follow); [Pikkit CLV](https://pikkit.com/closing-line-value))
- **Betstamp [PRICE-VERIFIED]**
  - A tracked bet counts as "verified" only if the odds were available at the sportsbook when it was tracked. Editing the odds afterward removes verification, and unverified picks do not count toward the public record.
  - CLV is tracked only for main-market bets, so player props get no Betstamp CLV.
  - App Store reviewers describe leaderboards sortable by ROI or CLV.

  ([Betstamp tutorial](https://www.betstamp.com/tutorials/track-bets); [App Store reviews](https://apps.apple.com/us/app/betstamp-bet-tracker-props/id1525948689?see-all=reviews))
- **Juice Reel [VERIFIED-SYNC]**
  - Says its rankings use sportsbook-synced results, not screenshots, and its cards show past-year NBA data.
  - Its FAQ says records can be broken out by market, but no prop-only results appeared on the page.

  ([Juice Reel NBA leaderboard](https://www.juicereel.com/best-nba-handicappers))
- **Action Network [PLATFORM-TRACKED]**
  - Says its experts track their prop bets in the Action app.
  - The page does not document grading price, CLV, or a props-only split.

  ([Action NBA props page](https://www.actionnetwork.com/nba/props))

#### Juice Reel NBA leaderboard snapshot [VERIFIED-SYNC]
Retrieved 2026-10-29. Window is "past year". All NBA markets, not prop-only. No CLV and no settled sample size shown.
- **Range.** Page one shows 36 cards, ranked #7 to #226, with ROI from -0.2% to +20.8%.
- **Examples.**

  | Handicapper | Rank | Profit | ROI |
  |---|---|---|---|
  | Ajp9 | #49 | +$56,029 | +4.5% |
  | KJEdge | #15 | +$43,792 | +5.9% |
  | JakeM | #12 | +$26,572 | +7.6% |
  | stat | #8 | +$21,654 | +9.4% |
  | brezo | #79 | +571.8u | +13.2% |
  | tommy227 | #87 | +$12,161 | +1.4% |

- **Bios not verified.** Some bios contain [SELF-REPORTED] claims the cards do not verify, such as JakeM's "about 32k bet sample" and "about 8.1% ROI all time", and BettorPat's "$70k+ profit".

([Juice Reel](https://www.juicereel.com/best-nba-handicappers))
- [COMPUTED] Profit divided by ROI gives implied past-year NBA handle: about $1,245,000 for Ajp9, $742,000 for KJEdge, $350,000 for JakeM and $230,000 for stat.

#### Action Network NBA leaderboard snapshot [PLATFORM-TRACKED]
Retrieved 2026-10-29. Window is the last 30 days only. No ROI, CLV or grading method shown.

| Expert | Record | Units | Picks |
|---|---|---|---|
| Ryan Minion | 37-29 | +13.0u | 66 |
| Brandon Kravitz | 16-5 | +9.5u | 21 |
| Wags Wins | 47-38 | +6.7u | 85 |
| Matt Moore | 38-32-1 | +4.4u | 71 |
| RoyalsProps | 16-12-2 | +3.1u | 30 |
| Joe Dellera | 16-17 | -1.5u | 33 |
| Collin Whitchurch | 12-17 | -2.6u | 29 |
| Brian Bitler | 6-8 | -6.0u | 14 |

([Action top experts](https://www.actionnetwork.com/nba/picks/top-experts))

The props page on the same date showed Kyle Murray at 56-46-1 (+10.8u) over the last 30 days. ([Action NBA props](https://www.actionnetwork.com/nba/props))

#### SportsLine [PLATFORM-TRACKED]
- SportsLine credits Prop Bet Guy (Doug, formerly at Action Network) with +67 units on NBA player props and 39-23 over his last 62 NBA prop picks. Dates were not shown in the extract. [UNVERIFIED EXTRACT] ([SportsLine](https://www.sportsline.com/experts/51314525/prop-betguy/?league=nba))

#### Model and tool vendors [SELF-REPORTED or no record]
- **Rithmm.** No public line-by-line ledger found. Users can backtest models in-app on about 2,000 games in its backlog [SELF-REPORTED], and reviewers report mixed user results. ([OddsPlays comparison](https://oddsplays.com/us/betting-tools/outlier-vs-rithmm/); [PropsBot tool comparison](https://propsbot.ai/best-ai-sports-betting-tools/))
- **Outlier and Props.cash.** Both are research dashboards that show how often a line cleared over L5, L10 or L20 windows. Neither makes a model-accuracy claim that could be verified. ([Outlier help center](https://help.outlier.bet/en/articles/6711738-research-player-propositions-with-outlier-s-prop-finder); [BetSmart comparison](https://www.betsmart.co/comparison-tool/outlier-vs-props-cash); [BettorEdge](https://www.bettoredge.com/post/props-cash-vs-other-prop-betting-tools))
- **Unabated.** Sells odds screens and an NBA prop simulator, reported at about $249 per month on top of a plan. It publishes no picks record. ([Unabated NBA](https://unabated.com/sports/nba); [BetSmart review](https://www.betsmart.co/tool-reviews/unabated))
- **Betstamp pricing.** Betstamp says its props pricing engine draws on 200+ sportsbooks and 5+ seasons of closing lines, and weights books by historical sharpness [SELF-REPORTED]. I found no outside audit. ([Betstamp PRO](https://www.betstamp.com/pro))
- **Hit-rate marketing example.** A PropsBot "High Hit Rate Signal" was described in search results as 82.6% in MLB and 86.5% in NHL, with no prices attached. It is not NBA, and the page was not fetched. [UNVERIFIED EXTRACT, SELF-REPORTED] ([directory listing](https://www.neura.market/ai-tools-directory/data-analytics/propsbot-ai))

#### Documented failure modes (records and backtests)
1. **No closing line logged.** Betstamp computes no CLV for props, and the Juice Reel and Action leaderboards show no CLV. Unabated says prop CLV carries weight only where a sharp book lists the market. ([Betstamp](https://www.betstamp.com/tutorials/track-bets); [Unabated](https://unabated.com/content/videos/you-re-using-closing-line-value-wrong))
2. **Grading at prices that could not be executed.**
   - Kaunitz et al. found that about 30% of the odds on their dashboard had already changed at the bookmaker by the time they tried to bet.
   - Their live operator bet about one-tenth as many games as the simulation over a similar period.
   - Betstamp's verify-at-tracking rule exists to block this problem.

   ([arXiv](https://arxiv.org/abs/1710.02824); [Betstamp](https://www.betstamp.com/tutorials/track-bets))
3. **Survivorship and selection.** Leaderboards display the ranked survivors ([Juice Reel](https://www.juicereel.com/best-nba-handicappers)). [COMPUTED, exact binomial] Chance that a bettor with zero edge shows a hit rate above break-even over one season:

   | Price | +2 pts over 330 bets | +2 pts over 495 bets | +3 pts over 330 bets | +3 pts over 495 bets |
   |---|---|---|---|---|
   | -300 | 18.7% | 14.3% | 10.1% | 5.5% |
   | -110 | 23.2% | 17.9% | 14.4% | 8.5% |

   Out of 100 zero-edge touts, about 14 to 23 would post a "+2 point" season.
4. **Feature leakage from actual minutes or lineups.**
   - The hobbyist PR states that actual minutes would cut MAE by 9% to 28%. A backtest that leaks realized minutes or the realized inactive list therefore shows accuracy no pregame model can reach; the honest model beat the naive baseline by only 0.5% to 2.7%. ([GitHub PR #49](https://github.com/lmaynor/mlb-betting/pull/49))
   - Another hobbyist PR (2026-10-26) uses a cutoff 30 minutes before tip, box scores from earlier dates only, and mutation tests for leakage. Its pre-specified 2024-25 simulation returned -3.9% ROI (95% CI -7.6% to -0.2%). ([GitHub PR #53](https://github.com/Eth91/tennis-odds-collector/pull/53))
5. **Post-hoc filters and in-sample selection.** An NBA prop research repo used FanDuel's line as the anchor and bet DraftKings, BetMGM or BetRivers whenever their price differed by 3 or more percentage points.
   - +6.1% ROI on 6,424 development bets (2020-21 to 2024-25).
   - -1.8% on its 35-bet pre-registered holdout.
   - README status: "no proven edge". The forward ledger started 2026-10-25.

   ([seantanger/nba-props-research](https://github.com/seantanger/nba-props-research))
6. **Open vs close price selection.** That repo does not say whether its historical prices are openers or closes. Dare et al. locate star-absence errors in opening lines, but openers are also where limits are lowest: per the Logic of Sports Betting summaries, market makers open with low limits and raise them as they take action. ([repo](https://github.com/seantanger/nba-props-research); [Dare et al.](https://www.sciencedirect.com/science/article/abs/pii/S1544612315000227); [SoBrief](https://sobrief.com/books/the-logic-of-sports-betting))
7. **Data-availability claims conflict.** One hobbyist PR asserts that no NBA prop odds history exists anywhere. The seantanger repo contradicts this: it sourced historical prop prices from BettingPros. ([PR #49](https://github.com/lmaynor/mlb-betting/pull/49); [repo](https://github.com/seantanger/nba-props-research))
8. **Account limiting ends profitable strategies.** Kaunitz et al. were capped at $1.25 to $11.11 maximum stakes within months; details are in Q5. ([arXiv](https://arxiv.org/abs/1710.02824))

### Inferences
- **Verified bets are not a verified edge.** Sync verification proves the bets were placed, not that the result reflects skill. Without CLV and multi-season prop-only samples, none of these records can separate a 2-3 point edge from variance (see Q3).
- **Holdouts are the realistic expectation.** The pattern of a strong development backtest followed by a weak honest holdout (+6.1% vs -1.8%; a pre-specified simulation at -3.9%) is what a skeptic should expect from most NBA prop backtests.
- **30-day records carry no information.** At 6 to 85 picks, Action's 30-day records have standard errors of about 5 to 20 hit-rate points [COMPUTED: sqrt(0.25/n)].
- **What a credible record needs.** A double-double bot should use pre-registered, timestamped forward logging. Each pick should record the executable price and book, the best available price, and a closing or derived fair price.

### Gaps
- **No qualifying record found.** None of Pikkit, Betstamp, BetQL, Action Network, Unabated, Rithmm, Juice Reel, Props.cash, Outlier or PropsHQ showed a multi-season, prop-only record with CLV for any named capper or model.
- **BetQL and PropsHQ.** No public record or methodology was found in this pass.
- **Stale Action figure.** A search extract attributed an NBA record of 693-609-51 (+170.07u) to Action's Brandon Anderson on an older version of the props page, which the extract described as about two years old. The live page on 2026-10-29 does not show it, so it is unverified.
- **No prop-specific aggregates.** Pikkit and Juice Reel publish no aggregate prop-only profitability rates.

## Q3. At -250, -300 and -400, what hit rate breaks even, and how many bets are needed to be 95% confident a 2 to 3 point edge is real? Also hold and parlay math.

### Takeaway
At -250, -300 and -400 the break-even hit rates are 71.43%, 75.00% and 80.00%. A "70% hit rate" on favored double-doubles therefore loses 2.0% to 12.5% of stake. Confirming a 2 to 3 point edge at those prices with 95% two-sided confidence takes about:
- 600 to 1,900 bets at 50% power.
- 1,350 to 3,950 bets at 80% power.

At 2 to 3 bets per night that is roughly 1.2 to 12 regular seasons.

### Cited Findings

#### Break-even and ROI formulas [COMPUTED]
- **Formulas.**
  - Negative odds -A: break-even p = A / (A + 100), and decimal odds d = 1 + 100/A.
  - Positive odds +B: break-even p = 100 / (B + 100), and d = 1 + B/100.
  - ROI per unit staked at true hit rate p: ROI = p x d - 1.
- **Break-even hit rates.**

  | Price | Break-even |
  |---|---|
  | -110 | 52.38% |
  | -115 | 53.49% |
  | -120 | 54.55% |
  | -200 | 66.67% |
  | -250 | 71.43% |
  | -300 | 75.00% |
  | -350 | 77.78% |
  | -400 | 80.00% |
  | -500 | 83.33% |

- **ROI at a given hit rate.**

  | Hit rate | -250 | -300 | -400 |
  |---|---|---|---|
  | 70% | -2.0% | -6.67% | -12.5% |
  | 72% | +0.8% | -4.0% | -10.0% |
  | 75% | +5.0% | 0.0% | -6.25% |
  | 78% | +9.2% | +4.0% | -2.5% |
  | 80% | +12.0% | +6.67% | 0.0% |
  | 82% | +14.8% | +9.33% | +2.5% |

- **Value of one hit-rate point.** One point of hit rate is worth d percent of ROI: 1.40% at -250, 1.33% at -300, 1.25% at -400, and 1.91% at -110.
- **Where 70% stops paying.** A 70% hit rate loses money at any price shorter than about -233 (break-even 70%).

#### Hold and margin
- [COMPUTED] Two-sided hold = 1 - 1/(p_a + p_b), where p_a and p_b are the implied probabilities of the two sides:

  | Market | Hold |
  |---|---|
  | -110/-110 | 4.55% |
  | -114/-114 | 6.14% |
  | -115/-115 | 6.52% |
  | -120/-110 | 6.48% |
  | -250/+190 | 5.58% |
  | -300/+220 | 5.88% |
  | -300/+200 | 7.69% |
  | -400/+280 | 5.94% |

- **Measured cross-sport averages.** Player props average 7.93% margin vs 4.77% on head-to-head main lines. ([LowJuiceSportsbooks / Mendeley panel](https://lowjuicesportsbooks.com/prop-market-margins-in-mlb-and-nba/))
- **Same-game parlays.** Secondary sources estimate SGP hold at 15% to 35%, because books price SGP legs with proprietary correlation models. Operators do not publish per-market SGP hold. ([Tech Insider](https://tech-insider.org/sports-betting/parlay-betting-explained/); [iGaming News](https://www.igamingnews.biz/same-game-parlay-sportsbook-margin-engine/))

#### Sample size [COMPUTED]
- **Formula.** This is a one-sample test of the hit rate against break-even p0 when the true rate is p1 = p0 + delta:
  - n = [ (z_alpha x sqrt(p0(1 - p0)) + z_beta x sqrt(p1(1 - p1))) / delta ]^2
  - Two-sided 95% uses z_alpha = 1.96; 80% power uses z_beta = 0.84; 50% power uses z_beta = 0.
  - At 50% power this simplifies to n = 1.96^2 x p(1 - p) / delta^2. That is the number of bets at which the expected result just reaches significance.
  - Equivalent ROI form: n = (1.96 x sigma / mu)^2, with sigma = d x sqrt(p(1 - p)) per unit staked and mu = p x d - 1.
  - Worked example at -300 with p = 0.77: mu = 2.67%, sigma = 0.561, so n = (1.96 x 0.561 / 0.0267)^2 = about 1,701.
- **Required bets (two-sided alpha = 0.05).**

  | Price | Edge | ROI | n at 50% power | n at 80% power | n, one-sided 95%, 80% power |
  |---|---|---|---|---|---|
  | -250 (p0 71.43%) | +2 pts | 2.8% | 1,874 | 3,952 | 3,108 |
  | -250 | +3 pts | 4.2% | 813 | 1,744 | 1,370 |
  | -300 (p0 75.00%) | +2 pts | 2.67% | 1,701 | 3,618 | 2,844 |
  | -300 | +3 pts | 4.0% | 733 | 1,593 | 1,251 |
  | -400 (p0 80.00%) | +2 pts | 2.5% | 1,418 | 3,066 | 2,408 |
  | -400 | +3 pts | 3.75% | 603 | 1,345 | 1,055 |
  | -110 (p0 52.38%), for comparison | +2 pts | 3.82% | 2,383 | 4,887 | not computed |
  | -110 | +3 pts | 5.73% | 1,055 | 2,170 | not computed |

- **Seasons required.** Assumption, not sourced: about 165 regular-season game nights, so 2 bets per night is about 330 bets and 3 bets per night about 495. The 2026-27 season opened 2026-10-20 per [Dimers](https://www.dimers.com/nba/news/nba-player-props-bans-regulated-betting-2026-27).

  | Price and edge | 50% power, 330/season | 50% power, 495/season | 80% power, 330/season | 80% power, 495/season |
  |---|---|---|---|---|
  | -300, +2 pts | 5.2 | 3.4 | 11.0 | 7.3 |
  | -300, +3 pts | 2.2 | 1.5 | 4.8 | 3.2 |
  | -400, +3 pts | 1.8 | 1.2 | 4.1 | 2.7 |
  | -250, +2 pts | 5.7 | 3.8 | 12.0 | 8.0 |

- **One season's precision.** The 95% confidence half-width on a hit rate near 75% is about +/-4.7 points at 330 bets and +/-3.8 points at 495 bets. It is still +/-2.7 points at 990 bets (two seasons at 3 per night). One season cannot separate a 2 to 3 point edge from zero.
- **CLV as a faster test.**
  - Secondary summaries of Joseph Buchdahl's Pinnacle work put the per-bet standard deviation of CLV near 0.10, versus about 1.00 for profit and loss at even money. ([Pinnacle Odds Dropper on Buchdahl](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl); [Sports Trading Network](https://www.sportstradingnetwork.com/article/using-the-closing-line-to-test-your-skill-in-betting/))
  - HowProsBet estimates that a 2% edge at decimal 2.00 needs about 6,800 bets to show significance from results, but about 70 measured by CLV. ([HowProsBet](https://howprosbet.com/how-to-verify-your-betting-edge/))
  - Caveat: Unabated says prop CLV is unreliable unless a sharp book also lists the market. ([Unabated](https://unabated.com/content/videos/you-re-using-closing-line-value-wrong))
- **Empirical illustration.** Kaunitz et al. earned +6.2% over 672 live and paper bets and still had p = 0.089 against random betting. ([arXiv](https://arxiv.org/abs/1710.02824))

#### Parlays and boosts [COMPUTED unless cited]
- **Independent legs.** When the parlay is priced as the product of the legs' decimal odds, parlay EV = (1 + e1)(1 + e2)...(1 + ek) - 1, where e is each leg's EV.
  - Positive legs compound: three legs at +2.67% each give +8.2%, four give +11.1%.
  - Negative legs compound too:
    - Three -110 legs on true 50/50 events (e = -4.55% each) give -13.0%; four give -17.0%.
    - Three -300 legs on true 73% events (e = -2.67%) give -7.8%; four give -10.3%.
- **Variance.** A 4-leg parlay of -300 legs pays decimal 3.16 and breaks even at 31.6% (0.75^4). Four true-77% legs hit only 35.2% of the time, so long losing streaks are routine even with a real edge.
- **Correlated legs.** SGP engines apply correlation adjustments and higher margin (estimated 15% to 35%). A correlated parlay is +EV only where the book's correlation model is wrong. For 2026-27, NBA partners may not offer parlays that combine multiple unders on one player in the same game. ([Dimers](https://www.dimers.com/nba/news/nba-player-props-bans-regulated-betting-2026-27))
- **Profit boosts.**
  - A 25% profit boost on -300 lifts decimal odds from 1.333 to 1.417, cutting break-even from 75.0% to 70.6%.
  - A 50% boost cuts it to 66.7%.
  - A 25% boost on -400 cuts break-even from 80.0% to 76.2%.

### Inferences
- **Heavy favorites are unforgiving.** At heavy-favorite prices each hit-rate point is worth less ROI, and each miss erases 2.5 to 4 wins. "70% hit rate" marketing on double-double favorites is consistent with losing money.
- **Validate on price, not wins.** A double-double bot cannot be validated on win rate within a season. Use CLV against the best available or derived fair price, plus forward pre-registered logging. If CLV is computed against soft-book closes on markets no sharp book lists, treat it as weak evidence (per Unabated).
- **Parlays amplify, they do not create.** Parlaying favored double-doubles multiplies whatever per-leg edge or vig exists. With typical vig and no real edge, a 3-leg parlay roughly triples the expected loss rate.

### Gaps
- **No operator disclosure.** I found no primary operator figure for NBA prop hold by market type (main props, alt lines, milestones, double-doubles). The 7.93% figure is cross-sport.
- **Game-night count is assumed.** The 165 game-night figure is my assumption, not a sourced number.

## Q4. Is there any published evidence specifically on the double-double or triple-double "yes" market (biases, limits, profitability)?

### Takeaway
I found no academic or rigorous industry study of NBA double-double (DD) or triple-double markets: no work on pricing bias, hold, limits or profitability. The evidence is indirect:
- DD markets are offered at DraftKings, FanDuel, BetMGM and Caesars.
- Quoted prices run from plus-money to heavy favorites.
- The "yes" side is an over-type derivative of the points, rebounds and assists distributions.
- Adjacent data on over-side underperformance and blowout minutes loss point against "yes" unless the price compensates.

### Cited Findings
- **Availability.** BettingPros lists DD props (for example, Giannis Antetokounmpo) at DraftKings, FanDuel, BetMGM and Caesars. It grades them with a projection plus EV built from historical DD hit rates. Live prices were not captured on retrieval. ([BettingPros](https://www.bettingpros.com/nba/props/giannis-antetokounmpo/double-double/))
- **Price examples.** [UNVERIFIED EXTRACT] Scottie Barnes DD at -120 on DraftKings. Separately, Action Network staff picked a DD at +130 at Caesars as better value than a points prop. ([SI](https://www.si.com/betting/nba-best-bets-today-predictions-prop-bets-jalen-brunson-scottie-barnes); [NBA.com / Action Network](https://www.nba.com/nbabet/the-action-network-staffs-2-best-nba-bets-for-tuesday-2))
- **Triple-double examples.** A vendor glossary gives illustrative triple-double prices: +200 for Russell Westbrook at his peak, +600 for LeBron James. It claims implied probabilities are usually within 5 points of true probability, an unsourced vendor claim. ([PropsBot glossary](https://propsbot.ai/glossary/triple-double/))
- **League restrictions for 2026-27** (effective 2026-10-20). DD and milestone markets are not mentioned in either source.
  - New: no parlays that combine multiple unders on one player in a game.
  - New: "first of" markets removed.
  - New: no unders on bench players expected to play less than about 12 minutes.
  - Existing: no props on two-way or 10-day players, and no bets on turnovers, fouls or missed free throws.

  ([Dimers, 2026-10-16](https://www.dimers.com/nba/news/nba-player-props-bans-regulated-betting-2026-27); [ESPN, 2025-10-30](https://www.espn.com/nba/story/_/id/46785871/nba-books-review-most-vulnerable-bets-wager-limits))
- **Adjacent evidence.**
  - Assists props carry higher median margins that can exceed 7%. This matters for guard DDs that depend on assists. ([LowJuiceSportsbooks](https://lowjuicesportsbooks.com/prop-market-margins-in-mlb-and-nba/))
  - NBA overs lost about 8.7% at close vs 3.8% for unders. [UNVERIFIED EXTRACT] ([Sickfade](https://sickfade.com/overs-vs-unders))
  - NBA over hit rates fall from 46.7% in games decided by 7 or fewer to 40.9% in games decided by 20 or more. ([DataStreak](https://datastreak.com/insights/nba-blowouts-4th-quarter-props))

### Inferences
- **The joint distribution is the test.** A DD "yes" is P(stat A >= 10 AND stat B >= 10). Minutes drive both stats, so they are positively correlated.
  - A model that multiplies the two marginal probabilities understates DD probability.
  - A model that ignores minutes variance (blowouts, foul trouble, in-game injury) overstates it for the most likely DDs.

  The DD price is therefore a test of the book's joint-distribution model, the kind of derivative Miller and Davidow describe as added faster than it can be priced.
- **Worst zone for the math.** The most likely DDs, priced -250 to -400, sit where the break-even math in Q3 is least forgiving and where blowout minutes risk for favored starters concentrates.
- **Estimating hold on one-sided boards.** Where only a "yes" price is posted, hold cannot be read from the board. It has to be estimated by deriving a fair DD probability from the component points, rebounds and assists markets at a sharper book.
- **Which CLV to trust.** Under Unabated's rule of thumb, if no sharp book lists DD markets, CLV on DD bets is weak evidence. CLV on the component props (rebounds, points) is the more defensible check.
- **Sharpness vs rebounds and assists over/unders.** No source compares DD sharpness to rebounds or assists O/U markets directly. The structural expectation follows from Unabated and Miller and Davidow: the component O/U markets get more two-way action and price discovery than a yes-only derivative. The DD market is likely softer but lower-limit and higher-margin.

### Gaps
- **No study found** of:
  - whether US books post a "No" side on NBA DD markets;
  - typical DD hold or DD bet limits;
  - DD-specific account limiting;
  - DD hit rates vs implied probability by price bucket (favorite-longshot pattern).
- **Not confirmed** whether Pinnacle, Circa or exchanges (Kalshi, ProphetX, Novig) list NBA DD markets.

## Q5. What do experienced prop bettors report about FanDuel and other US books limiting prop winners, and how does that cap the economic value of an edge?

### Takeaway
Regulator data and operator statements put the share of limited accounts under 1%: Massachusetts 0.64%, DraftKings "under 0.15%". But the limited group skews toward bettors who beat the closing line. Their stakes are commonly cut to 1% to 24% of the default, and some bettors report caps in single dollars or cents. A FanDuel representative publicly acknowledged limiting customers who simply have a better model. At heavy DD prices, a real 2 to 3 point edge capped at $25 to $100 per bet is worth roughly $330 to $2,100 per season [COMPUTED].

### Cited Findings
- **Massachusetts Gaming Commission data** (reported 2025-09-30):
  - About 0.64% of accounts were limited.
  - 57.6% of limited accounts were restricted to 1% to 24% of the default maximum, and 12.7% to under 1% (the 12.7% figure is an [UNVERIFIED EXTRACT] of SBC Americas, which returned 403).
  - Bettors who consistently beat the closing line were more likely to have their stake factor lowered. Those who did not were more likely to have it raised.
  - Accounts with raised limits were far more likely to be VIPs.
  - Sources conflict on the period: SBC Americas and SportsBettingDime describe Dec 2024 to Sep 2025, while Covers gives a 2024-12-10 snapshot.
  - There is no breakdown by bet type, sport or props.

  ([SBC Americas](https://sbcamericas.com/2025/09/30/mgc-data-limiting-bettors-ma/); [Covers](https://www.covers.com/industry/massachusetts-limiting-sports-betting-prediction-markets-exchanges-sharps-box-september-2025); [SportsBettingDime](https://www.sportsbettingdime.com/news/industry/analysis-massachusetts-sports-betting-player-limitation-numbers-are-low-but-consistent-winners-more-likely-to-be-limited/))
- **Notice rule.** Massachusetts then became the first state to require sportsbooks to notify limited bettors, with a reason and the affected markets. Reports give a 2026-06-01 effective date. ([CasinoBeats](https://casinobeats.com/2025/10/01/massachusetts-gaming-commission-sportsbooks-notify-bettors-limited/); [SCCG, 2026-06-02](https://sccgmanagement.com/sccg-articles/2026/06/02/massachusetts-becomes-first-state-mandate-specific/); [World Casino Directory](https://news.worldcasinodirectory.com/massachusetts-sets-sportsbook-limit-notice-rule-for-june-1-121877))
- **CBS News (2026-10-26):**
  - DraftKings says customer-specific limits apply to under 0.15% of accounts and are based on behavior, not on winning or losing.
  - A professional bettor was limited to $25 per bet at DraftKings, and from $1,000 to $5,000 per game down to $5 at BetMGM.
  - A DraftKings ticket showed a 49-cent maximum on an NBA Cup bet.
  - Big winners are often capped under $20.

  ([CBS News](https://www.cbsnews.com/news/online-betting-apps-losers-perks-limiting-winners/))
- **FanDuel.**
  - Spanky (Gadoon Kyrollos, so "Spanky and Gadoon" are one person) posted on 2024-09-11 that FanDuel's Cory Fox acknowledged limiting customers who have a better model or who arbitrage. ([X post](https://x.com/spanky/status/1833889459969970514); [Gambling911](https://www.gambling911.com/gambling/real-bookmakers-would-roll-out-red-carpet-for-arbitrage-bettors-091224.html); [The Ringer profile](https://www.theringer.com/2019/06/05/gambling/sports-betting-bettors-sharps-kicked-out-spanky-william-hill-new-jersey))
  - FanDuel separately said fewer than 1% of its players are limited; the date was not shown. ([Yahoo](https://www.yahoo.com/news/11-billion-online-sportsbook-bubble-150000397.html))
  - Wyoming regulators reported under 1% of customers limited. ([SportsBettingDime](https://www.sportsbettingdime.com/news/industry/wyoming-gaming-commission-finds-no-concerning-sports-betting-limitation-data/))
- **Props specifically.**
  - ESPN (2025-10-30) reports that prop limits are typically lower than spread limits on the same game. It also reports the NBA and partner books were still discussing limits for the bets most open to manipulation. ([ESPN](https://www.espn.com/nba/story/_/id/46785871/nba-books-review-most-vulnerable-bets-wager-limits))
  - Unabated says getting limited on props is easy for anyone who looks sharp. ([Unabated](https://unabated.com/content/videos/you-re-using-closing-line-value-wrong))
  - The Ringer (2019) reported that William Hill NJ took $5,000 bets on first-inning MLB props from Spanky before limiting him. ([The Ringer](https://www.theringer.com/2019/06/05/gambling/sports-betting-bettors-sharps-kicked-out-spanky-william-hill-new-jersey))
- **Time to limit.** Blog guides circulate estimates of a few weeks at DraftKings and FanDuel, but concede no controlled study exists. Treat these as folklore. ([BetSuite](https://betsuite.ai/blog/how-to-avoid-getting-limited); [BettingSite.net](https://www.bettingsite.net/blog/sportsbook-limiting-winning-bettors/))
- **Kaunitz et al.** (soccer, 2015-2016):
  - Within a few months of real-money betting, books capped stakes at 2,428 yen against 5,000 intended (William Hill), $11.11 (Interwetten), $1.25 (Sportingbet) and $10.45 (Betway).
  - Some wagers required manual review.
  - The authors stopped. They noted that limits also bias which bets get filled.

  ([arXiv](https://arxiv.org/abs/1710.02824))
- **Exchanges and prediction markets.** Covers quotes consultant Dustin Gouker describing prediction markets as exchanges where limits are not applied ([Covers](https://www.covers.com/industry/massachusetts-limiting-sports-betting-prediction-markets-exchanges-sharps-box-september-2025)). SmartStake's 2026 MLB study ranked Kalshi and ProphetX first on closing accuracy, which implies less mispricing left to exploit there ([SmartStake](https://www.smartstake.app/learn/sharpest-sportsbooks-mlb-player-props)).

#### Economic cap [COMPUTED]
Expected season profit = number of bets x maximum stake x ROI.

| Price and edge | ROI | Bets | $25 max | $100 max | $500 max | $1,000 max |
|---|---|---|---|---|---|---|
| -300, +2 pts | 2.67% | 495 | $330 | $1,322 | $6,608 | $13,216 |
| -300, +2 pts | 2.67% | 330 | $220 | $881 | $4,406 | $8,811 |
| -300, +3 pts | 4.0% | 495 | $495 | $1,980 | $9,900 | $19,800 |
| -250, +3 pts | 4.2% | 495 | $520 | $2,079 | $10,395 | $20,790 |

For comparison, an Unabated NBA prop simulator was reported at about $249 per month on top of a plan. ([BetSmart review](https://www.betsmart.co/tool-reviews/unabated))

### Inferences
- **Account life is the binding constraint.** For a winning retail prop bettor the limit is account life and stake caps, not model accuracy. The MGC data say CLV beaters are the ones most likely to be limited, so demonstrating an edge through CLV is also what triggers limits.
- **Small caps erase the value.** At heavy DD prices, a $25 to $100 cap makes even a real 2 to 3 point edge worth about the same as, or less than, one season of common tool subscriptions.
- **Practical paths.** Options are to spread volume across books, to use exchanges or prediction markets where available (no limiting, but sharper prices), or to treat the bot as a research and CLV-measurement tool rather than an income source until a forward record exists.

### Gaps
- **No prop-specific limiting data.** I found no public data on prop-specific limit rates, time to limit, or typical prop caps at FanDuel or DraftKings.
- **Venue unconfirmed.** I did not confirm where Cory Fox made the remark Spanky cited. A Massachusetts Gaming Commission roundtable on limits is likely but unverified.
- **No operator splits.** There are no operator-level MGC splits and no DD- or prop-specific limit data.
