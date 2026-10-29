"""
train_eval_v2.py: v2 walk-forward evaluation of the double-double models (minutes model, structured
probability, stacking, blends, calibration study, proxy-edge rule). Spec: docs/SPEC_v2.md.

Builds on tools/train_eval.py (v1) and imports its fold logic, Baseline A, calibration, metric functions and
LightGBM settings. Reads data/features/dataset_v1.parquet, the v1 test predictions in
data/eval/v1/predictions_v1.parquet, and the v1 boosters and calibrators in data/models/v1/ (used only to score
the v1 holdout slices; nothing from v1 is retrained or overwritten).

Per test season S (train on seasons before S; the last 15 percent of training rows by date is the holdout slice
H and the earlier training rows are the fit rows F, exactly as in v1):
  MIN_full, MIN_noabs      LightGBM minutes models on the v1 features with and without abs_ features:
                           regression_l1 (conditional median, q50) plus quantile models at 0.1 and 0.9.
  SIM, SIM_noabs           P(dd) as an equal-weight mixture over a grid of minutes quantiles of a split normal
                           fitted to q10, q50, q90 and truncated to [0, 48]. Per-minute rates are the l20 rates
                           shrunk toward position priors with 300 minutes of prior weight. Points, rebounds and
                           assists are negative binomial, steals and blocks Poisson, independent given minutes.
  C_stack, C_stack_noabs   C_full (C_noabs) features plus sim_p and min_pred, LightGBM trained like C_full.
  BLEND_A, BLEND_SIM       logit-space blends of calibrated C_full with calibrated Baseline A or calibrated SIM,
                           weight chosen on H.
  Calibration study        isotonic, Platt and beta calibration of C_full raw outputs, fitted on H.

Leakage: sim_p and min_pred on F are out-of-fold (K time-ordered blocks of F, each predicted by MIN models and
position priors fitted on the other blocks of F). On H and on the test season they come from the MIN models
fitted on F. The test season is used for scoring only.

Writes data/eval/v2/ (report_v2.md, CSV tables, predictions_v2.parquet, folds_v2.json) and data/models/v2/.
Run: PYTHONUTF8=1 python tools/train_eval_v2.py [--inner-folds 3] [--grid 15] [--report-only]
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
from scipy.special import expit, logit
from scipy.stats import nbinom, norm, poisson
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_eval as te  # noqa: E402  (v1 trainer: folds, Baseline A, metrics)
from common import (DATASET_PATH, EVAL_DIR as V1_EVAL_DIR, FEATURE_LIST_PATH,  # noqa: E402
                    MODELS_DIR as V1_MODELS_DIR, ROOT, SEED, TEST_SEASONS, safe_div, to_markdown)
from train_eval import (EARLY_STOP, LGB_PARAMS, P_CLIP, baseline_a, basic_metrics,  # noqa: E402
                        disagreement, fit_isotonic, holdout_split, log)

EVAL_DIR = ROOT / "data" / "eval" / "v2"
MODELS_DIR = ROOT / "data" / "models" / "v2"

SIM_STATS = ["points", "rebounds", "assists", "steals", "blocks"]
SIM_SHORT = ["pts", "reb", "ast", "stl", "blk"]
VMR = {"points": 2.78, "rebounds": 1.29, "assists": 1.17, "steals": 1.0, "blocks": 1.0}  # 1.0 = Poisson
K_RATE = 300.0           # minutes of prior weight in the rate shrinkage
L20_GAMES = 20.0
MIN_CAP = 48.0
Z90 = float(norm.ppf(0.9))
SIGMA_FLOOR = 0.25       # minutes; keeps the split normal proper when q10, q50, q90 cross or touch
MIN_PARAMS = {
    "q50": {"objective": "regression_l1", "metric": "l1"},
    "q10": {"objective": "quantile", "alpha": 0.1, "metric": "quantile"},
    "q90": {"objective": "quantile", "alpha": 0.9, "metric": "quantile"},
}
VARIANTS = ["full", "noabs"]
STACK_NAME = {"full": "C_stack", "noabs": "C_stack_noabs"}
STACK_COLS = {"full": ("sim_p", "min_pred"), "noabs": ("sim_p_noabs", "min_pred_noabs")}
CAL_METHODS = ["isotonic", "platt", "beta"]
EPS_CAL = 1e-6
W_GRID = np.round(np.arange(0.0, 1.0 + 1e-9, 0.05), 2)
EDGE_THRESHOLDS = [0.03, 0.05, 0.08, 0.10]
PROXY_MARGIN, PROXY_CAP = 1.08, 0.97
POSTED_Q_FLOOR = 1.0 / 51.0  # +5000, the longest FanDuel price in the 2026-10-29 snapshot (docs/SPEC_v1.md)
REPORT_MODELS = ["A", "C_full", "C_noabs", "SIM", "SIM_noabs", "C_stack", "C_stack_noabs", "BLEND_A", "BLEND_SIM"]
DIS_MODELS = ["C_stack", "BLEND_A", "C_stack_noabs", "BLEND_SIM", "SIM"]
EDGE_MODELS = ["A", "C_full", "C_noabs", "SIM", "SIM_noabs", "C_stack", "C_stack_noabs", "BLEND_A", "BLEND_SIM"]
CAL_BINS = [(i / 10, (i + 1) / 10, f"[{i / 10:.1f}, {(i + 1) / 10:.1f})") for i in range(9)] + [
    (0.9, 1.0001, "[0.9, 1.0]")]
TOP_BINS = ["[0.8, 0.9)", "[0.9, 1.0]"]
CAL_DISPLAY = {"isotonic": "isotonic", "platt": "Platt", "beta": "beta", "raw": "raw"}
# Same-calibration comparisons: (model, version, reference, reference version); "cal" = the blend output itself.
EQUAL_PAIRS = [("C_stack", "raw", "C_full", "raw"), ("C_stack", "platt", "C_full", "platt"),
               ("C_stack_noabs", "raw", "C_noabs", "raw"), ("BLEND_A", "cal", "C_full", "platt"),
               ("BLEND_SIM", "cal", "C_full", "platt")]
Q_BANDS = [(0.0, 1.0 / 51.0, "below 1/51"), (1.0 / 51.0, 0.05, "1/51 to 0.05"), (0.05, 0.10, "0.05 to 0.10"),
           (0.10, 0.20, "0.10 to 0.20"), (0.20, 0.40, "0.20 to 0.40"), (0.40, 1.0, "0.40 to 0.97")]
BAND_MODELS = ["C_full", "SIM", "C_stack", "BLEND_A", "BLEND_SIM"]
BAND_THRESHOLD = 0.05
# Sanity-check rows: the player's regular-season game closest to the target date (earlier date on ties).
SANITY_ROWS = [("Nikola Jokic", "2026-01-15", "star big"), ("Domantas Sabonis", "2026-01-15", "big"),
               ("Jalen Johnson", "2026-01-15", "forward"), ("Cade Cunningham", "2026-01-15", "guard"),
               ("Naz Reid", "2026-01-15", "bench big"), ("Tyrese Haliburton", "2025-01-15", "guard, 2025")]
FORBIDDEN = {"minutes", "points", "rebounds", "assists", "steals", "blocks", "starter", "dd", "td",
             "career_dd_rate_pre", "season_type", "game_id", "athlete_id"}


# --------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------
def clip_p(p, eps=P_CLIP):
    return np.clip(np.asarray(p, dtype=np.float64), eps, 1 - eps)


def logloss(y, p):
    """Mean log loss with the v1 clipping (same value as sklearn log_loss on clipped p)."""
    y = np.asarray(y, dtype=np.float64)
    pc = clip_p(p)
    return float(-np.mean(y * np.log(pc) + (1 - y) * np.log(1 - pc)))


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [jsonable(v) for v in o.tolist()]
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, pd.Timestamp):
        return str(o.date())
    return o


def time_blocks(frame, k):
    """Positional indices of k contiguous date blocks of a frame (about equal rows, cuts on date boundaries)."""
    dates = frame["game_date"].to_numpy()
    srt = np.sort(dates)
    cuts = [srt[int(np.floor(j * len(srt) / k))] for j in range(1, k)]
    out = []
    for lo, hi in zip([None] + cuts, cuts + [None]):
        m = np.ones(len(frame), dtype=bool)
        if lo is not None:
            m &= dates >= lo
        if hi is not None:
            m &= dates < hi
        out.append(np.nonzero(m)[0])
    assert sum(len(b) for b in out) == len(frame)
    return out


def lgb_train(params, X, y, Xv=None, yv=None, rounds=3000):
    """LightGBM fit; with a validation slice it early-stops like v1 and returns the best iteration."""
    dtr = lgb.Dataset(X, label=y, categorical_feature=["position"], free_raw_data=False)
    if Xv is None:
        return lgb.train(params, dtr, num_boost_round=rounds), int(rounds)
    dva = lgb.Dataset(Xv, label=yv, categorical_feature=["position"], reference=dtr, free_raw_data=False)
    b = lgb.train(params, dtr, num_boost_round=rounds, valid_sets=[dva], valid_names=["holdout"],
                  callbacks=[lgb.early_stopping(EARLY_STOP, verbose=False), lgb.log_evaluation(0)])
    best = b.best_iteration if b.best_iteration > 0 else b.current_iteration()
    return b, int(best)


# --------------------------------------------------------------------------------------------
# SIM: rates, minutes grid, mixture probability
# --------------------------------------------------------------------------------------------
def position_priors(rows):
    """League per-minute rates by position on the given rows: sum of the stat over sum of minutes."""
    g = rows.groupby(rows["position"].astype(object), dropna=True)
    mins = g["minutes"].sum()
    pri = pd.DataFrame({s: g[s].sum() / mins for s in SIM_STATS})
    league = pd.Series({s: rows[s].sum() / rows["minutes"].sum() for s in SIM_STATS})
    return pri, league


def l20_rates(x):
    """Per-minute rates over the last 20 played games and the window minutes (the shrinkage weight).

    pts/reb/ast use the stored l20 per-minute features (window sum over window minutes); steals and blocks use
    stl_l20 / min_l20, which is the same ratio because both are means over the same games. The weight is
    min(games in the window, 20) * mean minutes = the minutes in the window.
    """
    mins = x["min_l20"].to_numpy(np.float64)
    r = np.column_stack([x["pts_pm_l20"].to_numpy(np.float64), x["reb_pm_l20"].to_numpy(np.float64),
                         x["ast_pm_l20"].to_numpy(np.float64), safe_div(x["stl_l20"].to_numpy(np.float64), mins),
                         safe_div(x["blk_l20"].to_numpy(np.float64), mins)])
    w = np.minimum(x["games_played_career"].to_numpy(np.float64), L20_GAMES) * mins
    return r, w


def shrunk_rates(x, priors):
    """rate = (l20 rate * window minutes + prior rate * 300) / (window minutes + 300), per stat."""
    pri, league = priors
    r, w = l20_rates(x)
    P = pri.reindex(x["position"].astype(object).to_numpy()).to_numpy(np.float64)
    P = np.where(np.isfinite(P), P, league.to_numpy(np.float64)[None, :])
    ok = np.isfinite(r) & (np.isfinite(w) & (w > 0))[:, None]
    W = np.where(ok, w[:, None], 0.0)
    R = np.where(ok, r, 0.0)
    return (R * W + P * K_RATE) / (W + K_RATE)


def minutes_grid(q10, q50, q90, n_grid):
    """n_grid equal-probability quantiles of a split normal (median q50, lower sd from q10, upper sd from q90),
    truncated to [0, 48]: the quantile levels are spread evenly between F(0) and F(48)."""
    q10, q50, q90 = (np.asarray(a, dtype=np.float64) for a in (q10, q50, q90))
    s_lo = np.maximum(q50 - q10, SIGMA_FLOOR) / Z90
    s_hi = np.maximum(q90 - q50, SIGMA_FLOOR) / Z90

    def cdf(v):
        return np.where(v <= q50, norm.cdf((v - q50) / s_lo), norm.cdf((v - q50) / s_hi))
    f0, f1 = cdf(0.0), cdf(MIN_CAP)
    u = (np.arange(n_grid) + 0.5) / n_grid
    lev = f0[:, None] + u[None, :] * (f1 - f0)[:, None]
    z = norm.ppf(np.clip(lev, 1e-12, 1 - 1e-12))
    m = q50[:, None] + np.where(lev <= 0.5, s_lo[:, None], s_hi[:, None]) * z
    return np.clip(m, 0.0, MIN_CAP)


def tail10(mu, vmr):
    """P(X >= 10) for mean mu: negative binomial with variance vmr * mu (n = mu / (vmr - 1), p = 1 / vmr), or
    Poisson when vmr = 1."""
    mu = np.maximum(np.asarray(mu, dtype=np.float64), 1e-9)
    if vmr > 1.0:
        return nbinom.sf(9, mu / (vmr - 1.0), 1.0 / vmr)
    return poisson.sf(9, mu)


def sim_prob(rates, grid, chunk=40000):
    """Mean over the minutes grid of P(at least 2 of 5 stats reach 10 | m) = 1 - P(none) - P(exactly one),
    with the five stats independent given minutes. Exactly-0 and exactly-1 probabilities are accumulated one
    stat at a time (e1 <- e1 (1 - t) + e0 t, e0 <- e0 (1 - t)), which equals the closed form."""
    out = np.empty(len(rates))
    for s in range(0, len(rates), chunk):
        R, G = rates[s:s + chunk], grid[s:s + chunk]
        e0, e1 = np.ones_like(G), np.zeros_like(G)
        for k, stat in enumerate(SIM_STATS):
            t = tail10(R[:, k:k + 1] * G, VMR[stat])
            e1 = e1 * (1.0 - t) + e0 * t
            e0 = e0 * (1.0 - t)
        out[s:s + chunk] = np.clip(1.0 - e0 - e1, 0.0, 1.0).mean(axis=1)
    return out


def sim_from_quantiles(rates, q, n_grid):
    return sim_prob(rates, minutes_grid(q["q10"], q["q50"], q["q90"], n_grid))


def tails_at(rates, m):
    return np.column_stack([tail10(rates[:, k] * m, VMR[s]) for k, s in enumerate(SIM_STATS)])


# --------------------------------------------------------------------------------------------
# Calibrators and blends
# --------------------------------------------------------------------------------------------
class Platt:
    """Logistic regression on logit(p): p_cal = sigmoid(a * logit(p) + b). Unpenalized (C = 1e10)."""

    def fit(self, p, y):
        x = logit(clip_p(p, EPS_CAL))[:, None]
        lr = LogisticRegression(C=1e10, max_iter=5000).fit(x, y)
        self.a, self.b = float(lr.coef_[0, 0]), float(lr.intercept_[0])
        return self

    def predict(self, p):
        return expit(self.a * logit(clip_p(p, EPS_CAL)) + self.b)

    def params(self):
        return {"a": self.a, "b": self.b}


class BetaCal:
    """Beta calibration (Kull et al. 2017): logistic regression on log(p) and -log(1 - p),
    p_cal = sigmoid(a * log p - b * log(1 - p) + c), with a, b >= 0 (a negative term is dropped and refit)."""

    def fit(self, p, y):
        pc = clip_p(p, EPS_CAL)
        X = np.column_stack([np.log(pc), -np.log(1 - pc)])
        lr = LogisticRegression(C=1e10, max_iter=5000).fit(X, y)
        a, b = (float(v) for v in lr.coef_[0])
        c = float(lr.intercept_[0])
        self.dropped = None
        if a < 0 or b < 0:
            keep = 1 if a < 0 else 0
            lr = LogisticRegression(C=1e10, max_iter=5000).fit(X[:, [keep]], y)
            coef = float(lr.coef_[0, 0])
            a, b = (0.0, coef) if keep == 1 else (coef, 0.0)
            c = float(lr.intercept_[0])
            self.dropped = "a" if keep == 1 else "b"
        self.a, self.b, self.c = a, b, c
        return self

    def predict(self, p):
        pc = clip_p(p, EPS_CAL)
        return expit(self.a * np.log(pc) - self.b * np.log(1 - pc) + self.c)

    def params(self):
        return {"a": self.a, "b": self.b, "c": self.c, "dropped_term": self.dropped}


def fit_calibrator(method, p, y):
    if method == "isotonic":
        return fit_isotonic(p, y)
    if method == "platt":
        return Platt().fit(p, y)
    return BetaCal().fit(p, y)


def blend(pc, po, w):
    """Logit-space weighted average: sigmoid(w * logit(pc) + (1 - w) * logit(po)), inputs clipped as in log loss."""
    return expit(w * logit(clip_p(pc)) + (1.0 - w) * logit(clip_p(po)))


def choose_weight(pc, po, y):
    losses = np.array([logloss(y, blend(pc, po, w)) for w in W_GRID])
    i = int(np.argmin(losses))
    return float(W_GRID[i]), losses


# --------------------------------------------------------------------------------------------
# One walk-forward fold
# --------------------------------------------------------------------------------------------
def run_fold(df, pv1, S, feats, args, models_dir, t0):
    train = df[df["season"] < S]
    test = df[df["season"] == S]
    fit, hold, cut = holdout_split(train)
    y_fit, y_hold = fit["dd"].to_numpy(), hold["dd"].to_numpy()
    m_fit, m_hold = fit["minutes"].to_numpy(np.float64), hold["minutes"].to_numpy(np.float64)
    meta = {"season": S, "train_rows": len(train), "fit_rows": len(fit), "fit_end": str(fit["game_date"].max().date()),
            "holdout_rows": len(hold), "holdout_start": str(cut.date()),
            "holdout_end": str(hold["game_date"].max().date()), "test_rows": len(test)}
    secs = {}

    # v1 outputs: test rows from the saved predictions file, holdout rows scored with the saved v1 models
    t1 = time.time()
    v1 = test[["game_id", "athlete_id"]].merge(pv1, on=["game_id", "athlete_id"], how="left", validate="one_to_one")
    assert v1["p_C_full_raw"].notna().all(), "every test row must have a v1 prediction"
    league_rate = float(train["dd"].mean())
    with open(V1_MODELS_DIR / f"calibrators_S{S}.pkl", "rb") as fh:
        cals_v1 = pickle.load(fh)
    booster_v1 = lgb.Booster(model_file=str(V1_MODELS_DIR / f"C_full_S{S}.txt"))
    repro = float(np.abs(booster_v1.predict(test[feats["full"]]) - v1["p_C_full_raw"].to_numpy()).max())
    assert repro < 1e-9, f"saved v1 C_full booster does not reproduce the v1 test predictions ({repro})"
    meta["v1_reproduction_max_abs_diff"] = repro
    h_cf_raw = booster_v1.predict(hold[feats["full"]])
    h_cf_cal = cals_v1["C_full"].predict(h_cf_raw)
    h_a_cal = cals_v1["A"].predict(baseline_a(hold, league_rate))
    secs["v1_holdout_scoring"] = round(time.time() - t1, 1)

    # MIN: main models fitted on F with early stopping on H; they score H and the test season
    t1 = time.time()
    qh = {v: {} for v in VARIANTS}
    qt = {v: {} for v in VARIANTS}
    rounds = {}
    for v in VARIANTS:
        for q, qp in MIN_PARAMS.items():
            b, best = lgb_train({**LGB_PARAMS, **qp}, fit[feats[v]], m_fit, hold[feats[v]], m_hold, args.max_rounds)
            qh[v][q] = b.predict(hold[feats[v]], num_iteration=best)
            qt[v][q] = b.predict(test[feats[v]], num_iteration=best)
            b.save_model(str(models_dir / f"MIN_{v}_{q}_S{S}.txt"), num_iteration=best)
            rounds[(v, q)] = best
            meta[f"MIN_{v}_{q}_best_iteration"] = best
            meta[f"MIN_{v}_{q}_hit_round_cap"] = bool(best >= args.max_rounds - EARLY_STOP)
            meta[f"MIN_{v}_{q}_holdout_score"] = float(list(b.best_score["holdout"].values())[0])
    secs["min_main"] = round(time.time() - t1, 1)
    log(f"S{S}: MIN models done ({secs['min_main']}s; q50 rounds full {rounds[('full', 'q50')]}, "
        f"noabs {rounds[('noabs', 'q50')]})", t0)

    # SIM on H and the test season: priors from F, rates from pre-game l20 features
    t1 = time.time()
    priors = position_priors(fit)
    rates_h, rates_t = shrunk_rates(hold, priors), shrunk_rates(test, priors)
    sim_h = {v: sim_from_quantiles(rates_h, qh[v], args.grid) for v in VARIANTS}
    sim_t = {v: sim_from_quantiles(rates_t, qt[v], args.grid) for v in VARIANTS}
    sim_iso = {v: fit_isotonic(sim_h[v], y_hold) for v in VARIANTS}
    secs["sim_main"] = round(time.time() - t1, 1)

    # Out-of-fold sim_p and min_pred for the C_stack training rows (F): K time-ordered blocks of F; each block is
    # scored by MIN models (fixed rounds = the main model's early-stopping iteration, chosen on H) and position
    # priors fitted on the other blocks of F only.
    t1 = time.time()
    blocks = time_blocks(fit, args.inner_folds)
    oof_q = {v: {q: np.full(len(fit), np.nan) for q in MIN_PARAMS} for v in VARIANTS}
    oof_sim = {v: np.full(len(fit), np.nan) for v in VARIANTS}
    meta["inner_blocks"] = []
    for j, idx in enumerate(blocks):
        mask = np.ones(len(fit), dtype=bool)
        mask[idx] = False
        inner, blk = fit.iloc[mask], fit.iloc[idx]
        meta["inner_blocks"].append({"block": j + 1, "rows": len(blk), "start": str(blk["game_date"].min().date()),
                                     "end": str(blk["game_date"].max().date()), "train_rows": len(inner)})
        for v in VARIANTS:
            for q, qp in MIN_PARAMS.items():
                b, _ = lgb_train({**LGB_PARAMS, **qp}, inner[feats[v]], inner["minutes"].to_numpy(np.float64),
                                 rounds=rounds[(v, q)])
                oof_q[v][q][idx] = b.predict(blk[feats[v]], num_iteration=rounds[(v, q)])
        rates_b = shrunk_rates(blk, position_priors(inner))
        for v in VARIANTS:
            oof_sim[v][idx] = sim_from_quantiles(rates_b, {q: oof_q[v][q][idx] for q in MIN_PARAMS}, args.grid)
        log(f"S{S}: inner block {j + 1}/{len(blocks)} done ({len(blk)} rows)", t0)
    assert all(np.isfinite(oof_sim[v]).all() and np.isfinite(oof_q[v]["q50"]).all() for v in VARIANTS)
    secs["inner_oof"] = round(time.time() - t1, 1)
    meta["diagnostics"] = {}
    for v in VARIANTS:
        meta["diagnostics"][v] = {
            "fit_oof_min_mae": float(np.mean(np.abs(oof_q[v]["q50"] - m_fit))),
            "holdout_min_mae": float(np.mean(np.abs(qh[v]["q50"] - m_hold))),
            "fit_oof_sim_logloss": logloss(y_fit, oof_sim[v]),
            "holdout_sim_logloss": logloss(y_hold, sim_h[v]),
            "fit_oof_sim_mean": float(oof_sim[v].mean()), "holdout_sim_mean": float(sim_h[v].mean()),
            "fit_dd_rate": float(y_fit.mean()), "holdout_dd_rate": float(y_hold.mean())}

    # C_stack: C_full (C_noabs) features plus sim_p and min_pred, trained on F like C_full
    t1 = time.time()

    def stack_x(x, v, sim, mp):
        X = x[feats[v]].copy()
        X[STACK_COLS[v][0]] = sim
        X[STACK_COLS[v][1]] = mp
        return X
    st_h, st_t, importances = {}, {}, {}
    for v in VARIANTS:
        name = STACK_NAME[v]
        Xf = stack_x(fit, v, oof_sim[v], oof_q[v]["q50"])
        Xh = stack_x(hold, v, sim_h[v], qh[v]["q50"])
        Xt = stack_x(test, v, sim_t[v], qt[v]["q50"])
        b, best = lgb_train(LGB_PARAMS, Xf, y_fit, Xh, y_hold, args.max_rounds)
        st_h[name] = b.predict(Xh, num_iteration=best)
        st_t[name] = b.predict(Xt, num_iteration=best)
        b.save_model(str(models_dir / f"{name}_S{S}.txt"), num_iteration=best)
        gain = b.feature_importance(importance_type="gain", iteration=best)
        importances[name] = pd.Series(gain, index=b.feature_name()).sort_values(ascending=False)
        meta[f"{name}_best_iteration"] = best
        meta[f"{name}_hit_round_cap"] = bool(best >= args.max_rounds - EARLY_STOP)
        meta[f"{name}_holdout_logloss"] = float(b.best_score["holdout"]["binary_logloss"])
    secs["stack"] = round(time.time() - t1, 1)
    log(f"S{S}: C_stack best iteration {meta['C_stack_best_iteration']}, holdout logloss "
        f"{meta['C_stack_holdout_logloss']:.5f}; C_stack_noabs {meta['C_stack_noabs_best_iteration']}, "
        f"{meta['C_stack_noabs_holdout_logloss']:.5f}", t0)

    # Calibration study (fitted on H, applied to the test season) and the leak-free method check on H halves
    t1 = time.time()
    raw_h = {"C_full": h_cf_raw, **st_h}
    raw_t = {"C_full": v1["p_C_full_raw"].to_numpy(), **st_t}
    cal_objs, cal_t = {}, {}
    for model in ["C_full", "C_stack", "C_stack_noabs"]:
        for method in CAL_METHODS:
            c = cals_v1["C_full"] if (model, method) == ("C_full", "isotonic") else fit_calibrator(
                method, raw_h[model], y_hold)
            cal_objs[f"{model}|{method}"] = c
            cal_t[(model, method)] = c.predict(raw_t[model])
    meta["calibrator_params"] = {k: c.params() for k, c in cal_objs.items() if hasattr(c, "params")}
    h1, h2 = time_blocks(hold, 2)
    meta["cal_select"] = {"first_half": [str(hold["game_date"].iloc[h1].min().date()),
                                         str(hold["game_date"].iloc[h1].max().date())],
                          "second_half": [str(hold["game_date"].iloc[h2].min().date()),
                                          str(hold["game_date"].iloc[h2].max().date())], "n": int(len(h2))}
    for method in CAL_METHODS:
        c = fit_calibrator(method, h_cf_raw[h1], y_hold[h1])
        meta["cal_select"][method] = logloss(y_hold[h2], c.predict(h_cf_raw[h2]))

    # Blends: weight on calibrated C_full chosen on H by log loss
    h_sim_cal = sim_iso["full"].predict(sim_h["full"])
    w_a, loss_a = choose_weight(h_cf_cal, h_a_cal, y_hold)
    w_s, loss_s = choose_weight(h_cf_cal, h_sim_cal, y_hold)
    meta["blend"] = {"w_A": w_a, "w_SIM": w_s, "grid": W_GRID, "holdout_logloss_A": loss_a,
                     "holdout_logloss_SIM": loss_s}
    secs["calibration_blend"] = round(time.time() - t1, 1)
    with open(models_dir / f"calibrators_S{S}.pkl", "wb") as fh:
        pickle.dump({"SIM_isotonic": sim_iso, "calibrators": cal_objs, "blend_w_A": w_a, "blend_w_SIM": w_s}, fh)
    pri, league = priors
    (models_dir / f"sim_priors_S{S}.json").write_text(json.dumps(jsonable(
        {"per_minute_by_position": pri.to_dict(orient="index"), "league": league.to_dict(), "k_minutes": K_RATE,
         "vmr": VMR, "grid": args.grid, "rows": "fit rows (training seasons before the holdout slice)"}),
        indent=2), encoding="utf-8")

    # Test-season output rows
    cols = ["game_id", "athlete_id", "athlete_display_name", "team_abbreviation", "season", "season_type",
            "game_date", "game_date_time", "minutes", "points", "rebounds", "assists", "steals", "blocks", "starter",
            "last_starter", "min_l5", "min_ewm", "dd"]
    out = test[cols].reset_index(drop=True).copy()
    out.insert(4, "position", test["position"].astype(object).to_numpy())
    for c in ["p_A_raw", "p_A_cal", "p_B_raw", "p_B_cal", "p_C_full_raw", "p_C_full_cal", "p_C_noabs_raw",
              "p_C_noabs_cal"]:
        out[c] = v1[c].to_numpy()
    for v in VARIANTS:
        for q in ["q10", "q50", "q90"]:
            out[f"min_{q}_{v}"] = qt[v][q]
    for k, s in enumerate(SIM_SHORT):
        out[f"rate_{s}"] = rates_t[:, k]
    tails = tails_at(rates_t, qt["full"]["q50"])
    for k, s in enumerate(SIM_SHORT):
        out[f"p10_{s}_at_q50"] = tails[:, k]
    out["p_SIM_raw"], out["p_SIM_cal"] = sim_t["full"], sim_iso["full"].predict(sim_t["full"])
    out["p_SIM_noabs_raw"], out["p_SIM_noabs_cal"] = sim_t["noabs"], sim_iso["noabs"].predict(sim_t["noabs"])
    for method in CAL_METHODS:
        out[f"p_C_full_{method}"] = cal_t[("C_full", method)]
    for name in ["C_stack", "C_stack_noabs"]:
        out[f"p_{name}_raw"] = st_t[name]
        for method in CAL_METHODS:
            out[f"p_{name}_{method}"] = cal_t[(name, method)]
    out["p_BLEND_A_cal"] = blend(out["p_C_full_cal"], out["p_A_cal"], w_a)
    out["p_BLEND_SIM_cal"] = blend(out["p_C_full_cal"], out["p_SIM_cal"], w_s)
    meta["quantile_crossing_test"] = {v: {"q10_above_q50": float(np.mean(qt[v]["q10"] > qt[v]["q50"])),
                                          "q90_below_q50": float(np.mean(qt[v]["q90"] < qt[v]["q50"]))}
                                      for v in VARIANTS}
    meta["seconds"] = secs
    log(f"S{S}: fold done; blend w_A {w_a}, w_SIM {w_s}; seconds {secs}", t0)
    return out, meta, importances


# --------------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------------
def metric1_v2(reg, models):
    rows = []
    for season, g in list(reg.groupby("season")) + [("all", reg)]:
        for m in models:
            for v in ["raw", "cal"]:
                col = f"p_{m}_{v}"
                if col in g.columns:
                    rows.append({"season": season, "model": m, "version": v, **basic_metrics(g["dd"], g[col])})
    return pd.DataFrame(rows)


def metric4_v2(reg, models):
    """v1 metric 4 (train_eval.metric4) run on the v2 model list. Blends have no separate raw score, so the
    calibrated value doubles as the tie-break column."""
    d = reg.copy()
    for m in models:
        if f"p_{m}_raw" not in d.columns:
            d[f"p_{m}_raw"] = d[f"p_{m}_cal"]
    saved = te.MODELS
    te.MODELS = list(models)
    try:
        return te.metric4(d)
    finally:
        te.MODELS = saved


def minutes_table(reg):
    models = {"MIN_full (q50)": "min_q50_full", "MIN_noabs (q50)": "min_q50_noabs", "last-5 mean (min_l5)": "min_l5",
              "min_ewm": "min_ewm"}
    rows = []
    for season, g in list(reg.groupby("season")) + [("all", reg)]:
        y = g["minutes"].to_numpy(np.float64)
        st = g["last_starter"].to_numpy() == 1
        for name, col in models.items():
            e = g[col].to_numpy(np.float64) - y
            row = {"season": season, "model": name, "n": len(y), "mae": float(np.mean(np.abs(e))),
                   "rmse": float(np.sqrt(np.mean(e ** 2))), "bias": float(np.mean(e)),
                   "mae_starters": float(np.mean(np.abs(e[st]))), "n_starters": int(st.sum()),
                   "mae_nonstarters": float(np.mean(np.abs(e[~st]))), "n_nonstarters": int((~st).sum())}
            if col.startswith("min_q50_"):
                v = col.split("_")[-1]
                lo, hi = g[f"min_q10_{v}"].to_numpy(), g[f"min_q90_{v}"].to_numpy()
                row.update({"share_below_q10": float(np.mean(y < lo)), "share_below_q90": float(np.mean(y < hi)),
                            "mean_q90_minus_q10": float(np.mean(hi - lo))})
            rows.append(row)
    return pd.DataFrame(rows)


def calibration_study(reg):
    entries = [("C_full", "raw")] + [("C_full", m) for m in CAL_METHODS] + [
        (n, m) for n in ["C_stack", "C_stack_noabs"] for m in ["raw"] + CAL_METHODS]
    y = reg["dd"].to_numpy()
    scores, bins = [], []
    for model, method in entries:
        col = f"p_{model}_{method}"
        for season, g in list(reg.groupby("season")) + [("all", reg)]:
            scores.append({"season": season, "model": model, "method": method, **basic_metrics(g["dd"], g[col])})
        p = reg[col].to_numpy()
        for lo, hi, lab in CAL_BINS:
            sel = (p >= lo) & (p < hi)
            n = int(sel.sum())
            bins.append({"model": model, "method": method, "bin": lab, "n": n,
                         "mean_pred": float(p[sel].mean()) if n else np.nan,
                         "realized": float(y[sel].mean()) if n else np.nan,
                         "realized_minus_pred": float(y[sel].mean() - p[sel].mean()) if n else np.nan})
    return pd.DataFrame(scores), pd.DataFrame(bins)


def top_bins_table(bins):
    rows = []
    for (model, method), g in bins.groupby(["model", "method"], sort=False):
        g = g.set_index("bin")
        row = {"model": model, "method": method}
        for lab, tag in zip(TOP_BINS, ["0.8_0.9", "0.9_1.0"]):
            row[f"n_{tag}"] = int(g.loc[lab, "n"])
            row[f"pred_{tag}"] = g.loc[lab, "mean_pred"]
            row[f"real_{tag}"] = g.loc[lab, "realized"]
        rows.append(row)
    return pd.DataFrame(rows)


def proxy_edge(reg, models, q_floor=None):
    """Proxy-edge rule (an assumption, not a price backtest): stand-in implied probability
    q = min(0.97, 1.08 * A_cal); bet Yes when p - q >= threshold; flat 1-unit stake paid at the fair price of q,
    return per bet = hit * (1 - q) / q - (1 - hit)."""
    q_all = np.minimum(PROXY_CAP, PROXY_MARGIN * reg["p_A_cal"].to_numpy(np.float64))
    y_all = reg["dd"].to_numpy(np.float64)
    seasons = reg["season"].to_numpy()
    rows = []
    for m in models:
        p_all = reg[f"p_{m}_cal"].to_numpy(np.float64)
        for thr in EDGE_THRESHOLDS:
            base = (p_all - q_all >= thr) & (q_all > 0)
            if q_floor is not None:
                base &= q_all >= q_floor
            for season in sorted(set(seasons.tolist())) + ["all"]:
                sel = (base & (seasons == season)) if season != "all" else base
                n = int(sel.sum())
                row = {"season": season, "model": m, "threshold": thr, "n_bets": n}
                if n:
                    q, p, y = q_all[sel], p_all[sel], y_all[sel]
                    ret = y * (1 - q) / q - (1 - y)
                    row.update({"hit_rate": float(y.mean()), "mean_q": float(q.mean()), "mean_p": float(p.mean()),
                                "mean_return": float(ret.mean()), "total_return": float(ret.sum()),
                                "median_american_at_q": float(np.median(np.where(q >= 0.5, -100 * q / (1 - q),
                                                                                 100 * (1 - q) / q)))})
                else:
                    row.update({"hit_rate": np.nan, "mean_q": np.nan, "mean_p": np.nan, "mean_return": np.nan,
                                "total_return": 0.0, "median_american_at_q": np.nan})
                rows.append(row)
    return pd.DataFrame(rows)


def sanity_table(preds, raw_l20):
    """raw_l20: game_id, athlete_id, l20_{stat} per-minute rates before shrinkage and window_minutes."""
    reg = preds[preds["season_type"] == 2].sort_values(["game_date", "game_id"])
    cols = {}
    for name, target, role in SANITY_ROWS:
        g = reg[reg["athlete_display_name"] == name]
        if g.empty:
            continue
        r = g.loc[(g["game_date"] - pd.Timestamp(target)).abs().idxmin()]
        rr = raw_l20[(raw_l20["game_id"] == r["game_id"]) & (raw_l20["athlete_id"] == r["athlete_id"])].iloc[0]
        key = f"{name} ({role})"
        cols[key] = {
            "date": str(r["game_date"].date()), "team": r["team_abbreviation"], "position": str(r["position"]),
            "min_q10": r["min_q10_full"], "min_q50": r["min_q50_full"], "min_q90": r["min_q90_full"],
            "l20 window minutes (rate weight)": rr["window_minutes"],
            **{f"l20 {s} per min (before shrinkage)": rr[f"l20_{s}"] for s in SIM_SHORT},
            **{f"rate_{s}_per_min": r[f"rate_{s}"] for s in SIM_SHORT},
            **{f"P({s} >= 10 at q50)": r[f"p10_{s}_at_q50"] for s in SIM_SHORT},
            "SIM raw": r["p_SIM_raw"], "SIM isotonic": r["p_SIM_cal"], "C_full calibrated": r["p_C_full_cal"],
            "C_stack calibrated": r["p_C_stack_cal"], "Baseline A raw": r["p_A_raw"],
            "Baseline A calibrated": r["p_A_cal"], "actual minutes": r["minutes"],
            "actual pts/reb/ast/stl/blk": "/".join(str(int(r[s])) for s in SIM_STATS), "actual dd": int(r["dd"])}
    t = pd.DataFrame(cols)
    t.index.name = "field"
    return t.reset_index()


def equal_calibration(reg):
    """Log loss and AUC of model versus reference under the same calibration (raw versus raw, Platt versus Platt),
    plus the blends against Platt-calibrated C_full."""
    def label(m, v):
        return m if v == "cal" else f"{m} {CAL_DISPLAY[v]}"
    rows = []
    for season, g in list(reg.groupby("season")) + [("all", reg)]:
        for a, va, b, vb in EQUAL_PAIRS:
            ma, mb = basic_metrics(g["dd"], g[f"p_{a}_{va}"]), basic_metrics(g["dd"], g[f"p_{b}_{vb}"])
            rows.append({"season": season, "model": label(a, va), "reference": label(b, vb),
                         "model_log_loss": ma["log_loss"], "reference_log_loss": mb["log_loss"],
                         "log_loss_diff": ma["log_loss"] - mb["log_loss"], "model_auc": ma["auc"],
                         "reference_auc": mb["auc"], "auc_diff": ma["auc"] - mb["auc"]})
    return pd.DataFrame(rows)


def proxy_bands(reg, models, thr=BAND_THRESHOLD):
    """Proxy-edge bets (an assumption, not a price backtest) split by the stand-in implied probability q."""
    q = np.minimum(PROXY_CAP, PROXY_MARGIN * reg["p_A_cal"].to_numpy(np.float64))
    y = reg["dd"].to_numpy(np.float64)
    rows = []
    for m in models:
        p = reg[f"p_{m}_cal"].to_numpy(np.float64)
        sel = (p - q >= thr) & (q > 0)
        ret = np.zeros(len(q))
        ret[sel] = y[sel] * (1 - q[sel]) / q[sel] - (1 - y[sel])
        total = float(ret[sel].sum())
        for lo, hi, lab in Q_BANDS:
            b = sel & (q >= lo) & (q < hi)
            n = int(b.sum())
            rows.append({"model": m, "threshold": thr, "q_band": lab, "n_bets": n,
                         "hit_rate": float(y[b].mean()) if n else np.nan,
                         "mean_q": float(q[b].mean()) if n else np.nan,
                         "mean_return": float(ret[b].mean()) if n else np.nan,
                         "total_return": float(ret[b].sum()),
                         "share_of_total_return": float(ret[b].sum() / total) if total else np.nan})
    return pd.DataFrame(rows)


def shrink_note(sanity):
    """Plain sentences on how the rate shrinkage moves the sanity-check rows (computed from the table)."""
    t = sanity.set_index("field")
    parts, below, above = [], [], []
    for col in t.columns:
        name = col.split(" (")[0]
        raw, shr = float(t.loc["l20 ast per min (before shrinkage)", col]), float(t.loc["rate_ast_per_min", col])
        if raw - shr > 0.02:
            parts.append(f"{name} {raw:.3f} to {shr:.3f}")
        (below if float(t.loc["SIM raw", col]) < float(t.loc["Baseline A calibrated", col]) else above).append(name)
    out = ""
    if parts:
        out += ("Shrinkage toward the position prior (300 minutes of weight against the l20 window minutes) lowers "
                "high assist rates, l20 assists per minute to the shrunk rate: " + "; ".join(parts) + ". ")
    if below:
        out += "SIM raw is below Baseline A calibrated for " + ", ".join(below)
        out += (" and above it for " + ", ".join(above) + ". ") if above else ". "
    return out + "The isotonic step changes SIM's level, not its order."


def choose_cal_method(folds):
    tot = {m: 0.0 for m in CAL_METHODS}
    n = 0
    for f in folds:
        for m in CAL_METHODS:
            tot[m] += f["cal_select"][m] * f["cal_select"]["n"]
        n += f["cal_select"]["n"]
    pooled = {m: tot[m] / n for m in CAL_METHODS}
    return min(pooled, key=pooled.get), pooled


# --------------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------------
def fmt_table(df, digits=4, digits_map=None):
    return to_markdown(df, digits=digits, digits_map=digits_map)


def sign_list(per, a, b):
    return ", ".join(f"{s} {per.loc[s, a] - per.loc[s, b]:+.5f}" for s in per.index)


def summary_lines(ctx):
    m1, m4, mins, cs, tb, m8a, edge, folds = (ctx[k] for k in ["m1", "m4", "mins", "cs", "tb", "m8a", "edge",
                                                                "folds"])
    cal = m1[m1["version"] == "cal"]
    pooled = cal[cal["season"] == "all"].set_index("model")
    per = cal[cal["season"] != "all"].pivot(index="season", columns="model", values="log_loss")
    n_s = len(per)
    out = [f"Calibrated log loss pooled over the {n_s} test seasons: " + ", ".join(
        f"{m} {pooled.loc[m, 'log_loss']:.4f}" for m in REPORT_MODELS) + ". Pooled AUC: " + ", ".join(
        f"{m} {pooled.loc[m, 'auc']:.4f}" for m in REPORT_MODELS) + "."]
    for a, b in [("C_stack", "C_full"), ("C_stack_noabs", "C_noabs"), ("BLEND_A", "C_full"),
                 ("BLEND_SIM", "C_full"), ("SIM", "A")]:
        k = int((per[a] < per[b]).sum())
        out.append(f"{a} minus {b}, calibrated log loss per season: {sign_list(per, a, b)}; {a} is lower in {k} of "
                   f"{n_s} seasons.")
    eq = ctx["eq"][ctx["eq"]["season"] == "all"]
    eqs = ctx["eq"][ctx["eq"]["season"] != "all"]
    lower = {(r.model, r.reference): 0 for r in eq.itertuples()}
    for r in eqs.itertuples():
        lower[(r.model, r.reference)] += int(r.log_loss_diff < 0)
    out.append("Same-calibration comparisons, pooled log loss difference (negative favors the first model) and the "
               "number of seasons in which the first model is lower: " + "; ".join(
                   f"{r.model} minus {r.reference} {r.log_loss_diff:+.5f} ({lower[(r.model, r.reference)]} of {n_s})"
                   for r in eq.itertuples()) + ". Metric 1 compares "
        f"C_stack ({CAL_DISPLAY[ctx['cal_method']]}) with C_full (v1 isotonic); isotonic alone moves C_full from "
        f"{ctx['cf_raw']:.4f} raw to {ctx['cf_iso']:.4f}, so most of that gap is the calibration method, not the "
        "stacked features.")
    ma = mins[mins["season"] == "all"].set_index("model")
    out.append(
        f"Minutes, pooled test seasons: MIN_full median prediction MAE {ma.loc['MIN_full (q50)', 'mae']:.2f} minutes "
        f"(RMSE {ma.loc['MIN_full (q50)', 'rmse']:.2f}), MIN_noabs {ma.loc['MIN_noabs (q50)', 'mae']:.2f} "
        f"({ma.loc['MIN_noabs (q50)', 'rmse']:.2f}), min_ewm {ma.loc['min_ewm', 'mae']:.2f} "
        f"({ma.loc['min_ewm', 'rmse']:.2f}), last-5 mean {ma.loc['last-5 mean (min_l5)', 'mae']:.2f} "
        f"({ma.loc['last-5 mean (min_l5)', 'rmse']:.2f}). Starters (last_starter = 1): MIN_full "
        f"{ma.loc['MIN_full (q50)', 'mae_starters']:.2f} versus min_ewm {ma.loc['min_ewm', 'mae_starters']:.2f}; "
        f"non-starters: {ma.loc['MIN_full (q50)', 'mae_nonstarters']:.2f} versus "
        f"{ma.loc['min_ewm', 'mae_nonstarters']:.2f}.")
    csa = cs[cs["season"] == "all"].set_index(["model", "method"])
    out.append("Calibration study on C_full, pooled test log loss: " + ", ".join(
        f"{CAL_DISPLAY[m]} {csa.loc[('C_full', m), 'log_loss']:.4f}" for m in ["raw"] + CAL_METHODS) +
        f". Method applied to C_stack: {CAL_DISPLAY[ctx['cal_method']]} (lowest pooled log loss on the second half "
        "of each "
        "holdout slice when fitted on the first half: " + ", ".join(
            f"{CAL_DISPLAY[m]} {ctx['cal_pooled'][m]:.4f}" for m in CAL_METHODS) + ").")
    t = tb.set_index(["model", "method"])

    def bin_text(model, m, tag):
        n = int(t.loc[(model, m), f"n_{tag}"])
        if n == 0:
            return "empty"
        return f"{t.loc[(model, m), f'pred_{tag}']:.3f} versus {t.loc[(model, m), f'real_{tag}']:.3f} ({n})"
    out.append("Top two calibrated bins for C_full, mean predicted versus realized (n): " + "; ".join(
        f"{CAL_DISPLAY[m]}: [0.8, 0.9) {bin_text('C_full', m, '0.8_0.9')}, [0.9, 1.0] {bin_text('C_full', m, '0.9_1.0')}"
        for m in CAL_METHODS) + f". C_stack with {CAL_DISPLAY[ctx['cal_method']]}: [0.8, 0.9) "
        f"{bin_text('C_stack', ctx['cal_method'], '0.8_0.9')}, [0.9, 1.0] "
        f"{bin_text('C_stack', ctx['cal_method'], '0.9_1.0')}.")
    out.append("Blend weight on calibrated C_full chosen on each holdout slice: BLEND_A " + ", ".join(
        f"{f['season']} {f['blend']['w_A']:.2f}" for f in folds) + "; BLEND_SIM " + ", ".join(
        f"{f['season']} {f['blend']['w_SIM']:.2f}" for f in folds) + ".")
    tt = m4[m4["season"] == "all"].set_index("model")
    out.append("Nightly picks pooled over the test seasons, top-1 / top-2 / top-3 / all-three hit rates: " + "; ".join(
        f"{m} {tt.loc[m, 'top1_hit']:.3f} / {tt.loc[m, 'top2_hit']:.3f} / {tt.loc[m, 'top3_hit']:.3f} / "
        f"{tt.loc[m, 'all3_hit']:.3f}" for m in REPORT_MODELS) + ".")
    mid = m8a[(m8a["version"] == "cal") & (m8a["season"] == "all")].set_index("model")
    out.append(f"Mid-tier slice (Baseline A calibrated p from 0.25 to 0.65, n = {int(mid.loc['A', 'n'])}): calibrated "
               "log loss " + ", ".join(f"{m} {mid.loc[m, 'log_loss']:.4f}" for m in REPORT_MODELS) + "; AUC " +
               ", ".join(f"{m} {mid.loc[m, 'auc']:.4f}" for m in REPORT_MODELS) + ".")
    e = edge[(edge["season"] == "all") & (edge["threshold"] == 0.05)].set_index("model")
    out.append("Proxy-edge rule (an assumption, not a price backtest; q = min(0.97, 1.08 * A_cal), threshold 0.05), "
               "pooled bets, hit rate, and mean return per 1-unit bet at the fair price of q: " + "; ".join(
                   f"{m} {int(e.loc[m, 'n_bets'])}, {e.loc[m, 'hit_rate']:.3f}, {e.loc[m, 'mean_return']:+.3f}"
                   for m in EDGE_MODELS if e.loc[m, "n_bets"] > 0) + ".")
    bd = ctx["bands"]
    low = bd[bd["q_band"].isin(["below 1/51", "1/51 to 0.05"])].groupby("model")["share_of_total_return"].sum()
    out.append("Under the same assumption, bets priced at q below 0.05 supply " + ", ".join(
        f"{m} {100 * low.loc[m]:.0f}" for m in BAND_MODELS) + " percent of each model's total proxy return at "
        "threshold 0.05 (q-band table in the proxy-edge section).")
    out.append(ctx["se_note"])
    return out


def write_report(ctx, eval_dir):
    m1, m4, m5, m8a, m8b, mins, cs, cbins, tb, edge, edge_posted, imp, folds, sanity = (
        ctx[k] for k in ["m1", "m4", "m5", "m8a", "m8b", "mins", "cs", "cbins", "tb", "edge", "edge_posted", "imp",
                         "folds", "sanity"])
    args = ctx["args"]
    L = ["# Double Double Bot, v2 evaluation report", "",
         f"Generated by `tools/train_eval_v2.py` on {time.strftime('%Y-%m-%d %H:%M')} local time, following "
         "`docs/SPEC_v2.md`. Every table below is also written as a CSV in `data/eval/v2/`. The v1 results are in "
         "`data/eval/v1/report_v1.md`. Baseline A, C_full and C_noabs are read from "
         "`data/eval/v1/predictions_v1.parquet`, so every model is scored on the same rows.", "",
         "## Summary", ""] + [f"- {s}" for s in summary_lines(ctx)] + [""]

    L += ["## Setup", "",
          "- Folds, rows and holdout slices are the v1 ones: test seasons 2023 to 2026 (season end year), training on "
          "all earlier seasons from 2018, the last 15 percent of training rows by date (cut on a date boundary) as the "
          "holdout slice H, and the earlier training rows as the fit rows F. Metrics use regular-season test rows. "
          "The test season is never used for fitting.",
          "- A, C_full and C_noabs test outputs come from the v1 predictions file. Their holdout-slice outputs, needed "
          "for the blends and the calibration study, are scored with the saved v1 boosters and isotonic calibrators "
          "in `data/models/v1/`; the saved C_full booster reproduces the v1 test predictions exactly (maximum absolute "
          f"difference {max(f['v1_reproduction_max_abs_diff'] for f in folds):.1e}).",
          "- MIN: LightGBM minutes models with the v1 LightGBM settings (num_leaves 31, learning_rate 0.03, up to "
          f"{args.max_rounds} rounds with early stopping 100 on H, min_child_samples 100, feature_fraction 0.8, "
          "bagging_fraction 0.8, bagging_freq 1, lambda_l2 5, seed 42, deterministic). The point model uses objective "
          "regression_l1, so its prediction is the conditional median (q50); quantile models at 0.1 and 0.9 use the "
          "same features. MIN_full uses all 155 v1 features, MIN_noabs drops the 7 abs_ features. The target is the "
          "current game's minutes.",
          f"- SIM: for each row a grid of {args.grid} equal-probability minutes quantiles of a split normal with median "
          "q50, lower standard deviation (q50 - q10) / 1.2816 and upper standard deviation (q90 - q50) / 1.2816, "
          "truncated to [0, 48] (quantile levels spread evenly between the distribution function at 0 and at 48). "
          "Per-minute rates for points, rebounds, assists, steals and blocks: the v1 features do not store the EWM "
          "minutes weight, so the spec's fallback is used, rate = (l20 rate * w + prior * 300) / (w + 300) with "
          "w = min(games in the l20 window, 20) * min_l20. Position priors are per-minute league rates by ESPN position "
          "on the fit rows F. Given minutes m, points, rebounds and assists are negative binomial with mean rate * m "
          "and variance-to-mean ratios 2.78, 1.29 and 1.17; steals and blocks are Poisson. P(dd | m) = 1 - P(no stat "
          "reaches 10) - P(exactly one does), averaged over the grid with equal weights. SIM uses the MIN_full "
          "quantiles, SIM_noabs the MIN_noabs ones. SIM is reported raw and with isotonic calibration fitted on H.",
          "- C_stack: the C_full features plus sim_p (raw SIM) and min_pred (MIN_full q50), trained like C_full "
          "(LightGBM binary on F, early stopping on H). C_stack_noabs uses the C_noabs features plus sim_p_noabs and "
          f"min_pred_noabs. Calibrated outputs use the {CAL_DISPLAY[ctx['cal_method']]} method chosen in the "
          "calibration study.",
          "- BLEND_A: sigmoid(w * logit(C_full calibrated) + (1 - w) * logit(Baseline A calibrated)), with w on the "
          "grid 0.00 to 1.00 in steps of 0.05 chosen by log loss on H. BLEND_SIM uses calibrated SIM in place of "
          "Baseline A. Calibrated inputs are the v1 isotonic outputs (and the SIM isotonic outputs); on H these are "
          "in-sample, because the calibrators were fitted on H. Probabilities are clipped to [0.0001, 0.9999] before "
          "the logit, the same clipping log loss uses.",
          "- Calibration study: isotonic (the v1 calibrator), Platt (logistic regression on logit p) and beta "
          "calibration (logistic regression on log p and -log(1 - p), with both slopes kept non-negative), each "
          "fitted on H and applied to the test season, for C_full raw outputs, then for C_stack and C_stack_noabs.",
          "- Proxy-edge rule (an assumption, not a price backtest): described in its section below.",
          f"- Runtime: {ctx['runtime_min']:.1f} minutes from start to this report (four folds, metrics, report).",
          ""]

    L += ["### Leakage discipline", "",
          "- MIN target: the current game's minutes. MIN features: the v1 feature list, which uses only games before "
          "the current date; the abs_ features (MIN_full only) are lineup-known, as in C_full. The script asserts "
          "that no current-game outcome column is a feature.",
          "- SIM rates use pre-game l20 features. The only fitted SIM inputs are the position priors (outcomes of "
          "fit rows) and the MIN quantiles; the variance-to-mean ratios are fixed constants from the spec.",
          f"- C_stack training rows (F) get out-of-fold sim_p and min_pred. F is split into {args.inner_folds} "
          "contiguous date blocks. Each block is scored by MIN models (both variants, all three quantiles) and "
          "position priors fitted on the other blocks of F only. The number of boosting rounds of these inner models "
          "is fixed at the main MIN model's early-stopping iteration, which was chosen on H, so no block's own "
          "minutes or outcomes enter its sim_p, min_pred, or round count. Rows in later blocks do contain earlier "
          "blocks' minutes inside their pre-game window features, but only as inputs, never as targets, so they "
          "cannot carry a row's own target into its prediction.",
          "- C_stack holdout and test rows get sim_p and min_pred from the main MIN models fitted on F alone. The rows "
          "used for early stopping and calibration (H) and the test rows are therefore produced the same way, and "
          "neither was used to fit the MIN models (H only sets their early-stopping round).",
          "- Calibrators, SIM isotonic maps and blend weights are fitted on H. The calibration method applied to "
          "C_stack is chosen without test-season outcomes: each method is fitted on the first half of each fold's H "
          "(by date) and scored on the second half, pooled over the four folds.",
          "- Out-of-fold quality check (diagnostics table below), averaged over folds: MIN_full median MAE "
          f"{np.mean([f['diagnostics']['full']['fit_oof_min_mae'] for f in folds]):.2f} minutes on F from the inner "
          f"models versus {np.mean([f['diagnostics']['full']['holdout_min_mae'] for f in folds]):.2f} on H from the "
          "main models; raw SIM log loss "
          f"{np.mean([f['diagnostics']['full']['fit_oof_sim_logloss'] for f in folds]):.4f} on F versus "
          f"{np.mean([f['diagnostics']['full']['holdout_sim_logloss'] for f in folds]):.4f} on H. F and H cover "
          "different dates, so these are a check on scale, not an exact comparison.", ""]

    fd = pd.DataFrame([{"season": f["season"], "fit_rows": f["fit_rows"], "fit_end": f["fit_end"],
                        "holdout_rows": f["holdout_rows"], "holdout_start": f["holdout_start"],
                        "test_rows": f["test_rows"],
                        "inner_blocks": "; ".join(f"{b['start']} to {b['end']} ({b['rows']})" for b in f["inner_blocks"]),
                        "MIN_full_q50_iter": f["MIN_full_q50_best_iteration"],
                        "MIN_full_q10_iter": f["MIN_full_q10_best_iteration"],
                        "MIN_full_q90_iter": f["MIN_full_q90_best_iteration"],
                        "MIN_noabs_q50_iter": f["MIN_noabs_q50_best_iteration"],
                        "C_stack_iter": f["C_stack_best_iteration"],
                        "C_stack_noabs_iter": f["C_stack_noabs_best_iteration"]} for f in folds])
    L += ["### Folds", "", fmt_table(fd), ""]
    caps = [f"S{f['season']} {k.replace('_hit_round_cap', '')}" for f in folds for k, v in f.items()
            if k.endswith("_hit_round_cap") and v]
    L += [("- LightGBM reached the round cap in: " + ", ".join(caps) + ".") if caps else
          f"- No LightGBM fit reached the {args.max_rounds}-round cap; early stopping ended every fit.", ""]
    dg = pd.DataFrame([{"season": f["season"], "variant": v, **f["diagnostics"][v]} for f in folds for v in VARIANTS])
    L += ["Out-of-fold diagnostics (F rows scored by the inner models, H rows by the main models):", "",
          fmt_table(dg), ""]

    L += ["## Metric 1: log loss, Brier, AUC per season and model", "",
          "Calibrated outputs. A, C_full and C_noabs use the v1 isotonic calibration; SIM and SIM_noabs isotonic on H; "
          f"C_stack and C_stack_noabs the {CAL_DISPLAY[ctx['cal_method']]} method; the blends are the logit blends "
          "of calibrated "
          "inputs.", "", fmt_table(m1[m1["version"] == "cal"].drop(columns="version")), "",
          "Raw outputs (no raw version exists for the blends):", "",
          fmt_table(m1[m1["version"] == "raw"].drop(columns="version")), ""]
    L += ["### Same-calibration comparisons", "",
          "Metric 1 uses each model's own calibration, and the calibration study shows that the v1 isotonic step "
          f"raises C_full's pooled log loss from {ctx['cf_raw']:.4f} (raw) to {ctx['cf_iso']:.4f}. This table compares "
          "models under the same calibration: raw against raw, Platt against Platt, and the blends against "
          "Platt-calibrated C_full. Negative log_loss_diff and positive auc_diff favor the first model.", "",
          fmt_table(ctx["eq"], digits_map={"log_loss_diff": 5, "auc_diff": 5}), ""]

    L += ["## Minutes model (MIN)", "",
          "Regular-season test rows. Errors are prediction minus actual minutes. The MIN rows use the median model "
          "(q50). share_below_q10 and share_below_q90 are the shares of actual minutes below the q10 and q90 "
          "predictions (0.10 and 0.90 if the quantiles are calibrated); mean_q90_minus_q10 is the mean interval "
          "width. Starters and non-starters are split by last_starter (the previous game's starter flag).", "",
          fmt_table(mins, digits=3), ""]
    qc = pd.DataFrame([{"season": f["season"], "variant": v, **f["quantile_crossing_test"][v]} for f in folds
                       for v in VARIANTS])
    L += ["Quantile crossing on test rows (share of rows; the SIM grid floors each half-width at 0.25 minutes):", "",
          fmt_table(qc), ""]

    L += ["## Calibration study", "",
          "C_full raw outputs calibrated three ways (fitted on H, applied to the test season), then the same for "
          "C_stack and C_stack_noabs. Pooled test seasons:", "",
          fmt_table(cs[cs["season"] == "all"].drop(columns="season")), "",
          "Top two calibrated bins (pooled test seasons): n, mean predicted, realized.", "",
          fmt_table(tb, digits=3), "",
          "Method selection without test outcomes (fit on the first half of each holdout slice, log loss on the "
          "second half):", ""]
    sel = pd.DataFrame([{"season": f["season"], "second_half_rows": f["cal_select"]["n"],
                         "second_half": " to ".join(f["cal_select"]["second_half"]),
                         **{m: f["cal_select"][m] for m in CAL_METHODS}} for f in folds])
    sel = pd.concat([sel, pd.DataFrame([{"season": "pooled", "second_half_rows": int(sel["second_half_rows"].sum()),
                                         "second_half": "", **ctx["cal_pooled"]}])], ignore_index=True)
    L += [fmt_table(sel), "", f"Chosen method for C_stack and C_stack_noabs: {CAL_DISPLAY[ctx['cal_method']]}.",
          "",
          "Full calibration table for C_full (pooled test seasons, ten bins of calibrated p):", ""]
    for m in CAL_METHODS:
        L += [f"### C_full, {CAL_DISPLAY[m]}", "", fmt_table(cbins[(cbins["model"] == "C_full") & (cbins["method"] == m)].drop(
            columns=["model", "method"])), ""]
    L += [f"### C_stack, {CAL_DISPLAY[ctx['cal_method']]}", "", fmt_table(cbins[(cbins["model"] == "C_stack") & (
        cbins["method"] == ctx["cal_method"])].drop(columns=["model", "method"])), "",
          "Per-season scores and all bins for every model and method are in `calibration_scores.csv` and "
          "`calibration_bins.csv`. Platt and beta coefficients per fold are in `folds_v2.json`.", ""]

    L += ["## Metric 4: nightly top-N picks", "",
          "For each game date, regular-season rows are ranked by calibrated p (ties broken by the raw score; the "
          "blends have no raw score). topK_hit is the fraction of the top K picks that recorded a dd; all3_hit is the "
          "share of nights on which all three top picks hit; mean_p_all3 is the mean product of their calibrated "
          "probabilities. " + ctx["se_note"], "", fmt_table(m4.drop(columns="top10_names")), "",
          "Ten most frequent names in the nightly top 3, pooled test seasons:", "",
          fmt_table(m4[m4["season"] == "all"][["model", "top10_names"]]), ""]

    L += ["## Metric 5: disagreement against Baseline A", "",
          "Rows bucketed by model calibrated p minus Baseline A calibrated p. Pooled test seasons:", ""]
    for m in ["C_stack", "BLEND_A"]:
        L += [f"### {m}", "", fmt_table(m5[(m5["model"] == m) & (m5["season"] == "all")].drop(
            columns=["model", "season"])), ""]
    L += ["Per-season rows and the same buckets for C_stack_noabs, BLEND_SIM and SIM are in "
          "`metric5_disagreement.csv`.", ""]

    L += ["## Metric 8: mid-tier slice (Baseline A calibrated p between 0.25 and 0.65)", "",
          "Metric 1 on the slice, calibrated outputs:", "",
          fmt_table(m8a[m8a["version"] == "cal"].drop(columns="version")), "",
          "Metric 5 on the slice, pooled test seasons:", ""]
    for m in ["C_stack", "BLEND_A"]:
        L += [f"### {m}", "", fmt_table(m8b[(m8b["model"] == m) & (m8b["season"] == "all")].drop(
            columns=["model", "season"])), ""]
    L += ["Raw-output slice scores and per-season slice buckets are in `metric8_midtier_scores.csv` and "
          "`metric8_midtier_disagreement.csv`.", ""]

    L += ["## Proxy-edge rule (an assumption, not a price backtest)", "",
          "This section rests on an assumption about prices; no historical double-double prices were available. "
          "The assumed stand-in implied probability is q = min(0.97, 1.08 * Baseline A calibrated p), meant to mimic a "
          "Yes-only price with about 8 percent margin. A Yes bet is placed when model calibrated p minus q is at least "
          "the threshold. Returns assume a flat 1-unit stake paid at the fair price of q: return per bet = "
          "hit * (1 - q) / q - (1 - hit). Baseline A is listed for completeness: q is 1.08 times its calibrated p "
          "(capped at 0.97) and its largest calibrated p in these rows is "
          f"{ctx['max_a_cal']:.3f}, so its p never exceeds q by a threshold and it places no bets. "
          "Forward prices are logged in `data/odds/dd_prices.csv` for the real test; until that sample exists these "
          "figures say only how each model disagrees with Baseline A, not whether it beats a book. Baseline A has "
          "higher log loss than every model here (metric 1), and the bets are rows where Baseline A is low relative "
          "to the model; metric 5 shows the realized rate on such rows above Baseline A's mean (C_stack more than "
          f"0.10 above A: realized {ctx['dis_hi']['realized']:.3f} versus A mean {ctx['dis_hi']['mean_baseline_p']:.3f}, "
          f"n = {int(ctx['dis_hi']['n'])}). Positive returns under this assumption are therefore expected by "
          "construction. The median American price of the bets sits far down the longshot range, so a few hits at "
          "long implied odds move the mean return.", "",
          "Pooled test seasons (assumption-based):", "",
          fmt_table(edge[edge["season"] == "all"].drop(columns="season"), digits_map={"median_american_at_q": 0}), ""]
    per_season = edge[edge["season"] != "all"]
    pw = []
    for m in EDGE_MODELS:
        for thr in EDGE_THRESHOLDS:
            g = per_season[(per_season["model"] == m) & (per_season["threshold"] == thr)].set_index("season")
            row = {"model": m, "threshold": thr}
            for s in g.index:
                row[f"n_{s}"] = int(g.loc[s, "n_bets"])
                row[f"return_{s}"] = g.loc[s, "mean_return"]
            pw.append(row)
    L += ["Per season, bets and mean return per bet (assumption-based):", "", fmt_table(pd.DataFrame(pw), digits=3), "",
          "Per season at threshold 0.05, all columns (assumption-based; other thresholds per season are in "
          "`proxy_edge.csv`):", "",
          fmt_table(edge[(edge["season"] != "all") & (edge["threshold"] == 0.05) & (edge["model"] != "A")].drop(
              columns="threshold"), digits_map={"median_american_at_q": 0}), "",
          "Bets by stand-in implied probability q, threshold 0.05, pooled (assumption-based). share_of_total_return is "
          "each band's share of the model's total return under the proxy assumption:", "",
          fmt_table(ctx["bands"].drop(columns="threshold")), "",
          "Same assumption, restricted to rows with q at least 1/51 (no price longer than +5000, the longest Yes "
          "price in the 2026-10-29 FanDuel snapshot), pooled:", "",
          fmt_table(edge_posted[edge_posted["season"] == "all"].drop(columns="season"),
                    digits_map={"median_american_at_q": 0}), ""]

    bl = pd.DataFrame([{"season": f["season"], "w_A": f["blend"]["w_A"],
                        "holdout_logloss_at_w_A": float(np.min(f["blend"]["holdout_logloss_A"])),
                        "holdout_logloss_C_full_only": float(f["blend"]["holdout_logloss_A"][-1]),
                        "holdout_logloss_A_only": float(f["blend"]["holdout_logloss_A"][0]),
                        "w_SIM": f["blend"]["w_SIM"],
                        "holdout_logloss_at_w_SIM": float(np.min(f["blend"]["holdout_logloss_SIM"])),
                        "holdout_logloss_SIM_only": float(f["blend"]["holdout_logloss_SIM"][0])} for f in folds])
    L += ["## Blend weights per fold", "",
          "w is the weight on calibrated C_full in logit space, chosen on H. The holdout log losses use in-sample "
          "isotonic outputs and are optimistic by the same small amount for both inputs.", "", fmt_table(bl), ""]

    t6 = pd.DataFrame({"rank": range(1, 31),
                       "C_stack_feature": imp["C_stack"].index[:30], "C_stack_gain": imp["C_stack"].values[:30],
                       "C_stack_noabs_feature": imp["C_stack_noabs"].index[:30],
                       "C_stack_noabs_gain": imp["C_stack_noabs"].values[:30]})
    tot = imp["C_stack"].sum()
    L += [f"## Feature importance (gain), C_stack, last fold (test season {max(f['season'] for f in folds)}), top 30",
          "", f"sim_p carries {100 * imp['C_stack'].get('sim_p', 0) / tot:.1f} percent of C_stack's total gain and "
          f"min_pred {100 * imp['C_stack'].get('min_pred', 0) / tot:.1f} percent.", "",
          fmt_table(t6, digits_map={"C_stack_gain": 0, "C_stack_noabs_gain": 0}), ""]

    L += ["## SIM sanity check", "",
          "Hand-picked regular-season rows (the player's game closest to the listed target date). Minutes quantiles "
          "are MIN_full; rates are the shrunk per-minute rates; P(stat >= 10 at q50) is each marginal at the median "
          "minutes. Tyrese Haliburton has no 2026 rows in the data, so Cade Cunningham is the 2026 guard and "
          "Haliburton is shown on a 2025 date. " + ctx["shrink_note"], "", fmt_table(sanity, digits=3), ""]

    L += ["## Notes and deviations from the spec", ""] + [f"- {n}" for n in ctx["notes"]] + [""]
    L += ["## Files", "",
          "- `data/eval/v2/predictions_v2.parquet`: test-season rows (all season types) with the v1 outputs, MIN "
          "quantiles, shrunk rates, marginal tails at q50, SIM, C_stack under each calibration method, and the blends.",
          "- `data/eval/v2/metric1_scores.csv`, `metric4_topn.csv`, `metric4_top_names.csv`, "
          "`metric5_disagreement.csv`, `metric8_midtier_scores.csv`, `metric8_midtier_disagreement.csv`, "
          "`minutes_model.csv`, `calibration_scores.csv`, `calibration_bins.csv`, `calibration_top_bins.csv`, "
          "`calibration_selection.csv`, `blend_weights.csv`, `importance_c_stack.csv`, `sim_sanity_check.csv`, "
          "`equal_calibration.csv`, `folds_v2.json`, and the proxy-edge tables `proxy_edge.csv`, "
          "`proxy_edge_posted_range.csv` and `proxy_edge_q_bands.csv` (assumption-based, not a price backtest).",
          "- `data/models/v2/`: per fold, `MIN_{full,noabs}_{q10,q50,q90}_S{S}.txt` (main minutes models), "
          "`C_stack_S{S}.txt`, `C_stack_noabs_S{S}.txt`, `calibrators_S{S}.pkl` (SIM isotonic maps, C_full and "
          "C_stack calibrators, blend weights), and `sim_priors_S{S}.json` (position priors). The inner out-of-fold "
          "minutes models are not saved; only their predictions on F were used.", ""]
    text = "\n".join(L)
    assert "\u2014" not in text and "!" not in text, "report must not contain em-dashes or exclamation points"
    (eval_dir / "report_v2.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------------------------
def evaluate(preds, folds, imp, run_info, args, eval_dir, t0, report_only=False):
    reg = preds[preds["season_type"] == 2].reset_index(drop=True)
    m1 = metric1_v2(reg, REPORT_MODELS)
    m4, names = metric4_v2(reg, REPORT_MODELS)
    m5 = pd.concat([disagreement(reg, m) for m in DIS_MODELS], ignore_index=True)
    mid = reg[(reg["p_A_cal"] >= 0.25) & (reg["p_A_cal"] <= 0.65)].reset_index(drop=True)
    m8a = metric1_v2(mid, REPORT_MODELS)
    m8b = pd.concat([disagreement(mid, m) for m in DIS_MODELS], ignore_index=True)
    mins = minutes_table(reg)
    cs, cbins = calibration_study(reg)
    tb = top_bins_table(cbins)
    edge = proxy_edge(reg, EDGE_MODELS)
    edge_posted = proxy_edge(reg, EDGE_MODELS, q_floor=POSTED_Q_FLOOR)
    ds = pd.read_parquet(DATASET_PATH, columns=["game_id", "athlete_id", "pts_pm_l20", "reb_pm_l20", "ast_pm_l20",
                                                "stl_l20", "blk_l20", "min_l20", "games_played_career"])
    r20, w20 = l20_rates(ds)
    raw_l20 = ds[["game_id", "athlete_id"]].copy()
    for k, s in enumerate(SIM_SHORT):
        raw_l20[f"l20_{s}"] = r20[:, k]
    raw_l20["window_minutes"] = w20
    sanity = sanity_table(preds, raw_l20)
    eq = equal_calibration(reg)
    bands = proxy_bands(reg, BAND_MODELS)
    csa_all = cs[(cs["season"] == "all") & (cs["model"] == "C_full")].set_index("method")
    cal_method, cal_pooled = run_info["cal_method"], run_info["cal_pooled"]
    sel = pd.DataFrame([{"season": f["season"], "second_half_rows": f["cal_select"]["n"],
                         **{m: f["cal_select"][m] for m in CAL_METHODS}} for f in folds])
    bl = pd.DataFrame([{"season": f["season"], "w_A": f["blend"]["w_A"], "w_SIM": f["blend"]["w_SIM"],
                        **{f"holdout_logloss_A_w{w:.2f}": x for w, x in zip(f["blend"]["grid"],
                                                                             f["blend"]["holdout_logloss_A"])},
                        **{f"holdout_logloss_SIM_w{w:.2f}": x for w, x in zip(f["blend"]["grid"],
                                                                               f["blend"]["holdout_logloss_SIM"])}}
                       for f in folds])
    imp_df = pd.concat([imp[n].rename("gain").reset_index().assign(model=n) for n in ["C_stack", "C_stack_noabs"]],
                       ignore_index=True).rename(columns={"index": "feature"})
    imp_df["rank"] = imp_df.groupby("model").cumcount() + 1
    for name, t in [("metric1_scores", m1), ("metric4_topn", m4), ("metric4_top_names", names),
                    ("metric5_disagreement", m5), ("metric8_midtier_scores", m8a),
                    ("metric8_midtier_disagreement", m8b), ("minutes_model", mins), ("calibration_scores", cs),
                    ("calibration_bins", cbins), ("calibration_top_bins", tb), ("calibration_selection", sel),
                    ("proxy_edge", edge), ("proxy_edge_posted_range", edge_posted), ("blend_weights", bl),
                    ("importance_c_stack", imp_df[["model", "rank", "feature", "gain"]]),
                    ("sim_sanity_check", sanity), ("equal_calibration", eq), ("proxy_edge_q_bands", bands)]:
        t.to_csv(eval_dir / f"{name}.csv", index=False)

    per_season = m4[(m4["season"] != "all") & (m4["model"] == "C_full")]
    nights = float(per_season["nights"].mean())
    p1, p3 = float(per_season["top1_hit"].mean()), float(per_season["top3_hit"].mean())
    se_note = (f"For scale, the binomial standard error of one season's top-1 hit rate (about {nights:.0f} nights, "
               f"rate near {p1:.2f}) is about {np.sqrt(p1 * (1 - p1) / nights):.3f}, and of a top-3 hit rate "
               f"(about {3 * nights:.0f} picks, rate near {p3:.2f}) about {np.sqrt(p3 * (1 - p3) / (3 * nights)):.3f}.")
    k = args.inner_folds
    inner_min = sum(f["seconds"]["inner_oof"] for f in folds) / 60
    factor = (5 * 4 / 5) / (k * (k - 1) / k)
    est5 = total_minutes(run_info, t0, report_only) + inner_min * (factor - 1)
    eqa = eq[eq["season"] == "all"].set_index("model")
    blend_rel = {b: ("lower" if eqa.loc[b, "log_loss_diff"] < 0 else "higher") for b in ["BLEND_A", "BLEND_SIM"]}
    blend_diff = {b: eqa.loc[b, "log_loss_diff"] for b in ["BLEND_A", "BLEND_SIM"]}
    if blend_rel["BLEND_A"] == blend_rel["BLEND_SIM"]:
        blend_txt = (f"both blends have {blend_rel['BLEND_A']} pooled log loss than Platt-calibrated C_full "
                     f"(BLEND_A {blend_diff['BLEND_A']:+.5f}, BLEND_SIM {blend_diff['BLEND_SIM']:+.5f})")
    else:
        blend_txt = (f"BLEND_A has {blend_rel['BLEND_A']} ({blend_diff['BLEND_A']:+.5f}) and BLEND_SIM "
                     f"{blend_rel['BLEND_SIM']} ({blend_diff['BLEND_SIM']:+.5f}) pooled log loss than "
                     "Platt-calibrated C_full")
    notes = [
        f"Inner out-of-fold split: {k} time-ordered blocks of the fit rows instead of the 5 suggested in the task. "
        "The choice was made before the full run from a timing test on the largest fold (about 30 seconds per "
        "median minutes fit), which projected about 35 minutes in total for 5 blocks against the spec's 30-minute "
        f"budget. In the measured run the {k}-block inner fits took {inner_min:.1f} minutes; 5 blocks would take "
        f"about {factor:.1f} times as long, about {est5:.0f} minutes in total, "
        + (f"inside the budget with about {30 - est5:.0f} minutes of margin. " if est5 <= 30 else "over the budget. ")
        + "`--inner-folds 5` runs that version. Each block's inner models train on "
        f"{100 * (k - 1) / k:.0f} percent of F; the diagnostics table compares their quality with the main models.",
        f"Metric 1 scores C_stack with {CAL_DISPLAY[ctx_cal(run_info)]} and C_full with the v1 isotonic calibration, as "
        "the spec directs. The isotonic step raises C_full's pooled log loss from "
        f"{csa_all.loc['raw', 'log_loss']:.4f} to {csa_all.loc['isotonic', 'log_loss']:.4f}, so the same-calibration "
        "table is the measure of what sim_p and min_pred add.",
        f"BLEND_A and BLEND_SIM blend the v1 isotonic C_full, as the spec directs; {blend_txt}. The weight on C_full "
        "is at "
        f"least {min(min(f['blend']['w_A'], f['blend']['w_SIM']) for f in folds):.2f} in every fold.",
        "The proxy-edge figures (an assumption, not a price backtest) use Baseline A as the stand-in market, and "
        "Baseline A has higher log loss than every other model here, so they measure disagreement with a weak reference.",
        "The EWM minutes weight is not stored in the v1 features, so the SIM rates use the spec's fallback: l20 "
        "per-minute rates with weight min(games in the window, 20) * min_l20. The EWM sum of weights could be "
        "rebuilt from games_played_career (about 12 games at most for half-life 8), but the spec designates the "
        "l20 fallback for this case.",
        "Steals and blocks have no stored per-minute features; their l20 rates are stl_l20 / min_l20 and "
        "blk_l20 / min_l20, equal to the ratio of window sums because both are means over the same games.",
        "The variance-to-mean ratios (2.78, 1.29, 1.17) were measured on raw game logs within player-seasons, so "
        "they include minutes variation. SIM applies them conditional on minutes and also mixes over minutes, so its "
        "spread is wider than the measured one; the isotonic step corrects the level, not the ranking.",
        "Position priors are computed on the fit rows F (the rows the MIN models are fitted on), and on F minus the "
        "block for the out-of-fold rows.",
        "The minutes grid is the truncated split normal described in Setup. When separately fitted quantile models "
        "cross (q10 above q50 or q90 below q50), each half-width is floored at 0.25 minutes; crossing rates are in "
        "the minutes section.",
        "C_full calibrated outputs in metric 1 stay the v1 isotonic ones, so they match `report_v1.md`. Platt and "
        "beta versions are in the calibration study. The blends use the v1 isotonic C_full.",
        "The calibration method for C_stack is chosen on holdout halves, not on test seasons, so that C_stack's "
        "reported calibrated scores carry no test-season selection.",
        "The proxy-edge returns are an assumption-based illustration, not a backtest against prices. Under the "
        f"assumption, q goes as low as {ctx_min_q(reg):.4f} because Baseline A calibrated p goes that low, and a few "
        "longshot hits can dominate the mean return; the posted-range table restricts q to 1/51 or more.",
        "The optional v2 features (arena_ast_excess_prev and the abs_ season-boundary fix) were not built. Both "
        "change the C_full feature set, so they need a rebuilt dataset and retrained C_full and C_noabs to report "
        "metric 7, which does not fit next to this run in the 30-minute budget; v1 predictions were kept as the "
        "comparison point as the spec asks.",
        "Metrics 2, 3, 6 and 7 of v1 are not repeated; the calibration study covers calibration for the models that "
        "changed, and metric 7 is unchanged because C_full and C_noabs are the v1 models.",
        "Baseline B is kept in the predictions file but not in the v2 tables, which follow the spec's model list.",
    ]
    ctx = {"m1": m1, "m4": m4, "m5": m5, "m8a": m8a, "m8b": m8b, "mins": mins, "cs": cs, "cbins": cbins, "tb": tb,
           "edge": edge, "edge_posted": edge_posted, "imp": imp, "folds": folds, "sanity": sanity,
           "cal_method": cal_method, "cal_pooled": cal_pooled, "args": args, "notes": notes, "se_note": se_note,
           "runtime_min": total_minutes(run_info, t0, report_only),
           "dis_hi": m5[(m5["model"] == "C_stack") & (m5["season"] == "all")].set_index("bucket").loc["> 0.10"],
           "max_a_cal": float(reg["p_A_cal"].max()), "eq": eq, "bands": bands, "shrink_note": shrink_note(sanity),
           "cf_raw": float(csa_all.loc["raw", "log_loss"]), "cf_iso": float(csa_all.loc["isotonic", "log_loss"])}
    write_report(ctx, eval_dir)
    log(f"wrote report and CSVs to {eval_dir}", t0)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    ff = lambda v: f"{v:.4f}"  # noqa: E731
    print(m1[m1["version"] == "cal"].to_string(index=False, float_format=ff))
    print(mins.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(cs[cs["season"] == "all"].to_string(index=False, float_format=ff))
    print(tb.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(m4[["season", "model", "top1_hit", "top2_hit", "top3_hit", "all3_hit"]].to_string(index=False,
                                                                                         float_format=ff))
    print(m8a[(m8a["version"] == "cal")].to_string(index=False, float_format=ff))
    print(edge[edge["season"] == "all"].to_string(index=False, float_format=ff))
    print(edge_posted[edge_posted["season"] == "all"].to_string(index=False, float_format=ff))
    print(sanity.to_string(index=False))


def ctx_cal(run_info):
    return run_info["cal_method"]


def total_minutes(run_info, t0, report_only):
    """Run time from start to the report; a report-only pass reuses the saved full-run figure."""
    return float(run_info["total_minutes"]) if report_only else (time.time() - t0) / 60


def ctx_min_q(reg):
    return float(np.minimum(PROXY_CAP, PROXY_MARGIN * reg["p_A_cal"].to_numpy(np.float64)).min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=3000)
    ap.add_argument("--inner-folds", type=int, default=3)
    ap.add_argument("--grid", type=int, default=15, help="minutes quantiles per row in SIM")
    ap.add_argument("--seasons", type=int, nargs="*", default=TEST_SEASONS)
    ap.add_argument("--out-dir", type=str, default=None, help="write eval/ and models/ here instead (smoke tests)")
    ap.add_argument("--report-only", action="store_true",
                    help="recompute metrics and the report from saved predictions, folds and models")
    args = ap.parse_args()
    t0 = time.time()
    np.random.seed(SEED)
    eval_dir = Path(args.out_dir) / "eval" if args.out_dir else EVAL_DIR
    models_dir = Path(args.out_dir) / "models" if args.out_dir else MODELS_DIR
    eval_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    spec = json.loads(FEATURE_LIST_PATH.read_text(encoding="utf-8"))
    feats = {"full": spec["features"], "noabs": [f for f in spec["features"] if not f.startswith("abs_")]}
    for v in VARIANTS:
        assert not FORBIDDEN & set(feats[v]), "current-game outcome columns must not be features"
        assert not FORBIDDEN & set(STACK_COLS[v])

    if args.report_only:
        preds = pd.read_parquet(eval_dir / "predictions_v2.parquet")
        saved = json.loads((eval_dir / "folds_v2.json").read_text(encoding="utf-8"))
        folds, run_info = saved["folds"], saved["run"]
        args.inner_folds, args.grid = run_info["inner_folds"], run_info["grid"]
        last = max(f["season"] for f in folds)
        imp = {}
        for n in ["C_stack", "C_stack_noabs"]:
            b = lgb.Booster(model_file=str(models_dir / f"{n}_S{last}.txt"))
            imp[n] = pd.Series(b.feature_importance(importance_type="gain"), index=b.feature_name()).sort_values(
                ascending=False)
    else:
        df = pd.read_parquet(DATASET_PATH)
        df["position"] = pd.Categorical(df["position"].astype(object), categories=spec["position_categories"])
        pv1 = pd.read_parquet(V1_EVAL_DIR / "predictions_v1.parquet")
        pv1 = pv1[["game_id", "athlete_id", "p_A_raw", "p_A_cal", "p_B_raw", "p_B_cal", "p_C_full_raw", "p_C_full_cal",
                   "p_C_noabs_raw", "p_C_noabs_cal"]]
        log(f"dataset {df.shape}; v1 predictions {pv1.shape}; inner folds {args.inner_folds}; grid {args.grid}", t0)
        outs, folds, imp = [], [], None
        for S in args.seasons:
            out, meta, imp = run_fold(df, pv1, S, feats, args, models_dir, t0)
            outs.append(out)
            folds.append(meta)
        preds = pd.concat(outs, ignore_index=True)
        cal_method, cal_pooled = choose_cal_method(folds)
        for n in ["C_stack", "C_stack_noabs"]:
            preds[f"p_{n}_cal"] = preds[f"p_{n}_{cal_method}"]
        preds.to_parquet(eval_dir / "predictions_v2.parquet", index=False)
        run_info = {"max_rounds": args.max_rounds, "inner_folds": args.inner_folds, "grid": args.grid,
                    "cal_method": cal_method, "cal_pooled": cal_pooled,
                    "train_minutes": round((time.time() - t0) / 60, 2), "finished": time.strftime("%Y-%m-%d %H:%M")}
        run_info["total_minutes"] = run_info["train_minutes"]
        (eval_dir / "folds_v2.json").write_text(json.dumps(jsonable({"run": run_info, "folds": folds}), indent=2),
                                                encoding="utf-8")
    evaluate(preds, folds, imp, run_info, args, eval_dir, t0, args.report_only)
    if not args.report_only:
        run_info["total_minutes"] = round((time.time() - t0) / 60, 2)
        (eval_dir / "folds_v2.json").write_text(json.dumps(jsonable({"run": run_info, "folds": folds}), indent=2),
                                                encoding="utf-8")
    log(f"total runtime {(time.time() - t0) / 60:.1f} minutes", t0)


if __name__ == "__main__":
    main()
