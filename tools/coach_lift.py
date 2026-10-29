#!/usr/bin/env python
"""Full-history lift test for a team-game feature set, coaching-staff features by default.

Same rows, features, folds and hyperparameters as the v1 backtest: test seasons 2022-23 through 2025-26, each trained
on every earlier season back to 2017-18 (all season types), the last 15 percent of training rows by date held out for
early stopping and Platt calibration, metrics on regular-season test rows. Two variants on identical rows: BASE (the
155 v1 features) and BASE+<name> (plus the new features merged on the given keys). Block bootstrap by game date on the
log-loss difference, mid-tier slice, nightly top-3, proxy-edge picks, disagreement buckets, gain share of the new group.

Usage: PYTHONUTF8=1 python tools/coach_lift.py
       PYTHONUTF8=1 python tools/coach_lift.py --features data/features/x.parquet --keys game_id team_id --prefixes x_ --name X --out data/eval/x
"""
import argparse
import json
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

import recency_lift as rl  # shared helpers: metrics, Platt, holdout split, bootstrap, tables

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data" / "features"
T0 = time.time()


def log(msg):
    print(f"[{(time.time() - T0) / 60:5.1f} min] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default=str(FEAT / "coach_features.parquet"))
    ap.add_argument("--keys", nargs="+", default=["game_id", "team_id"])
    ap.add_argument("--prefixes", nargs="+", default=["coach_", "staff_", "assoc_", "oppc_"])
    ap.add_argument("--name", default="COACH")
    ap.add_argument("--out", default=str(ROOT / "data" / "eval" / "coach"))
    ap.add_argument("--test-seasons", nargs="+", type=int, default=rl.TEST_SEASONS)
    ap.add_argument("--max-rounds", type=int, default=3000)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads((FEAT / "dataset_v1_features.json").read_text(encoding="utf-8"))
    base = spec["features"]
    meta = ["game_id", "athlete_id", "athlete_display_name", "team_abbreviation", "team_id", "season", "season_type",
            "game_date", "game_date_time", "minutes", "dd"]
    df = pd.read_parquet(FEAT / "dataset_v1.parquet", columns=meta + base)
    df["position"] = pd.Categorical(df["position"].astype(object), categories=spec["position_categories"])
    df["game_date"] = pd.to_datetime(df["game_date"])
    new = pd.read_parquet(args.features)
    new_feats = [c for c in new.columns if c.startswith(tuple(args.prefixes))]
    df = df.merge(new[args.keys + new_feats], on=args.keys, how="left")
    pred_v1 = pd.read_parquet(ROOT / "data" / "eval" / "v1" / "predictions_v1.parquet",
                              columns=["game_id", "athlete_id", "p_A_cal", "p_C_full_cal"])
    name = f"BASE+{args.name}"
    variants = {"BASE": base, name: base + new_feats}
    cov = df.groupby("season")[new_feats].apply(lambda g: g.notna().mean().mean()).rename("mean_non_null").reset_index()
    log(f"rows {len(df)}; base {len(base)} features; {args.name} {len(new_feats)} features; "
        f"coverage by season {cov.set_index('season')['mean_non_null'].round(3).to_dict()}")

    for v in variants:
        df[f"p_{v}_raw"] = np.nan
        df[f"p_{v}_cal"] = np.nan
    fold_info, importances = {}, {}
    for S in args.test_seasons:
        train = df[df["season"] < S]
        test_idx = df.index[df["season"] == S]
        fit, hold, cut = rl.holdout_split(train)
        info = {"n_fit": int(len(fit)), "n_hold": int(len(hold)), "n_test": int(len(test_idx)), "cut_date": str(cut.date())}
        for v, feats in variants.items():
            t1 = time.time()
            dtr = lgb.Dataset(fit[feats], label=fit["dd"].to_numpy(), categorical_feature=["position"], free_raw_data=False)
            dho = lgb.Dataset(hold[feats], label=hold["dd"].to_numpy(), categorical_feature=["position"], reference=dtr,
                              free_raw_data=False)
            booster = lgb.train(rl.LGB_PARAMS, dtr, num_boost_round=args.max_rounds, valid_sets=[dho], valid_names=["holdout"],
                                callbacks=[lgb.early_stopping(rl.EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
            best = booster.best_iteration if booster.best_iteration > 0 else booster.current_iteration()
            ph = booster.predict(hold[feats], num_iteration=best)
            pt = booster.predict(df.loc[test_idx, feats], num_iteration=best)
            cal = rl.fit_platt(ph, hold["dd"].to_numpy())
            df.loc[test_idx, f"p_{v}_raw"] = pt
            df.loc[test_idx, f"p_{v}_cal"] = rl.apply_platt(cal, pt)
            gain = pd.Series(booster.feature_importance(importance_type="gain", iteration=best), index=booster.feature_name())
            importances[(v, S)] = gain
            info[f"{v}_best_iteration"] = int(best)
            info[f"{v}_holdout_logloss"] = float(booster.best_score["holdout"]["binary_logloss"])
            log(f"S{S} {v}: best iteration {best}, holdout logloss {info[f'{v}_holdout_logloss']:.5f}, {time.time() - t1:.0f}s")
        fold_info[str(S)] = info
    (out / "fold_info.json").write_text(json.dumps(fold_info, indent=2), encoding="utf-8")

    test = df[df["season"].isin(args.test_seasons) & (df["season_type"] == 2)].copy()
    test = test.merge(pred_v1, on=["game_id", "athlete_id"], how="left")
    cols = {"A": "p_A_cal", "V1_isotonic": "p_C_full_cal", "BASE": "p_BASE_cal", name: f"p_{name}_cal"}
    rows_m, rows_mid, rows_top, rows_edge = [], [], [], []
    for season, g in list(test.groupby("season")) + [("all", test)]:
        gm = g[g["p_A_cal"].between(0.25, 0.65)]
        for m, c in cols.items():
            gg, ggm = g.dropna(subset=[c]), gm.dropna(subset=[c])
            rows_m.append({"season": season, "model": m, **rl.basic_metrics(gg["dd"], gg[c])})
            rows_mid.append({"season": season, "model": m, **rl.basic_metrics(ggm["dd"], ggm[c])})
            rows_top.append({"season": season, "model": m, **rl.top3(gg, c)})
            rows_edge.append({"season": season, "model": m, **rl.edge_top3(gg, c)})
    metrics, metrics_mid, topn, edge = (pd.DataFrame(r) for r in (rows_m, rows_mid, rows_top, rows_edge))
    boots = []
    for season, g in list(test.groupby("season")) + [("all", test)]:
        b = rl.block_bootstrap(g, [f"p_{name}_cal"], "p_BASE_cal")
        b.insert(0, "season", season)
        boots.append(b)
    boot = pd.concat(boots, ignore_index=True)
    diff = test[f"p_{name}_cal"] - test["p_BASE_cal"]
    bins = pd.cut(diff, [-np.inf, -0.05, -0.02, 0.02, 0.05, np.inf],
                  labels=["< -0.05", "[-0.05, -0.02)", "[-0.02, 0.02]", "(0.02, 0.05]", "> 0.05"])
    dis = test.assign(bucket=bins).groupby("bucket", observed=False).agg(
        n=("dd", "size"), mean_base=("p_BASE_cal", "mean"), mean_model=(f"p_{name}_cal", "mean"), realized=("dd", "mean")).reset_index()
    grp_rows, imp_rows = [], []
    for (v, S), gain in importances.items():
        share = gain / gain.sum() if gain.sum() > 0 else gain
        is_new = share.index.isin(new_feats)
        grp_rows.append({"model": v, "season": S, "group": args.name, "gain_share": float(share[is_new].sum()), "n_features": int(is_new.sum())})
        grp_rows.append({"model": v, "season": S, "group": "BASE", "gain_share": float(share[~is_new].sum()), "n_features": int((~is_new).sum())})
        if v == name:
            for i, (f, val) in enumerate(share[is_new].sort_values(ascending=False).head(20).items(), 1):
                imp_rows.append({"season": S, "rank": i, "feature": f, "gain_share": float(val)})
    grp, imp = pd.DataFrame(grp_rows), pd.DataFrame(imp_rows)
    for nm, d in [("metrics", metrics), ("metrics_midtier", metrics_mid), ("top3", topn), ("edge_top3", edge),
                  ("bootstrap", boot), ("disagreement", dis), ("gain_by_group", grp), ("importance_new_top20", imp), ("coverage", cov)]:
        d.to_csv(out / f"{nm}.csv", index=False)
    keep = meta + ["p_A_cal", "p_C_full_cal"] + [f"p_{v}_cal" for v in variants] + [f"p_{v}_raw" for v in variants]
    test[keep].to_parquet(out / f"predictions_{args.name.lower()}.parquet", index=False)
    L = [f"# {args.name} feature lift test (full history)\n",
         f"v1 rows, features and folds (test 2022-23 through 2025-26, trained on every earlier season back to 2017-18, all season "
         f"types; metrics on regular-season test rows). BASE is the 155 v1 features with Platt calibration; BASE+{args.name} adds "
         f"{len(new_feats)} features from `{Path(args.features).name}` merged on {args.keys}. Same rows, hyperparameters, seed, "
         f"holdout and calibration, so the difference comes from the features alone. V1_isotonic is the saved v1 prediction for scale.\n",
         "## Coverage of the new features (mean non-null share) by season\n" + rl.md(cov) + "\n",
         "## Calibrated log loss, Brier, AUC\n" + rl.md(metrics) + "\n",
         "## Bootstrap of the log-loss difference against BASE (block bootstrap by game date, 1000 resamples; negative favors the new features)\n" + rl.md(boot, 5) + "\n",
         "## Mid-tier slice (Baseline A between 0.25 and 0.65)\n" + rl.md(metrics_mid) + "\n",
         "## Nightly top-3 by probability\n" + rl.md(topn) + "\n",
         f"## Nightly top-3 by proxy edge (q >= {rl.Q_MIN}; assumption, not a price backtest)\n" + rl.md(edge) + "\n",
         "## Disagreement buckets (BASE+new minus BASE, calibrated)\n" + rl.md(dis) + "\n",
         "## Gain share by group\n" + rl.md(grp) + "\n",
         "## Top 20 new features by gain share\n" + rl.md(imp, 5) + "\n",
         "## Folds\n```\n" + json.dumps(fold_info, indent=2) + "\n```\n"]
    (out / f"report_{args.name.lower()}.md").write_text("\n".join(L), encoding="utf-8")
    log(f"wrote {out / f'report_{args.name.lower()}.md'}")


if __name__ == "__main__":
    main()
