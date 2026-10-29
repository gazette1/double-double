"""
train_eval.py: walk-forward training and evaluation of the v1 double-double models.

Reads data/features/dataset_v1.parquet (built by tools/build_dataset.py). For each test season S in
2023..2026 (season end year) it trains on all seasons before S, holds out the last 15 percent of training
rows by date for early stopping and calibration, and scores season S. Models: Baseline A (shrunk season
rate), Baseline B (logistic regression), C_full (LightGBM with abs_ features), C_noabs (LightGBM without).
Writes models to data/models/v1/, predictions, metric CSVs, and report_v1.md to data/eval/v1/.
Run: PYTHONUTF8=1 python tools/train_eval.py [--max-rounds 3000]
"""
import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATASET_PATH, EVAL_DIR, FEATURE_LIST_PATH, MODELS_DIR, SEED, TEST_SEASONS,
                    american_odds, to_markdown)

MODELS = ["A", "B", "C_full", "C_noabs"]
K_PRIOR = 10
HOLDOUT_FRAC = 0.15
P_CLIP = 1e-4  # probabilities are clipped to [P_CLIP, 1 - P_CLIP] inside log loss only
EARLY_STOP = 100
B_FEATURES = ["dd_rate_l10", "pA_raw", "min_l10", "reb_l10", "ast_l10", "pts_l10", "home"]
LGB_PARAMS = {
    "objective": "binary", "metric": "binary_logloss", "num_leaves": 31, "learning_rate": 0.03,
    "min_child_samples": 100, "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1,
    "lambda_l2": 5.0, "seed": SEED, "deterministic": True, "force_col_wise": True, "num_threads": 8,
    "verbose": -1,
}
DIS_BUCKETS = ["< -0.10", "[-0.10, -0.05)", "[-0.05, 0.05]", "(0.05, 0.10]", "> 0.10"]
THRESH_BINS = [(0.5, 0.6, "[0.5, 0.6)"), (0.6, 0.7, "[0.6, 0.7)"), (0.7, 0.8, "[0.7, 0.8)"),
               (0.8, 0.9, "[0.8, 0.9)"), (0.9, 1.0001, "[0.9, 1.0]")]


def log(msg, t0):
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


# --------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------
def baseline_a(df, league_rate):
    prior = df["prev_dd_rate"].fillna(df["career_dd_rate_pre"]).fillna(league_rate)
    return ((df["dd_count_season"] + K_PRIOR * prior) / (df["gp_season"] + K_PRIOR)).to_numpy(np.float64)


def fit_isotonic(p, y):
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0, increasing=True)
    iso.fit(p, y)
    return iso


def holdout_split(train):
    """Last HOLDOUT_FRAC of training rows by date; the cut falls on a date boundary."""
    order = train.sort_values(["game_date_time", "game_id", "athlete_id"])
    dates = order["game_date"].to_numpy()
    cut_date = dates[int(np.floor((1 - HOLDOUT_FRAC) * len(order)))]
    hold = order["game_date"] >= cut_date
    return order[~hold], order[hold], pd.Timestamp(cut_date)


def run_fold(df, S, feats_full, feats_noabs, max_rounds, t0):
    train = df[df["season"] < S]
    test = df[df["season"] == S].copy()
    fit, hold, cut = holdout_split(train)
    meta = {"season": S, "train_rows": len(train), "fit_rows": len(fit), "holdout_rows": len(hold),
            "holdout_start": str(cut.date()), "holdout_end": str(hold["game_date"].max().date()),
            "fit_end": str(fit["game_date"].max().date()), "test_rows": len(test)}
    league_rate = float(train["dd"].mean())
    meta["league_rate"] = league_rate
    preds = {}
    cals = {}

    # Baseline A
    pa_fit, pa_hold, pa_test = (baseline_a(x, league_rate) for x in (fit, hold, test))
    cals["A"] = fit_isotonic(pa_hold, hold["dd"].to_numpy())
    preds["A"] = (pa_test, cals["A"].predict(pa_test))

    # Baseline B
    def b_matrix(x, pa):
        m = x[[c for c in B_FEATURES if c != "pA_raw"]].copy()
        m["pA_raw"] = pa
        return m[B_FEATURES].to_numpy(np.float64)
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                       LogisticRegression(max_iter=2000, random_state=SEED))
    lr.fit(b_matrix(fit, pa_fit), fit["dd"].to_numpy())
    pb_hold = lr.predict_proba(b_matrix(hold, pa_hold))[:, 1]
    pb_test = lr.predict_proba(b_matrix(test, pa_test))[:, 1]
    cals["B"] = fit_isotonic(pb_hold, hold["dd"].to_numpy())
    preds["B"] = (pb_test, cals["B"].predict(pb_test))
    coef = lr.named_steps["logisticregression"]
    meta["B_coefficients_standardized"] = dict(zip(B_FEATURES, [float(c) for c in coef.coef_[0]]))
    meta["B_intercept"] = float(coef.intercept_[0])
    with open(MODELS_DIR / f"B_logreg_S{S}.pkl", "wb") as fh:
        pickle.dump(lr, fh)
    log(f"S{S}: baselines done (fit {len(fit)}, holdout {len(hold)} from {cut.date()}, test {len(test)})", t0)

    # Model C variants
    importances = {}
    for name, feats in [("C_full", feats_full), ("C_noabs", feats_noabs)]:
        t1 = time.time()
        dtr = lgb.Dataset(fit[feats], label=fit["dd"].to_numpy(), categorical_feature=["position"],
                          free_raw_data=False)
        dho = lgb.Dataset(hold[feats], label=hold["dd"].to_numpy(), categorical_feature=["position"],
                          reference=dtr, free_raw_data=False)
        booster = lgb.train(LGB_PARAMS, dtr, num_boost_round=max_rounds, valid_sets=[dho], valid_names=["holdout"],
                            callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
        best = booster.best_iteration if booster.best_iteration > 0 else booster.current_iteration()
        ph = booster.predict(hold[feats], num_iteration=best)
        pt = booster.predict(test[feats], num_iteration=best)
        cals[name] = fit_isotonic(ph, hold["dd"].to_numpy())
        preds[name] = (pt, cals[name].predict(pt))
        booster.save_model(str(MODELS_DIR / f"{name}_S{S}.txt"), num_iteration=best)
        gain = booster.feature_importance(importance_type="gain", iteration=best)
        importances[name] = pd.Series(gain, index=booster.feature_name()).sort_values(ascending=False)
        meta[f"{name}_best_iteration"] = int(best)
        meta[f"{name}_hit_round_cap"] = bool(best >= max_rounds - EARLY_STOP)
        meta[f"{name}_holdout_logloss"] = float(booster.best_score["holdout"]["binary_logloss"])
        meta[f"{name}_fit_seconds"] = round(time.time() - t1, 1)
        log(f"S{S}: {name} best iteration {best}, holdout logloss {meta[f'{name}_holdout_logloss']:.5f}, "
            f"{meta[f'{name}_fit_seconds']}s", t0)

    with open(MODELS_DIR / f"calibrators_S{S}.pkl", "wb") as fh:
        pickle.dump(cals, fh)
    out = test[["game_id", "athlete_id", "athlete_display_name", "team_abbreviation", "season", "season_type",
                "game_date", "game_date_time", "minutes", "dd"]].copy()
    for m in MODELS:
        out[f"p_{m}_raw"] = preds[m][0]
        out[f"p_{m}_cal"] = preds[m][1]
    return out, meta, importances


# --------------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------------
def basic_metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p, dtype=np.float64)
    pc = np.clip(p, P_CLIP, 1 - P_CLIP)
    return {"n": len(y), "base_rate": float(y.mean()), "log_loss": float(log_loss(y, pc, labels=[0, 1])),
            "brier": float(brier_score_loss(y, p)), "auc": float(roc_auc_score(y, p))}


def metric1(reg):
    rows = []
    for season, g in list(reg.groupby("season")) + [("all", reg)]:
        for m in MODELS:
            for v in ["raw", "cal"]:
                rows.append({"season": season, "model": m, "version": v, **basic_metrics(g["dd"], g[f"p_{m}_{v}"])})
    return pd.DataFrame(rows)


def metric2(reg):
    rows = []
    for m in MODELS:
        for v in ["raw", "cal"]:
            p = reg[f"p_{m}_{v}"].to_numpy()
            tie = reg[f"p_{m}_raw"].to_numpy()
            order = np.lexsort((tie, p))
            ranks = np.empty(len(p), dtype=np.int64)
            ranks[order] = np.arange(len(p))
            dec = ranks * 10 // len(p) + 1
            g = pd.DataFrame({"dec": dec, "p": p, "y": reg["dd"].to_numpy()}).groupby("dec")
            t = g.agg(n=("y", "size"), mean_pred=("p", "mean"), realized=("y", "mean"), p_min=("p", "min"),
                      p_max=("p", "max")).reset_index()
            t.insert(0, "version", v)
            t.insert(0, "model", m)
            rows.append(t.rename(columns={"dec": "decile"}))
    return pd.concat(rows, ignore_index=True)


def metric3(reg):
    rows = []
    for season, g in [("all", reg)] + list(reg.groupby("season")):
        for m in MODELS:
            p = g[f"p_{m}_cal"].to_numpy()
            for lo, hi, label in THRESH_BINS:
                sel = (p >= lo) & (p < hi)
                n = int(sel.sum())
                realized = float(g["dd"].to_numpy()[sel].mean()) if n else np.nan
                rows.append({"season": season, "model": m, "bin": label, "n": n,
                             "mean_pred": float(p[sel].mean()) if n else np.nan, "realized": realized,
                             "breakeven_american": float(american_odds(np.array([realized]))[0]) if n else np.nan})
    return pd.DataFrame(rows)


def ranked_picks(g, m):
    d = g.sort_values(["game_date", f"p_{m}_cal", f"p_{m}_raw", "athlete_id"], ascending=[True, False, False, True])
    d = d.assign(rk=d.groupby("game_date").cumcount() + 1)
    return d[d["rk"] <= 3]


def metric4(reg):
    rows, names = [], []
    for season, g in list(reg.groupby("season")) + [("all", reg)]:
        for m in MODELS:
            top = ranked_picks(g, m)
            pc = f"p_{m}_cal"
            per_night = top.groupby("game_date").agg(hits=("dd", "sum"), n=("dd", "size"), prod=(pc, "prod"))
            full = per_night[per_night["n"] == 3]
            freq = top.groupby("athlete_display_name").size().sort_values(ascending=False, kind="stable")
            freq = freq.reset_index(name="count").sort_values(["count", "athlete_display_name"],
                                                               ascending=[False, True]).head(10)
            rows.append({
                "season": season, "model": m, "nights": int(top["game_date"].nunique()),
                "top1_hit": float(top.loc[top["rk"] == 1, "dd"].mean()),
                "top2_hit": float(top.loc[top["rk"] <= 2, "dd"].mean()),
                "top3_hit": float(top["dd"].mean()),
                "all3_hit": float((full["hits"] == 3).mean()),
                "mean_p_top1": float(top.loc[top["rk"] == 1, pc].mean()),
                "mean_p_top2": float(top.loc[top["rk"] <= 2, pc].mean()),
                "mean_p_top3": float(top[pc].mean()),
                "mean_p_all3": float(full["prod"].mean()),
                "distinct_top3_players": int(top["athlete_id"].nunique()),
                "top10_names": "; ".join(f"{r.athlete_display_name} ({r.count})" for r in freq.itertuples()),
            })
            for i, r in enumerate(freq.itertuples(), 1):
                names.append({"season": season, "model": m, "rank": i, "name": r.athlete_display_name,
                              "top3_nights": int(r.count)})
    return pd.DataFrame(rows), pd.DataFrame(names)


def disagreement(df, m):
    diff = (df[f"p_{m}_cal"] - df["p_A_cal"]).to_numpy()
    bucket = np.select([diff < -0.10, diff < -0.05, diff <= 0.05, diff <= 0.10], DIS_BUCKETS[:4], DIS_BUCKETS[4])
    rows = []
    for season, g in [("all", df)] + list(df.groupby("season")):
        b = bucket[df.index.get_indexer(g.index)]
        for lab in DIS_BUCKETS:
            sel = b == lab
            n = int(sel.sum())
            y = g["dd"].to_numpy()[sel]
            pa = g["p_A_cal"].to_numpy()[sel]
            pm = g[f"p_{m}_cal"].to_numpy()[sel]
            rows.append({"season": season, "model": m, "bucket": lab, "n": n,
                         "mean_baseline_p": float(pa.mean()) if n else np.nan,
                         "mean_model_p": float(pm.mean()) if n else np.nan,
                         "realized": float(y.mean()) if n else np.nan,
                         "realized_minus_baseline": float(y.mean() - pa.mean()) if n else np.nan,
                         "realized_minus_model": float(y.mean() - pm.mean()) if n else np.nan})
    return pd.DataFrame(rows)


def metric5(reg):
    return pd.concat([disagreement(reg, "C_full"), disagreement(reg, "C_noabs")], ignore_index=True)


def metric7(m1, m4):
    rows = []
    for season in [s for s in m1["season"].unique()]:
        a = m1[(m1["season"] == season) & (m1["version"] == "cal")].set_index("model")
        r = m1[(m1["season"] == season) & (m1["version"] == "raw")].set_index("model")
        t = m4[m4["season"] == season].set_index("model")
        rows.append({"season": season,
                     "logloss_cal_full": a.loc["C_full", "log_loss"], "logloss_cal_noabs": a.loc["C_noabs", "log_loss"],
                     "logloss_cal_diff": a.loc["C_full", "log_loss"] - a.loc["C_noabs", "log_loss"],
                     "logloss_raw_diff": r.loc["C_full", "log_loss"] - r.loc["C_noabs", "log_loss"],
                     "auc_cal_diff": a.loc["C_full", "auc"] - a.loc["C_noabs", "auc"],
                     "top3_hit_full": t.loc["C_full", "top3_hit"], "top3_hit_noabs": t.loc["C_noabs", "top3_hit"],
                     "top3_hit_diff": t.loc["C_full", "top3_hit"] - t.loc["C_noabs", "top3_hit"],
                     "top1_hit_diff": t.loc["C_full", "top1_hit"] - t.loc["C_noabs", "top1_hit"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------------
def fmt_table(df, digits=4, digits_map=None):
    return to_markdown(df, digits=digits, digits_map=digits_map)


def summary_lines(ctx):
    """Plain factual summary sentences computed from the metric tables."""
    m1, m4, m5, m7, m8a, m8b = (ctx[k] for k in ["m1", "m4", "m5", "m7", "m8a", "m8b"])
    cal = m1[m1["version"] == "cal"]
    pooled = cal[cal["season"] == "all"].set_index("model")
    per = cal[cal["season"] != "all"].pivot(index="season", columns="model", values="log_loss")
    n_seasons = len(per)
    out = []
    out.append("Calibrated log loss pooled over the test seasons: " + ", ".join(
        f"{m} {pooled.loc[m, 'log_loss']:.4f}" for m in MODELS) + ". Pooled AUC: " + ", ".join(
        f"{m} {pooled.loc[m, 'auc']:.4f}" for m in MODELS) + ".")
    for m in ["B", "C_full", "C_noabs"]:
        k = int((per[m] < per["A"]).sum())
        out.append(f"{m} has lower calibrated log loss than Baseline A in {k} of {n_seasons} test seasons "
                   f"(per-season differences from A: " + ", ".join(
                       f"{s} {per.loc[s, m] - per.loc[s, 'A']:+.4f}" for s in per.index) + ").")
    t = m4[m4["season"] == "all"].set_index("model")
    out.append("Nightly picks pooled over the test seasons, top-1 / top-2 / top-3 hit rates: " + "; ".join(
        f"{m} {t.loc[m, 'top1_hit']:.3f} / {t.loc[m, 'top2_hit']:.3f} / {t.loc[m, 'top3_hit']:.3f}"
        for m in MODELS) + ".")
    d = m5[(m5["model"] == "C_full") & (m5["season"] == "all")].set_index("bucket")
    for b in ["> 0.10", "< -0.10"]:
        r = d.loc[b]
        side = "above" if b == "> 0.10" else "below"
        out.append(f"Where C_full is more than 0.10 {side} Baseline A (n = {int(r['n'])}), the realized dd rate is "
                   f"{r['realized']:.3f} against a Baseline A mean of {r['mean_baseline_p']:.3f} and a C_full mean of "
                   f"{r['mean_model_p']:.3f}.")
    mid = m8a[(m8a["version"] == "cal") & (m8a["season"] == "all")].set_index("model")
    out.append(f"Mid-tier slice (Baseline A calibrated p from 0.25 to 0.65, n = {int(mid.loc['A', 'n'])}, realized "
               f"rate {mid.loc['A', 'base_rate']:.3f}): calibrated log loss " + ", ".join(
                   f"{m} {mid.loc[m, 'log_loss']:.4f}" for m in MODELS) + "; AUC " + ", ".join(
                   f"{m} {mid.loc[m, 'auc']:.4f}" for m in MODELS) + ".")
    dm = m8b[(m8b["model"] == "C_full") & (m8b["season"] == "all")].set_index("bucket")
    out.append("In the mid-tier slice, C_full minus Baseline A buckets (n, realized, A mean, C_full mean): " + "; ".join(
        f"{b}: {int(dm.loc[b, 'n'])}, {dm.loc[b, 'realized']:.3f}, {dm.loc[b, 'mean_baseline_p']:.3f}, "
        f"{dm.loc[b, 'mean_model_p']:.3f}" for b in DIS_BUCKETS if dm.loc[b, "n"] > 0) + ".")
    s7 = m7[m7["season"] != "all"]
    out.append(f"Knowing who plays (C_full minus C_noabs) changes calibrated log loss by "
               f"{s7['logloss_cal_diff'].min():+.4f} to {s7['logloss_cal_diff'].max():+.4f} per season and the "
               f"nightly top-3 hit rate by {s7['top3_hit_diff'].min():+.3f} to {s7['top3_hit_diff'].max():+.3f}.")
    m3 = ctx["m3"]
    top = m3[(m3["season"] == "all") & (m3["bin"] == THRESH_BINS[-1][2])].set_index("model")
    over = [m for m in MODELS if top.loc[m, "n"] > 0 and top.loc[m, "mean_pred"] > top.loc[m, "realized"]]
    out.append("Top calibrated bin [0.9, 1.0], mean predicted versus realized: " + "; ".join(
        f"{m} {top.loc[m, 'mean_pred']:.3f} versus {top.loc[m, 'realized']:.3f} (n = {int(top.loc[m, 'n'])})"
        for m in MODELS) + f". The realized rate is below the prediction for {len(over)} of {len(MODELS)} models "
        "in this bin, so the isotonic top step fitted on the calibration slice runs high.")
    out.append(ctx["se_note"])
    return out


def write_report(ctx):
    m1, m2, m3, m4, names, m5, imp, m7, m8a, m8b = (ctx[k] for k in
                                                   ["m1", "m2", "m3", "m4", "names", "m5", "imp", "m7", "m8a", "m8b"])
    folds, info = ctx["folds"], ctx["info"]
    L = ["# Double Double Bot, v1 evaluation report", "",
         f"Generated by `tools/train_eval.py` on {time.strftime('%Y-%m-%d %H:%M')} local time. Every table below "
         "is also written as a CSV in `data/eval/v1/`. Feature definitions are in `docs/FEATURES_v1.md`.", "",
         "## Summary", ""] + [f"- {s}" for s in summary_lines(ctx)] + ["",
         "## Setup", "",
         f"- Dataset: `data/features/dataset_v1.parquet`, {info['rows']} rows, {info['n_features']} features "
         f"({info['n_abs']} abs_ features). Base rate of dd by season is in the data section below.",
         "- Walk-forward by season (season end year). For test season S the models train on all seasons before S "
         "(from 2018). The last 15 percent of training rows by date (cut on a date boundary) is the early stopping "
         "and calibration slice. The test season is never used for fitting.",
         "- Metrics use regular-season rows (season_type 2) of the test season unless stated. Playoff and play-in "
         "rows are scored and saved in the predictions file but excluded from the tables.",
         f"- Baseline A: p = (dd_count_season + {K_PRIOR} * prior) / (gp_season + {K_PRIOR}). prior = previous "
         "season dd rate, else the player's career dd rate before this season, else the league dd rate of the "
         "training seasons. Isotonic calibration fitted on the calibration slice.",
         "- Baseline B: logistic regression with median imputation and standardized inputs on dd_rate_l10, "
         "Baseline A raw probability, min_l10, reb_l10, ast_l10, pts_l10, home. Fitted on the training rows "
         "before the calibration slice; isotonic calibration fitted on the slice.",
         f"- Model C: LightGBM binary, num_leaves 31, learning_rate 0.03, up to {ctx['max_rounds']} rounds with "
         "early stopping 100 on the calibration slice, min_child_samples 100, feature_fraction 0.8, "
         "bagging_fraction 0.8, bagging_freq 1, lambda_l2 5, seed 42, deterministic. C_full uses all features; "
         "C_noabs drops the abs_ features. Isotonic calibration fitted on the same slice.",
         f"- Log loss clips probabilities to [{P_CLIP}, {1 - P_CLIP}] because raw Baseline A and isotonic outputs "
         "can be exactly 0. Brier and AUC use unclipped values.",
         f"- Training and scoring runtime: {ctx['runtime_min']:.1f} minutes for the four folds.", ""]
    fd = pd.DataFrame([{k: f.get(k) for k in ["season", "fit_rows", "fit_end", "holdout_rows", "holdout_start",
                                               "holdout_end", "test_rows", "league_rate", "C_full_best_iteration",
                                               "C_noabs_best_iteration"]} for f in folds])
    L += ["### Folds", "", fmt_table(fd, digits_map={"league_rate": 4}), ""]
    caps = [f"S{f['season']} {m}" for f in folds for m in ["C_full", "C_noabs"] if f.get(f"{m}_hit_round_cap")]
    L += [("- LightGBM reached the round cap in: " + ", ".join(caps) + ".") if caps else
          f"- No LightGBM fit reached the {ctx['max_rounds']}-round cap; early stopping ended every fit.", ""]
    L += ["### Data", "", fmt_table(ctx["season_table"], digits_map={"dd_rate": 4, "reg_dd_rate": 4}), "",
          ctx["shift_note"], ""]

    L += ["## Metric 1: log loss, Brier, AUC per season and model", "",
          "Calibrated outputs (isotonic on the calibration slice):", "",
          fmt_table(m1[m1["version"] == "cal"].drop(columns="version")), "",
          "Raw outputs:", "", fmt_table(m1[m1["version"] == "raw"].drop(columns="version")), ""]

    L += ["## Metric 2: calibration by predicted-probability decile (pooled test seasons, calibrated)", ""]
    for m in MODELS:
        t = m2[(m2["model"] == m) & (m2["version"] == "cal")].drop(columns=["model", "version"])
        L += [f"### {m}", "", fmt_table(t), ""]
    L += ["Raw-output decile tables are in `metric2_calibration.csv`.", ""]

    L += ["## Metric 3: threshold precision on calibrated p (pooled test seasons)", "",
          "breakeven_american is the American price at which the realized rate breaks even "
          "(negative = -100 * p / (1 - p)). Per-season rows are in `metric3_threshold.csv`.", "",
          fmt_table(m3[m3["season"] == "all"].drop(columns="season"), digits_map={"breakeven_american": 0}), ""]

    L += ["## Metric 4: nightly top-N picks", "",
          "For each game date, regular-season rows are ranked by calibrated p (ties broken by the raw score). "
          "topK_hit is the fraction of the top K picks that recorded a dd. all3_hit is the share of nights on which "
          "all three top picks hit; mean_p_all3 is the mean product of their calibrated probabilities. "
          + ctx["se_note"], "",
          fmt_table(m4.drop(columns="top10_names")), "", "Ten most frequent names in the nightly top 3:", ""]
    t = m4[m4["season"] != "all"][["season", "model", "top10_names"]]
    L += [fmt_table(t), ""]

    L += ["## Metric 5: disagreement test against Baseline A", "",
          "Rows bucketed by model calibrated p minus Baseline A calibrated p. Pooled test seasons:", ""]
    for m in ["C_full", "C_noabs"]:
        t = m5[(m5["model"] == m) & (m5["season"] == "all")].drop(columns=["model", "season"])
        L += [f"### {m}", "", fmt_table(t), ""]
    L += ["Per season (C_full):", "",
          fmt_table(m5[(m5["model"] == "C_full") & (m5["season"] != "all")].drop(columns=["model"])), "",
          "Per-season rows for C_noabs are in `metric5_disagreement.csv`.", ""]

    L += ["## Metric 6: feature importance (gain), last fold (test season 2026), top 30", ""]
    t6 = pd.DataFrame({"rank": range(1, 31),
                       "C_full_feature": imp["C_full"].index[:30], "C_full_gain": imp["C_full"].values[:30],
                       "C_noabs_feature": imp["C_noabs"].index[:30], "C_noabs_gain": imp["C_noabs"].values[:30]})
    L += [fmt_table(t6, digits_map={"C_full_gain": 0, "C_noabs_gain": 0}), ""]

    L += ["## Metric 7: absence-feature sensitivity (C_full minus C_noabs)", "",
          "Negative log loss differences and positive hit-rate differences favor C_full (lineups known).", "",
          fmt_table(m7), ""]

    L += ["## Metric 8: mid-tier slice (Baseline A calibrated p between 0.25 and 0.65)", "",
          "Metric 1 on the slice, calibrated outputs:", "",
          fmt_table(m8a[m8a["version"] == "cal"].drop(columns="version")), "",
          "Raw outputs:", "", fmt_table(m8a[m8a["version"] == "raw"].drop(columns="version")), "",
          "Metric 5 on the slice, pooled test seasons:", ""]
    for m in ["C_full", "C_noabs"]:
        t = m8b[(m8b["model"] == m) & (m8b["season"] == "all")].drop(columns=["model", "season"])
        L += [f"### {m}", "", fmt_table(t), ""]
    L += ["Per-season slice rows are in `metric8_midtier_disagreement.csv`.", ""]

    L += ["## Notes and deviations from the spec", ""] + [f"- {n}" for n in ctx["notes"]] + [""]
    L += ["## Files", "",
          "- `data/eval/v1/predictions_v1.parquet`: test-season predictions (all season types), raw and calibrated.",
          "- `data/eval/v1/metric1_scores.csv`, `metric2_calibration.csv`, `metric3_threshold.csv`, `metric4_topn.csv`, "
          "`metric4_top_names.csv`, `metric5_disagreement.csv`, `metric6_importance_gain.csv`, "
          "`metric7_absence_sensitivity.csv`, `metric8_midtier_scores.csv`, `metric8_midtier_disagreement.csv`, "
          "`folds_v1.json`.",
          "- `data/models/v1/`: per fold, `C_full_S{S}.txt` and `C_noabs_S{S}.txt` (LightGBM), `B_logreg_S{S}.pkl`, "
          "`calibrators_S{S}.pkl` (isotonic per model), and `baseline_A_S{S}.json`.", ""]
    text = "\n".join(L)
    assert "—" not in text and "!" not in text, "report must not contain em-dashes or exclamation points"
    (EVAL_DIR / "report_v1.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------------------------
def load_importance(S):
    """Gain importance from the saved boosters of fold S (saved at the best iteration)."""
    imp = {}
    for name in ["C_full", "C_noabs"]:
        booster = lgb.Booster(model_file=str(MODELS_DIR / f"{name}_S{S}.txt"))
        gain = booster.feature_importance(importance_type="gain")
        imp[name] = pd.Series(gain, index=booster.feature_name()).sort_values(ascending=False)
    return imp


def season_shift_note(df):
    """Compare the last test season with the mean of the earlier test seasons on regular-season rows."""
    reg = df[df["season_type"] == 2]
    last, prev = TEST_SEASONS[-1], TEST_SEASONS[:-1]
    tg = reg.groupby(["season", "game_id", "team_id"]).agg(rows=("dd", "size"), reb=("rebounds", "sum"))
    tg = tg.groupby("season").mean()
    st = reg[reg["starter"] == 1].groupby("season")["minutes"].mean()
    r10 = (reg["rebounds"] >= 10).groupby(reg["season"]).mean()
    dd = reg.groupby("season")["dd"].mean()

    def pair(s, digits):
        return f"{s.loc[last]:.{digits}f} versus {s.loc[prev].mean():.{digits}f}"
    return (f"Regular-season dataset rows, {last} versus the mean of {prev[0]} to {prev[-1]}: dd rate {pair(dd, 4)}; "
            f"share of games with 10 or more rebounds {pair(r10, 4)}; player rows per team-game "
            f"{pair(tg['rows'], 2)}; starters' mean minutes {pair(st, 1)}; player rebounds per team-game "
            f"{pair(tg['reb'], 1)}. The {last} test season therefore checks how each model carries a base rate "
            "learned on earlier seasons into a season where rebounds were spread across more players.")


def evaluate(df, spec, preds, folds, last_imp, run_info, t0):
    reg = preds[preds["season_type"] == 2].reset_index(drop=True)
    m1 = metric1(reg)
    m2 = metric2(reg)
    m3 = metric3(reg)
    m4, names = metric4(reg)
    m5 = metric5(reg)
    m7 = metric7(m1, m4)
    mid = reg[(reg["p_A_cal"] >= 0.25) & (reg["p_A_cal"] <= 0.65)].reset_index(drop=True)
    m8a = metric1(mid)
    m8b = metric5(mid)
    imp_df = pd.concat([last_imp["C_full"].rename("gain").reset_index().assign(model="C_full"),
                        last_imp["C_noabs"].rename("gain").reset_index().assign(model="C_noabs")],
                       ignore_index=True).rename(columns={"index": "feature"})
    imp_df["rank"] = imp_df.groupby("model").cumcount() + 1
    for name, t in [("metric1_scores", m1), ("metric2_calibration", m2), ("metric3_threshold", m3),
                    ("metric4_topn", m4), ("metric4_top_names", names), ("metric5_disagreement", m5),
                    ("metric6_importance_gain", imp_df[["model", "rank", "feature", "gain"]]),
                    ("metric7_absence_sensitivity", m7), ("metric8_midtier_scores", m8a),
                    ("metric8_midtier_disagreement", m8b)]:
        t.to_csv(EVAL_DIR / f"{name}.csv", index=False)

    season_table = df.groupby("season").agg(rows=("dd", "size"), dd_rate=("dd", "mean"),
                                            reg_rows=("season_type", lambda s: int((s == 2).sum())))
    season_table["reg_dd_rate"] = df[df["season_type"] == 2].groupby("season")["dd"].mean()
    season_table = season_table.reset_index()
    per_season = m4[(m4["season"] != "all") & (m4["model"] == "C_full")]
    nights = float(per_season["nights"].mean())
    p1, p3 = float(per_season["top1_hit"].mean()), float(per_season["top3_hit"].mean())
    se_note = (f"For scale, the binomial standard error of one season's top-1 hit rate (about {nights:.0f} nights, "
               f"rate near {p1:.2f}) is about {np.sqrt(p1 * (1 - p1) / nights):.3f}, and of a top-3 hit rate "
               f"(about {3 * nights:.0f} picks, rate near {p3:.2f}) about {np.sqrt(p3 * (1 - p3) / (3 * nights)):.3f}.")
    build = spec.get("build_info", {})
    dropped = ", ".join(str(g) for g in build.get("same_date_conflict_games_dropped", []))
    notes = [
        f"All-Star and Rising Stars games ({build.get('exhibition_games_dropped', 'n/a')} games) are coded as "
        "season_type 2 with non-franchise team ids; they are dropped before any feature is computed.",
        f"Second ESPN athlete ids for the same player in the same game were dropped "
        f"({build.get('alias_duplicate_played_rows_dropped', 'n/a')} played rows, mostly 2018-19). The spec's "
        "(game_id, athlete_id) dedup alone does not catch them; the raw files have no exact (game_id, athlete_id) "
        "duplicates.",
        f"Game {dropped} was dropped: a corrupted timestamp put two Golden State games on 2020-03-01.",
        "The six 2020-21 play-in games are missing from team_box and have no played rows in the player box. They "
        "count for scores and schedule features and are skipped inside box-stat windows.",
        "The team rank features (team_reb_rank, team_ast_rank) rank the player among the team's pre-game regulars, "
        "not among the players who played the game, so that C_noabs carries no lineup information.",
        "Regulars exclude players whose latest played game before the current date was for another team "
        "(traded or signed elsewhere), following the spec's word teammates.",
        "The abs_ regular window runs across seasons as the spec's N-game rule implies. In a team's first games of "
        "a season it counts departed regulars as absent (mean abs_n_absent_regulars "
        f"{build.get('abs_mean_team_game_1', float('nan')):.2f} in game 1 versus "
        f"{build.get('abs_mean_team_game_6_plus', float('nan')):.2f} from game 6 on).",
        "Team possessions use the turnovers column of team_box (player turnovers); total_turnovers is missing for "
        "2017-18. Opponent allowed rebounds use player-credited rebounds (oreb + dreb), not total_rebounds, which "
        "includes team rebounds.",
        "team_days_rest is capped at 10 like the player rest feature.",
        "Baseline A and Baseline B calibration use the same holdout slice as Model C (the spec calls it the "
        "training slice for Baseline A).",
        "The league-rate fallback of Baseline A uses all training rows of the fold (rows with at least 5 earlier "
        "games).",
        "Games played career and the 5-game filter count games since 2017-18 only, the start of the data.",
    ]
    if run_info["max_rounds"] < 3000:
        notes.append(f"LightGBM rounds capped at {run_info['max_rounds']} instead of 3000 to keep runtime practical.")
    ctx = {"m1": m1, "m2": m2, "m3": m3, "m4": m4, "names": names, "m5": m5, "imp": last_imp, "m7": m7,
           "m8a": m8a, "m8b": m8b, "folds": folds, "max_rounds": run_info["max_rounds"],
           "info": {"rows": len(df), "n_features": len(spec["features"]),
                    "n_abs": len(spec["abs_features"])},
           "season_table": season_table, "notes": notes, "runtime_min": run_info["train_minutes"],
           "se_note": se_note, "shift_note": season_shift_note(df)}
    write_report(ctx)
    log(f"wrote report and CSVs to {EVAL_DIR}", t0)
    pd.set_option("display.width", 250)
    print(m1[m1["version"] == "cal"].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(m4[["season", "model", "top1_hit", "top2_hit", "top3_hit", "all3_hit"]].to_string(
        index=False, float_format=lambda v: f"{v:.4f}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=3000)
    ap.add_argument("--report-only", action="store_true",
                    help="recompute metrics and the report from saved predictions and models")
    args = ap.parse_args()
    t0 = time.time()
    np.random.seed(SEED)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    spec = json.loads(FEATURE_LIST_PATH.read_text(encoding="utf-8"))
    feats_full = spec["features"]
    feats_noabs = [f for f in feats_full if not f.startswith("abs_")]
    forbidden = {"minutes", "points", "rebounds", "assists", "steals", "blocks", "starter", "dd", "td",
                 "career_dd_rate_pre", "season_type", "game_id", "athlete_id"}
    assert not forbidden & set(feats_full), "current-game outcome columns must not be features"
    df = pd.read_parquet(DATASET_PATH)
    df["position"] = pd.Categorical(df["position"].astype(object), categories=spec["position_categories"])
    log(f"dataset {df.shape}, {len(feats_full)} features, {len(feats_full) - len(feats_noabs)} abs_", t0)

    if args.report_only:
        preds = pd.read_parquet(EVAL_DIR / "predictions_v1.parquet")
        saved = json.loads((EVAL_DIR / "folds_v1.json").read_text(encoding="utf-8"))
        folds, run_info = saved["folds"], saved["run"]
        last_imp = load_importance(TEST_SEASONS[-1])
    else:
        all_preds, folds, last_imp = [], [], None
        for S in TEST_SEASONS:
            out, meta, imp = run_fold(df, S, feats_full, feats_noabs, args.max_rounds, t0)
            (MODELS_DIR / f"baseline_A_S{S}.json").write_text(json.dumps(
                {"k": K_PRIOR, "league_rate": meta["league_rate"],
                 "formula": "(dd_count_season + k * prior) / (gp_season + k)",
                 "prior": "prev_dd_rate, else career_dd_rate_pre, else league_rate"}, indent=2), encoding="utf-8")
            all_preds.append(out)
            folds.append(meta)
            last_imp = imp
        preds = pd.concat(all_preds, ignore_index=True)
        preds.to_parquet(EVAL_DIR / "predictions_v1.parquet", index=False)
        run_info = {"max_rounds": args.max_rounds, "train_minutes": round((time.time() - t0) / 60, 2),
                    "finished": time.strftime("%Y-%m-%d %H:%M")}
        (EVAL_DIR / "folds_v1.json").write_text(json.dumps({"run": run_info, "folds": folds}, indent=2),
                                                encoding="utf-8")
    evaluate(df, spec, preds, folds, last_imp, run_info, t0)


if __name__ == "__main__":
    main()
