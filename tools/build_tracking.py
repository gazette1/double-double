#!/usr/bin/env python
"""Match stats.nba.com tracking rows to ESPN player ids and build point-in-time tracking features.

Inputs: per-date files written by tools/pull_tracking.py under data/raw/tracking/{reb,pass,hustle}/ and the
hoopR player box scores. Outputs:
  data/raw/tracking/crosswalk.csv              NBA PLAYER_ID to ESPN athlete_id, with match counts
  data/features/tracking_games.parquet         one row per matched player-game with the raw tracking columns
  data/features/tracking_team_games.parquet    team-game sums of the tracking columns (for opponent features)
  data/features/tracking_features.parquet      point-in-time player features (prior tracked games only), keyed
                                               by athlete_id and game_date, prefix trk_; since 2026-10-30 also the
                                               box-out success ratios (own rebound, team rebound and defensive share
                                               per box out) over trailing 10, 20 and EWM windows
Matching: exact on normalized name + team + date, then name + date, then a fuzzy pass within team-date with
minutes agreement. One-to-one assignment by matched-row count. The report printed at the end gives the share
of tracking rows and of hoopR played rows that matched.

Usage: PYTHONUTF8=1 python tools/build_tracking.py [--seasons 2024 2025 2026 2027]
"""
import argparse
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TRK = RAW / "tracking"
FEAT = ROOT / "data" / "features"
TEAM_MAP = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}
SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}
KEEP = {
    "reb": ["MIN", "OREB", "DREB", "REB", "OREB_CHANCES", "DREB_CHANCES", "REB_CHANCES", "REB_CONTEST",
            "REB_UNCONTEST", "REB_CHANCE_DEFER", "AVG_REB_DIST"],
    "pass": ["MIN", "PASSES_MADE", "PASSES_RECEIVED", "AST", "FT_AST", "SECONDARY_AST", "POTENTIAL_AST",
             "AST_PTS_CREATED"],
    "hustle": ["MIN", "CONTESTED_SHOTS", "DEFLECTIONS", "CHARGES_DRAWN", "SCREEN_ASSISTS",
               "LOOSE_BALLS_RECOVERED", "OFF_BOXOUTS", "DEF_BOXOUTS", "BOX_OUT_PLAYER_REBS", "BOX_OUTS",
               "BOX_OUT_PLAYER_TEAM_REBS"],
}
TEAM_AGG = {"reb_REB_CHANCES": "rebch", "reb_REB": "trk_reb", "reb_REB_CONTEST": "rebcon",
            "pass_POTENTIAL_AST": "potast", "pass_PASSES_MADE": "passes", "pass_AST": "trk_ast",
            "hustle_BOX_OUTS": "boxouts", "hustle_DEF_BOXOUTS": "defbox", "hustle_OFF_BOXOUTS": "offbox",
            "hustle_CONTESTED_SHOTS": "contested", "hustle_DEFLECTIONS": "deflect",
            "hustle_SCREEN_ASSISTS": "screenast", "hustle_LOOSE_BALLS_RECOVERED": "loose", "trk_min": "min"}
HALFLIFE = 8


def norm_name(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("'", "").replace("’", "").replace(".", "")
    s = re.sub(r"[-,]", " ", s)
    return " ".join(t for t in s.split() if t not in SUFFIX)


def load_tracking(seasons):
    parts = {}
    for m in KEEP:
        files = [f for y in seasons for f in sorted((TRK / m).glob(f"{y}_*.parquet"))]
        frames = [pd.read_parquet(f) for f in files]
        frames = [f for f in frames if len(f)]
        if not frames:
            parts[m] = None
            continue
        df = pd.concat(frames, ignore_index=True)
        df = df.rename(columns={"G": "GP"})
        cols = ["game_date", "season", "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION"] + KEEP[m]
        df = df[cols].rename(columns={c: f"{m}_{c}" for c in KEEP[m]})
        parts[m] = df
    base = None
    for m, df in parts.items():
        if df is None:
            continue
        if base is None:
            base = df
        else:
            base = base.merge(df, on=["game_date", "season", "PLAYER_ID"], how="outer", suffixes=("", f"_{m}"))
            for c in ["PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION"]:
                if f"{c}_{m}" in base:
                    base[c] = base[c].fillna(base[f"{c}_{m}"])
                    base = base.drop(columns=[f"{c}_{m}"])
    base["game_date"] = pd.to_datetime(base["game_date"]).dt.normalize()
    mins = base[[c for c in base.columns if c.endswith("_MIN")]].bfill(axis=1).iloc[:, 0]
    base["trk_min"] = mins
    base["nname"] = base["PLAYER_NAME"].map(norm_name)
    return base.drop_duplicates(["PLAYER_ID", "game_date"])


def load_hoopr(seasons):
    frames = []
    for y in seasons:
        pb = pd.read_parquet(RAW / "hoopr" / f"player_box_{y}.parquet",
                             columns=["game_id", "game_date", "season", "season_type", "athlete_id",
                                      "athlete_display_name", "team_id", "team_abbreviation",
                                      "opponent_team_id", "minutes"])
        frames.append(pb[(pb["season_type"] == 2) & (pb["minutes"] > 0)])
    h = pd.concat(frames, ignore_index=True)
    h["game_date"] = pd.to_datetime(h["game_date"]).dt.normalize()
    h["team_nba"] = h["team_abbreviation"].map(lambda t: TEAM_MAP.get(t, t))
    h["nname"] = h["athlete_display_name"].map(norm_name)
    return h.drop_duplicates(["athlete_id", "game_date"])


def match(trk, hp):
    """Return (one-to-one pairs with PLAYER_ID, athlete_id, n, method) and the row-level match table."""
    t = trk[["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "game_date", "nname", "trk_min"]].copy()
    t["last"] = t["nname"].str.split().str[-1]
    h = hp[["athlete_id", "athlete_display_name", "team_nba", "game_date", "nname", "minutes"]].copy()
    h["last"] = h["nname"].str.split().str[-1]
    matched = []
    m1 = t.merge(h, left_on=["nname", "TEAM_ABBREVIATION", "game_date"],
                 right_on=["nname", "team_nba", "game_date"])
    m1["method"] = "name_team_date"
    matched.append(m1)
    done_t = set(zip(m1["PLAYER_ID"], m1["game_date"]))
    done_h = set(zip(m1["athlete_id"], m1["game_date"]))
    t2 = t[[k not in done_t for k in zip(t["PLAYER_ID"], t["game_date"])]]
    h2 = h[[k not in done_h for k in zip(h["athlete_id"], h["game_date"])]]
    m2 = t2.merge(h2, on=["nname", "game_date"])
    m2["method"] = "name_date"
    matched.append(m2)
    done_t |= set(zip(m2["PLAYER_ID"], m2["game_date"]))
    done_h |= set(zip(m2["athlete_id"], m2["game_date"]))
    t3 = t[[k not in done_t for k in zip(t["PLAYER_ID"], t["game_date"])]]
    h3 = h[[k not in done_h for k in zip(h["athlete_id"], h["game_date"])]]
    rows = []
    hg = {k: g for k, g in h3.groupby(["team_nba", "game_date"])}
    for r in t3.itertuples(index=False):
        g = hg.get((r.TEAM_ABBREVIATION, r.game_date))
        if g is None:
            continue
        best, best_s = None, 0.0
        for c in g.itertuples(index=False):
            s = SequenceMatcher(None, r.nname, c.nname).ratio()
            if c.last == r.last:
                s = max(s, 0.8)
            if s > best_s:
                best, best_s = c, s
        if best is not None and best_s >= 0.75 and abs(float(best.minutes) - float(r.trk_min)) <= 2:
            rows.append({"PLAYER_ID": r.PLAYER_ID, "PLAYER_NAME": r.PLAYER_NAME, "game_date": r.game_date,
                         "athlete_id": best.athlete_id, "athlete_display_name": best.athlete_display_name,
                         "method": "fuzzy_team_date"})
    matched.append(pd.DataFrame(rows))
    cols = ["PLAYER_ID", "PLAYER_NAME", "athlete_id", "athlete_display_name", "game_date", "method"]
    allm = pd.concat([m[cols] for m in matched if len(m)], ignore_index=True)
    pairs = (allm.groupby(["PLAYER_ID", "athlete_id"])
             .agg(n=("game_date", "size"), PLAYER_NAME=("PLAYER_NAME", "first"),
                  athlete_display_name=("athlete_display_name", "first"),
                  method=("method", lambda s: s.value_counts().index[0]))
             .reset_index().sort_values("n", ascending=False))
    used_p, used_a, keep = set(), set(), []
    for r in pairs.itertuples(index=False):
        if r.PLAYER_ID in used_p or r.athlete_id in used_a:
            continue
        used_p.add(r.PLAYER_ID)
        used_a.add(r.athlete_id)
        keep.append(r)
    return pd.DataFrame(keep), allm


def point_in_time_features(g):
    """g: one player's matched games sorted by date. Every feature uses prior tracked games only."""
    g = g.sort_values("game_date")
    num = {
        "rebch": g["reb_REB_CHANCES"], "orebch": g["reb_OREB_CHANCES"], "drebch": g["reb_DREB_CHANCES"],
        "reb": g["reb_REB"], "rebcon": g["reb_REB_CONTEST"], "rebdefer": g["reb_REB_CHANCE_DEFER"],
        "potast": g["pass_POTENTIAL_AST"], "ast": g["pass_AST"], "passes": g["pass_PASSES_MADE"],
        "passrec": g["pass_PASSES_RECEIVED"], "secast": g["pass_SECONDARY_AST"],
        "astpts": g["pass_AST_PTS_CREATED"], "boxouts": g["hustle_BOX_OUTS"], "defbox": g["hustle_DEF_BOXOUTS"],
        "boxreb": g["hustle_BOX_OUT_PLAYER_REBS"], "deflect": g["hustle_DEFLECTIONS"],
        "boxteamreb": g["hustle_BOX_OUT_PLAYER_TEAM_REBS"],
        "screenast": g["hustle_SCREEN_ASSISTS"], "contested": g["hustle_CONTESTED_SHOTS"],
        "loose": g["hustle_LOOSE_BALLS_RECOVERED"], "min": g["trk_min"],
        "rebdist": g["reb_AVG_REB_DIST"] * g["reb_REB"],
    }
    X = pd.DataFrame(num).astype(float).shift(1)
    out = pd.DataFrame(index=g.index)
    out["trk_games_prior"] = np.arange(len(g))
    pm_keys = ["rebch", "orebch", "drebch", "rebdefer", "potast", "passes", "passrec", "secast", "astpts",
               "boxouts", "defbox", "boxreb", "deflect", "screenast", "contested", "loose"]
    for w in (5, 10, 20):
        S = X.rolling(w, min_periods=1).sum()
        for k in (pm_keys if w == 10 else ["rebch", "potast", "boxouts", "passes"]):
            out[f"trk_{k}_pm_l{w}"] = S[k] / S["min"]
        out[f"trk_rebch_conv_l{w}"] = S["reb"] / S["rebch"]
        out[f"trk_ast_conv_l{w}"] = S["ast"] / S["potast"]
        if w in (10, 20):
            # Russ, 2026-10-30: "successful box out rates". Share of box outs that end as the player's own
            # rebound, as any team rebound, and the defensive share of his box outs.
            out[f"trk_boxout_success_l{w}"] = S["boxreb"] / S["boxouts"]
            out[f"trk_boxout_teamsuccess_l{w}"] = S["boxteamreb"] / S["boxouts"]
            out[f"trk_boxout_defshare_l{w}"] = S["defbox"] / S["boxouts"]
        if w == 10:
            out["trk_reb_contest_share_l10"] = S["rebcon"] / S["reb"]
            out["trk_rebdist_l10"] = S["rebdist"] / S["reb"]
    E = X.ewm(halflife=HALFLIFE, min_periods=1).mean()
    for k in pm_keys:
        out[f"trk_{k}_pm_ewm"] = E[k] / E["min"]
    out["trk_rebch_conv_ewm"] = E["reb"] / E["rebch"]
    out["trk_ast_conv_ewm"] = E["ast"] / E["potast"]
    out["trk_boxout_success_ewm"] = E["boxreb"] / E["boxouts"]
    out["trk_boxout_teamsuccess_ewm"] = E["boxteamreb"] / E["boxouts"]
    out["trk_rebch_pg_ewm"] = E["rebch"]
    out["trk_potast_pg_ewm"] = E["potast"]
    out["trk_min_ewm"] = E["min"]
    out["trk_rebch_last"] = X["rebch"]
    out["trk_potast_last"] = X["potast"]
    out["trk_boxouts_last"] = X["boxouts"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026, 2027])
    args = ap.parse_args()
    trk = load_tracking(args.seasons)
    hp = load_hoopr(args.seasons)
    print(f"tracking player-games: {len(trk)} across {trk['game_date'].nunique()} dates; "
          f"hoopR played rows on those dates: {int(hp['game_date'].isin(trk['game_date'].unique()).sum())}")
    pairs, allm = match(trk, hp)
    pairs.to_csv(TRK / "crosswalk.csv", index=False)
    cw = pairs.set_index("PLAYER_ID")["athlete_id"]
    trk["athlete_id"] = trk["PLAYER_ID"].map(cw)
    n_t = len(trk)
    unmatched = trk[trk["athlete_id"].isna()]
    print(f"crosswalk: {len(pairs)} player pairs; methods: {pairs['method'].value_counts().to_dict()}")
    print(f"tracking rows mapped: {n_t - len(unmatched)} of {n_t} ({(n_t - len(unmatched)) / n_t:.3%})")
    if len(unmatched):
        print("most frequent unmatched tracking names:",
              unmatched["PLAYER_NAME"].value_counts().head(15).to_dict())
    games = trk.dropna(subset=["athlete_id"]).copy()
    games["athlete_id"] = games["athlete_id"].astype(int)
    games = games.merge(hp[["athlete_id", "game_date", "game_id", "team_id", "opponent_team_id"]],
                        on=["athlete_id", "game_date"], how="left")
    on_dates = hp[hp["game_date"].isin(games["game_date"].unique())]
    cov = on_dates.merge(games[["athlete_id", "game_date"]], on=["athlete_id", "game_date"], how="left",
                         indicator=True)
    print(f"hoopR played rows with a tracking row (same player, same date): "
          f"{(cov['_merge'] == 'both').mean():.3%} of {len(cov)}; "
          f"with minutes >= 10: {(cov.loc[cov['minutes'] >= 10, '_merge'] == 'both').mean():.3%}")
    miss = cov[cov["_merge"] != "both"]
    if len(miss):
        print("hoopR names most often without a tracking row:",
              miss["athlete_display_name"].value_counts().head(10).to_dict())
    games = games.sort_values(["athlete_id", "game_date"]).reset_index(drop=True)
    games.drop(columns=["nname"]).to_parquet(FEAT / "tracking_games.parquet", index=False)

    tg = games.dropna(subset=["game_id"]).copy()
    for c in ["game_id", "team_id", "opponent_team_id"]:
        tg[c] = tg[c].astype(int)
    tg = (tg.groupby(["game_id", "team_id", "opponent_team_id", "game_date", "season"])[list(TEAM_AGG)]
          .sum(min_count=1).rename(columns=TEAM_AGG).reset_index())
    tg.to_parquet(FEAT / "tracking_team_games.parquet", index=False)

    feats = games.groupby("athlete_id", group_keys=False).apply(point_in_time_features).sort_index()
    feats = feats.replace([np.inf, -np.inf], np.nan)
    feats.insert(0, "game_date", games.loc[feats.index, "game_date"].values)
    feats.insert(0, "athlete_id", games.loc[feats.index, "athlete_id"].values)
    feats.to_parquet(FEAT / "tracking_features.parquet", index=False)
    print(f"wrote tracking_games ({len(games)} rows), tracking_team_games ({len(tg)} rows) and "
          f"tracking_features ({len(feats)} rows, {feats.shape[1] - 2} features)")


if __name__ == "__main__":
    main()
