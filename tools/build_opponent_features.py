#!/usr/bin/env python
"""Point-in-time opponent and matchup features for the double-double model.

Three groups, all keyed by (game_id, athlete_id) for rows of data/features/dataset_v1.parquet:
  oppx_  what the opponent allowed to the player's position group (G, F, C) over its prior 10 and 20 games,
         from the ESPN box scores: rebounds, assists, points and double-doubles per game, per-36 rates, and
         the difference from the league mean as of that date.
  oppt_  the opponent's team-level tracking and hustle profile over its prior 10 and 20 games: box outs,
         contested shots, deflections, and what it allowed in rebound chances, rebound-chance conversion,
         potential assists and assist conversion (from data/features/tracking_team_games.parquet).
  mu_    matchup features from the prior season's defender-offender matchup totals (data/raw/matchups) and the
         opponent's roster from its previous game: the expected defender mix by position for this player,
         those defenders' points and assists allowed versus expectation, the player's own defended-by profile
         and scoring by defender position, head-to-head history against tonight's roster, the best available
         defender at the player's position, and the expected defenders' current-season box-out and
         rebound-chance rates.
Every window uses games strictly before the row's game. Season-level matchup files are used only as the prior
season's profile, never the current season's, because they are full-season totals.

Usage: PYTHONUTF8=1 python tools/build_opponent_features.py [--seasons 2024 2025 2026 2027]
Writes data/features/opponent_features.parquet.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FEAT = ROOT / "data" / "features"
MU = RAW / "matchups"
POSGRP = {"G": "G", "PG": "G", "SG": "G", "F": "F", "SF": "F", "PF": "F", "C": "C"}
GRPS = ["G", "F", "C"]
BOX_COLS = ["game_id", "game_date", "season", "season_type", "athlete_id", "athlete_position_abbreviation",
            "team_id", "opponent_team_id", "minutes", "points", "rebounds", "assists", "steals", "blocks"]
TRK_DEF_COLS = ["trk_boxouts_pm_ewm", "trk_defbox_pm_ewm", "trk_rebch_pm_ewm"]


def load_box(seasons):
    pb = pd.concat([pd.read_parquet(RAW / "hoopr" / f"player_box_{y}.parquet", columns=BOX_COLS)
                    for y in seasons], ignore_index=True)
    pb = pb[(pb["minutes"] > 0) & (pb["team_id"] <= 30) & (pb["opponent_team_id"] <= 30)]
    pb = pb.drop_duplicates(["game_id", "athlete_id"]).copy()
    pb["game_date"] = pd.to_datetime(pb["game_date"]).dt.normalize().astype("datetime64[ns]")
    pb["posgrp"] = pb["athlete_position_abbreviation"].map(POSGRP).fillna("F")
    pb["dd"] = ((pb[["points", "rebounds", "assists", "steals", "blocks"]] >= 10).sum(axis=1) >= 2).astype(int)
    return pb


def rolling_prior(df, stat_cols, windows=(10, 20), min_games=3):
    """df: one row per team-game with team_id, game_id, game_date and stat_cols. Returns a frame aligned to
    df with <stat>_l<w> sums over the team's prior w games and n_l<w> counts of those games."""
    df = df.sort_values(["team_id", "game_date", "game_id"])
    sh = df.groupby("team_id")[stat_cols].shift(1)
    out = df[["team_id", "game_id", "game_date"]].copy()
    ones = sh[stat_cols[0]].notna().astype(float)
    for w in windows:
        S = sh.groupby(df["team_id"]).transform(lambda s: s.rolling(w, min_periods=min_games).sum())
        for c in stat_cols:
            out[f"{c}_l{w}"] = S[c]
        out[f"n_l{w}"] = ones.groupby(df["team_id"]).transform(lambda s: s.rolling(w, min_periods=min_games).sum())
    return out


def position_allowed(pb, rows):
    g = (pb.groupby(["opponent_team_id", "game_id", "game_date", "season", "posgrp"])
         .agg(reb=("rebounds", "sum"), ast=("assists", "sum"), pts=("points", "sum"), mins=("minutes", "sum"),
              dd=("dd", "sum")).reset_index().rename(columns={"opponent_team_id": "team_id"}))
    w = g.pivot_table(index=["team_id", "game_id", "game_date", "season"], columns="posgrp",
                      values=["reb", "ast", "pts", "mins", "dd"], aggfunc="sum", fill_value=0)
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    stat_cols = [c for c in w.columns if c not in ("team_id", "game_id", "game_date", "season")]
    r = rolling_prior(w, stat_cols)
    daily = w.groupby(["season", "game_date"])[stat_cols].sum()
    daily["n"] = w.groupby(["season", "game_date"]).size()
    prior = daily.groupby(level=0).cumsum().groupby(level=0).shift(1)
    lg = prior[stat_cols].div(prior["n"], axis=0)
    season_mean = daily[stat_cols].groupby(level=0).sum().div(daily["n"].groupby(level=0).sum(), axis=0)
    prev_mean = season_mean.shift(1)
    lg = lg.reset_index()
    for c in stat_cols:
        lg[c] = lg[c].fillna(lg["season"].map(prev_mean[c]))
    lg = lg.rename(columns={c: f"lg_{c}" for c in stat_cols})
    r = r.merge(w[["team_id", "game_id", "season"]], on=["team_id", "game_id"])
    r = r.merge(lg, on=["season", "game_date"], how="left")
    x = rows.merge(r, left_on=["opponent_team_id", "game_id"], right_on=["team_id", "game_id"], how="left",
                   suffixes=("", "_r"))
    conds = [(x["posgrp"] == p).to_numpy() for p in GRPS]

    def pick(stat, w):
        return np.select(conds, [x[f"{stat}_{p}_l{w}"].to_numpy(float) for p in GRPS], np.nan)

    def pick_lg(stat):
        return np.select(conds, [x[f"lg_{stat}_{p}"].to_numpy(float) for p in GRPS], np.nan)

    out = rows[["game_id", "athlete_id"]].copy()
    for w in (10, 20):
        n = x[f"n_l{w}"].to_numpy(float)
        for stat in ("reb", "ast", "pts"):
            out[f"oppx_{stat}_allowed_pos_l{w}"] = pick(stat, w) / n
    n = x["n_l20"].to_numpy(float)
    mins = pick("mins", 20)
    out["oppx_dd_allowed_pos_l20"] = pick("dd", 20) / n
    out["oppx_mins_allowed_pos_l20"] = mins / n
    for stat in ("reb", "ast", "pts"):
        out[f"oppx_{stat}36_allowed_pos_l20"] = pick(stat, 20) / mins * 36
        out[f"oppx_{stat}_allowed_pos_rel_l20"] = pick(stat, 20) / n - pick_lg(stat)
    return out


def opponent_tracking(rows):
    f = FEAT / "tracking_team_games.parquet"
    if not f.exists():
        print("  tracking_team_games.parquet missing, skipping oppt_ features")
        return None
    tg = pd.read_parquet(f)
    sums = [c for c in tg.columns if c not in ("game_id", "team_id", "opponent_team_id", "game_date", "season")]
    other = (tg[["game_id", "team_id"] + sums].rename(columns={"team_id": "opponent_team_id"})
             .rename(columns={c: f"al_{c}" for c in sums}))
    m = tg.merge(other, on=["game_id", "opponent_team_id"], how="left")
    stat_cols = sums + [f"al_{c}" for c in sums]
    r = rolling_prior(m, stat_cols)
    x = rows.merge(r, left_on=["opponent_team_id", "game_id"], right_on=["team_id", "game_id"], how="left",
                   suffixes=("", "_r"))
    out = rows[["game_id", "athlete_id"]].copy()
    v = lambda c: x[c].to_numpy(float)
    for w in (10, 20):
        n = v(f"n_l{w}")
        for c in ("boxouts", "defbox", "contested", "deflect"):
            out[f"oppt_{c}_l{w}"] = v(f"{c}_l{w}") / n
        out[f"oppt_al_rebch_l{w}"] = v(f"al_rebch_l{w}") / n
        out[f"oppt_al_rebch_conv_l{w}"] = v(f"al_trk_reb_l{w}") / v(f"al_rebch_l{w}")
        out[f"oppt_al_potast_l{w}"] = v(f"al_potast_l{w}") / n
        out[f"oppt_al_ast_conv_l{w}"] = v(f"al_trk_ast_l{w}") / v(f"al_potast_l{w}")
    n = v("n_l20")
    out["oppt_loose_l20"] = v("loose_l20") / n
    out["oppt_screenast_l20"] = v("screenast_l20") / n
    out["oppt_rebch_conv_l20"] = v("trk_reb_l20") / v("rebch_l20")
    out["oppt_al_passes_l20"] = v("al_passes_l20") / n
    out["oppt_al_rebcon_share_l20"] = v("al_rebcon_l20") / v("al_trk_reb_l20")
    return out


def weighted(X, col, w="wh"):
    """Weighted-sum numerator and the weight mass where col is known, for NaN-aware weighted means."""
    X[f"num_{col}"] = X[w] * X[col]
    X[f"den_{col}"] = X[w].where(X[col].notna())


def matchup_features(rows, pb, trkf):
    cw_path = RAW / "tracking" / "crosswalk.csv"
    if not cw_path.exists():
        print("  crosswalk.csv missing, skipping mu_ features")
        return None
    cw = pd.read_csv(cw_path).set_index("PLAYER_ID")["athlete_id"]
    pos = (pb.groupby(["season", "athlete_id"])["posgrp"]
           .agg(lambda s: s.value_counts().index[0]).reset_index())
    tg = pb[["team_id", "game_id", "game_date"]].drop_duplicates().sort_values(["team_id", "game_date", "game_id"])
    tg["prev_game_id"] = tg.groupby("team_id")["game_id"].shift(1)
    ros = (pb.loc[pb["minutes"] >= 10, ["team_id", "game_id", "athlete_id", "minutes"]]
           .rename(columns={"game_id": "prev_game_id", "athlete_id": "def_aid", "minutes": "prev_min"}))
    roster = tg.merge(ros, on=["team_id", "prev_game_id"])[["team_id", "game_id", "def_aid", "prev_min"]]
    roster["def_aid"] = roster["def_aid"].astype("int64")
    T = None
    if trkf is not None:
        T = (trkf[["athlete_id", "game_date"] + TRK_DEF_COLS].rename(columns={"athlete_id": "def_aid"}))
        T["def_aid"] = T["def_aid"].astype("int64")
        T["game_date"] = pd.to_datetime(T["game_date"]).astype("datetime64[ns]")
        T = T.sort_values("game_date")
    outs = []
    for y in sorted(rows["season"].unique()):
        f = MU / f"matchups_{y - 1}.parquet"
        r = rows[rows["season"] == y]
        if not f.exists():
            print(f"  matchups: no prior-season file for season {y}, skipping mu_ for that season")
            continue
        m = pd.read_parquet(f)
        m["off_aid"] = m["OFF_PLAYER_ID"].map(cw)
        m["def_aid"] = m["DEF_PLAYER_ID"].map(cw)
        m = m.dropna(subset=["off_aid", "def_aid"]).astype({"off_aid": "int64", "def_aid": "int64"})
        m = m.rename(columns={"PARTIAL_POSS": "poss", "PLAYER_PTS": "pts", "MATCHUP_AST": "ast"})
        m = m.loc[m["poss"] > 0, ["off_aid", "def_aid", "poss", "pts", "ast"]]
        pprev = pos[pos["season"] == y - 1].set_index("athlete_id")["posgrp"]
        pcur = pos[pos["season"] == y].set_index("athlete_id")["posgrp"]
        m["off_pg"] = m["off_aid"].map(pprev).fillna(m["off_aid"].map(pcur)).fillna("F")
        m["def_pg"] = m["def_aid"].map(pprev).fillna(m["def_aid"].map(pcur)).fillna("F")
        off = m.groupby("off_aid").agg(poss=("poss", "sum"), pts=("pts", "sum"), ast=("ast", "sum"))
        off["pts100"] = off["pts"] / off["poss"] * 100
        off["ast100"] = off["ast"] / off["poss"] * 100
        m["exp_pts"] = m["off_aid"].map(off["pts100"]) * m["poss"] / 100
        m["exp_ast"] = m["off_aid"].map(off["ast100"]) * m["poss"] / 100
        d = m.groupby("def_aid").agg(poss=("poss", "sum"), pts=("pts", "sum"), ast=("ast", "sum"),
                                     exp_pts=("exp_pts", "sum"), exp_ast=("exp_ast", "sum"))
        d["pts_vs_exp"] = (d["pts"] - d["exp_pts"]) / d["poss"] * 100
        d["ast_vs_exp"] = (d["ast"] - d["exp_ast"]) / d["poss"] * 100
        sh = m.pivot_table(index="def_aid", columns="off_pg", values="poss", aggfunc="sum", fill_value=0)
        vp = m.pivot_table(index="def_aid", columns="off_pg", values="pts", aggfunc="sum", fill_value=0)
        sh = sh.reindex(columns=GRPS, fill_value=0)
        vp = vp.reindex(columns=GRPS, fill_value=0)
        for p in GRPS:
            d[f"share_{p}"] = sh[p] / d["poss"]
            d[f"pa100_vs_{p}"] = vp[p] / sh[p].replace(0, np.nan) * 100
        d = d[d["poss"] >= 100]
        lg_share = m.pivot_table(index="def_pg", columns="off_pg", values="poss", aggfunc="sum", fill_value=0)
        lg_share = lg_share.reindex(columns=GRPS, fill_value=0)
        lg_share = lg_share.div(lg_share.sum(axis=1), axis=0)
        osh = m.pivot_table(index="off_aid", columns="def_pg", values="poss", aggfunc="sum", fill_value=0)
        opt = m.pivot_table(index="off_aid", columns="def_pg", values="pts", aggfunc="sum", fill_value=0)
        osh = osh.reindex(columns=GRPS, fill_value=0)
        opt = opt.reindex(columns=GRPS, fill_value=0)
        o = off.copy()
        for p in GRPS:
            o[f"defby_{p}"] = osh[p] / o["poss"]
            o[f"pts100_vs_{p}"] = opt[p] / osh[p].replace(0, np.nan) * 100
        o = o[o["poss"] >= 100]
        h2h = (m.groupby(["off_aid", "def_aid"])
               .agg(h_poss=("poss", "sum"), h_pts=("pts", "sum"), h_ast=("ast", "sum")).reset_index())

        X = r[["game_id", "athlete_id", "opponent_team_id", "game_date", "posgrp"]].merge(
            roster, left_on=["opponent_team_id", "game_id"], right_on=["team_id", "game_id"], how="inner")
        X["athlete_id"] = X["athlete_id"].astype("int64")
        X = X.merge(d.add_prefix("d_"), left_on="def_aid", right_index=True, how="left")
        X["def_pg"] = X["def_aid"].map(pcur).fillna(X["def_aid"].map(pprev)).fillna("F")
        for p in GRPS:
            X[f"d_share_{p}"] = X[f"d_share_{p}"].fillna(X["def_pg"].map(lg_share[p]))
        X["d_pts_vs_exp"] = X["d_pts_vs_exp"].fillna(0.0)
        X["d_ast_vs_exp"] = X["d_ast_vs_exp"].fillna(0.0)
        conds = [(X["posgrp"] == p).to_numpy() for p in GRPS]
        X["share_vs_p"] = np.select(conds, [X[f"d_share_{p}"].to_numpy(float) for p in GRPS], np.nan)
        X["pa100_vs_p"] = np.select(conds, [X[f"d_pa100_vs_{p}"].to_numpy(float) for p in GRPS], np.nan)
        X = X.merge(h2h, left_on=["athlete_id", "def_aid"], right_on=["off_aid", "def_aid"], how="left")
        for c in ("h_poss", "h_pts", "h_ast"):
            X[c] = X[c].fillna(0.0)
        X["w0"] = X["prev_min"] * X["share_vs_p"]
        grp = X.groupby(["game_id", "athlete_id"])
        X["w"] = X["w0"] / grp["w0"].transform("sum")
        X["hs"] = grp["h_poss"].transform("sum")
        X["wh"] = np.where(X["hs"] >= 20, 0.5 * X["w"] + 0.5 * X["h_poss"] / X["hs"].where(X["hs"] > 0), X["w"])
        if T is not None:
            X["game_date"] = pd.to_datetime(X["game_date"]).astype("datetime64[ns]")
            X = pd.merge_asof(X.sort_values("game_date"), T, on="game_date", by="def_aid", direction="backward")
        for p in GRPS:
            X[f"pos_{p}"] = (X["def_pg"] == p).astype(float)
        wcols = ["d_pts_vs_exp", "d_ast_vs_exp", "pa100_vs_p", "pos_G", "pos_F", "pos_C"] + (TRK_DEF_COLS if T is not None else [])
        for c in wcols:
            weighted(X, c)
        elig = X["d_poss"].notna() & (X["share_vs_p"] >= 0.4)
        X["elig_pve"] = X["d_pts_vs_exp"].where(elig)
        agg = {f"num_{c}": (f"num_{c}", "sum") for c in wcols}
        agg.update({f"den_{c}": (f"den_{c}", "sum") for c in wcols})
        agg.update(mu_h2h_poss=("h_poss", "sum"), h_pts=("h_pts", "sum"), h_ast=("h_ast", "sum"),
                   mu_best_def_vs_pos=("elig_pve", "min"), mu_n_def_vs_pos=("elig_pve", "count"),
                   mu_n_roster=("def_aid", "size"))
        A = X.groupby(["game_id", "athlete_id"]).agg(**agg).reset_index()
        names = {"d_pts_vs_exp": "mu_def_pts_vs_exp", "d_ast_vs_exp": "mu_def_ast_vs_exp",
                 "pa100_vs_p": "mu_def_pa100_vs_pos", "pos_G": "mu_def_pos_G", "pos_F": "mu_def_pos_F",
                 "pos_C": "mu_def_pos_C", "trk_boxouts_pm_ewm": "mu_def_boxouts_pm",
                 "trk_defbox_pm_ewm": "mu_def_defbox_pm", "trk_rebch_pm_ewm": "mu_def_rebch_pm"}
        for c in wcols:
            A[names[c]] = A[f"num_{c}"] / A[f"den_{c}"].where(A[f"den_{c}"] > 0)
            A = A.drop(columns=[f"num_{c}", f"den_{c}"])
        A["mu_h2h_pts100"] = (A["h_pts"] / A["mu_h2h_poss"] * 100).where(A["mu_h2h_poss"] >= 10)
        A["mu_h2h_ast100"] = (A["h_ast"] / A["mu_h2h_poss"] * 100).where(A["mu_h2h_poss"] >= 10)
        A = A.drop(columns=["h_pts", "h_ast"])
        A = A.merge(o[["pts100", "ast100"] + [f"defby_{p}" for p in GRPS] + [f"pts100_vs_{p}" for p in GRPS]]
                    .rename(columns={"pts100": "mu_off_pts100", "ast100": "mu_off_ast100",
                                     **{f"defby_{p}": f"mu_off_defby_{p}" for p in GRPS}}),
                    left_on="athlete_id", right_index=True, how="left")
        fit = np.zeros(len(A))
        for p in GRPS:
            fit = fit + A[f"mu_def_pos_{p}"].fillna(0).to_numpy() * A[f"pts100_vs_{p}"].fillna(A["mu_off_pts100"]).to_numpy()
        A["mu_off_fit"] = fit - A["mu_off_pts100"].to_numpy()
        A = A.drop(columns=[f"pts100_vs_{p}" for p in GRPS])
        outs.append(A)
        print(f"  matchups season {y}: prior-season pairs {len(m)}, defender profiles {len(d)}, "
              f"offense profiles {len(o)}, rows with features {len(A)} of {len(r)}")
    if not outs:
        return None
    return pd.concat(outs, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026, 2027])
    args = ap.parse_args()
    box_seasons = list(range(min(args.seasons) - 2, max(args.seasons) + 1))
    pb = load_box([y for y in box_seasons if (RAW / "hoopr" / f"player_box_{y}.parquet").exists()])
    ds = pd.read_parquet(FEAT / "dataset_v1.parquet",
                         columns=["game_id", "athlete_id", "team_id", "opponent_team_id", "game_date", "season",
                                  "season_type", "position"])
    rows = ds[ds["season"].isin(args.seasons)].copy()
    rows["game_date"] = pd.to_datetime(rows["game_date"]).dt.normalize().astype("datetime64[ns]")
    rows["posgrp"] = rows["position"].astype(str).map(POSGRP).fillna("F")
    print(f"rows: {len(rows)} dataset rows in seasons {args.seasons}")
    out = rows[["game_id", "athlete_id"]].copy()
    px = position_allowed(pb, rows)
    out = out.merge(px, on=["game_id", "athlete_id"], how="left")
    print(f"oppx_: {px.shape[1] - 2} features, non-null share {px.filter(like='oppx_').notna().mean().mean():.3f}")
    pt = opponent_tracking(rows)
    if pt is not None:
        out = out.merge(pt, on=["game_id", "athlete_id"], how="left")
        print(f"oppt_: {pt.shape[1] - 2} features, non-null share {pt.filter(like='oppt_').notna().mean().mean():.3f}")
    trkf = pd.read_parquet(FEAT / "tracking_features.parquet") if (FEAT / "tracking_features.parquet").exists() else None
    mu = matchup_features(rows, pb, trkf)
    if mu is not None:
        out = out.merge(mu, on=["game_id", "athlete_id"], how="left")
        print(f"mu_: {mu.shape[1] - 2} features, non-null share "
              f"{out.filter(like='mu_').notna().mean().mean():.3f} over all rows")
    out = out.replace([np.inf, -np.inf], np.nan)
    out.to_parquet(FEAT / "opponent_features.parquet", index=False)
    print(f"wrote opponent_features.parquet: {out.shape[0]} rows, {out.shape[1] - 2} features")


if __name__ == "__main__":
    main()
