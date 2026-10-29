# Features v1

This file is written by `tools/build_dataset.py`. It documents every model feature in `data/features/dataset_v1.parquet`. The ordered feature list is in `data/features/dataset_v1_features.json`.

## Rows and target

- One row per player-game where the player recorded minutes > 0 and had at least 5 earlier played games in the data (any season). The data starts with the 2017-18 season.
- Built from 301430 raw box score rows. Duplicate (game_id, athlete_id) rows dropped: 0. All-Star and Rising Stars exhibition games dropped: 17 games (357 rows); ESPN codes them as season_type 2 with non-franchise team ids. Second ESPN athlete ids for the same player in the same game (same team and display name) dropped: 36 rows, 31 of them played rows (mostly 2018-19). Games dropped because a team had two games on one date: [401161536] (a corrupted 2019-20 timestamp).
- Played rows before the 5-game filter: 246172. Final table: 239334 rows and 176 columns, of which 155 are model features (7 with the abs_ prefix).
- Target `dd` = 1 when at least two of points, rebounds, assists, steals, blocks are 10 or more. `td` (three or more) is kept for reference and is not modeled.
- All season types are kept. `is_playoff` marks playoffs (3) and play-in (5).
- Team totals come from team_box. 12 team-game rows (the six 2020-21 play-in games) are missing from team_box and have no played rows in the player box; they count for scores, point differential, and schedule features, and are skipped inside box-stat windows (a window mean divides by the games that have stats). 2 team-game rows exist only in team_box; they count for team features but have no player rows. Roster windows (abs_, rank, share) use the team-games that have played rows.
- The abs_ regular window runs across seasons, as all N-game windows do. In each team's first games of a season it therefore counts last season's regulars who left the team and have not yet played for a new team as absent. Measured on team-games in this dataset: mean abs_n_absent_regulars is 2.60 in a team's first game of a season, 1.29 in games 2 to 5, and 0.90 from game 6 on.

## Leakage discipline

- Rows are sorted by game_date_time then game_id before any shift or window. Player features group by athlete_id; team features group by team_id.
- Every window is computed over earlier rows only (an exclusive cumulative sum, equivalent to shifting by one game before the window). A player plays at most one game per date, so earlier rows are earlier dates. The build asserts this.
- Rolling N-game windows run across seasons. Season-to-date windows reset at the `season` column. N-game windows with fewer than N earlier games use the games available.
- Features prefixed `abs_` are lineup-known: they use who played in the current game. The trainer drops them for C_noabs. The team rank features use only pre-game regulars, so C_noabs stays lineup-free.
- The build recomputes dd_rate_l5, min_l5, reb_l20, min_sd_l20, pts_ewm, and pts_szn with pandas groupby, shift, and rolling and asserts they match the vectorized values.

## Columns that are not features

Identifiers and current-game outcomes are stored for evaluation only: game_id, season, season_type, game_date, game_date_time, athlete_id, athlete_display_name, team_id, team_abbreviation, opponent_team_id, home_away, minutes, points, rebounds, assists, steals, blocks, starter, dd, td, and career_dd_rate_pre (the player's dd rate over all seasons before this one, used only as the Baseline A fallback prior).

## Player form (100)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `min_l5` | Mean minutes per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_l5` | Mean points per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_l5` | Mean rebounds per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_l5` | Mean assists per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `stl_l5` | Mean steals per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `blk_l5` | Mean blocks per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fga_l5` | Mean field goal attempts per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fta_l5` | Mean free throw attempts per played game. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_pm_l5` | Points per minute: window sum of points divided by window sum of minutes. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_pm_l5` | Rebounds per minute: window sum of rebounds divided by window sum of minutes. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_pm_l5` | Assists per minute: window sum of assists divided by window sum of minutes. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `dd_rate_l5` | Share of played games with a double-double (dd = 1). | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb8_rate_l5` | Share of played games with rebounds >= 8. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast8_rate_l5` | Share of played games with assists >= 8. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts8_rate_l5` | Share of played games with points >= 8. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb10_rate_l5` | Share of played games with rebounds >= 10. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast10_rate_l5` | Share of played games with assists >= 10. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts10_rate_l5` | Share of played games with points >= 10. | last 5 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `min_l10` | Mean minutes per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_l10` | Mean points per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_l10` | Mean rebounds per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_l10` | Mean assists per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `stl_l10` | Mean steals per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `blk_l10` | Mean blocks per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fga_l10` | Mean field goal attempts per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fta_l10` | Mean free throw attempts per played game. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_pm_l10` | Points per minute: window sum of points divided by window sum of minutes. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_pm_l10` | Rebounds per minute: window sum of rebounds divided by window sum of minutes. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_pm_l10` | Assists per minute: window sum of assists divided by window sum of minutes. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `dd_rate_l10` | Share of played games with a double-double (dd = 1). | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb8_rate_l10` | Share of played games with rebounds >= 8. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast8_rate_l10` | Share of played games with assists >= 8. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts8_rate_l10` | Share of played games with points >= 8. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb10_rate_l10` | Share of played games with rebounds >= 10. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast10_rate_l10` | Share of played games with assists >= 10. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts10_rate_l10` | Share of played games with points >= 10. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `min_l20` | Mean minutes per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_l20` | Mean points per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_l20` | Mean rebounds per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_l20` | Mean assists per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `stl_l20` | Mean steals per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `blk_l20` | Mean blocks per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fga_l20` | Mean field goal attempts per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fta_l20` | Mean free throw attempts per played game. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_pm_l20` | Points per minute: window sum of points divided by window sum of minutes. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_pm_l20` | Rebounds per minute: window sum of rebounds divided by window sum of minutes. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_pm_l20` | Assists per minute: window sum of assists divided by window sum of minutes. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `dd_rate_l20` | Share of played games with a double-double (dd = 1). | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb8_rate_l20` | Share of played games with rebounds >= 8. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast8_rate_l20` | Share of played games with assists >= 8. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts8_rate_l20` | Share of played games with points >= 8. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb10_rate_l20` | Share of played games with rebounds >= 10. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast10_rate_l20` | Share of played games with assists >= 10. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts10_rate_l20` | Share of played games with points >= 10. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `min_szn` | Mean minutes per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `pts_szn` | Mean points per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `reb_szn` | Mean rebounds per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `ast_szn` | Mean assists per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `stl_szn` | Mean steals per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `blk_szn` | Mean blocks per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `fga_szn` | Mean field goal attempts per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `fta_szn` | Mean free throw attempts per played game. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `pts_pm_szn` | Points per minute: window sum of points divided by window sum of minutes. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `reb_pm_szn` | Rebounds per minute: window sum of rebounds divided by window sum of minutes. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `ast_pm_szn` | Assists per minute: window sum of assists divided by window sum of minutes. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `dd_rate_szn` | Share of played games with a double-double (dd = 1). | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `reb8_rate_szn` | Share of played games with rebounds >= 8. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `ast8_rate_szn` | Share of played games with assists >= 8. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `pts8_rate_szn` | Share of played games with points >= 8. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `reb10_rate_szn` | Share of played games with rebounds >= 10. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `ast10_rate_szn` | Share of played games with assists >= 10. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `pts10_rate_szn` | Share of played games with points >= 10. | season to date (played games this season) | Shifted one played game; resets at the season column; earlier games only. |
| `min_ewm` | Mean minutes per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_ewm` | Mean points per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_ewm` | Mean rebounds per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_ewm` | Mean assists per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `stl_ewm` | Mean steals per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `blk_ewm` | Mean blocks per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fga_ewm` | Mean field goal attempts per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `fta_ewm` | Mean free throw attempts per played game. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts_pm_ewm` | Points per minute: window sum of points divided by window sum of minutes. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_pm_ewm` | Rebounds per minute: window sum of rebounds divided by window sum of minutes. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_pm_ewm` | Assists per minute: window sum of assists divided by window sum of minutes. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `dd_rate_ewm` | Share of played games with a double-double (dd = 1). | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb8_rate_ewm` | Share of played games with rebounds >= 8. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast8_rate_ewm` | Share of played games with assists >= 8. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts8_rate_ewm` | Share of played games with points >= 8. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb10_rate_ewm` | Share of played games with rebounds >= 10. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast10_rate_ewm` | Share of played games with assists >= 10. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `pts10_rate_ewm` | Share of played games with points >= 10. | exponential weights, half-life 8 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `min_sd_l20` | Sample standard deviation of minutes (volatility); needs 2 or more games. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `reb_sd_l20` | Sample standard deviation of rebounds (volatility); needs 2 or more games. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `ast_sd_l20` | Sample standard deviation of assists (volatility); needs 2 or more games. | last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `last_min` | Value of minutes in the player's previous played game. | previous played game | Shifted one played game: only the player's earlier played games (earlier dates). |
| `last_pts` | Value of points in the player's previous played game. | previous played game | Shifted one played game: only the player's earlier played games (earlier dates). |
| `last_reb` | Value of rebounds in the player's previous played game. | previous played game | Shifted one played game: only the player's earlier played games (earlier dates). |
| `last_ast` | Value of assists in the player's previous played game. | previous played game | Shifted one played game: only the player's earlier played games (earlier dates). |
| `last_starter` | Value of the starter flag (1 = started) in the player's previous played game. | previous played game | Shifted one played game: only the player's earlier played games (earlier dates). |
| `starter_rate_l10` | Share of played games started. | last 10 played games | Shifted one played game: only the player's earlier played games (earlier dates). |
| `min_trend` | Minutes trend: mean minutes over the last 5 minus mean minutes over the last 20 played games. | last 5 and last 20 played games | Shifted one played game: only the player's earlier played games (earlier dates). |

## Player history (8)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `gp_season` | Games played this season before this game. | season to date | Shifted one played game; resets at the season column; earlier games only. |
| `games_played_career` | Played games before this game across all seasons in the data (the data starts with 2017-18, so longer careers are truncated there). | all earlier seasons in the data | Shifted one played game: only the player's earlier played games (earlier dates). |
| `dd_count_season` | Double-doubles this season before this game. | season to date | Shifted one played game; resets at the season column; earlier games only. |
| `prev_games` | Played games in the previous season (all season types). | previous season | Previous season (season - 1) only; NaN when the player has no played games that season. |
| `prev_min` | Mean minutes per played game in the previous season. | previous season | Previous season (season - 1) only; NaN when the player has no played games that season. |
| `prev_dd_rate` | Double-double rate in the previous season. | previous season | Previous season (season - 1) only; NaN when the player has no played games that season. |
| `prev_reb_pm` | Rebounds per minute in the previous season. | previous season | Previous season (season - 1) only; NaN when the player has no played games that season. |
| `prev_ast_pm` | Assists per minute in the previous season. | previous season | Previous season (season - 1) only; NaN when the player has no played games that season. |

## Schedule (8)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `days_rest` | Days since the player's previous played game, capped at 10. | previous played game | Earlier game dates only; the current date is known before tip. |
| `b2b` | 1 if the player's previous played game was the day before. | previous played game | Earlier game dates only; the current date is known before tip. |
| `games_last7` | Player's played games in the 7 days before this game's date (dates d-7 to d-1). | 7 calendar days | Earlier game dates only; the current date is known before tip. |
| `home` | 1 if the player's team is the home team (ESPN home_away). | current game | Known before tip. |
| `is_playoff` | 1 if season_type is 3 (playoffs) or 5 (play-in). | current game | Known before tip. |
| `team_days_rest` | Days since the team's previous game, capped at 10. | team's previous game | Team schedule; earlier team game dates only. |
| `team_b2b` | 1 if the team played the day before. | team's previous game | Team schedule; earlier team game dates only. |
| `team_game_num` | Team's game number this season including this game (1 = first game). | season to date | Team schedule; earlier team game dates only. |

## Position (1)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `position` | ESPN athlete_position_abbreviation as a LightGBM native categorical (C, F, G, PF, PG, SF, SG; missing or NA left empty). | current roster listing | Static roster attribute, known before tip. |

## Team context (31)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `team_poss_l10` | Team possessions per game, fga - oreb + turnovers + 0.44 * fta (pace proxy). | team's last 10 games | Team's earlier games only (team game sequence shifted one game). |
| `opp_poss_l10` | Opponent's own possessions per game (pace proxy). | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_pd_l10` | Team point differential per game (strength proxy). | team's last 10 games | Team's earlier games only (team game sequence shifted one game). |
| `opp_pd_l10` | Opponent point differential per game. | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `pd_diff_l10` | team_pd minus opp_pd for the same window (expected margin proxy for blowout risk). | team's last 10 games | Team's earlier games only (team game sequence shifted one game). Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_reb_l10` | Rebounds per game recorded against the opponent by its opponents (player-credited oreb + dreb). | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_ast_l10` | Assists per game recorded against the opponent by its opponents. | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_pts_l10` | Points per game allowed by the opponent. | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_dreb_rate_l10` | Opponent defensive rebound rate: opponent dreb / (opponent dreb + its opponents' oreb), as a ratio of window sums. | opponent's last 10 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_poss_l20` | Team possessions per game, fga - oreb + turnovers + 0.44 * fta (pace proxy). | team's last 20 games | Team's earlier games only (team game sequence shifted one game). |
| `opp_poss_l20` | Opponent's own possessions per game (pace proxy). | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_pd_l20` | Team point differential per game (strength proxy). | team's last 20 games | Team's earlier games only (team game sequence shifted one game). |
| `opp_pd_l20` | Opponent point differential per game. | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `pd_diff_l20` | team_pd minus opp_pd for the same window (expected margin proxy for blowout risk). | team's last 20 games | Team's earlier games only (team game sequence shifted one game). Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_reb_l20` | Rebounds per game recorded against the opponent by its opponents (player-credited oreb + dreb). | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_ast_l20` | Assists per game recorded against the opponent by its opponents. | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_pts_l20` | Points per game allowed by the opponent. | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_dreb_rate_l20` | Opponent defensive rebound rate: opponent dreb / (opponent dreb + its opponents' oreb), as a ratio of window sums. | opponent's last 20 games | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_poss_szn` | Team possessions per game, fga - oreb + turnovers + 0.44 * fta (pace proxy). | team's games this season to date | Team's earlier games only (team game sequence shifted one game). |
| `opp_poss_szn` | Opponent's own possessions per game (pace proxy). | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_pd_szn` | Team point differential per game (strength proxy). | team's games this season to date | Team's earlier games only (team game sequence shifted one game). |
| `opp_pd_szn` | Opponent point differential per game. | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `pd_diff_szn` | team_pd minus opp_pd for the same window (expected margin proxy for blowout risk). | team's games this season to date | Team's earlier games only (team game sequence shifted one game). Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_reb_szn` | Rebounds per game recorded against the opponent by its opponents (player-credited oreb + dreb). | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_ast_szn` | Assists per game recorded against the opponent by its opponents. | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_allow_pts_szn` | Points per game allowed by the opponent. | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `opp_dreb_rate_szn` | Opponent defensive rebound rate: opponent dreb / (opponent dreb + its opponents' oreb), as a ratio of window sums. | opponent's games this season to date | Opponent's earlier games only (opponent game sequence shifted one game). |
| `team_reb_share_l20` | Player's rebounds for this team over the team's last 20 games divided by the team's total player rebounds in those games (0 when he did not play in them). | team's last 20 games | Team's earlier games only. |
| `team_ast_share_l20` | Same as team_reb_share_l20 for assists. | team's last 20 games | Team's earlier games only. |
| `team_reb_rank` | Player's rank by rolling rebounds per game (his last 20 played games) among the team's pre-game regulars (regular definition as in the abs_ features) plus the player; 1 = highest. Teammate values are as of the day before. | last 20 played games of each player | Lineup-free: regulars and their values come from earlier games only; does not use who plays in the current game. |
| `team_ast_rank` | Same as team_reb_rank for assists per game. | last 20 played games of each player | Lineup-free: regulars and their values come from earlier games only; does not use who plays in the current game. |

## Teammate absence (7)

| Name | Definition | Window | Leakage note |
|---|---|---|---|
| `abs_n_absent_regulars` | Number of regulars who did not play this game. Regulars are players averaging >= 15 minutes per team game over the team's last 10 games (missed games count as 0) whose latest played game before this date was for this team. Absent means no played row (minutes > 0) for this team in the current game. | team's last 10 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_absent_minutes_share` | Sum of absent regulars' average minutes per team game divided by 240. | team's last 10 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_absent_rebounds_pg` | Sum of absent regulars' rebounds per team game. | team's last 10 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_absent_assists_pg` | Sum of absent regulars' assists per team game. | team's last 10 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_absent_points_pg` | Sum of absent regulars' points per team game. | team's last 10 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_top_rebounder_absent` | 1 if the team's leading rebounder by total rebounds over the team's last 20 games (still on the team) did not play this game. | team's last 20 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
| `abs_top_assister_absent` | Same as abs_top_rebounder_absent for assists. | team's last 20 games | LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's earlier games only. Excluded from C_noabs. |
