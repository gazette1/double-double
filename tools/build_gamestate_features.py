"""
build_gamestate_features.py: pre-game game-state and foul-trouble features, for the controlled lift test.

Why (2026-10-30): the Stokastic reading named a double-digit spread as the blowout risk and foul trouble as the
reason one player's minutes spread differs from another's, with no numbers. tools/pair_correlation.py then
showed the mechanism is real after the fact: with a final margin under 10 points, two legs in the same game hit
together 1.05 to 1.17 times the product of their probabilities; at 20 points or more, about 0.5 times. The v1
model has no spread, total or pace-matchup input, so this builds point-in-time proxies from the box scores the
bot already holds (no price history is needed) and tools/coach_lift.py tests whether they add accuracy.

Team-game features (keyed game_id, team_id), all from games before the one in question:
  gs_exp_margin      team trailing-20 point differential minus the opponent's, plus 2.5 for home and minus 2.5
                     for away: a stand-in for the spread from the team's side
  gs_abs_exp_margin  its absolute value: the blowout proxy
  gs_exp_total       (team points for + against + opponent points for + against, trailing 20) / 2
  gs_exp_pace        team possessions x opponent possessions / league possessions (trailing 20, league to date)
  gs_pace_gap        team trailing pace minus opponent trailing pace
  gs_opp_pd_l20      the opponent's trailing-20 point differential
Player-game features (keyed game_id, athlete_id), from the player's earlier games with minutes:
  foul_pg_l10, foul_pm_l20, foul5_share_l10 (share of the last 10 games with 5 or more fouls)
  minv_cv_l10 (minutes standard deviation over mean, last 10), minv_q10_l10 (10th percentile of minutes, last 10)

Also prints the residual table that motivates the test: outcome minus v1 probability by expected-margin bucket.
Outputs data/features/gamestate_features.parquet and data/features/foul_features.parquet.
Run: PYTHONUTF8=1 python tools/build_gamestate_features.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "hoopr"
FEAT = ROOT / "data" / "features"
SEASONS = list(range(2018, 2028))
L = 20
HCA = 2.5


def log(msg, t0):
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


def team_games():
    frames = []
    for s in SEASONS:
        p = RAW / f"team_box_{s}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=[
                "game_id", "season", "season_type", "game_date_time", "team_id", "opponent_team_id", "team_home_away",
                "team_score", "opponent_team_score", "field_goals_attempted", "offensive_rebounds", "turnovers",
                "free_throws_attempted"]))
    tb = pd.concat(frames, ignore_index=True).drop_duplicates(["game_id", "team_id"])
    tb["game_date_time"] = pd.to_datetime(tb["game_date_time"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    tb = tb.sort_values(["team_id", "game_date_time", "game_id"]).reset_index(drop=True)
    tb["pd"] = tb["team_score"] - tb["opponent_team_score"]
    tb["poss"] = tb["field_goals_attempted"] - tb["offensive_rebounds"] + tb["turnovers"] + 0.44 * tb["free_throws_attempted"]
    tb["home"] = (tb["team_home_away"] == "home").astype(int)
    g = tb.groupby("team_id", sort=False)
    for c in ["pd", "team_score", "opponent_team_score", "poss"]:
        tb[f"{c}_l{L}"] = g[c].transform(lambda x: x.shift(1).rolling(L, min_periods=3).mean())
    # league possessions to date within season (shifted so the game itself is excluded)
    tb = tb.sort_values(["season", "game_date_time", "game_id"])
    tb["league_poss"] = tb.groupby("season")["poss"].transform(lambda x: x.shift(1).expanding(min_periods=30).mean())
    tb["league_poss"] = tb["league_poss"].fillna(tb.groupby("season")["poss"].transform("mean"))
    opp = tb[["game_id", "team_id", f"pd_l{L}", f"team_score_l{L}", f"opponent_team_score_l{L}", f"poss_l{L}"]].rename(
        columns={"team_id": "opponent_team_id", f"pd_l{L}": "o_pd", f"team_score_l{L}": "o_pf",
                 f"opponent_team_score_l{L}": "o_pa", f"poss_l{L}": "o_poss"})
    tb = tb.merge(opp, on=["game_id", "opponent_team_id"], how="left")
    out = tb[["game_id", "team_id", "season", "game_date_time"]].copy()
    out["gs_exp_margin"] = tb[f"pd_l{L}"] - tb["o_pd"] + HCA * np.where(tb["home"] == 1, 1, -1)
    out["gs_abs_exp_margin"] = out["gs_exp_margin"].abs()
    out["gs_exp_total"] = (tb[f"team_score_l{L}"] + tb[f"opponent_team_score_l{L}"] + tb["o_pf"] + tb["o_pa"]) / 2
    out["gs_exp_pace"] = tb[f"poss_l{L}"] * tb["o_poss"] / tb["league_poss"]
    out["gs_pace_gap"] = tb[f"poss_l{L}"] - tb["o_poss"]
    out["gs_opp_pd_l20"] = tb["o_pd"]
    out["final_margin"] = tb["pd"].abs()
    return out


def player_feats():
    frames = []
    for s in SEASONS:
        p = RAW / f"player_box_{s}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=["game_id", "athlete_id", "game_date_time", "minutes", "fouls"]))
    pb = pd.concat(frames, ignore_index=True).drop_duplicates(["game_id", "athlete_id"])
    pb["game_date_time"] = pd.to_datetime(pb["game_date_time"], utc=True, errors="coerce")
    pb = pb[pb["minutes"].fillna(0) > 0].sort_values(["athlete_id", "game_date_time", "game_id"]).reset_index(drop=True)
    pb["fouls"] = pb["fouls"].fillna(0).astype(float)
    pb["f5"] = (pb["fouls"] >= 5).astype(float)
    g = pb.groupby("athlete_id", sort=False)
    out = pb[["game_id", "athlete_id"]].copy()
    out["foul_pg_l10"] = g["fouls"].transform(lambda x: x.shift(1).rolling(10, min_periods=3).mean())
    out["foul5_share_l10"] = g["f5"].transform(lambda x: x.shift(1).rolling(10, min_periods=3).mean())
    fsum = g["fouls"].transform(lambda x: x.shift(1).rolling(20, min_periods=3).sum())
    msum = g["minutes"].transform(lambda x: x.shift(1).rolling(20, min_periods=3).sum())
    out["foul_pm_l20"] = fsum / msum.replace(0, np.nan)
    msd = g["minutes"].transform(lambda x: x.shift(1).rolling(10, min_periods=4).std())
    mmean = g["minutes"].transform(lambda x: x.shift(1).rolling(10, min_periods=4).mean())
    out["minv_cv_l10"] = msd / mmean.replace(0, np.nan)
    out["minv_q10_l10"] = g["minutes"].transform(lambda x: x.shift(1).rolling(10, min_periods=4).quantile(0.1))
    return out


def residual_table(gs, t0):
    meta = pd.read_parquet(FEAT / "dataset_v1.parquet", columns=["game_id", "athlete_id", "team_id", "starter"])
    pred = pd.read_parquet(ROOT / "data" / "eval" / "v1" / "predictions_v1.parquet",
                           columns=["game_id", "athlete_id", "dd", "p_C_full_cal", "season_type"])
    d = pred.merge(meta, on=["game_id", "athlete_id"]).merge(gs, on=["game_id", "team_id"], how="left")
    if d["season_type"].nunique() > 1:
        d = d[d["season_type"] == 2]
    d = d[d["p_C_full_cal"] >= 0.10]
    d["bucket"] = pd.cut(d["gs_abs_exp_margin"], [0, 3, 6, 9, 12, 99], right=False,
                         labels=["0-3", "3-6", "6-9", "9-12", "12+"])
    d["fav"] = np.where(d["gs_exp_margin"] > 0, "favorite", "underdog")
    lines = ["| expected |margin| | side | rows | realized | model p | realized minus p | mean final margin |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for (b, f), g in d.groupby(["bucket", "fav"], observed=True):
        lines.append(f"| {b} | {f} | {len(g):,} | {g.dd.mean():.4f} | {g.p_C_full_cal.mean():.4f} | "
                     f"{g.dd.mean() - g.p_C_full_cal.mean():+.4f} | {g.final_margin.mean():.1f} |")
    lines.append("")
    lines.append("Starters only:")
    lines.append("| expected |margin| | rows | realized | model p | realized minus p |")
    lines.append("|---|---:|---:|---:|---:|")
    for b, g in d[d["starter"] == 1].groupby("bucket", observed=True):
        lines.append(f"| {b} | {len(g):,} | {g.dd.mean():.4f} | {g.p_C_full_cal.mean():.4f} | {g.dd.mean() - g.p_C_full_cal.mean():+.4f} |")
    corr = d[["gs_abs_exp_margin", "final_margin"]].corr().iloc[0, 1]
    lines.append("")
    lines.append(f"Correlation of the expected-margin proxy with the realized final margin: {corr:.3f} "
                 f"(weak; a market closing spread would track the final margin far better, so this test understates what a real spread could add).")
    text = "\n".join(lines)
    print(text)
    (ROOT / "data" / "eval" / "pairs" / "residual_by_expected_margin.md").write_text(
        "# Outcome minus v1 probability by expected-margin bucket (test seasons, p at least 0.10)\n\n" + text + "\n",
        encoding="utf-8")
    log("residual table written to data/eval/pairs/residual_by_expected_margin.md", t0)


def main():
    t0 = time.time()
    gs = team_games()
    cov = gs[[c for c in gs.columns if c.startswith("gs_")]].notna().mean().round(3).to_dict()
    log(f"game-state features: {len(gs):,} team-games, coverage {cov}", t0)
    gs.drop(columns=["final_margin"]).to_parquet(FEAT / "gamestate_features.parquet", index=False)
    pf = player_feats()
    cov = pf[[c for c in pf.columns if c.startswith(("foul_", "minv_"))]].notna().mean().round(3).to_dict()
    log(f"foul and minutes-volatility features: {len(pf):,} player-games, coverage {cov}", t0)
    pf.to_parquet(FEAT / "foul_features.parquet", index=False)
    residual_table(gs, t0)


if __name__ == "__main__":
    main()
