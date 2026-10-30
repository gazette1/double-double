"""
build_shot_features.py: open-look features from the closest-defender shot pull, for the controlled lift test.

Russ, 2026-10-30: "open 3s taken (for assist)". From data/raw/shots/ (tools/pull_shot_quality.py: each player's
attempts per game in the 4-6 feet "open" and 6+ feet "wide open" bands) and the hoopR box scores, keyed to the
bot's rows through the tracking crosswalk. Every feature uses games before the one in question.

Player (prefix shot_):
  shot_open3a_pm_l10 / _ewm   open plus wide-open three-point attempts per minute
  shot_wide3a_pm_l10          wide-open three-point attempts per minute
  shot_open3_share_l20        share of the player's threes that were open or wide open
  shot_open3_pct_l20          make rate on those open threes
  shot_openfga_pm_l10         open plus wide-open attempts of any kind per minute
Teammates and opponent, for the passer and the rebounder:
  shot_tm_open3a_pg_l10       the team's open plus wide-open threes per game (trailing 10)
  shot_tmx_open3a_pg_l10      the same less the player's own: the open looks his teammates take
  shot_tm_open3_share_l20     share of the team's threes that were open
  shot_tm_open3_pct_l20       the team's make rate on open threes (assists need makes)
  shot_opp_open3a_allowed_l10 open plus wide-open threes the opponent has allowed per game (trailing 10)
Output data/features/shot_features.parquet keyed game_id, athlete_id. Works on a partial pull (missing dates are
simply absent from the trailing windows), so run it again after the pull completes.
Run: PYTHONUTF8=1 python tools/build_shot_features.py
"""
import glob
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FEAT = ROOT / "data" / "features"
HALFLIFE = 8


def log(msg, t0):
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


def load_shots():
    files = [f for f in glob.glob(str(RAW / "shots" / "*.parquet")) if not Path(f).name.startswith("shots_")]
    df = pd.concat([pd.read_parquet(f, columns=["season", "game_date", "band", "PLAYER_ID", "PLAYER_LAST_TEAM_ID",
                                                "FGA", "FG3A", "FG3M"]) for f in files], ignore_index=True)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.normalize()
    w = df.pivot_table(index=["game_date", "PLAYER_ID"], columns="band", values=["FGA", "FG3A", "FG3M"],
                       aggfunc="sum", fill_value=0)
    w.columns = [f"{b}_{v.lower()}" for v, b in w.columns]
    w = w.reset_index()
    for c in ["open_fga", "open_fg3a", "open_fg3m", "wide_fga", "wide_fg3a", "wide_fg3m"]:
        if c not in w:
            w[c] = 0
    w["o3a"] = w["open_fg3a"] + w["wide_fg3a"]
    w["o3m"] = w["open_fg3m"] + w["wide_fg3m"]
    w["ofga"] = w["open_fga"] + w["wide_fga"]
    dates = sorted(df["game_date"].unique())
    return w[["game_date", "PLAYER_ID", "o3a", "o3m", "ofga", "wide_fg3a"]], dates


def main():
    t0 = time.time()
    shots, dates = load_shots()
    log(f"shot rows {len(shots):,} over {len(dates)} game dates ({dates[0]:%Y-%m-%d} to {dates[-1]:%Y-%m-%d})", t0)
    cw = pd.read_csv(RAW / "tracking" / "crosswalk.csv").dropna(subset=["athlete_id"])
    cw["athlete_id"] = cw["athlete_id"].astype(int)
    shots = shots.merge(cw[["PLAYER_ID", "athlete_id"]].drop_duplicates("PLAYER_ID"), on="PLAYER_ID", how="inner")
    tg = pd.read_parquet(FEAT / "tracking_games.parquet",
                         columns=["athlete_id", "game_id", "game_date", "team_id", "opponent_team_id", "trk_min"])
    tg["game_date"] = pd.to_datetime(tg["game_date"]).dt.normalize()
    tg = tg[tg["game_date"].isin(dates)].dropna(subset=["game_id"]).copy()
    tg["game_id"] = tg["game_id"].astype(int)
    frames = []
    for y in sorted({d.year + (1 if d.month >= 7 else 0) for d in dates}):
        p = RAW / "hoopr" / f"player_box_{y}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=["game_id", "athlete_id", "field_goals_attempted",
                                                     "three_point_field_goals_attempted"]))
    pb = pd.concat(frames, ignore_index=True).drop_duplicates(["game_id", "athlete_id"])
    pb = pb.rename(columns={"field_goals_attempted": "fga", "three_point_field_goals_attempted": "fg3a"})
    d = tg.merge(shots.drop(columns=["PLAYER_ID"]), on=["athlete_id", "game_date"], how="left")
    d = d.merge(pb, on=["game_id", "athlete_id"], how="left")
    for c in ["o3a", "o3m", "ofga", "wide_fg3a"]:
        d[c] = d[c].fillna(0.0)
    log(f"player-games on pulled dates {len(d):,}; with any open attempt {(d.o3a + d.ofga > 0).mean():.3f}", t0)

    # player point-in-time
    d = d.sort_values(["athlete_id", "game_date", "game_id"]).reset_index(drop=True)
    g = d.groupby("athlete_id", sort=False)
    X = d[["o3a", "o3m", "ofga", "wide_fg3a", "fg3a", "trk_min"]].astype(float)
    Xs = X.groupby(d["athlete_id"]).shift(1)
    out = d[["game_id", "athlete_id"]].copy()

    def rsum(col, w):
        return Xs[col].groupby(d["athlete_id"]).transform(lambda x: x.rolling(w, min_periods=3).sum())

    out["shot_open3a_pm_l10"] = rsum("o3a", 10) / rsum("trk_min", 10)
    out["shot_wide3a_pm_l10"] = rsum("wide_fg3a", 10) / rsum("trk_min", 10)
    out["shot_openfga_pm_l10"] = rsum("ofga", 10) / rsum("trk_min", 10)
    out["shot_open3_share_l20"] = rsum("o3a", 20) / rsum("fg3a", 20).replace(0, np.nan)
    out["shot_open3_pct_l20"] = rsum("o3m", 20) / rsum("o3a", 20).replace(0, np.nan)
    E = Xs.groupby(d["athlete_id"]).transform(lambda x: x.ewm(halflife=HALFLIFE, min_periods=3).mean())
    out["shot_open3a_pm_ewm"] = E["o3a"] / E["trk_min"]
    own_pg10 = rsum("o3a", 10) / 10.0

    # team point-in-time
    tm = d.groupby(["team_id", "game_id", "game_date", "opponent_team_id"], as_index=False)[["o3a", "o3m", "fg3a"]].sum()
    tm = tm.sort_values(["team_id", "game_date", "game_id"]).reset_index(drop=True)
    T = tm[["o3a", "o3m", "fg3a"]].groupby(tm["team_id"]).shift(1)

    def tsum(col, w):
        return T[col].groupby(tm["team_id"]).transform(lambda x: x.rolling(w, min_periods=3).sum())

    def tcnt(w):
        return T["o3a"].groupby(tm["team_id"]).transform(lambda x: x.rolling(w, min_periods=3).count())

    tm["shot_tm_open3a_pg_l10"] = tsum("o3a", 10) / tcnt(10)
    tm["shot_tm_open3_share_l20"] = tsum("o3a", 20) / tsum("fg3a", 20).replace(0, np.nan)
    tm["shot_tm_open3_pct_l20"] = tsum("o3m", 20) / tsum("o3a", 20).replace(0, np.nan)
    # allowed: what this team's opponents took against it, trailing
    allowed = tm[["game_id", "team_id", "o3a"]].rename(columns={"team_id": "opponent_team_id", "o3a": "o3a_allowed"})
    tm = tm.merge(allowed, on=["game_id", "opponent_team_id"], how="left")
    A = tm["o3a_allowed"].groupby(tm["team_id"]).shift(1)
    tm["own_allowed_l10"] = A.groupby(tm["team_id"]).transform(lambda x: x.rolling(10, min_periods=3).mean())
    opp_allowed = tm[["game_id", "team_id", "own_allowed_l10"]].rename(
        columns={"team_id": "opponent_team_id", "own_allowed_l10": "shot_opp_open3a_allowed_l10"})
    tm = tm.merge(opp_allowed, on=["game_id", "opponent_team_id"], how="left")
    tcols = ["shot_tm_open3a_pg_l10", "shot_tm_open3_share_l20", "shot_tm_open3_pct_l20", "shot_opp_open3a_allowed_l10"]
    out = out.merge(d[["game_id", "athlete_id", "team_id"]], on=["game_id", "athlete_id"]).merge(
        tm[["game_id", "team_id"] + tcols], on=["game_id", "team_id"], how="left")
    out["shot_tmx_open3a_pg_l10"] = out["shot_tm_open3a_pg_l10"] - own_pg10.to_numpy()
    out = out.drop(columns=["team_id"]).drop_duplicates(["game_id", "athlete_id"])
    feats = [c for c in out.columns if c.startswith("shot_")]
    log(f"features {len(feats)}: coverage {out[feats].notna().mean().round(3).to_dict()}", t0)
    print(out[feats].describe().T[["mean", "50%", "std"]].round(3).to_string())
    out.to_parquet(FEAT / "shot_features.parquet", index=False)
    log(f"wrote {FEAT / 'shot_features.parquet'} ({len(out):,} rows)", t0)


if __name__ == "__main__":
    main()
