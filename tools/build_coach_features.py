#!/usr/bin/env python
"""Coaching-staff features, point in time, from the stats.nba.com staff snapshots and the ESPN box scores.

Russ (2026-10-29): coaches and lead assistants change teams like players do and carry their characteristics with
them, so the staff on each bench should be tracked alongside the roster.

Inputs
  data/raw/coaches/coaches_snapshots.parquet   staff per team per league year (tools/pull_coaches.py). The snapshot
                                               of league year Y is taken after that season, so the staff that opened
                                               season Y is the snapshot of Y-1.
  data/raw/coaches/midseason_changes.csv       curated in-season head-coach changes with dates (verified flag)
  data/raw/hoopr/team_box_{Y}.parquet, player_box_{Y}.parquet   ESPN box scores (season key = end year)

Head-coach timeline: opening head coach of season Y = head coach in snapshot Y-1, replaced on the dates in the curated
table. When the snapshots of Y-1 and Y disagree and the table has no row, the change is assumed to have happened after
the season and the case is written to data/features/coach_review.csv for checking.

Features per team-game (keys game_id, team_id), all from prior games or pre-season facts:
  coach_tenure_games, coach_career_games (since 2017-18), coach_new_team, coach_changed_this_season,
  coach_games_since_change, staff_size, staff_retained_share (assistants kept from the previous end-of-year snapshot),
  assoc_hc_present, coach_fp_<style> (EWM half-life 40 games over the coach's prior games with any team: pace,
  dreb_share, oreb_share, ast_rate, fg3a_rate, fta_rate, top5_min_share, n10, starters_min_share, ast_allowed_rate,
  fg3a_allowed_rate, oreb_allowed_share, margin), coach_fp_minus_team_<style> (coach fingerprint minus the team's own
  trailing 20 games) for pace, dreb_share, ast_rate and top5_min_share, and the opponent's coach as oppc_*.

Output: data/features/coach_features.parquet, data/features/coach_timeline.csv, data/features/coach_review.csv.
Usage: PYTHONUTF8=1 python tools/build_coach_features.py --seasons 2018 ... 2027
"""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FEAT = ROOT / "data" / "features"
TEAM_MAP = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}
HL_COACH = 40
L_TEAM = 20
STYLE = ["pace", "dreb_share", "oreb_share", "ast_rate", "fg3a_rate", "fta_rate", "top5_min_share", "n10",
         "starters_min_share", "ast_allowed_rate", "fg3a_allowed_rate", "oreb_allowed_share", "margin"]
DELTA = ["pace", "dreb_share", "ast_rate", "top5_min_share"]
OPP_STYLE = ["pace", "ast_allowed_rate", "fg3a_allowed_rate", "oreb_allowed_share", "dreb_share", "top5_min_share"]


def load_team_games(seasons):
    cols = ["game_id", "season", "season_type", "game_date", "game_date_time", "team_id", "team_abbreviation",
            "opponent_team_id", "assists", "defensive_rebounds", "offensive_rebounds", "field_goals_made",
            "field_goals_attempted", "three_point_field_goals_attempted", "free_throws_attempted", "turnovers",
            "team_score", "opponent_team_score"]
    frames = []
    for y in seasons:
        p = RAW / "hoopr" / f"team_box_{y}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=cols))
    tb = pd.concat(frames, ignore_index=True)
    tb = tb[(tb["team_id"] <= 30) & (tb["opponent_team_id"] <= 30)].copy()
    tb["game_date"] = pd.to_datetime(tb["game_date"]).astype("datetime64[ns]")
    tb["game_date_time"] = pd.to_datetime(tb["game_date_time"], utc=True)
    num = ["assists", "defensive_rebounds", "offensive_rebounds", "field_goals_made", "field_goals_attempted",
           "three_point_field_goals_attempted", "free_throws_attempted", "turnovers", "team_score", "opponent_team_score"]
    for c in num:
        tb[c] = pd.to_numeric(tb[c], errors="coerce")
    tb = tb.rename(columns={"assists": "ast", "defensive_rebounds": "dreb", "offensive_rebounds": "oreb",
                            "field_goals_made": "fgm", "field_goals_attempted": "fga",
                            "three_point_field_goals_attempted": "fg3a", "free_throws_attempted": "fta",
                            "turnovers": "tov"})
    tb["poss"] = tb["fga"] - tb["oreb"] + tb["tov"] + 0.44 * tb["fta"]
    opp = tb[["game_id", "team_id", "ast", "fgm", "oreb", "dreb", "fg3a", "fga", "poss"]].rename(
        columns={"team_id": "opponent_team_id", "ast": "o_ast", "fgm": "o_fgm", "oreb": "o_oreb", "dreb": "o_dreb",
                 "fg3a": "o_fg3a", "fga": "o_fga", "poss": "o_poss"})
    tb = tb.merge(opp, on=["game_id", "opponent_team_id"], how="left")
    tb["pace"] = (tb["poss"] + tb["o_poss"]) / 2
    tb["dreb_share"] = tb["dreb"] / (tb["dreb"] + tb["o_oreb"])
    tb["oreb_share"] = tb["oreb"] / (tb["oreb"] + tb["o_dreb"])
    tb["ast_rate"] = tb["ast"] / tb["fgm"]
    tb["fg3a_rate"] = tb["fg3a"] / tb["fga"]
    tb["fta_rate"] = tb["fta"] / tb["fga"]
    tb["ast_allowed_rate"] = tb["o_ast"] / tb["o_fgm"]
    tb["fg3a_allowed_rate"] = tb["o_fg3a"] / tb["o_fga"]
    tb["oreb_allowed_share"] = 1 - tb["dreb_share"]
    tb["margin"] = tb["team_score"] - tb["opponent_team_score"]
    return tb


def rotation(seasons):
    frames = []
    for y in seasons:
        p = RAW / "hoopr" / f"player_box_{y}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=["game_id", "team_id", "athlete_id", "minutes", "starter"]))
    pb = pd.concat(frames, ignore_index=True)
    pb = pb[pb["minutes"].fillna(0) > 0].copy()
    pb["starter"] = pb["starter"].fillna(False).astype(bool)
    pb = pb.sort_values(["game_id", "team_id", "minutes"], ascending=[True, True, False])
    pb["rk"] = pb.groupby(["game_id", "team_id"]).cumcount() + 1
    g = pb.groupby(["game_id", "team_id"])
    out = pd.DataFrame({
        "total_min": g["minutes"].sum(),
        "top5_min": pb[pb["rk"] <= 5].groupby(["game_id", "team_id"])["minutes"].sum(),
        "n10": g["minutes"].apply(lambda s: int((s >= 10).sum())),
        "starters_min": pb[pb["starter"]].groupby(["game_id", "team_id"])["minutes"].sum(),
    }).reset_index()
    out["top5_min_share"] = out["top5_min"] / out["total_min"]
    out["starters_min_share"] = out["starters_min"] / out["total_min"]
    return out[["game_id", "team_id", "top5_min_share", "n10", "starters_min_share"]]


def head_coach_timeline(tb, snaps, mid):
    """Per (team_id, season): ordered segments [(start_date, coach_id, coach_name, source)]."""
    abbr_of = tb.drop_duplicates("team_id").set_index("team_id")["team_abbreviation"].map(lambda a: TEAM_MAP.get(a, a))
    espn_of = {v: k for k, v in abbr_of.items()}
    snaps = snaps.copy()
    snaps["team_id"] = snaps["TEAM_ABBR"].map(espn_of)
    snaps = snaps.dropna(subset=["team_id"])
    snaps["team_id"] = snaps["team_id"].astype(int)
    hc = snaps[snaps["IS_ASSISTANT"] == 1].sort_values(["season", "team_id", "SORT_SEQUENCE"]).drop_duplicates(["season", "team_id"])
    hc_by = {(int(r.season), int(r.team_id)): (int(r.COACH_ID), r.COACH_NAME) for r in hc.itertuples()}
    names_by = {}
    for r in snaps.itertuples():
        names_by.setdefault((int(r.season), int(r.team_id)), {})[r.COACH_NAME.lower()] = int(r.COACH_ID)
    mid = mid.copy()
    mid["change_date"] = pd.to_datetime(mid["change_date"])
    mid["team_id"] = mid["team_abbr"].map(espn_of)
    seasons = sorted(tb["season"].unique())
    segments, review = {}, []
    for y in seasons:
        for t in sorted(tb.loc[tb["season"] == y, "team_id"].unique()):
            opening = hc_by.get((y - 1, t))
            source = "snapshot_prev"
            if not opening:  # the team was between coaches when the previous snapshot was taken: use the end-of-year staff
                opening = hc_by.get((y, t))
                source = "snapshot_same"
                if opening:
                    review.append({"season": y, "team_id": t, "team": abbr_of[t], "opening_hc": opening[1],
                                   "end_of_year_hc": opening[1],
                                   "status": "no head coach in the previous snapshot; opening coach taken from the end-of-year snapshot"})
            segs = []
            if opening:
                segs.append((pd.Timestamp("1900-01-01"), opening[0], opening[1], source))
            else:
                segs.append((pd.Timestamp("1900-01-01"), -1, "unknown", "missing"))
            first_game = tb.loc[(tb["season"] == y) & (tb["team_id"] == t), "game_date"].min()
            rows = mid[(mid["season"] == y) & (mid["team_id"] == t)].sort_values("change_date")
            for r in rows.itertuples():
                cid = names_by.get((y, t), {}).get(r.in_coach.lower())
                if cid is None:  # an interim absent from every snapshot: a deterministic synthetic id
                    cid = 90000000 + int(hashlib.md5(r.in_coach.encode("utf-8")).hexdigest()[:6], 16)
                if r.change_date <= first_game:  # a pre-season change: the new coach opens the season
                    segs[0] = (pd.Timestamp("1900-01-01"), cid, r.in_coach, "preseason_table")
                else:
                    segs.append((r.change_date, cid, r.in_coach, "midseason_table"))
            end = hc_by.get((y, t))
            if end and opening and end[0] != opening[0] and not len(rows):
                review.append({"season": y, "team_id": t, "team": abbr_of[t], "opening_hc": opening[1],
                               "end_of_year_hc": end[1], "status": "assumed post-season change; verify"})
            if end and len(rows) and end[0] != segs[-1][1] and segs[-1][1] > 0:
                review.append({"season": y, "team_id": t, "team": abbr_of[t], "opening_hc": opening[1] if opening else "",
                               "end_of_year_hc": end[1], "status": f"midseason table ends with {segs[-1][2]}, snapshot shows {end[1]}"})
            segments[(y, t)] = segs
    return segments, pd.DataFrame(review), snaps, abbr_of


def assign_coaches(tb, segments):
    hc_id = np.empty(len(tb), dtype=np.int64)
    hc_name = np.empty(len(tb), dtype=object)
    changed = np.zeros(len(tb), dtype=np.int8)
    change_date = np.full(len(tb), np.datetime64("NaT"), dtype="datetime64[ns]")
    for i, r in enumerate(tb[["season", "team_id", "game_date"]].itertuples(index=False)):
        segs = segments[(int(r.season), int(r.team_id))]
        cur = segs[0]
        for s in segs[1:]:
            if r.game_date >= s[0]:
                cur = s
        hc_id[i], hc_name[i] = cur[1], cur[2]
        if cur[3] == "midseason_table":
            changed[i] = 1
            change_date[i] = np.datetime64(cur[0], "ns")
    tb = tb.copy()
    tb["hc_id"], tb["hc_name"], tb["coach_changed_this_season"] = hc_id, hc_name, changed
    tb["change_date"] = change_date
    return tb


def staff_facts(snaps):
    """Pre-season staff facts for season Y from snapshots Y-1 (staff) and Y-2 (continuity)."""
    asst = snaps[snaps["IS_ASSISTANT"] == 2]
    rows = []
    keys = snaps[["season", "team_id"]].drop_duplicates()
    sets = {(int(r.season), int(r.team_id)): set(asst[(asst["season"] == r.season) & (asst["team_id"] == r.team_id)]["COACH_ID"])
            for r in keys.itertuples()}
    assoc = {(int(r.season), int(r.team_id)) for r in snaps[snaps["COACH_TYPE"] == "Associate Head Coach"][["season", "team_id"]].drop_duplicates().itertuples()}
    for (y, t), s in sets.items():
        prev = sets.get((y - 1, t))
        rows.append({"season": y + 1, "team_id": t, "staff_size": len(s),
                     "staff_retained_share": (len(s & prev) / len(prev)) if prev else np.nan,
                     "assoc_hc_present": int((y, t) in assoc)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=list(range(2018, 2028)))
    args = ap.parse_args()
    snaps = pd.read_parquet(RAW / "coaches" / "coaches_snapshots.parquet")
    mid = pd.read_csv(RAW / "coaches" / "midseason_changes.csv")
    tb = load_team_games(args.seasons)
    rot = rotation(args.seasons)
    tb = tb.merge(rot, on=["game_id", "team_id"], how="left")
    segments, review, snaps, abbr_of = head_coach_timeline(tb, snaps, mid)
    tb = assign_coaches(tb, segments)
    print(f"team-games {len(tb)}; head coach unknown on {(tb['hc_id'] == -1).sum()} rows; "
          f"{len(review)} snapshot disagreements for review")

    # coach fingerprints over prior games with any team, and tenure counts
    tb = tb.sort_values(["hc_id", "game_date_time", "game_id"]).reset_index(drop=True)
    g = tb.groupby("hc_id", sort=False)
    for s in STYLE:
        tb[f"coach_fp_{s}"] = g[s].transform(lambda x: x.shift(1).ewm(halflife=HL_COACH, min_periods=5).mean())
    tb["coach_career_games"] = g.cumcount()
    tb["coach_tenure_games"] = tb.groupby(["hc_id", "team_id"], sort=False).cumcount()
    first = tb.groupby(["hc_id", "team_id"])["game_date"].transform("min")
    season_start = tb.groupby(["team_id", "season"])["game_date"].transform("min")
    tb["coach_new_team"] = (first >= season_start).astype(np.int8)
    since = tb.groupby(["hc_id", "team_id", "season"]).cumcount()
    tb["coach_games_since_change"] = np.where(tb["coach_changed_this_season"] == 1, since, np.nan)
    tb.loc[tb["hc_id"] == -1, [c for c in tb.columns if c.startswith("coach_")]] = np.nan

    # the team's own trailing habits, for the coach-minus-team deltas
    tb = tb.sort_values(["team_id", "game_date_time", "game_id"]).reset_index(drop=True)
    gt = tb.groupby("team_id", sort=False)
    for s in DELTA:
        team_l = gt[s].transform(lambda x: x.shift(1).rolling(L_TEAM, min_periods=5).mean())
        tb[f"coach_fp_minus_team_{s}"] = tb[f"coach_fp_{s}"] - team_l

    facts = staff_facts(snaps)
    tb = tb.merge(facts, on=["season", "team_id"], how="left")

    # the opponent's coach
    opp_cols = [f"coach_fp_{s}" for s in OPP_STYLE] + ["coach_tenure_games", "coach_career_games", "coach_new_team",
                                                        "coach_changed_this_season"]
    opp = tb[["game_id", "team_id"] + opp_cols].rename(columns={"team_id": "opponent_team_id"})
    opp = opp.rename(columns={c: "oppc_" + c[len("coach_"):] for c in opp_cols})
    tb = tb.merge(opp, on=["game_id", "opponent_team_id"], how="left")

    feats = [c for c in tb.columns if c.startswith(("coach_", "staff_", "assoc_", "oppc_"))]
    out = tb[["game_id", "team_id", "opponent_team_id", "season", "game_date", "hc_id", "hc_name"] + feats]
    out.to_parquet(FEAT / "coach_features.parquet", index=False)
    tl = tb.groupby(["season", "team_id", "hc_id", "hc_name"]).agg(first_game=("game_date", "min"), last_game=("game_date", "max"),
                                                                   games=("game_id", "size")).reset_index()
    tl["team"] = tl["team_id"].map(abbr_of)
    tl.sort_values(["season", "team", "first_game"]).to_csv(FEAT / "coach_timeline.csv", index=False)
    review.to_csv(FEAT / "coach_review.csv", index=False)
    cov = out[feats].notna().mean()
    print(f"wrote coach_features.parquet: {len(out)} team-games, {len(feats)} features; "
          f"mean non-null share {cov.mean():.3f}; lowest {cov.idxmin()} {cov.min():.3f}")
    print("head coaches per season:", tl.groupby("season")["hc_id"].nunique().to_dict())
    if len(review):
        print("review cases:")
        print(review.to_string(index=False))


if __name__ == "__main__":
    main()
