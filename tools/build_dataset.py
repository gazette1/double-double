"""
build_dataset.py: build the v1 player-game feature table for NBA double-double modeling.

Inputs : data/raw/hoopr/player_box_{Y}.parquet and team_box_{Y}.parquet, Y = 2018..2027 (season end year).
Outputs: data/features/dataset_v1.parquet, data/features/dataset_v1_features.json, docs/FEATURES_v1.md.
Run    : PYTHONUTF8=1 python tools/build_dataset.py

Leakage rule: every feature of a player-game uses only games on earlier dates. Player features shift
the player's played-game sequence by one game before any window; team features shift the team's game
sequence; opponent features use the opponent's earlier games. The abs_ features are the documented
exception: they use who played in the current game (lineup-known) and can be switched off.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATASET_PATH, DOCS_DIR, FEATURE_LIST_PATH, FEATURES_DIR, MIN_PRIOR_GAMES, SEED,
                    add_targets, drop_alias_duplicates, exhibition_mask, load_player_box, load_team_box,
                    prior_cumsum, safe_div, same_date_conflict_games, to_markdown, window_from_prior,
                    window_sums_nan, within_group_index)

EWM_HALFLIFE = 8
REST_CAP = 10
HCA = 2.5  # home-court points in the expected-margin proxy (game-state features, adopted 2026-10-30)
REGULAR_MIN = 15.0
POSITIONS = ["C", "F", "G", "PF", "PG", "SF", "SG"]
DOC = []  # feature documentation registry, written to docs/FEATURES_v1.md


def doc(name, group, definition, window, leakage):
    DOC.append({"name": name, "group": group, "definition": definition, "window": window,
                "leakage": leakage})


def log(msg, t0):
    print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)


# --------------------------------------------------------------------------------------------
# Loading and cleaning
# --------------------------------------------------------------------------------------------
def load_clean():
    info = {}
    pb = load_player_box()
    tb = load_team_box()
    info["raw_player_rows"] = len(pb)
    pb = pb.drop_duplicates(["game_id", "athlete_id"], keep="first")
    tb = tb.drop_duplicates(["game_id", "team_id"], keep="first")
    info["duplicate_player_rows_dropped"] = info["raw_player_rows"] - len(pb)
    ex = exhibition_mask(pb)
    info["exhibition_games_dropped"] = int(pb.loc[ex, "game_id"].nunique())
    info["exhibition_player_rows_dropped"] = int(ex.sum())
    pb = pb[~ex]
    tb = tb[~exhibition_mask(tb)]
    before = pb[pb["minutes"] > 0].shape[0]
    pb, n_alias = drop_alias_duplicates(pb)
    info["alias_duplicate_rows_dropped"] = n_alias
    info["alias_duplicate_played_rows_dropped"] = int(before - pb[pb["minutes"] > 0].shape[0])
    both = pd.concat([pb[["game_id", "team_id", "game_date", "game_date_time"]],
                      tb[["game_id", "team_id", "game_date", "game_date_time"]]], ignore_index=True)
    conflict = same_date_conflict_games(both)
    info["same_date_conflict_games_dropped"] = sorted(int(g) for g in conflict)
    pb = pb[~pb["game_id"].isin(conflict)].reset_index(drop=True)
    tb = tb[~tb["game_id"].isin(conflict)].reset_index(drop=True)
    info["player_rows_after_cleaning"] = len(pb)
    return pb, tb, info


# --------------------------------------------------------------------------------------------
# Player form and history
# --------------------------------------------------------------------------------------------
PF_STATS = [("min", "minutes", "minutes"), ("pts", "points", "points"), ("reb", "rebounds", "rebounds"),
            ("ast", "assists", "assists"), ("stl", "steals", "steals"), ("blk", "blocks", "blocks"),
            ("fga", "field_goals_attempted", "field goal attempts"),
            ("fta", "free_throws_attempted", "free throw attempts")]
PF_INDS = [("dd", "a double-double (dd = 1)"), ("reb8", "rebounds >= 8"), ("ast8", "assists >= 8"),
           ("pts8", "points >= 8"), ("reb10", "rebounds >= 10"), ("ast10", "assists >= 10"),
           ("pts10", "points >= 10")]
PF_RATES = [("pts", "points"), ("reb", "rebounds"), ("ast", "assists")]
WIN_LABEL = {"l5": "last 5 played games", "l10": "last 10 played games", "l20": "last 20 played games",
             "szn": "season to date (played games this season)",
             "ewm": f"exponential weights, half-life {EWM_HALFLIFE} played games"}
LEAK_PLAYER = "Shifted one played game: only the player's earlier played games (earlier dates)."
LEAK_SZN = "Shifted one played game; resets at the season column; earlier games only."


def ewm_prior(frame, keys, halflife):
    """EWM mean of each column over earlier rows of the same group (group-sorted frame, RangeIndex)."""
    ew = frame.groupby(keys, sort=False).ewm(halflife=halflife).mean()
    ew = ew.reset_index(level=0, drop=True).sort_index()
    return ew.groupby(keys, sort=False).shift(1)


def player_form(p):
    """p: played rows sorted by athlete_id, game_date_time, game_id with a RangeIndex."""
    aid = p["athlete_id"].to_numpy()
    k = within_group_index(aid)
    skey = aid.astype(np.int64) * 10000 + p["season"].to_numpy()
    ks = within_group_index(skey)
    base = pd.DataFrame({
        "min": p["minutes"], "pts": p["points"], "reb": p["rebounds"], "ast": p["assists"],
        "stl": p["steals"], "blk": p["blocks"], "fga": p["field_goals_attempted"],
        "fta": p["free_throws_attempted"], "dd": p["dd"],
        "reb8": p["rebounds"] >= 8, "ast8": p["assists"] >= 8, "pts8": p["points"] >= 8,
        "reb10": p["rebounds"] >= 10, "ast10": p["assists"] >= 10, "pts10": p["points"] >= 10,
        "starter": p["starter"].astype(bool),
        "min_sq": p["minutes"] ** 2, "reb_sq": p["rebounds"] ** 2, "ast_sq": p["assists"] ** 2,
    }).astype(np.float64)
    ci = {c: i for i, c in enumerate(base.columns)}
    V = base.to_numpy()
    P = prior_cumsum(V, aid)
    Ps = prior_cumsum(V, skey)
    win = {tag: window_from_prior(P, k, n) for tag, n in [("l5", 5), ("l10", 10), ("l20", 20)]}
    win["szn"] = (Ps, ks.astype(np.float64))
    ew_cols = [s for s, _, _ in PF_STATS] + [s for s, _ in PF_INDS]
    ew = ewm_prior(base[ew_cols], aid, EWM_HALFLIFE)

    out = {}
    for tag in ["l5", "l10", "l20", "szn", "ewm"]:
        if tag == "ewm":
            def mean_of(c):
                return ew[c].to_numpy()

            def ratio(a, b):
                return safe_div(ew[a].to_numpy(), ew[b].to_numpy())
        else:
            S, cnt = win[tag]

            def mean_of(c, S=S, cnt=cnt):
                return safe_div(S[:, ci[c]], cnt)

            def ratio(a, b, S=S):
                return safe_div(S[:, ci[a]], S[:, ci[b]])
        leak = LEAK_SZN if tag == "szn" else LEAK_PLAYER
        for short, _, label in PF_STATS:
            name = f"{short}_{tag}"
            out[name] = mean_of(short)
            doc(name, "Player form", f"Mean {label} per played game.", WIN_LABEL[tag], leak)
        for short, label in PF_RATES:
            name = f"{short}_pm_{tag}"
            out[name] = ratio(short, "min")
            doc(name, "Player form",
                f"{label.capitalize()} per minute: window sum of {label} divided by window sum of minutes.",
                WIN_LABEL[tag], leak)
        for short, label in PF_INDS:
            name = f"{short}_rate_{tag}"
            out[name] = mean_of(short)
            doc(name, "Player form", f"Share of played games with {label}.", WIN_LABEL[tag], leak)

    S20, c20 = win["l20"]
    for short, label in [("min", "minutes"), ("reb", "rebounds"), ("ast", "assists")]:
        s, ss = S20[:, ci[short]], S20[:, ci[f"{short}_sq"]]
        var = safe_div(ss - safe_div(s ** 2, c20), c20 - 1)
        var = np.where(c20 >= 2, np.maximum(var, 0.0), np.nan)
        out[f"{short}_sd_l20"] = np.sqrt(var)
        doc(f"{short}_sd_l20", "Player form",
            f"Sample standard deviation of {label} (volatility); needs 2 or more games.",
            WIN_LABEL["l20"], LEAK_PLAYER)

    prev_ok = k >= 1
    for short, col, label in [("min", "min", "minutes"), ("pts", "pts", "points"), ("reb", "reb", "rebounds"),
                              ("ast", "ast", "assists"), ("starter", "starter", "the starter flag (1 = started)")]:
        arr = np.full(len(p), np.nan)
        arr[1:] = V[:-1, ci[col]]
        arr[~prev_ok] = np.nan
        out[f"last_{short}"] = arr
        doc(f"last_{short}", "Player form", f"Value of {label} in the player's previous played game.",
            "previous played game", LEAK_PLAYER)
    S10, c10 = win["l10"]
    out["starter_rate_l10"] = safe_div(S10[:, ci["starter"]], c10)
    doc("starter_rate_l10", "Player form", "Share of played games started.", WIN_LABEL["l10"], LEAK_PLAYER)
    out["min_trend"] = out["min_l5"] - out["min_l20"]
    doc("min_trend", "Player form",
        "Minutes trend: mean minutes over the last 5 minus mean minutes over the last 20 played games.",
        "last 5 and last 20 played games", LEAK_PLAYER)

    # player history counters
    out["gp_season"] = ks.astype(np.float64)
    doc("gp_season", "Player history", "Games played this season before this game.", "season to date", LEAK_SZN)
    out["games_played_career"] = k.astype(np.float64)
    doc("games_played_career", "Player history",
        "Played games before this game across all seasons in the data (the data starts with 2017-18, "
        "so longer careers are truncated there).", "all earlier seasons in the data", LEAK_PLAYER)
    out["dd_count_season"] = Ps[:, ci["dd"]]
    doc("dd_count_season", "Player history", "Double-doubles this season before this game.", "season to date",
        LEAK_SZN)
    return out, k, ks


def player_history(p):
    """Prior-season aggregates (season - 1) and career dd rate before this season (Baseline A fallback)."""
    ps = p.groupby(["athlete_id", "season"], as_index=False).agg(
        games=("minutes", "size"), min_sum=("minutes", "sum"), dd_sum=("dd", "sum"),
        reb_sum=("rebounds", "sum"), ast_sum=("assists", "sum"))
    prev = ps.assign(season=ps["season"] + 1)
    prev["prev_games"] = prev["games"].astype(np.float64)
    prev["prev_min"] = prev["min_sum"] / prev["games"]
    prev["prev_dd_rate"] = prev["dd_sum"] / prev["games"]
    prev["prev_reb_pm"] = safe_div(prev["reb_sum"], prev["min_sum"])
    prev["prev_ast_pm"] = safe_div(prev["ast_sum"], prev["min_sum"])
    ps = ps.sort_values(["athlete_id", "season"])
    cum = ps.groupby("athlete_id")[["games", "dd_sum"]].cumsum() - ps[["games", "dd_sum"]]
    ps["career_dd_rate_pre"] = safe_div(cum["dd_sum"], cum["games"])
    m = p[["athlete_id", "season"]].merge(
        prev[["athlete_id", "season", "prev_games", "prev_min", "prev_dd_rate", "prev_reb_pm", "prev_ast_pm"]],
        on=["athlete_id", "season"], how="left").merge(
        ps[["athlete_id", "season", "career_dd_rate_pre"]], on=["athlete_id", "season"], how="left")
    assert len(m) == len(p)
    leak = "Previous season (season - 1) only; NaN when the player has no played games that season."
    doc("prev_games", "Player history", "Played games in the previous season (all season types).",
        "previous season", leak)
    doc("prev_min", "Player history", "Mean minutes per played game in the previous season.", "previous season",
        leak)
    doc("prev_dd_rate", "Player history", "Double-double rate in the previous season.", "previous season", leak)
    doc("prev_reb_pm", "Player history", "Rebounds per minute in the previous season.", "previous season", leak)
    doc("prev_ast_pm", "Player history", "Assists per minute in the previous season.", "previous season", leak)
    cols = ["prev_games", "prev_min", "prev_dd_rate", "prev_reb_pm", "prev_ast_pm"]
    return {c: m[c].to_numpy(np.float64) for c in cols}, m["career_dd_rate_pre"].to_numpy(np.float64)


def player_schedule(p, k):
    aid = p["athlete_id"].to_numpy()
    dn = p["game_date"].to_numpy().astype("datetime64[D]").astype(np.int64)
    prev = np.full(len(p), np.nan)
    prev[1:] = dn[:-1]
    prev[k == 0] = np.nan
    gap = dn - prev
    out = {"days_rest": np.minimum(gap, REST_CAP),
           "b2b": np.where(np.isnan(gap), np.nan, (gap == 1).astype(np.float64))}
    codes = pd.factorize(aid, sort=True)[0].astype(np.int64)
    key = codes * 100000 + dn
    assert np.all(np.diff(key) > 0), "player rows must be sorted with one game per player per date"
    lo = np.searchsorted(key, key - 7, side="left")
    out["games_last7"] = (np.arange(len(p)) - lo).astype(np.float64)
    leak = "Earlier game dates only; the current date is known before tip."
    doc("days_rest", "Schedule", f"Days since the player's previous played game, capped at {REST_CAP}.",
        "previous played game", leak)
    doc("b2b", "Schedule", "1 if the player's previous played game was the day before.", "previous played game",
        leak)
    doc("games_last7", "Schedule",
        "Player's played games in the 7 days before this game's date (dates d-7 to d-1).", "7 calendar days", leak)
    return out


# --------------------------------------------------------------------------------------------
# Team context
# --------------------------------------------------------------------------------------------
TEAM_STATS = ["field_goals_attempted", "free_throws_attempted", "offensive_rebounds", "defensive_rebounds",
              "assists", "turnovers"]
TEAM_WIN_LABEL = {"l10": "team's last 10 games", "l20": "team's last 20 games",
                  "szn": "team's games this season to date"}
OPP_WIN_LABEL = {"l10": "opponent's last 10 games", "l20": "opponent's last 20 games",
                 "szn": "opponent's games this season to date"}


def team_games(pb, tb):
    key = ["game_id", "team_id"]
    cols = ["game_id", "team_id", "opponent_team_id", "season", "season_type", "game_date", "game_date_time",
            "home_away", "team_score", "opponent_team_score"]
    pg = pb.drop_duplicates(key)[cols]
    tbx = tb.rename(columns={"team_home_away": "home_away"})
    only = tbx.merge(pg[key], on=key, how="left", indicator=True)
    only = only.loc[only["_merge"] == "left_only", cols]
    tg = pd.concat([pg, only], ignore_index=True)
    tg = tg.merge(tb[key + TEAM_STATS], on=key, how="left")
    # team-games missing from team_box: use player box sums only when the player box has played rows
    played_tg = pb[pb["minutes"] > 0].groupby(key, as_index=False)[TEAM_STATS].sum()
    miss = tg["field_goals_attempted"].isna()
    fill = tg.loc[miss, key].merge(played_tg, on=key, how="left")
    tg.loc[miss, TEAM_STATS] = fill[TEAM_STATS].to_numpy()
    n_fallback = int(fill["field_goals_attempted"].notna().sum())
    n_nostats = int(tg["field_goals_attempted"].isna().sum())
    assert not tg.duplicated(key).any()
    return tg, n_fallback, n_nostats, len(only)


def team_features(tg):
    tg = tg.copy()
    tg["poss"] = (tg["field_goals_attempted"] - tg["offensive_rebounds"] + tg["turnovers"]
                  + 0.44 * tg["free_throws_attempted"])
    tg["pd"] = tg["team_score"] - tg["opponent_team_score"]
    tg["pf"] = tg["team_score"]
    opp = tg[["game_id", "team_id", "offensive_rebounds", "defensive_rebounds", "assists", "team_score"]].rename(
        columns={"team_id": "opponent_team_id", "offensive_rebounds": "o_oreb", "defensive_rebounds": "o_dreb",
                 "assists": "o_ast", "team_score": "o_pts"})
    tg = tg.merge(opp, on=["game_id", "opponent_team_id"], how="left", indicator=True)
    assert (tg["_merge"] == "both").all(), "every team-game needs its opponent row"
    tg = tg.drop(columns="_merge")
    tg["allow_reb"] = tg["o_oreb"] + tg["o_dreb"]
    tg["allow_ast"] = tg["o_ast"]
    tg["allow_pts"] = tg["o_pts"]
    tg["dreb"] = tg["defensive_rebounds"]
    # a team-game whose own or opponent box stats are missing counts for scores but not for box-stat windows
    box_ok = tg[["poss", "dreb", "o_oreb", "allow_reb", "allow_ast"]].notna().all(axis=1)
    tg.loc[~box_ok, ["poss", "dreb", "o_oreb", "allow_reb", "allow_ast"]] = np.nan
    tg = tg.sort_values(["team_id", "game_date_time", "game_id"]).reset_index(drop=True)
    tid = tg["team_id"].to_numpy()
    kt = within_group_index(tid)
    tskey = tid.astype(np.int64) * 10000 + tg["season"].to_numpy()
    kts = within_group_index(tskey)
    vcols = ["poss", "pd", "pf", "allow_reb", "allow_ast", "allow_pts", "dreb", "o_oreb"]
    vi = {c: i for i, c in enumerate(vcols)}
    V = tg[vcols].to_numpy(np.float64)
    wins = {"l10": window_sums_nan(V, tid, kt, 10), "l20": window_sums_nan(V, tid, kt, 20),
            "szn": window_sums_nan(V, tskey, kts, None)}
    cols = {"game_id": tg["game_id"].to_numpy(), "team_id": tg["team_id"].to_numpy()}
    for tag, (S, N) in wins.items():
        for c in ["poss", "pd", "pf", "allow_reb", "allow_ast", "allow_pts"]:
            cols[f"{c}_{tag}"] = safe_div(S[:, vi[c]], N[:, vi[c]])
        cols[f"dreb_rate_{tag}"] = safe_div(S[:, vi["dreb"]], S[:, vi["dreb"]] + S[:, vi["o_oreb"]])
    # league possessions per team-game to date within the season, from earlier dates only (same-day games and
    # the pending games of a live run never enter); a season's first 30 team-games use the previous season's mean
    day = tg.groupby(["season", "game_date"], sort=True)["poss"].agg(["sum", "count"]).reset_index()
    day["cs"] = day.groupby("season")["sum"].cumsum() - day["sum"]
    day["cn"] = day.groupby("season")["count"].cumsum() - day["count"]
    season_mean = (day.groupby("season")["sum"].sum() / day.groupby("season")["count"].sum()).sort_index()
    prev_mean = season_mean.shift(1)
    day["league_poss"] = np.where(day["cn"] >= 30, safe_div(day["cs"], day["cn"]), day["season"].map(prev_mean))
    key_day = pd.MultiIndex.from_frame(tg[["season", "game_date"]])
    cols["league_poss"] = key_day.map(day.set_index(["season", "game_date"])["league_poss"]).to_numpy(np.float64)
    dn = tg["game_date"].to_numpy().astype("datetime64[D]").astype(np.int64)
    prev = np.full(len(tg), np.nan)
    prev[1:] = dn[:-1]
    prev[kt == 0] = np.nan
    gap = dn - prev
    cols["team_days_rest"] = np.minimum(gap, REST_CAP)
    cols["team_b2b"] = np.where(np.isnan(gap), np.nan, (gap == 1).astype(np.float64))
    cols["team_game_num"] = (kts + 1).astype(np.float64)
    return pd.DataFrame(cols)


def doc_gamestate():
    lt = "Both teams' earlier games only (trailing-20 windows shifted one game); home court is known before tip."
    w = "team's and opponent's last 20 games"
    doc("gs_exp_margin", "Team context",
        f"Expected margin proxy: pd_diff_l20 plus {HCA} for the home team, minus {HCA} for the away team. "
        "Adopted 2026-10-30 with the other gs_ features after the controlled test in data/eval/gamestate/.", w, lt)
    doc("gs_abs_exp_margin", "Team context", "Absolute expected margin (blowout risk in either direction).", w, lt)
    doc("gs_exp_total", "Team context",
        "Expected total: mean over the two teams of trailing-20 points for plus points against.", w, lt)
    doc("gs_exp_pace", "Team context",
        "Expected pace: team_poss_l20 x opp_poss_l20 / league possessions per team-game this season from earlier "
        "dates only (the previous season's mean in a season's first 30 team-games).", w, lt)
    doc("gs_pace_gap", "Team context", "team_poss_l20 minus opp_poss_l20.", w, lt)


def doc_team():
    lt = "Team's earlier games only (team game sequence shifted one game)."
    lo = "Opponent's earlier games only (opponent game sequence shifted one game)."
    for tag in ["l10", "l20", "szn"]:
        w, wo = TEAM_WIN_LABEL[tag], OPP_WIN_LABEL[tag]
        doc(f"team_poss_{tag}", "Team context",
            "Team possessions per game, fga - oreb + turnovers + 0.44 * fta (pace proxy).", w, lt)
        doc(f"opp_poss_{tag}", "Team context", "Opponent's own possessions per game (pace proxy).", wo, lo)
        doc(f"team_pd_{tag}", "Team context", "Team point differential per game (strength proxy).", w, lt)
        doc(f"opp_pd_{tag}", "Team context", "Opponent point differential per game.", wo, lo)
        doc(f"pd_diff_{tag}", "Team context",
            "team_pd minus opp_pd for the same window (expected margin proxy for blowout risk).", w, lt + " " + lo)
        doc(f"opp_allow_reb_{tag}", "Team context",
            "Rebounds per game recorded against the opponent by its opponents (player-credited oreb + dreb).", wo, lo)
        doc(f"opp_allow_ast_{tag}", "Team context",
            "Assists per game recorded against the opponent by its opponents.", wo, lo)
        doc(f"opp_allow_pts_{tag}", "Team context", "Points per game allowed by the opponent.", wo, lo)
        doc(f"opp_dreb_rate_{tag}", "Team context",
            "Opponent defensive rebound rate: opponent dreb / (opponent dreb + its opponents' oreb), "
            "as a ratio of window sums.", wo, lo)
    ls = "Team schedule; earlier team game dates only."
    doc("team_days_rest", "Schedule", f"Days since the team's previous game, capped at {REST_CAP}.",
        "team's previous game", ls)
    doc("team_b2b", "Schedule", "1 if the team played the day before.", "team's previous game", ls)
    doc("home", "Schedule", "1 if the player's team is the home team (ESPN home_away).", "current game",
        "Known before tip.")
    doc("is_playoff", "Schedule", "1 if season_type is 3 (playoffs) or 5 (play-in).", "current game",
        "Known before tip.")
    doc("team_game_num", "Schedule", "Team's game number this season including this game (1 = first game).",
        "season to date", ls)


# --------------------------------------------------------------------------------------------
# Roster-based features: rank and share (lineup-free) and teammate absence (abs_, lineup-known)
# --------------------------------------------------------------------------------------------
def explode_window(app, W):
    """Each appearance at team game kk contributes to the windows of team games kk+1 .. kk+W."""
    n = len(app)
    rep = np.repeat(np.arange(n), W)
    off = np.tile(np.arange(1, W + 1, dtype=np.int64), n)
    E = pd.DataFrame({
        "team_id": app["team_id"].to_numpy()[rep],
        "kk": app["kk"].to_numpy(np.int64)[rep] + off,
        "athlete_id": app["athlete_id"].to_numpy()[rep],
        "min": app["minutes"].to_numpy(np.float64)[rep],
        "reb": app["rebounds"].to_numpy(np.float64)[rep],
        "ast": app["assists"].to_numpy(np.float64)[rep],
        "pts": app["points"].to_numpy(np.float64)[rep],
    })
    return E.groupby(["team_id", "kk", "athlete_id"], as_index=False, sort=False).sum()


def roster_features(p, pre_l20, post_l20):
    """pre_l20 / post_l20: arrays (n, 2) of rebounds and assists per game over the last 20 played games,
    before and after each played row of p."""
    # team game sequence for roster windows: team-games with at least one played row
    tgp = p.drop_duplicates(["game_id", "team_id"])[["team_id", "game_id", "game_date", "game_date_time"]]
    tgp = tgp.sort_values(["team_id", "game_date_time", "game_id"]).reset_index(drop=True)
    tgp["kk"] = within_group_index(tgp["team_id"].to_numpy())
    app = p[["team_id", "game_id", "athlete_id", "minutes", "rebounds", "assists", "points"]].copy()
    app["row"] = np.arange(len(p))
    app = app.merge(tgp[["team_id", "game_id", "kk"]], on=["team_id", "game_id"], how="left")
    assert app["kk"].notna().all() and len(app) == len(p)
    app = app.sort_values("row").reset_index(drop=True)
    cur = app[["team_id", "kk", "athlete_id"]].assign(played_now=1)

    pg = p[["athlete_id", "game_date", "team_id"]].rename(columns={"team_id": "last_team"}).sort_values("game_date")

    def still_on_team(c):
        """Drop candidates whose latest played game before this date was for another team."""
        c = c.sort_values("game_date")
        m = pd.merge_asof(c, pg, on="game_date", by="athlete_id", allow_exact_matches=False,
                          direction="backward")
        return m[m["last_team"] == m["team_id"]].drop(columns="last_team")

    tgk = tgp[["team_id", "kk", "game_date"]]
    agg10 = explode_window(app, 10).merge(tgk, on=["team_id", "kk"], how="inner")
    agg20 = explode_window(app, 20).merge(tgk, on=["team_id", "kk"], how="inner")

    # regulars: average >= 15 minutes per team game over the team's last 10 games, still on the team
    ng = np.minimum(agg10["kk"].to_numpy(), 10).astype(np.float64)
    for c in ["min", "reb", "ast", "pts"]:
        agg10[f"avg_{c}"] = agg10[c].to_numpy() / ng
    regs = still_on_team(agg10[agg10["avg_min"] >= REGULAR_MIN])
    regs = regs.merge(cur, on=["team_id", "kk", "athlete_id"], how="left")
    regs["absent"] = regs["played_now"].isna()

    ab = regs[regs["absent"]].groupby(["team_id", "kk"], as_index=False).agg(
        abs_n_absent_regulars=("athlete_id", "size"), abs_min=("avg_min", "sum"),
        abs_absent_rebounds_pg=("avg_reb", "sum"), abs_absent_assists_pg=("avg_ast", "sum"),
        abs_absent_points_pg=("avg_pts", "sum"))
    ab["abs_absent_minutes_share"] = ab.pop("abs_min") / 240.0
    tf = tgp[["team_id", "kk"]].merge(ab, on=["team_id", "kk"], how="left")
    abs_cols = ["abs_n_absent_regulars", "abs_absent_minutes_share", "abs_absent_rebounds_pg",
                "abs_absent_assists_pg", "abs_absent_points_pg"]
    tf[abs_cols] = tf[abs_cols].fillna(0.0)

    # team leaders over the last 20 team games (players still on the team)
    c20 = still_on_team(agg20)
    flag_cols = []
    for stat, name in [("reb", "abs_top_rebounder_absent"), ("ast", "abs_top_assister_absent")]:
        top = c20.sort_values(["team_id", "kk", stat, "athlete_id"], ascending=[True, True, False, True])
        top = top.drop_duplicates(["team_id", "kk"])[["team_id", "kk", "athlete_id"]]
        top = top.merge(cur, on=["team_id", "kk", "athlete_id"], how="left")
        top[name] = top["played_now"].isna().astype(np.float64)
        tf = tf.merge(top[["team_id", "kk", name]], on=["team_id", "kk"], how="left")
        flag_cols.append(name)
    tf.loc[tf["kk"] == 0, abs_cols + flag_cols] = np.nan
    rowf = app[["row", "team_id", "kk"]].merge(tf, on=["team_id", "kk"], how="left").sort_values("row")
    assert len(rowf) == len(p)
    out = {c: rowf[c].to_numpy(np.float64) for c in abs_cols + flag_cols}

    # share of team rebounds and assists over the team's last 20 games
    tot = agg20.groupby(["team_id", "kk"], as_index=False)[["reb", "ast"]].sum().rename(
        columns={"reb": "t_reb", "ast": "t_ast"})
    own = app[["row", "team_id", "kk", "athlete_id"]].merge(
        agg20[["team_id", "kk", "athlete_id", "reb", "ast"]], on=["team_id", "kk", "athlete_id"], how="left")
    own = own.merge(tot, on=["team_id", "kk"], how="left").sort_values("row")
    own[["reb", "ast"]] = own[["reb", "ast"]].fillna(0.0)
    out["team_reb_share_l20"] = safe_div(own["reb"].to_numpy(), own["t_reb"].to_numpy())
    out["team_ast_share_l20"] = safe_div(own["ast"].to_numpy(), own["t_ast"].to_numpy())

    # rank among the team's pre-game regulars by rolling last-20 rebounds and assists per game
    post = p[["athlete_id", "game_date"]].assign(v_reb=post_l20[:, 0], v_ast=post_l20[:, 1]).sort_values(
        "game_date")
    rg = regs[["team_id", "kk", "athlete_id", "game_date"]].sort_values("game_date")
    rg = pd.merge_asof(rg, post, on="game_date", by="athlete_id", allow_exact_matches=False, direction="backward")
    me = app[["row", "team_id", "kk", "athlete_id"]].assign(o_reb=pre_l20[:, 0], o_ast=pre_l20[:, 1])
    mm = me.merge(rg.drop(columns="game_date").rename(columns={"athlete_id": "reg_id"}),
                  on=["team_id", "kk"], how="inner")
    mm = mm[mm["reg_id"] != mm["athlete_id"]]
    mm = mm.assign(gr=(mm["v_reb"] > mm["o_reb"]).astype(np.int64), ga=(mm["v_ast"] > mm["o_ast"]).astype(np.int64))
    gt = mm.groupby("row")[["gr", "ga"]].sum().reindex(np.arange(len(p)), fill_value=0)
    out["team_reb_rank"] = np.where(np.isnan(pre_l20[:, 0]), np.nan, 1.0 + gt["gr"].to_numpy())
    out["team_ast_rank"] = np.where(np.isnan(pre_l20[:, 1]), np.nan, 1.0 + gt["ga"].to_numpy())

    stats = {"regular_team_game_rows": int(len(regs)), "absent_regular_team_game_rows": int(regs["absent"].sum()),
             "team_games_in_player_box_sequence": int(len(tgp))}
    return out, stats


def doc_roster():
    lr = ("Lineup-free: regulars and their values come from earlier games only; does not use who plays "
          "in the current game.")
    doc("team_reb_rank", "Team context",
        "Player's rank by rolling rebounds per game (his last 20 played games) among the team's pre-game regulars "
        "(regular definition as in the abs_ features) plus the player; 1 = highest. Teammate values are as of "
        "the day before.", "last 20 played games of each player", lr)
    doc("team_ast_rank", "Team context", "Same as team_reb_rank for assists per game.",
        "last 20 played games of each player", lr)
    doc("team_reb_share_l20", "Team context",
        "Player's rebounds for this team over the team's last 20 games divided by the team's total player "
        "rebounds in those games (0 when he did not play in them).", "team's last 20 games",
        "Team's earlier games only.")
    doc("team_ast_share_l20", "Team context", "Same as team_reb_share_l20 for assists.", "team's last 20 games",
        "Team's earlier games only.")
    la = ("LINEUP-KNOWN: uses who played in the current game. Regular status and averages use the team's "
          "earlier games only. Excluded from C_noabs.")
    reg = ("Regulars are players averaging >= 15 minutes per team game over the team's last 10 games (missed "
           "games count as 0) whose latest played game before this date was for this team. Absent means no "
           "played row (minutes > 0) for this team in the current game.")
    doc("abs_n_absent_regulars", "Teammate absence", "Number of regulars who did not play this game. " + reg,
        "team's last 10 games", la)
    doc("abs_absent_minutes_share", "Teammate absence",
        "Sum of absent regulars' average minutes per team game divided by 240.", "team's last 10 games", la)
    doc("abs_absent_rebounds_pg", "Teammate absence", "Sum of absent regulars' rebounds per team game.",
        "team's last 10 games", la)
    doc("abs_absent_assists_pg", "Teammate absence", "Sum of absent regulars' assists per team game.",
        "team's last 10 games", la)
    doc("abs_absent_points_pg", "Teammate absence", "Sum of absent regulars' points per team game.",
        "team's last 10 games", la)
    doc("abs_top_rebounder_absent", "Teammate absence",
        "1 if the team's leading rebounder by total rebounds over the team's last 20 games (still on the team) "
        "did not play this game.", "team's last 20 games", la)
    doc("abs_top_assister_absent", "Teammate absence", "Same as abs_top_rebounder_absent for assists.",
        "team's last 20 games", la)
    doc("position", "Position",
        "ESPN athlete_position_abbreviation as a LightGBM native categorical (C, F, G, PF, PG, SF, SG; "
        "missing or NA left empty).", "current roster listing", "Static roster attribute, known before tip.")


# --------------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------------
def verify_windows(p, feats):
    """Recompute a sample of features with pandas groupby, shift, rolling; return max abs differences."""
    key = p["athlete_id"]
    sh = p.groupby("athlete_id", sort=False)[["dd", "minutes", "rebounds", "points"]].shift(1)
    g = sh.groupby(key, sort=False)
    r5 = g.rolling(5, min_periods=1).mean().reset_index(level=0, drop=True).sort_index()
    r20 = g.rolling(20, min_periods=1).mean().reset_index(level=0, drop=True).sort_index()
    sd20 = g.rolling(20, min_periods=2).std().reset_index(level=0, drop=True).sort_index()
    ew = g.ewm(halflife=EWM_HALFLIFE).mean().reset_index(level=0, drop=True).sort_index()
    checks = {
        "dd_rate_l5": np.nanmax(np.abs(r5["dd"].to_numpy() - feats["dd_rate_l5"])),
        "min_l5": np.nanmax(np.abs(r5["minutes"].to_numpy() - feats["min_l5"])),
        "reb_l20": np.nanmax(np.abs(r20["rebounds"].to_numpy() - feats["reb_l20"])),
        "min_sd_l20": np.nanmax(np.abs(sd20["minutes"].to_numpy() - feats["min_sd_l20"])),
        "pts_ewm": np.nanmax(np.abs(ew["points"].to_numpy() - feats["pts_ewm"])),
    }
    shs = p.groupby(["athlete_id", "season"], sort=False)["points"].shift(1)
    szn = shs.groupby([p["athlete_id"], p["season"]], sort=False).expanding().mean()
    szn = szn.reset_index(level=[0, 1], drop=True).sort_index()
    checks["pts_szn"] = np.nanmax(np.abs(szn.to_numpy() - feats["pts_szn"]))
    nan_match = {
        "dd_rate_l5": bool((np.isnan(r5["dd"].to_numpy()) == np.isnan(feats["dd_rate_l5"])).all()),
        "pts_szn": bool((np.isnan(szn.to_numpy()) == np.isnan(feats["pts_szn"])).all()),
        "min_sd_l20": bool((np.isnan(sd20["minutes"].to_numpy()) == np.isnan(feats["min_sd_l20"])).all()),
    }
    return checks, nan_match


def spot_check(ds, p):
    """Last 12 dataset rows for a star and a bench player, with the 5-game windows recomputed by hand."""
    lines = []
    star = ds.loc[ds["athlete_display_name"].str.contains("Jokic", case=False, na=False), "athlete_id"]
    star_id = int(star.mode().iloc[0]) if len(star) else int(ds.groupby("athlete_id")["dd"].sum().idxmax())
    s26 = ds[ds["season"] == 2026].groupby("athlete_id").agg(n=("minutes", "size"), mpg=("minutes", "mean"))
    cand = s26[(s26["n"] >= 40) & (s26["mpg"] >= 10) & (s26["mpg"] <= 18)].index
    tail = ds[ds["athlete_id"].isin(cand)].sort_values(["game_date_time", "game_id"]).groupby("athlete_id").tail(12)
    t12 = tail.groupby("athlete_id").agg(dd=("dd", "sum"), starts=("starter", "sum"), mpg=("minutes", "mean"))
    t12 = t12[(t12["starts"] == 0) & (t12["mpg"] <= 20)].sort_index()  # came off the bench in all 12 rows
    bench_id = int(t12["dd"].sort_values(ascending=False, kind="stable").index[0])
    for label, pid in [("STAR", star_id), ("BENCH", bench_id)]:
        hist = p[p["athlete_id"] == pid].sort_values(["game_date_time", "game_id"])
        dd_list = hist["dd"].tolist()
        min_list = hist["minutes"].tolist()
        pos = {gid: i for i, gid in enumerate(hist["game_id"].tolist())}
        rows = ds[ds["athlete_id"] == pid].sort_values(["game_date_time", "game_id"]).tail(12).copy()
        chk_dd, chk_min = [], []
        for gid in rows["game_id"]:
            i = pos[gid]
            prev_dd = dd_list[max(0, i - 5):i]
            prev_min = min_list[max(0, i - 5):i]
            chk_dd.append(sum(prev_dd) / len(prev_dd))
            chk_min.append(sum(prev_min) / len(prev_min))
        rows["hand_dd_l5"] = chk_dd
        rows["hand_min_l5"] = chk_min
        rows["match"] = (np.isclose(rows["dd_rate_l5"], rows["hand_dd_l5"], atol=1e-5)
                         & np.isclose(rows["min_l5"], rows["hand_min_l5"], atol=1e-4))
        name = rows["athlete_display_name"].iloc[-1]
        lines.append(f"{label}: {name} (athlete_id {pid})")
        show = rows[["game_date", "season", "minutes", "rebounds", "assists", "dd", "dd_rate_l5", "min_l5",
                     "hand_dd_l5", "hand_min_l5", "match"]].copy()
        show["game_date"] = show["game_date"].dt.strftime("%Y-%m-%d")
        lines.append(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------
# Documentation
# --------------------------------------------------------------------------------------------
def write_features_md(feature_names, info, n_rows, n_cols):
    by_name = {d["name"]: d for d in DOC}
    missing = [f for f in feature_names if f not in by_name]
    assert not missing, f"undocumented features: {missing}"
    groups = ["Player form", "Player history", "Schedule", "Position", "Team context", "Teammate absence"]
    out = ["# Features v1", "",
           "This file is written by `tools/build_dataset.py`. It documents every model feature in "
           "`data/features/dataset_v1.parquet`. The ordered feature list is in "
           "`data/features/dataset_v1_features.json`.", "",
           "## Rows and target", "",
           f"- One row per player-game where the player recorded minutes > 0 and had at least {MIN_PRIOR_GAMES} "
           "earlier played games in the data (any season). The data starts with the 2017-18 season.",
           f"- Built from {info['raw_player_rows']} raw box score rows. Duplicate (game_id, athlete_id) rows "
           f"dropped: {info['duplicate_player_rows_dropped']}. All-Star and Rising Stars exhibition games dropped: "
           f"{info['exhibition_games_dropped']} games ({info['exhibition_player_rows_dropped']} rows); ESPN codes "
           "them as season_type 2 with non-franchise team ids. Second ESPN athlete ids for the same player in "
           f"the same game (same team and display name) dropped: {info['alias_duplicate_rows_dropped']} rows, "
           f"{info['alias_duplicate_played_rows_dropped']} of them played rows (mostly 2018-19). Games dropped "
           f"because a team had two games on one date: {info['same_date_conflict_games_dropped']} (a corrupted "
           "2019-20 timestamp).",
           f"- Played rows before the 5-game filter: {info['played_rows']}. Final table: {n_rows} rows and "
           f"{n_cols} columns, of which {len(feature_names)} are model features "
           f"({sum(f.startswith('abs_') for f in feature_names)} with the abs_ prefix).",
           "- Target `dd` = 1 when at least two of points, rebounds, assists, steals, blocks are 10 or more. "
           "`td` (three or more) is kept for reference and is not modeled.",
           "- All season types are kept. `is_playoff` marks playoffs (3) and play-in (5).",
           f"- Team totals come from team_box. {info['team_games_without_box_stats']} team-game rows (the six "
           "2020-21 play-in games) are missing from team_box and have no played rows in the player box; they "
           "count for scores, point differential, and schedule features, and are skipped inside box-stat "
           "windows (a window mean divides by the games that have stats). "
           + (f"{info['team_games_from_player_box_sums']} other team-game rows use player box sums. "
              if info["team_games_from_player_box_sums"] else "") +
           f"{info['team_games_only_in_team_box']} team-game rows exist only in team_box; they count for team "
           "features but have no player rows. Roster windows (abs_, rank, share) use the team-games that have "
           "played rows.",
           "- The abs_ regular window runs across seasons, as all N-game windows do. In each team's first games "
           "of a season it therefore counts last season's regulars who left the team and have not yet played for "
           "a new team as absent. Measured on team-games in this dataset: mean abs_n_absent_regulars is "
           f"{info['abs_mean_team_game_1']:.2f} in a team's first game of a season, "
           f"{info['abs_mean_team_game_2_5']:.2f} in games 2 to 5, and {info['abs_mean_team_game_6_plus']:.2f} "
           "from game 6 on.", "",
           "## Leakage discipline", "",
           "- Rows are sorted by game_date_time then game_id before any shift or window. Player features group "
           "by athlete_id; team features group by team_id.",
           "- Every window is computed over earlier rows only (an exclusive cumulative sum, equivalent to shifting "
           "by one game before the window). A player plays at most one game per date, so earlier rows are "
           "earlier dates. The build asserts this.",
           "- Rolling N-game windows run across seasons. Season-to-date windows reset at the `season` column. "
           "N-game windows with fewer than N earlier games use the games available.",
           "- Features prefixed `abs_` are lineup-known: they use who played in the current game. The trainer "
           "drops them for C_noabs. The team rank features use only pre-game regulars, so C_noabs stays "
           "lineup-free.",
           "- The build recomputes dd_rate_l5, min_l5, reb_l20, min_sd_l20, pts_ewm, and pts_szn with pandas "
           "groupby, shift, and rolling and asserts they match the vectorized values.", "",
           "## Columns that are not features", "",
           "Identifiers and current-game outcomes are stored for evaluation only: game_id, season, season_type, "
           "game_date, game_date_time, athlete_id, athlete_display_name, team_id, team_abbreviation, "
           "opponent_team_id, home_away, minutes, points, rebounds, assists, steals, blocks, starter, dd, td, and "
           "career_dd_rate_pre (the player's dd rate over all seasons before this one, used only as the Baseline A "
           "fallback prior).", ""]
    for grp in groups:
        names = [f for f in feature_names if by_name[f]["group"] == grp]
        out.append(f"## {grp} ({len(names)})")
        out.append("")
        tbl = pd.DataFrame([{"Name": f"`{n}`", "Definition": by_name[n]["definition"],
                             "Window": by_name[n]["window"], "Leakage note": by_name[n]["leakage"]}
                            for n in names])
        out.append(to_markdown(tbl))
        out.append("")
    text = "\n".join(out)
    assert "—" not in text and "!" not in text
    (DOCS_DIR / "FEATURES_v1.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------------------------
def build_table(pb, tb, info, t0=None, verify=True):
    """Compute every v1 feature for the played rows of pb (minutes > 0), the shared code path of the
    historical dataset (main) and the live pipeline (tools/daily_run.py, which appends pending rows for
    today's games with placeholder stats and reads their features back out).

    Returns (ds, p, feature_names, meta_cols): ds holds every played row with meta columns and features,
    before the MIN_PRIOR_GAMES filter and unsorted; p is the played-row frame the features were built on.
    """
    t0 = time.time() if t0 is None else t0
    DOC.clear()
    p = pb[pb["minutes"] > 0].copy()
    p = add_targets(p)
    p = p.sort_values(["athlete_id", "game_date_time", "game_id"]).reset_index(drop=True)
    info["played_rows"] = len(p)
    log(f"played rows {len(p)}", t0)

    feats, k, ks = player_form(p)
    log("player form done", t0)
    hist, career_pre = player_history(p)
    feats.update(hist)
    feats.update(player_schedule(p, k))
    feats["home"] = (p["home_away"] == "home").astype(np.float64).to_numpy()
    feats["is_playoff"] = p["season_type"].isin([3, 5]).astype(np.float64).to_numpy()
    log("history and schedule done", t0)

    tg, n_fallback, n_nostats, n_tb_only = team_games(pb, tb)
    info["team_games_from_player_box_sums"] = n_fallback
    info["team_games_without_box_stats"] = n_nostats
    info["team_games_only_in_team_box"] = n_tb_only
    tf = team_features(tg)
    keyed = p[["game_id", "team_id", "opponent_team_id"]].copy()
    own = keyed.merge(tf, on=["game_id", "team_id"], how="left")
    opp = keyed.merge(tf.rename(columns={"team_id": "opponent_team_id"}), on=["game_id", "opponent_team_id"],
                      how="left")
    assert len(own) == len(p) and len(opp) == len(p)
    for tag in ["l10", "l20", "szn"]:
        feats[f"team_poss_{tag}"] = own[f"poss_{tag}"].to_numpy()
        feats[f"opp_poss_{tag}"] = opp[f"poss_{tag}"].to_numpy()
        feats[f"team_pd_{tag}"] = own[f"pd_{tag}"].to_numpy()
        feats[f"opp_pd_{tag}"] = opp[f"pd_{tag}"].to_numpy()
        feats[f"pd_diff_{tag}"] = feats[f"team_pd_{tag}"] - feats[f"opp_pd_{tag}"]
        feats[f"opp_allow_reb_{tag}"] = opp[f"allow_reb_{tag}"].to_numpy()
        feats[f"opp_allow_ast_{tag}"] = opp[f"allow_ast_{tag}"].to_numpy()
        feats[f"opp_allow_pts_{tag}"] = opp[f"allow_pts_{tag}"].to_numpy()
        feats[f"opp_dreb_rate_{tag}"] = opp[f"dreb_rate_{tag}"].to_numpy()
    for c in ["team_days_rest", "team_b2b", "team_game_num"]:
        feats[c] = own[c].to_numpy()
    doc_team()
    # game-state features (adopted 2026-10-30 after the controlled test in data/eval/gamestate/): the expected
    # margin from the two trailing-20 point differentials plus home court, its size, the expected total, the
    # expected pace as team x opponent / league possessions, and the pace gap. gs_opp_pd_l20 of the test is
    # opp_pd_l20 above and is not repeated.
    side = np.where(feats["home"] == 1.0, 1.0, -1.0)
    feats["gs_exp_margin"] = feats["pd_diff_l20"] + HCA * side
    feats["gs_abs_exp_margin"] = np.abs(feats["gs_exp_margin"])
    feats["gs_exp_total"] = (own["pf_l20"].to_numpy() + own["allow_pts_l20"].to_numpy()
                             + opp["pf_l20"].to_numpy() + opp["allow_pts_l20"].to_numpy()) / 2.0
    feats["gs_exp_pace"] = safe_div(feats["team_poss_l20"] * feats["opp_poss_l20"], own["league_poss"].to_numpy())
    feats["gs_pace_gap"] = feats["team_poss_l20"] - feats["opp_poss_l20"]
    doc_gamestate()
    log(f"team context done (team-games {len(tg)}, {n_fallback} from player box sums, {n_nostats} without box stats)", t0)

    # rolling last-20 rebounds and assists per game, before and after each played row (for the rank)
    aid = p["athlete_id"].to_numpy()
    V = p[["rebounds", "assists"]].to_numpy(np.float64)
    incl = prior_cumsum(V, aid) + V
    S_post, _ = window_from_prior(incl, k, 20)
    post_l20 = S_post / np.minimum(k + 1, 20)[:, None]
    pre_l20 = np.column_stack([feats["reb_l20"], feats["ast_l20"]])
    roster, rstats = roster_features(p, pre_l20, post_l20)
    feats.update(roster)
    info.update(rstats)
    doc_roster()
    log("rank, share, and absence features done", t0)

    if verify:
        checks, nan_match = verify_windows(p, feats)
        info["window_check_max_abs_diff"] = {c: float(v) for c, v in checks.items()}
        info["window_check_nan_pattern_match"] = nan_match
        log(f"window recomputation check max abs diff {info['window_check_max_abs_diff']}, NaN patterns {nan_match}", t0)
        assert all(v < 1e-6 for v in checks.values()) and all(nan_match.values())

    # assemble
    pos = p["athlete_position_abbreviation"].where(p["athlete_position_abbreviation"].isin(POSITIONS))
    meta = pd.DataFrame({
        "game_id": p["game_id"], "season": p["season"], "season_type": p["season_type"],
        "game_date": p["game_date"], "game_date_time": p["game_date_time"], "athlete_id": p["athlete_id"],
        "athlete_display_name": p["athlete_display_name"], "team_id": p["team_id"],
        "team_abbreviation": p["team_abbreviation"], "opponent_team_id": p["opponent_team_id"],
        "home_away": p["home_away"], "minutes": p["minutes"], "points": p["points"], "rebounds": p["rebounds"],
        "assists": p["assists"], "steals": p["steals"], "blocks": p["blocks"],
        "starter": p["starter"].astype(np.int8), "dd": p["dd"], "td": p["td"],
        "career_dd_rate_pre": career_pre,
    })
    group_order = ["Player form", "Player history", "Schedule", "Position", "Team context", "Teammate absence"]
    by_name = {d["name"]: d for d in DOC}
    all_names = list(feats.keys()) + ["position"]
    feature_names = [n for g in group_order for n in all_names if by_name[n]["group"] == g]
    assert sorted(feature_names) == sorted(all_names)
    fdf = pd.DataFrame({n: np.asarray(feats[n], dtype=np.float32) for n in feature_names if n != "position"})
    fdf["position"] = pd.Categorical(pos, categories=POSITIONS)
    fdf = fdf[feature_names]
    ds = pd.concat([meta, fdf], axis=1)
    assert len(ds) == len(p)
    meta_cols = list(meta.columns)
    assert not set(feature_names) & set(meta_cols)
    return ds, p, feature_names, meta_cols


def main():
    t0 = time.time()
    np.random.seed(SEED)
    pb, tb, info = load_clean()
    log(f"loaded player box {info['raw_player_rows']} rows, {len(pb)} after cleaning", t0)
    ds, p, feature_names, meta_cols = build_table(pb, tb, info, t0)
    ds = ds[ds["games_played_career"] >= MIN_PRIOR_GAMES]
    ds = ds.sort_values(["game_date_time", "game_id", "athlete_id"]).reset_index(drop=True)

    tgd = ds.drop_duplicates(["game_id", "team_id"])
    info["abs_mean_team_game_1"] = float(tgd.loc[tgd["team_game_num"] == 1, "abs_n_absent_regulars"].mean())
    info["abs_mean_team_game_2_5"] = float(tgd.loc[tgd["team_game_num"].between(2, 5), "abs_n_absent_regulars"].mean())
    info["abs_mean_team_game_6_plus"] = float(tgd.loc[tgd["team_game_num"] >= 6, "abs_n_absent_regulars"].mean())

    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    ds.to_parquet(DATASET_PATH, index=False)
    abs_features = [f for f in feature_names if f.startswith("abs_")]
    FEATURE_LIST_PATH.write_text(json.dumps({
        "features": feature_names, "abs_features": abs_features, "categorical": ["position"],
        "position_categories": POSITIONS, "meta_columns": meta_cols, "build_info": info,
    }, indent=2, default=str), encoding="utf-8")
    write_features_md(feature_names, info, len(ds), ds.shape[1])
    log(f"wrote {DATASET_PATH.name} shape {ds.shape}, {len(feature_names)} features ({len(abs_features)} abs_)", t0)

    by_season = ds.groupby("season").agg(rows=("dd", "size"), dd_rate=("dd", "mean"), td_rate=("td", "mean"),
                                         reg_rows=("season_type", lambda s: int((s == 2).sum())))
    by_season["reg_dd_rate"] = ds[ds["season_type"] == 2].groupby("season")["dd"].mean()
    print(by_season.to_string(float_format=lambda v: f"{v:.4f}"))
    print()
    print(spot_check(ds, p))
    log("done", t0)


if __name__ == "__main__":
    main()
