"""
train_production.py: fit the production double-double model on every season through yesterday.

Model: v1 C_full, LightGBM binary on the 155 point-in-time features (abs_ features included), early-stopped
and Platt-calibrated on the last 15 percent of rows by date, the protocol of the backtests
(tools/train_eval.py, tools/train_eval_v2.py). Why not the v2 C_stack: under the same Platt calibration the
stack beats C_full by 0.0002 pooled log loss over the four test seasons (data/eval/v2/report_v2.md,
same-calibration table), inside noise, and it would put the minutes model and the simulation on the daily
path. The tracking and matchup features stay out (no measured lift, data/eval/tracking/report_tracking.md).

Data: the feature table is rebuilt from data/raw/hoopr through build_dataset.build_table (the shared code
path) into data/features/dataset_prod.parquet; dataset_v1.parquet, the backtest table, is not touched.

Outputs in data/models/production/: C_full_prod.txt (LightGBM at the best iteration), platt.json, the
manifest (train cutoff, rows, features, holdout scores, league rate for the proxy) and features.json.
Each run also appends to training_history.csv. Retrain weekly (tools/daily_run.py retrains when the
manifest is older than 7 days).

Run: PYTHONUTF8=1 python tools/train_production.py [--cutoff YYYY-MM-DD] [--no-rebuild] [--max-rounds 3000]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dataset as bd  # noqa: E402
from common import FEATURE_LIST_PATH, FEATURES_DIR, MIN_PRIOR_GAMES, RAW, ROOT, SEASONS, SEED  # noqa: E402
from paper_common import PROD_DIR, now_et, yesterday_et  # noqa: E402
from train_eval import EARLY_STOP, LGB_PARAMS, P_CLIP, holdout_split  # noqa: E402
from train_eval_v2 import Platt  # noqa: E402

PROD_DATASET = FEATURES_DIR / "dataset_prod.parquet"
MODEL_PATH = PROD_DIR / "C_full_prod.txt"
PLATT_PATH = PROD_DIR / "platt.json"
MANIFEST_PATH = PROD_DIR / "manifest.json"
FEATURES_PATH = PROD_DIR / "features.json"
HISTORY_PATH = PROD_DIR / "training_history.csv"
MODEL_REASON = ("v1 C_full with Platt calibration. The v2 C_stack gains 0.0002 pooled log loss under the same "
                "calibration (inside noise) and would add the minutes model and the simulation to the daily path. "
                "Tracking and matchup features excluded: no measured lift in the controlled test of 2026-10-29.")


def log(msg, t0):
    print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)


def rebuild_dataset(t0):
    """Historical feature table through the shared build_table code path; same 155 features as v1."""
    pb, tb, info = bd.load_clean()
    log(f"raw player box {info['raw_player_rows']} rows, {len(pb)} after cleaning, through "
        f"{pb['game_date'].max().date()}", t0)
    ds, p, feature_names, meta_cols = bd.build_table(pb, tb, info, t0, verify=True)
    ds = ds[ds["games_played_career"] >= MIN_PRIOR_GAMES]
    ds = ds.sort_values(["game_date_time", "game_id", "athlete_id"]).reset_index(drop=True)
    v1 = json.loads(FEATURE_LIST_PATH.read_text(encoding="utf-8"))
    assert feature_names == v1["features"], "production feature list differs from the v1 list"
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    ds.to_parquet(PROD_DATASET, index=False)
    log(f"wrote {PROD_DATASET.name} {ds.shape} (rows with at least {MIN_PRIOR_GAMES} prior games)", t0)
    return ds, feature_names, info


def raw_file_dates():
    out = {}
    for y in SEASONS:
        f = RAW / f"player_box_{y}.parquet"
        if f.exists():
            d = pd.read_parquet(f, columns=["game_date"])["game_date"]
            out[str(y)] = str(pd.to_datetime(d).max().date())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", default=None, help="last game date to train on (default yesterday, ET)")
    ap.add_argument("--no-rebuild", action="store_true", help="reuse data/features/dataset_prod.parquet")
    ap.add_argument("--max-rounds", type=int, default=3000)
    args = ap.parse_args()
    t0 = time.time()
    np.random.seed(SEED)
    PROD_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = pd.Timestamp(args.cutoff or yesterday_et())

    spec = json.loads(FEATURE_LIST_PATH.read_text(encoding="utf-8"))
    if args.no_rebuild and PROD_DATASET.exists():
        df = pd.read_parquet(PROD_DATASET)
        feats, build_info = spec["features"], {"reused": str(PROD_DATASET)}
        log(f"reused {PROD_DATASET.name} {df.shape}", t0)
    else:
        df, feats, build_info = rebuild_dataset(t0)
    df["position"] = pd.Categorical(df["position"].astype(object), categories=spec["position_categories"])
    train = df[df["game_date"] <= cutoff]
    dropped = len(df) - len(train)
    log(f"training rows through {cutoff.date()}: {len(train)} ({dropped} later rows excluded)", t0)

    fit, hold, cut = holdout_split(train)
    y_fit, y_hold = fit["dd"].to_numpy(), hold["dd"].to_numpy()
    dtr = lgb.Dataset(fit[feats], label=y_fit, categorical_feature=["position"], free_raw_data=False)
    dho = lgb.Dataset(hold[feats], label=y_hold, categorical_feature=["position"], reference=dtr,
                      free_raw_data=False)
    booster = lgb.train(LGB_PARAMS, dtr, num_boost_round=args.max_rounds, valid_sets=[dho], valid_names=["holdout"],
                        callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
    best = booster.best_iteration if booster.best_iteration > 0 else booster.current_iteration()
    p_hold = booster.predict(hold[feats], num_iteration=best)
    platt = Platt().fit(p_hold, y_hold)
    p_hold_cal = platt.predict(p_hold)

    def clip(p):
        return np.clip(p, P_CLIP, 1 - P_CLIP)
    scores = {"holdout_logloss_raw": float(log_loss(y_hold, clip(p_hold), labels=[0, 1])),
              "holdout_logloss_platt": float(log_loss(y_hold, clip(p_hold_cal), labels=[0, 1])),
              "holdout_auc": float(roc_auc_score(y_hold, p_hold)), "holdout_dd_rate": float(y_hold.mean()),
              "holdout_mean_p_platt": float(p_hold_cal.mean())}
    log(f"C_full best iteration {best}; holdout log loss raw {scores['holdout_logloss_raw']:.5f}, "
        f"Platt {scores['holdout_logloss_platt']:.5f}, AUC {scores['holdout_auc']:.4f}", t0)

    booster.save_model(str(MODEL_PATH), num_iteration=best)
    PLATT_PATH.write_text(json.dumps({"method": "platt", "a": platt.a, "b": platt.b,
                                      "formula": "p_cal = sigmoid(a * logit(p_raw) + b)"}, indent=2),
                          encoding="utf-8")
    FEATURES_PATH.write_text(json.dumps({"features": feats, "categorical": ["position"],
                                         "position_categories": spec["position_categories"]}, indent=2),
                             encoding="utf-8")
    gain = pd.Series(booster.feature_importance(importance_type="gain", iteration=best),
                     index=booster.feature_name()).sort_values(ascending=False)
    manifest = {
        "model": "C_full", "calibration": "platt", "reason": MODEL_REASON,
        "trained_at": now_et().strftime("%Y-%m-%d %H:%M"), "train_cutoff": str(cutoff.date()),
        "dataset": str(PROD_DATASET.relative_to(ROOT)),
        "dataset_rows": int(len(df)), "dataset_max_date": str(df["game_date"].max().date()),
        "train_rows": int(len(train)), "fit_rows": int(len(fit)), "holdout_rows": int(len(hold)),
        "fit_end": str(fit["game_date"].max().date()), "holdout_start": str(cut.date()),
        "holdout_end": str(hold["game_date"].max().date()),
        "seasons": sorted(int(s) for s in train["season"].unique()),
        "best_iteration": int(best), "hit_round_cap": bool(best >= args.max_rounds - EARLY_STOP),
        "max_rounds": args.max_rounds, "lgb_params": LGB_PARAMS, "n_features": len(feats),
        "feature_hash": hashlib.sha1(",".join(feats).encode()).hexdigest()[:12],
        "league_dd_rate_train": float(train["dd"].mean()), "proxy_k": 10,
        "platt": {"a": platt.a, "b": platt.b}, **scores,
        "top_gain_features": {k: float(v) for k, v in gain.head(15).items()},
        "raw_file_max_dates": raw_file_dates(), "build_info": build_info,
        "files": {"model": MODEL_PATH.name, "platt": PLATT_PATH.name, "features": FEATURES_PATH.name},
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    hist = pd.DataFrame([{"trained_at": manifest["trained_at"], "train_cutoff": manifest["train_cutoff"],
                          "train_rows": len(train), "fit_rows": len(fit), "holdout_rows": len(hold),
                          "best_iteration": best, **scores, "minutes": round((time.time() - t0) / 60, 2)}])
    hist.to_csv(HISTORY_PATH, mode="a", header=not HISTORY_PATH.exists(), index=False)
    log(f"saved {MODEL_PATH.name}, {PLATT_PATH.name}, {MANIFEST_PATH.name}; top features: "
        + ", ".join(gain.head(8).index), t0)


if __name__ == "__main__":
    main()
