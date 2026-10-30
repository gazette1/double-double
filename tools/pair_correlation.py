"""
pair_correlation.py: how double-double outcomes move together inside a game, for pricing multi-leg combos.

Why (2026-10-30): the Stokastic NBA DFS articles Russ asked to be read claim, without numbers, that same-team
usage is close to zero-sum (negative link between teammates' ceilings), that a passer and his finisher move
together, that a starter and his direct backup are negatively linked, and that pace, total and blowouts move
everyone in a game the same way (positive link, opponents included). None of that was measured. A combo priced
as the product of independent legs is wrong by exactly these links, so this measures them on the v1 test
seasons (2022-23 to 2025-26, regular season) with the production model's own probabilities.

For every game, every pair of scored players with calibrated probability at least P_MIN is labelled same-team
or opponents, and the report gives per group: pairs, mean joint hit rate, mean product of the two
probabilities, their ratio (1.00 means independence holds; above 1 means the combo is worth more than the
product), the phi correlation of the two outcomes, and the correlation of the two residuals (outcome minus
probability). The ratio carries a block-bootstrap interval by game date. Splits: pair type; both legs at least
LEG_MIN (the band a real combo would use); starters against starter-plus-bench on the same team; center pairs;
game pace tercile from the trailing team possessions; final margin bucket (after the fact, to show the blowout
mechanism); the team pair's positions.

Outputs: data/eval/pairs/report_pairs.md and pairs_summary.csv.
Run: PYTHONUTF8=1 python tools/pair_correlation.py [--p-min 0.10] [--leg-min 0.30] [--boot 500]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "data" / "features"
OUT = ROOT / "data" / "eval" / "pairs"
SEED = 42


def log(msg, t0):
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


def load(t0):
    import pyarrow.parquet as pq
    names = pq.read_schema(FEAT / "dataset_v1.parquet").names
    pos_col = next((c for c in names if "position" in c.lower()), None)
    cols = ["game_id", "athlete_id", "season", "season_type", "game_date", "team_abbreviation", "opponent_team_id",
            "starter", "dd", "team_poss_l10", "opp_poss_l10"] + ([pos_col] if pos_col else [])
    df = pd.read_parquet(FEAT / "dataset_v1.parquet", columns=cols)
    pred = pd.read_parquet(ROOT / "data" / "eval" / "v1" / "predictions_v1.parquet",
                           columns=["game_id", "athlete_id", "p_C_full_cal"])
    df = df.merge(pred, on=["game_id", "athlete_id"], how="inner")
    if df["season_type"].nunique() > 1:
        reg = 2 if (df["season_type"] == 2).any() else df["season_type"].mode().iloc[0]
        df = df[df["season_type"] == reg]
    df = df.rename(columns={"p_C_full_cal": "p"})
    df["pos"] = df[pos_col].astype(str) if pos_col else "NA"
    df["big"] = df["pos"].str.upper().str.startswith("C")
    log(f"{len(df):,} scored test rows, seasons {sorted(df.season.unique())}, position column {pos_col}", t0)
    # final margin per game from hoopR team box scores
    frames = []
    for s in sorted(df["season"].unique()):
        p = ROOT / "data" / "raw" / "hoopr" / f"team_box_{int(s)}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p, columns=["game_id", "team_score", "opponent_team_score"]))
    if frames:
        tb = pd.concat(frames).drop_duplicates("game_id")
        tb["margin"] = (tb["team_score"] - tb["opponent_team_score"]).abs()
        df = df.merge(tb[["game_id", "margin"]], on="game_id", how="left")
    else:
        df["margin"] = np.nan
    # game pace: mean trailing possessions of the two teams
    pace = df.groupby("game_id")["team_poss_l10"].mean().rename("pace")
    df = df.merge(pace, on="game_id", how="left")
    return df


def build_pairs(df, p_min, t0):
    d = df[df["p"] >= p_min].copy()
    d["date_i"] = pd.factorize(d["game_date"].astype(str))[0]
    rows = []
    cols = ["athlete_id", "team_abbreviation", "starter", "dd", "p", "big", "pos"]
    for gid, g in d.groupby("game_id", sort=False):
        if len(g) < 2:
            continue
        a = g[cols].to_numpy()
        n = len(a)
        ii, jj = np.triu_indices(n, k=1)
        same = a[ii, 1] == a[jj, 1]
        rows.append(pd.DataFrame({
            "game_id": gid, "date_i": g["date_i"].iloc[0], "pace": g["pace"].iloc[0], "margin": g["margin"].iloc[0],
            "same_team": same,
            "y1": a[ii, 3].astype(float), "y2": a[jj, 3].astype(float),
            "p1": a[ii, 4].astype(float), "p2": a[jj, 4].astype(float),
            "s1": a[ii, 2].astype(float), "s2": a[jj, 2].astype(float),
            "b1": a[ii, 5].astype(bool), "b2": a[jj, 5].astype(bool),
            "pos1": a[ii, 6], "pos2": a[jj, 6]}))
    pr = pd.concat(rows, ignore_index=True)
    pr["joint"] = pr["y1"] * pr["y2"]
    pr["prod"] = pr["p1"] * pr["p2"]
    pr["r1"] = pr["y1"] - pr["p1"]
    pr["r2"] = pr["y2"] - pr["p2"]
    log(f"{len(pr):,} pairs from {pr.game_id.nunique():,} games (p at least {p_min})", t0)
    return pr


def summarize(pr, label, rng, boot):
    n = len(pr)
    if n < 50:
        return None
    joint, prod = pr["joint"].mean(), pr["prod"].mean()
    phi = np.corrcoef(pr["y1"], pr["y2"])[0, 1] if pr["y1"].std() > 0 and pr["y2"].std() > 0 else np.nan
    rc = np.corrcoef(pr["r1"], pr["r2"])[0, 1]
    # block bootstrap by game date for the ratio
    di = pr["date_i"].to_numpy()
    uniq, inv = np.unique(di, return_inverse=True)
    sj = np.bincount(inv, weights=pr["joint"].to_numpy())
    sp = np.bincount(inv, weights=pr["prod"].to_numpy())
    srr = np.bincount(inv, weights=(pr["r1"] * pr["r2"]).to_numpy())
    cnt = np.bincount(inv)
    ratios, covs = [], []
    for _ in range(boot):
        k = rng.integers(0, len(uniq), len(uniq))
        ratios.append(sj[k].sum() / max(sp[k].sum(), 1e-9))
        covs.append(srr[k].sum() / max(cnt[k].sum(), 1))
    lo, hi = np.percentile(ratios, [2.5, 97.5])
    clo, chi = np.percentile(covs, [2.5, 97.5])
    return {"group": label, "pairs": n, "games": pr["game_id"].nunique(), "joint": joint, "product": prod,
            "ratio": joint / prod, "ratio_lo": lo, "ratio_hi": hi, "phi": phi, "resid_corr": rc,
            "resid_cov": (pr["r1"] * pr["r2"]).mean(), "resid_cov_lo": clo, "resid_cov_hi": chi,
            "mean_p1": pr["p1"].mean(), "mean_p2": pr["p2"].mean()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p-min", type=float, default=0.10)
    ap.add_argument("--leg-min", type=float, default=0.30)
    ap.add_argument("--boot", type=int, default=500)
    args = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    df = load(t0)
    pr = build_pairs(df, args.p_min, t0)
    legs = (pr["p1"] >= args.leg_min) & (pr["p2"] >= args.leg_min)
    same, opp = pr["same_team"], ~pr["same_team"]
    both_start = (pr["s1"] == 1) & (pr["s2"] == 1)
    mixed = ((pr["s1"] == 1) ^ (pr["s2"] == 1))
    both_big = pr["b1"] & pr["b2"]
    pace_t = pd.qcut(pr["pace"], 3, labels=["slow", "mid", "fast"]) if pr["pace"].notna().sum() > 100 else None
    groups = [
        ("all pairs", np.ones(len(pr), bool)),
        ("same team", same), ("opponents", opp),
        (f"same team, both legs p>={args.leg_min}", same & legs),
        (f"opponents, both legs p>={args.leg_min}", opp & legs),
        ("same team, both starters", same & both_start),
        ("same team, starter + bench", same & mixed),
        ("same team, both bench", same & (pr["s1"] == 0) & (pr["s2"] == 0)),
        ("same team, both centers", same & both_big),
        ("same team, center + non-center", same & (pr["b1"] ^ pr["b2"])),
        ("same team, neither a center", same & ~pr["b1"] & ~pr["b2"]),
        ("opponents, both centers", opp & both_big),
        ("opponents, both starters", opp & both_start),
    ]
    if pace_t is not None:
        for lab in ["slow", "mid", "fast"]:
            groups.append((f"same team, pace {lab}", same & (pace_t == lab).to_numpy()))
            groups.append((f"opponents, pace {lab}", opp & (pace_t == lab).to_numpy()))
    if pr["margin"].notna().any():
        for lab, lo, hi in [("final margin < 10", 0, 10), ("final margin 10 to 19", 10, 20), ("final margin 20+", 20, 999)]:
            m = (pr["margin"] >= lo) & (pr["margin"] < hi)
            groups.append((f"same team, {lab}", same & m))
            groups.append((f"opponents, {lab}", opp & m))
            groups.append((f"same team, both starters, {lab}", same & both_start & m))
    rows = [summarize(pr[g], lab, rng, args.boot) for lab, g in groups]
    rows = [r for r in rows if r]
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "pairs_summary.csv", index=False)
    # position pairs on the same team, top by count
    pp = pr[same].copy()
    pp["pospair"] = ["+".join(sorted([a, b])) for a, b in zip(pp["pos1"], pp["pos2"])]
    pos_rows = []
    for lab, g in pp.groupby("pospair"):
        if len(g) >= 2000:
            r = summarize(g, f"same team {lab}", rng, max(100, args.boot // 5))
            if r:
                pos_rows.append(r)
    pos = pd.DataFrame(pos_rows).sort_values("pairs", ascending=False) if pos_rows else pd.DataFrame()
    md = ["# Pair correlation of double-double outcomes (v1 test seasons, regular season)", "",
          f"Rows: scored test players with calibrated p at least {args.p_min}; pairs formed inside each game. "
          f"ratio = mean joint hit rate / mean product of the two probabilities (1.00 = independence); interval is a "
          f"{args.boot}-resample block bootstrap by game date. phi = correlation of the two outcomes; resid_corr = "
          f"correlation of (outcome - p). Seasons {sorted(df.season.unique())}.", "",
          "| group | pairs | games | joint | product | ratio | 95% interval | phi | resid corr | mean p1 | mean p2 |",
          "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['group']} | {r['pairs']:,} | {r['games']:,} | {r['joint']:.4f} | {r['product']:.4f} | "
                  f"{r['ratio']:.3f} | {r['ratio_lo']:.3f} to {r['ratio_hi']:.3f} | {r['phi']:+.4f} | "
                  f"{r['resid_corr']:+.4f} | {r['mean_p1']:.3f} | {r['mean_p2']:.3f} |")
    if len(pos):
        md += ["", "## Same-team position pairs (at least 2,000 pairs)", "",
               "| pair | pairs | joint | product | ratio | interval | resid corr |", "|---|---:|---:|---:|---:|---|---:|"]
        for r in pos.itertuples():
            md.append(f"| {r.group} | {r.pairs:,} | {r.joint:.4f} | {r.product:.4f} | {r.ratio:.3f} | "
                      f"{r.ratio_lo:.3f} to {r.ratio_hi:.3f} | {r.resid_corr:+.4f} |")
    (OUT / "report_pairs.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    log(f"wrote {OUT / 'report_pairs.md'}", t0)


if __name__ == "__main__":
    main()
