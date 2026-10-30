#!/usr/bin/env python
"""Controlled lift test: do tracking, opponent and matchup features add information over the v1 feature set?

Rows: regular-season rows of data/features/dataset_v1.parquet in the tracking era (season keys 2024 to 2026),
with data/features/tracking_features.parquet (player tracking, prefix trk_), data/features/opponent_features.parquet
(oppx_ position-allowed, oppt_ opponent tracking profile, mu_ matchup) and the saved v1 predictions.

Walk-forward: test 2025 trained on 2024; test 2026 trained on 2024 and 2025. The last 15 percent of training
rows by date are the holdout for early stopping and Platt calibration, as in v1 and v2. Variants share the
identical rows, hyperparameters, seed and calibration, so differences come from the feature groups alone:
  BASE       the 155 v1 features (including abs_ and position)
  BASE+TRK   plus player tracking features and two composites (expected rebound chances and potential assists)
  BASE+OPP   plus opponent position-allowed and opponent tracking profile
  BASE+MU    plus matchup features
  BASE+ALL   plus all three groups
  REF        the saved v1 C_full calibrated prediction (trained on 2018 onward, all season types), for scale
  STACK_BASE small LightGBM on logit(REF), min_ewm and position (a recalibration of REF)
  STACK_ALL  the same plus all new features: the incremental information over the full-history model
  RESID_NONE residual boosting from logit(REF) as init_score with only min_ewm and position (control)
  RESID_TRK  residual boosting from logit(REF) with the tracking features: zero trees equals REF exactly
  RESID_OPP  the same with the opponent features
  RESID_MU   the same with the matchup features
  RESID_ALL  the same with all three groups
  BLEND      0.5/0.5 logit blend of REF and BASE+ALL (diagnostic)
  --extra FILE adds one more feature group keyed game_id, athlete_id (prefixes --extra-prefix, label --extra-name):
             BASE+NAME, BASE+TRK+NAME, RESID_NAME and RESID_TRK+NAME, bootstrapped against BASE, BASE+TRK, REF,
             RESID_NONE and RESID_TRK (used 2026-10-30 for the open-look shot features, data/eval/shots_era/)
Outputs under data/eval/tracking/: report_tracking.md and CSVs. Models under data/models/tracking/.

Usage: PYTHONUTF8=1 python tools/tracking_lift.py [--out DIR]
       [--extra data/features/shot_features.parquet --extra-prefix shot_ --extra-name SHOT]
"""
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data" / "features"
EVAL = ROOT / "data" / "eval" / "tracking"
MODELS = ROOT / "data" / "models" / "tracking"
SEED = 42
HOLDOUT_FRAC = 0.15
EARLY_STOP = 100
MAX_ROUNDS = 3000
P_CLIP = 1e-4
Q_MIN = 0.20
TEST_SEASONS = [2025, 2026]
FIRST_TRAIN = 2024
EXTRA_NAME = None  # an optional extra feature group, see --extra
EXTRA_PREFIXES = ()
LGB_PARAMS = {
    "objective": "binary", "metric": "binary_logloss", "num_leaves": 31, "learning_rate": 0.03,
    "min_child_samples": 100, "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1,
    "lambda_l2": 5.0, "seed": SEED, "deterministic": True, "force_col_wise": True, "num_threads": 8,
    "verbose": -1,
}
STACK_PARAMS = dict(LGB_PARAMS, num_leaves=15, min_child_samples=200)
T0 = time.time()


def log(msg):
    print(f"[{(time.time() - T0) / 60:5.1f} min] {msg}", flush=True)


def clip(p):
    return np.clip(np.asarray(p, dtype=float), P_CLIP, 1 - P_CLIP)


def logit(p):
    p = clip(p)
    return np.log(p / (1 - p))


def sigmoid(z):
    return 1 / (1 + np.exp(-np.asarray(z, dtype=float)))


def ll_rows(y, p):
    p = clip(p)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def basic_metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return {"n": int(len(y)), "base_rate": float(y.mean()), "logloss": float(ll_rows(y, p).mean()),
            "brier": float(((p - y) ** 2).mean()),
            "auc": float(roc_auc_score(y, p)) if 0 < y.mean() < 1 else np.nan}


def fit_platt(p, y):
    lr = LogisticRegression(C=1e6, max_iter=1000)
    lr.fit(logit(p).reshape(-1, 1), y)
    return lr


def apply_platt(lr, p):
    return lr.predict_proba(logit(p).reshape(-1, 1))[:, 1]


def holdout_split(train):
    order = train.sort_values(["game_date", "game_id", "athlete_id"])
    dates = order["game_date"].to_numpy()
    cut = dates[int(np.floor((1 - HOLDOUT_FRAC) * len(order)))]
    hold = order["game_date"] >= cut
    return order[~hold], order[hold], pd.Timestamp(cut)


def group_of(feature):
    if EXTRA_PREFIXES and feature.startswith(tuple(EXTRA_PREFIXES)):
        return EXTRA_NAME
    if feature.startswith(("trk_", "exp_")):
        return "TRK"
    if feature.startswith(("oppx_", "oppt_")):
        return "OPP"
    if feature.startswith("mu_"):
        return "MU"
    if feature in ("z_ref",):
        return "REF"
    return "BASE"


def md(df, digits=4):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else f"{v:.{digits}f}")
    lines = ["| " + " | ".join(str(c) for c in df.columns) + " |",
             "|" + "|".join(["---"] * len(df.columns)) + "|"]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in r) + " |")
    return "\n".join(lines)


def top3(df, col):
    d = df.sort_values(["game_date", col, "athlete_id"], ascending=[True, False, True]).copy()
    d["rk"] = d.groupby("game_date").cumcount() + 1
    top = d[d["rk"] <= 3]
    per = top.groupby("game_date")["dd"].agg(["sum", "size"])
    full = per[per["size"] == 3]
    return {"nights": int(top["game_date"].nunique()), "top1_hit": float(top.loc[top["rk"] == 1, "dd"].mean()),
            "top3_hit": float(top["dd"].mean()), "all3_hit": float((full["sum"] == 3).mean()),
            "mean_p_top3": float(top[col].mean()), "distinct_players": int(top["athlete_id"].nunique())}


def edge_top3(df, col):
    q = np.minimum(0.97, 1.08 * df["p_A_cal"].to_numpy(float))
    d = df.assign(q=q, edge=df[col].to_numpy(float) - q)
    d = d[d["q"] >= Q_MIN].sort_values(["game_date", "edge", "athlete_id"], ascending=[True, False, True]).copy()
    d["rk"] = d.groupby("game_date").cumcount() + 1
    top = d[d["rk"] <= 3]
    ret = top["dd"] * (1 - top["q"]) / top["q"] - (1 - top["dd"])
    return {"picks": int(len(top)), "hit": float(top["dd"].mean()), "mean_q": float(top["q"].mean()),
            "mean_p": float(top[col].mean()), "mean_edge": float(top["edge"].mean()),
            "ret_per_unit": float(ret.mean())}


def block_bootstrap(df, cols, base_col, n_boot=1000):
    y = df["dd"].to_numpy(float)
    per = pd.DataFrame({c: ll_rows(y, df[c].to_numpy(float)) for c in cols + [base_col]})
    per["game_date"] = df["game_date"].to_numpy()
    per = per.groupby("game_date").sum()
    cnt = df.groupby("game_date").size().reindex(per.index).to_numpy(float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(per), size=(n_boot, len(per)))
    n = cnt[idx].sum(axis=1)
    base = per[base_col].to_numpy()[idx].sum(axis=1)
    rows = []
    for c in cols:
        diff = (per[c].to_numpy()[idx].sum(axis=1) - base) / n
        rows.append({"model": c, "vs": base_col, "logloss_diff": float((per[c].sum() - per[base_col].sum()) / cnt.sum()),
                     "ci_lo": float(np.quantile(diff, 0.025)), "ci_hi": float(np.quantile(diff, 0.975)),
                     "share_resamples_better": float((diff < 0).mean())})
    return pd.DataFrame(rows)


def disagreement(df, col, base_col):
    diff = df[col] - df[base_col]
    bins = pd.cut(diff, [-np.inf, -0.05, 0.05, np.inf], labels=["< -0.05", "[-0.05, 0.05]", "> 0.05"])
    g = df.assign(bucket=bins).groupby("bucket", observed=False)
    out = g.agg(n=("dd", "size"), mean_base=(base_col, "mean"), mean_model=(col, "mean"), realized=("dd", "mean")).reset_index()
    out.insert(0, "model", col)
    out.insert(1, "vs", base_col)
    return out


def main():
    import argparse
    global TEST_SEASONS, FIRST_TRAIN, EVAL, EXTRA_NAME, EXTRA_PREFIXES
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-seasons", nargs="+", type=int, default=TEST_SEASONS)
    ap.add_argument("--first-train", type=int, default=FIRST_TRAIN)
    ap.add_argument("--out", default=str(EVAL))
    ap.add_argument("--extra", default=None, help="parquet keyed game_id, athlete_id with one more feature group")
    ap.add_argument("--extra-prefix", nargs="+", default=["shot_"])
    ap.add_argument("--extra-name", default="SHOT")
    args = ap.parse_args()
    TEST_SEASONS, FIRST_TRAIN, EVAL = args.test_seasons, args.first_train, Path(args.out)
    EXTRA_NAME, EXTRA_PREFIXES = args.extra_name, tuple(args.extra_prefix)
    EVAL.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    spec = json.load(open(FEAT / "dataset_v1_features.json"))
    base_feats = spec["features"]
    meta = ["game_id", "athlete_id", "athlete_display_name", "team_id", "opponent_team_id", "game_date",
            "season", "season_type", "minutes", "dd"]
    ds = pd.read_parquet(FEAT / "dataset_v1.parquet", columns=meta + base_feats)
    ds = ds[ds["season"].between(FIRST_TRAIN, max(TEST_SEASONS)) & (ds["season_type"] == 2)].copy()
    ds["game_date"] = pd.to_datetime(ds["game_date"]).dt.normalize().astype("datetime64[ns]")
    trk = pd.read_parquet(FEAT / "tracking_features.parquet")
    trk["game_date"] = pd.to_datetime(trk["game_date"]).dt.normalize().astype("datetime64[ns]")
    opp = pd.read_parquet(FEAT / "opponent_features.parquet")
    pred = pd.read_parquet(ROOT / "data" / "eval" / "v1" / "predictions_v1.parquet",
                           columns=["game_id", "athlete_id", "p_A_cal", "p_C_full_cal"])
    df = ds.merge(trk, on=["athlete_id", "game_date"], how="left").merge(opp, on=["game_id", "athlete_id"], how="left")
    df = df.merge(pred, on=["game_id", "athlete_id"], how="inner")
    extra_feats = []
    if args.extra:
        ex = pd.read_parquet(args.extra)
        extra_feats = [c for c in ex.columns if c.startswith(EXTRA_PREFIXES)]
        df = df.merge(ex[["game_id", "athlete_id"] + extra_feats].drop_duplicates(["game_id", "athlete_id"]),
                      on=["game_id", "athlete_id"], how="left")
    df["exp_rebch"] = df["trk_rebch_pm_ewm"] * df["min_ewm"]
    df["exp_potast"] = df["trk_potast_pm_ewm"] * df["min_ewm"]
    df["z_ref"] = logit(df["p_C_full_cal"])
    trk_feats = [c for c in df.columns if c.startswith("trk_")] + ["exp_rebch", "exp_potast"]
    opp_feats = [c for c in df.columns if c.startswith(("oppx_", "oppt_"))]
    mu_feats = [c for c in df.columns if c.startswith("mu_")]
    variants = {
        "BASE": base_feats,
        "BASE+TRK": base_feats + trk_feats,
        "BASE+OPP": base_feats + opp_feats,
        "BASE+MU": base_feats + mu_feats,
        "BASE+ALL": base_feats + trk_feats + opp_feats + mu_feats,
    }
    if extra_feats:
        variants[f"BASE+{EXTRA_NAME}"] = base_feats + extra_feats
        variants[f"BASE+TRK+{EXTRA_NAME}"] = base_feats + trk_feats + extra_feats
    stacks = {
        "STACK_BASE": ["z_ref", "min_ewm", "position"],
        "STACK_ALL": ["z_ref", "min_ewm", "position"] + trk_feats + opp_feats + mu_feats,
    }
    resids = {
        "RESID_NONE": ["min_ewm", "position"],
        "RESID_TRK": ["min_ewm", "position"] + trk_feats,
        "RESID_OPP": ["min_ewm", "position"] + opp_feats,
        "RESID_MU": ["min_ewm", "position"] + mu_feats,
        "RESID_ALL": ["min_ewm", "position"] + trk_feats + opp_feats + mu_feats,
    }
    if extra_feats:
        resids[f"RESID_{EXTRA_NAME}"] = ["min_ewm", "position"] + extra_feats
        resids[f"RESID_TRK+{EXTRA_NAME}"] = ["min_ewm", "position"] + trk_feats + extra_feats
    log(f"rows {len(df)}; features base {len(base_feats)}, trk {len(trk_feats)}, opp {len(opp_feats)}, mu {len(mu_feats)}, "
        f"extra {len(extra_feats)}")
    coverage = pd.DataFrame({
        "season": sorted(df["season"].unique()),
        "rows": [int((df["season"] == s).sum()) for s in sorted(df["season"].unique())],
        "trk_5plus_prior": [float((df.loc[df["season"] == s, "trk_games_prior"] >= 5).mean()) for s in sorted(df["season"].unique())],
        "oppt_present": [float(df.loc[df["season"] == s, opp_feats[0] if opp_feats else "dd"].notna().mean()) for s in sorted(df["season"].unique())],
        "mu_present": [float(df.loc[df["season"] == s, "mu_def_pts_vs_exp"].notna().mean()) if "mu_def_pts_vs_exp" in df else np.nan for s in sorted(df["season"].unique())],
    })
    if extra_feats:
        coverage[f"{EXTRA_NAME.lower()}_present"] = [float(df.loc[df["season"] == s, extra_feats[0]].notna().mean())
                                                  for s in sorted(df["season"].unique())]
    coverage.to_csv(EVAL / "coverage.csv", index=False)

    fold_info = {}
    importances = {}
    all_models = list(variants) + list(stacks) + list(resids)
    for name in all_models:
        df[f"p_{name}_raw"] = np.nan
        df[f"p_{name}_cal"] = np.nan
    for S in TEST_SEASONS:
        train = df[(df["season"] >= FIRST_TRAIN) & (df["season"] < S)]
        test_idx = df.index[df["season"] == S]
        fit, hold, cut = holdout_split(train)
        info = {"n_fit": int(len(fit)), "n_hold": int(len(hold)), "n_test": int(len(test_idx)), "cut_date": str(cut.date())}
        for name, feats in list(variants.items()) + list(stacks.items()) + list(resids.items()):
            resid = name in resids
            params = LGB_PARAMS if name in variants else STACK_PARAMS
            t1 = time.time()
            dtr = lgb.Dataset(fit[feats], label=fit["dd"].to_numpy(), categorical_feature=["position"], free_raw_data=False,
                              init_score=fit["z_ref"].to_numpy() if resid else None)
            dho = lgb.Dataset(hold[feats], label=hold["dd"].to_numpy(), categorical_feature=["position"], reference=dtr,
                              free_raw_data=False, init_score=hold["z_ref"].to_numpy() if resid else None)
            booster = lgb.train(params, dtr, num_boost_round=MAX_ROUNDS, valid_sets=[dho], valid_names=["holdout"],
                                callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
            best = booster.best_iteration if booster.best_iteration > 0 else booster.current_iteration()
            if resid:  # predict returns the tree sum only; add the initial score back
                ph = sigmoid(hold["z_ref"].to_numpy() + booster.predict(hold[feats], num_iteration=best, raw_score=True))
                pt = sigmoid(df.loc[test_idx, "z_ref"].to_numpy()
                             + booster.predict(df.loc[test_idx, feats], num_iteration=best, raw_score=True))
            else:
                ph = booster.predict(hold[feats], num_iteration=best)
                pt = booster.predict(df.loc[test_idx, feats], num_iteration=best)
            cal = fit_platt(ph, hold["dd"].to_numpy())
            df.loc[test_idx, f"p_{name}_raw"] = pt
            df.loc[test_idx, f"p_{name}_cal"] = apply_platt(cal, pt)
            booster.save_model(str(MODELS / f"{name.replace('+', '_')}_S{S}.txt"), num_iteration=best)
            gain = pd.Series(booster.feature_importance(importance_type="gain", iteration=best), index=booster.feature_name())
            importances[(name, S)] = gain
            info[f"{name}_best_iteration"] = int(best)
            info[f"{name}_holdout_logloss"] = float(booster.best_score["holdout"]["binary_logloss"])
            log(f"S{S} {name}: best iteration {best}, holdout logloss {info[f'{name}_holdout_logloss']:.5f}, {time.time() - t1:.0f}s")
        fold_info[str(S)] = info
    json.dump(fold_info, open(EVAL / "fold_info.json", "w"), indent=2)

    test = df[df["season"].isin(TEST_SEASONS)].copy()
    test["p_REF_cal"] = test["p_C_full_cal"]
    test["p_A_cal_m"] = test["p_A_cal"]
    cols = {"A": "p_A_cal_m", "REF": "p_REF_cal"}
    cols.update({m: f"p_{m}_cal" for m in all_models})
    test["p_BLEND_cal"] = sigmoid(0.5 * logit(test["p_REF_cal"]) + 0.5 * logit(test["p_BASE+ALL_cal"]))
    cols.update({f"{m} raw": f"p_{m}_raw" for m in resids})
    cols["BLEND_REF_ALL"] = "p_BLEND_cal"
    mid = test[test["p_A_cal"].between(0.25, 0.65)]
    rows_m, rows_mid, rows_top, rows_edge = [], [], [], []
    for season, g in list(test.groupby("season")) + [("all", test)]:
        gm = g[g["p_A_cal"].between(0.25, 0.65)]
        for m, c in cols.items():
            rows_m.append({"season": season, "model": m, **basic_metrics(g["dd"], g[c])})
            rows_mid.append({"season": season, "model": m, **basic_metrics(gm["dd"], gm[c])})
            rows_top.append({"season": season, "model": m, **top3(g, c)})
            rows_edge.append({"season": season, "model": m, **edge_top3(g, c)})
    metrics = pd.DataFrame(rows_m)
    metrics_mid = pd.DataFrame(rows_mid)
    topn = pd.DataFrame(rows_top)
    edge = pd.DataFrame(rows_edge)
    metrics.to_csv(EVAL / "metrics.csv", index=False)
    metrics_mid.to_csv(EVAL / "metrics_midtier.csv", index=False)
    topn.to_csv(EVAL / "top3.csv", index=False)
    edge.to_csv(EVAL / "edge_top3.csv", index=False)

    boots = []
    for season, g in list(test.groupby("season")) + [("all", test)]:
        b1 = block_bootstrap(g, [f"p_{m}_cal" for m in variants if m != "BASE"], "p_BASE_cal")
        b2 = block_bootstrap(g, ["p_STACK_ALL_cal"], "p_STACK_BASE_cal")
        b3 = block_bootstrap(g, ["p_STACK_ALL_cal", "p_STACK_BASE_cal", "p_BASE+ALL_cal"], "p_REF_cal")
        b4 = block_bootstrap(g, [f"p_{m}_cal" for m in resids] + [f"p_{m}_raw" for m in resids] + ["p_BLEND_cal"], "p_REF_cal")
        b5 = block_bootstrap(g, [f"p_{m}_raw" for m in resids if m != "RESID_NONE"], "p_RESID_NONE_raw")
        bl = [b1, b2, b3, b4, b5]
        if extra_feats:
            bl.append(block_bootstrap(g, [f"p_RESID_TRK+{EXTRA_NAME}_raw", f"p_RESID_{EXTRA_NAME}_raw"], "p_RESID_TRK_raw"))
            bl.append(block_bootstrap(g, [f"p_BASE+TRK+{EXTRA_NAME}_cal"], "p_BASE+TRK_cal"))
        b = pd.concat(bl, ignore_index=True)
        b.insert(0, "season", season)
        boots.append(b)
    boot = pd.concat(boots, ignore_index=True)
    boot.to_csv(EVAL / "bootstrap.csv", index=False)

    dis = pd.concat([disagreement(test, "p_BASE+ALL_cal", "p_BASE_cal"),
                     disagreement(test, "p_RESID_ALL_raw", "p_REF_cal"),
                     disagreement(test, "p_STACK_ALL_cal", "p_REF_cal"),
                     disagreement(test, "p_BASE+TRK_cal", "p_BASE_cal"),
                     disagreement(test, "p_BASE+OPP_cal", "p_BASE_cal"),
                     disagreement(test, "p_BASE+MU_cal", "p_BASE_cal")]
                    + ([disagreement(test, f"p_RESID_{EXTRA_NAME}_raw", "p_REF_cal"),
                        disagreement(test, f"p_BASE+{EXTRA_NAME}_cal", "p_BASE_cal")] if extra_feats else []),
                    ignore_index=True)
    dis.to_csv(EVAL / "disagreement.csv", index=False)

    imp_rows, grp_rows = [], []
    for (name, S), gain in importances.items():
        share = gain / gain.sum() if gain.sum() > 0 else gain
        grp = share.groupby(share.index.map(group_of)).sum()
        for gname, v in grp.items():
            grp_rows.append({"model": name, "season": S, "group": gname, "gain_share": float(v),
                             "n_features": int((share.index.map(group_of) == gname).sum())})
        if name in ("BASE+ALL", "STACK_ALL", "RESID_ALL", f"BASE+TRK+{EXTRA_NAME}", f"RESID_TRK+{EXTRA_NAME}"):
            for i, (f, v) in enumerate(share.sort_values(ascending=False).head(30).items(), 1):
                imp_rows.append({"model": name, "season": S, "rank": i, "feature": f, "group": group_of(f), "gain_share": float(v)})
    imp = pd.DataFrame(imp_rows)
    grp_gain = pd.DataFrame(grp_rows)
    imp.to_csv(EVAL / "importance_top30.csv", index=False)
    grp_gain.to_csv(EVAL / "gain_by_group.csv", index=False)
    keep = meta + ["p_A_cal", "p_C_full_cal"] + [f"p_{m}_cal" for m in all_models] + [f"p_{m}_raw" for m in all_models] + ["p_BLEND_cal"]
    test[keep].to_parquet(EVAL / "predictions_tracking.parquet", index=False)

    L = []
    L.append("# Tracking, opponent and matchup feature lift test\n")
    L.append("Regular-season rows, season keys 2024 to 2026 (2023-24 to 2025-26). Test 2025 is trained on 2024; test 2026 on 2024 and 2025. "
             "All variants use identical rows, hyperparameters, seed, holdout split and Platt calibration. REF is the saved v1 C_full prediction, "
             "trained on 2018 onward with all season types, so it has more history than the era-only variants; the STACK rows measure the "
             "new features as increments over REF. The RESID rows boost from logit(REF) as the initial score and see only the new "
             "features (plus min_ewm and position), so zero trees equals REF exactly and every departure from REF is chosen by the holdout; "
             "RESID_NONE is the control with no new features, and the raw rows skip the Platt step. BLEND_REF_ALL is a 0.5/0.5 logit blend "
             "of REF and BASE+ALL. The proxy price q = min(0.97, 1.08 x Baseline A) is an assumption, not a book price.\n")
    if extra_feats:
        L.append(f"Extra group {EXTRA_NAME}: {len(extra_feats)} features from {args.extra} (prefixes "
                 f"{', '.join(EXTRA_PREFIXES)}), merged on game_id and athlete_id; variants BASE+{EXTRA_NAME}, "
                 f"BASE+TRK+{EXTRA_NAME}, RESID_{EXTRA_NAME} and RESID_TRK+{EXTRA_NAME}.\n")
    L.append("## Coverage\n" + md(coverage) + "\n")
    L.append("## Metric 1: calibrated log loss, Brier, AUC\n" + md(metrics) + "\n")
    L.append("## Bootstrap of log-loss differences (block bootstrap by game date, 1000 resamples; negative favors the model)\n" + md(boot, 5) + "\n")
    L.append("## Mid-tier slice (Baseline A between 0.25 and 0.65)\n" + md(metrics_mid) + "\n")
    L.append("## Nightly top-3 by probability\n" + md(topn) + "\n")
    L.append(f"## Nightly top-3 by proxy edge (q >= {Q_MIN}; assumption, not a price backtest)\n" + md(edge) + "\n")
    L.append("## Disagreement buckets (model minus comparison, calibrated)\n" + md(dis) + "\n")
    L.append("## Gain share by feature group\n" + md(grp_gain) + "\n")
    L.append("## Top 30 features by gain share (BASE+ALL, STACK_ALL and RESID_ALL)\n" + md(imp, 5) + "\n")
    L.append("## Folds\n```\n" + json.dumps(fold_info, indent=2) + "\n```\n")
    (EVAL / "report_tracking.md").write_text("\n".join(L), encoding="utf-8")
    log(f"wrote {EVAL / 'report_tracking.md'}")


if __name__ == "__main__":
    main()
