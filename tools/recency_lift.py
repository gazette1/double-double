#!/usr/bin/env python
"""Recency weighting test: does weighting recent seasons more than old ones improve the v1 model out of sample?

Russ (2026-10-29): "we need to weigh todays data more than 3-4 years ago data." Same rows, features, folds and
hyperparameters as the v1 backtest (tools/train_eval.py): test seasons 2022-23 through 2025-26, each trained on every
earlier season back to 2017-18 (all season types), the last 15 percent of training rows by date held out for early
stopping and Platt calibration, metrics on regular-season test rows.

Variants, all on the full C_full feature list:
  H_inf  no decay (the v1 model refit with Platt calibration; the reference)
  H5 H3 H2 H1  sample weight 0.5 ** (age / H), age = latest training season minus the row's season, in seasons
  W3     no decay, only the last three training seasons
The holdout carries no weights, so early stopping and calibration judge every variant on the most recent data.

Outputs under data/eval/recency/: report_recency.md, metrics.csv, metrics_midtier.csv, bootstrap.csv, drift.csv,
top3.csv, edge_top3.csv, fold_info.json, predictions_recency.parquet.
Usage: PYTHONUTF8=1 python tools/recency_lift.py [--variants H_inf H3 H1] [--max-rounds 3000]
"""
import argparse
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
EVAL = ROOT / "data" / "eval" / "recency"
SEED = 42
HOLDOUT_FRAC = 0.15
EARLY_STOP = 100
P_CLIP = 1e-4
Q_MIN = 0.20
TEST_SEASONS = [2023, 2024, 2025, 2026]
LGB_PARAMS = {
    "objective": "binary", "metric": "binary_logloss", "num_leaves": 31, "learning_rate": 0.03,
    "min_child_samples": 100, "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1,
    "lambda_l2": 5.0, "seed": SEED, "deterministic": True, "force_col_wise": True, "num_threads": 8,
    "verbose": -1,
}
VARIANTS = {"H_inf": None, "H5": 5.0, "H3": 3.0, "H2": 2.0, "H1": 1.0, "W3": "window3"}
T0 = time.time()


def log(msg):
    print(f"[{(time.time() - T0) / 60:5.1f} min] {msg}", flush=True)


def clip(p):
    return np.clip(np.asarray(p, dtype=float), P_CLIP, 1 - P_CLIP)


def logit(p):
    p = clip(p)
    return np.log(p / (1 - p))


def ll_rows(y, p):
    p = clip(p)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def basic_metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return {"n": int(len(y)), "base_rate": float(y.mean()), "mean_p": float(p.mean()),
            "logloss": float(ll_rows(y, p).mean()), "brier": float(((p - y) ** 2).mean()),
            "auc": float(roc_auc_score(y, p)) if 0 < y.mean() < 1 else np.nan}


def fit_platt(p, y):
    lr = LogisticRegression(C=1e6, max_iter=1000)
    lr.fit(logit(p).reshape(-1, 1), y)
    return lr


def apply_platt(lr, p):
    return lr.predict_proba(logit(p).reshape(-1, 1))[:, 1]


def holdout_split(train):
    """Last HOLDOUT_FRAC of training rows by date; the cut falls on a date boundary (as in v1)."""
    order = train.sort_values(["game_date_time", "game_id", "athlete_id"])
    dates = order["game_date"].to_numpy()
    cut = dates[int(np.floor((1 - HOLDOUT_FRAC) * len(order)))]
    hold = order["game_date"] >= cut
    return order[~hold], order[hold], pd.Timestamp(cut)


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
            "mean_p_top3": float(top[col].mean())}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--max-rounds", type=int, default=3000)
    ap.add_argument("--test-seasons", nargs="+", type=int, default=TEST_SEASONS)
    args = ap.parse_args()
    EVAL.mkdir(parents=True, exist_ok=True)
    spec = json.loads((FEAT / "dataset_v1_features.json").read_text(encoding="utf-8"))
    feats = spec["features"]
    meta = ["game_id", "athlete_id", "athlete_display_name", "team_abbreviation", "season", "season_type",
            "game_date", "game_date_time", "minutes", "dd"]
    df = pd.read_parquet(FEAT / "dataset_v1.parquet", columns=meta + feats)
    df["position"] = pd.Categorical(df["position"].astype(object), categories=spec["position_categories"])
    df["game_date"] = pd.to_datetime(df["game_date"])
    pred_v1 = pd.read_parquet(ROOT / "data" / "eval" / "v1" / "predictions_v1.parquet",
                              columns=["game_id", "athlete_id", "p_A_cal", "p_C_full_cal"])
    log(f"dataset {df.shape}; variants {args.variants}; test seasons {args.test_seasons}")

    variants = {k: VARIANTS[k] for k in args.variants}
    for v in variants:
        df[f"p_{v}_raw"] = np.nan
        df[f"p_{v}_cal"] = np.nan
    fold_info = {}
    for S in args.test_seasons:
        train = df[df["season"] < S]
        test_idx = df.index[df["season"] == S]
        fit, hold, cut = holdout_split(train)
        latest = int(fit["season"].max())
        info = {"n_fit": int(len(fit)), "n_hold": int(len(hold)), "n_test": int(len(test_idx)),
                "cut_date": str(cut.date()), "latest_train_season": latest}
        for v, h in variants.items():
            t1 = time.time()
            f = fit
            if h == "window3":
                f = fit[fit["season"] >= S - 3]
                w = None
            elif h is None:
                w = None
            else:
                age = (latest - f["season"].to_numpy(float))
                w = 0.5 ** (age / h)
            dtr = lgb.Dataset(f[feats], label=f["dd"].to_numpy(), weight=w, categorical_feature=["position"],
                              free_raw_data=False)
            dho = lgb.Dataset(hold[feats], label=hold["dd"].to_numpy(), categorical_feature=["position"],
                              reference=dtr, free_raw_data=False)
            booster = lgb.train(LGB_PARAMS, dtr, num_boost_round=args.max_rounds, valid_sets=[dho],
                                valid_names=["holdout"],
                                callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
            best = booster.best_iteration if booster.best_iteration > 0 else booster.current_iteration()
            ph = booster.predict(hold[feats], num_iteration=best)
            pt = booster.predict(df.loc[test_idx, feats], num_iteration=best)
            cal = fit_platt(ph, hold["dd"].to_numpy())
            df.loc[test_idx, f"p_{v}_raw"] = pt
            df.loc[test_idx, f"p_{v}_cal"] = apply_platt(cal, pt)
            eff = float(w.sum() ** 2 / (w ** 2).sum()) if w is not None else float(len(f))
            info[f"{v}_best_iteration"] = int(best)
            info[f"{v}_holdout_logloss"] = float(booster.best_score["holdout"]["binary_logloss"])
            info[f"{v}_fit_rows"] = int(len(f))
            info[f"{v}_effective_rows"] = round(eff)
            info[f"{v}_seconds"] = round(time.time() - t1)
            log(f"S{S} {v}: rows {len(f)} (effective {eff:.0f}), best iteration {best}, "
                f"holdout logloss {info[f'{v}_holdout_logloss']:.5f}, {time.time() - t1:.0f}s")
        fold_info[str(S)] = info
    (EVAL / "fold_info.json").write_text(json.dumps(fold_info, indent=2), encoding="utf-8")

    test = df[df["season"].isin(args.test_seasons) & (df["season_type"] == 2)].copy()
    test = test.merge(pred_v1, on=["game_id", "athlete_id"], how="left")
    cols = {"A": "p_A_cal", "V1_isotonic": "p_C_full_cal"}
    cols.update({v: f"p_{v}_cal" for v in variants})
    rows_m, rows_mid, rows_top, rows_edge, rows_drift = [], [], [], [], []
    for season, g in list(test.groupby("season")) + [("all", test)]:
        gm = g[g["p_A_cal"].between(0.25, 0.65)]
        for m, c in cols.items():
            gg = g.dropna(subset=[c])
            ggm = gm.dropna(subset=[c])
            rows_m.append({"season": season, "model": m, **basic_metrics(gg["dd"], gg[c])})
            rows_mid.append({"season": season, "model": m, **basic_metrics(ggm["dd"], ggm[c])})
            rows_top.append({"season": season, "model": m, **top3(gg, c)})
            rows_edge.append({"season": season, "model": m, **edge_top3(gg, c)})
            rows_drift.append({"season": season, "model": m, "mean_p": float(gg[c].mean()),
                               "realized": float(gg["dd"].mean()),
                               "over_prediction": float(gg[c].mean() - gg["dd"].mean())})
    metrics, metrics_mid = pd.DataFrame(rows_m), pd.DataFrame(rows_mid)
    topn, edge, drift = pd.DataFrame(rows_top), pd.DataFrame(rows_edge), pd.DataFrame(rows_drift)
    for name, d in [("metrics", metrics), ("metrics_midtier", metrics_mid), ("top3", topn), ("edge_top3", edge),
                    ("drift", drift)]:
        d.to_csv(EVAL / f"{name}.csv", index=False)

    boots = []
    others = [f"p_{v}_cal" for v in variants if v != "H_inf"]
    for season, g in list(test.groupby("season")) + [("all", test)]:
        b = block_bootstrap(g, others, "p_H_inf_cal") if "H_inf" in variants and others else pd.DataFrame()
        if len(b):
            b.insert(0, "season", season)
            boots.append(b)
    boot = pd.concat(boots, ignore_index=True) if boots else pd.DataFrame()
    boot.to_csv(EVAL / "bootstrap.csv", index=False)
    keep = meta + ["p_A_cal", "p_C_full_cal"] + [f"p_{v}_cal" for v in variants] + [f"p_{v}_raw" for v in variants]
    test[keep].to_parquet(EVAL / "predictions_recency.parquet", index=False)

    L = ["# Recency weighting test\n",
         "v1 rows, features and folds (test 2022-23 through 2025-26, each trained on every earlier season back to 2017-18, "
         "all season types; metrics on regular-season test rows). Sample weight 0.5 ** (age / H) with age in seasons from "
         "the latest training season; W3 keeps only the last three training seasons. The holdout (last 15 percent of "
         "training rows by date) is unweighted and drives early stopping and Platt calibration. V1_isotonic is the saved v1 "
         "C_full prediction with its isotonic calibration, for scale; H_inf is the same model refit here with Platt.\n",
         "## Calibrated log loss, Brier, AUC\n" + md(metrics) + "\n",
         "## Bootstrap of log-loss differences against H_inf (block bootstrap by game date, 1000 resamples; negative favors the variant)\n"
         + md(boot, 5) + "\n",
         "## Over-prediction by season (mean calibrated p minus realized rate)\n" + md(drift) + "\n",
         "## Mid-tier slice (Baseline A between 0.25 and 0.65)\n" + md(metrics_mid) + "\n",
         "## Nightly top-3 by probability\n" + md(topn) + "\n",
         f"## Nightly top-3 by proxy edge (q >= {Q_MIN}; assumption, not a price backtest)\n" + md(edge) + "\n",
         "## Folds\n```\n" + json.dumps(fold_info, indent=2) + "\n```\n"]
    (EVAL / "report_recency.md").write_text("\n".join(L), encoding="utf-8")
    log(f"wrote {EVAL / 'report_recency.md'}")


if __name__ == "__main__":
    main()
