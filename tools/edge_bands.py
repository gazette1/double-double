"""edge_bands.py: assumption-based edge view by price band, using the v2 predictions.
Proxy implied probability q = min(0.97, 1.08 * Baseline A calibrated p) stands in for a Yes-only price
with about 8 percent margin (an assumption, not a price backtest). Reports, by band of q, how the
model's disagreement with q translated into realized rates, and compares nightly top-3 by edge with
nightly top-3 by probability inside the posted range. Run: python tools/edge_bands.py"""
import pandas as pd, numpy as np
pd.set_option("display.width", 220)
p = pd.read_parquet("data/eval/v2/predictions_v2.parquet")
p = p[p.season_type == 2].copy()
p["q"] = np.minimum(0.97, 1.08 * p.p_A_cal)
def ret(hit, q): return hit * (1 - q) / q - (1 - hit)
models = {"C_stack": "p_C_stack_cal", "BLEND_SIM": "p_BLEND_SIM_cal", "C_full": "p_C_full_cal"}
bands = [(0.02, 0.10), (0.10, 0.25), (0.25, 0.45), (0.45, 0.65), (0.65, 0.80), (0.80, 0.971)]
rows = []
for name, col in models.items():
    p["edge"] = p[col] - p.q
    for lo, hi in bands:
        b = p[(p.q >= lo) & (p.q < hi)]
        for thr in (0.03, 0.05, 0.08):
            s = b[b.edge >= thr]
            if len(s) >= 30:
                rows.append({"model": name, "q_band": f"[{lo:.2f},{hi:.2f})", "rule": f"p-q>={thr}", "n": len(s), "mean_q": s.q.mean(), "mean_p": s[col].mean(), "realized": s.dd.mean(), "ret_per_unit": ret(s.dd.mean(), s.q.mean()), "ret_mean_rowwise": ret(s.dd, s.q).mean()})
        s = b[b.edge <= -0.05]
        if len(s) >= 30:
            rows.append({"model": name, "q_band": f"[{lo:.2f},{hi:.2f})", "rule": "p-q<=-0.05 (pass)", "n": len(s), "mean_q": s.q.mean(), "mean_p": s[col].mean(), "realized": s.dd.mean(), "ret_per_unit": ret(s.dd.mean(), s.q.mean()), "ret_mean_rowwise": ret(s.dd, s.q).mean()})
out = pd.DataFrame(rows)
print("Edge by proxy price band (assumption: q = 1.08 x Baseline A, capped 0.97). ret = flat 1u at fair price q.")
print(out.round(3).to_string(index=False))
out.to_csv("data/eval/v2/edge_bands.csv", index=False)
# nightly top-3 by edge vs by probability, within posted range q >= 0.20 (about +400 or shorter)
res = []
for name, col in models.items():
    d = p[p.q >= 0.20].copy(); d["edge"] = d[col] - d.q
    by_edge = d.sort_values("edge", ascending=False).groupby("game_date").head(3)
    by_prob = d.sort_values(col, ascending=False).groupby("game_date").head(3)
    for lab, s in (("top3 by edge", by_edge), ("top3 by prob", by_prob)):
        res.append({"model": name, "selection": lab, "picks": len(s), "nights": s.game_date.nunique(), "hit": s.dd.mean(), "mean_q": s.q.mean(), "mean_p": s[col].mean(), "mean_edge": s.edge.mean(), "ret_mean_rowwise": ret(s.dd, s.q).mean()})
    be = by_edge.copy(); be["season"] = pd.to_datetime(be.game_date).dt.year + (pd.to_datetime(be.game_date).dt.month >= 8)
    print(f"\n{name}: top-3 by edge, per season (q>=0.20): " + "; ".join(f"{int(k)}: n={len(g)} hit={g.dd.mean():.3f} ret={ret(g.dd, g.q).mean():+.3f}" for k, g in be.groupby('season')))
r = pd.DataFrame(res); print("\nNightly top-3 within posted range (q >= 0.20), pooled 4 seasons:"); print(r.round(3).to_string(index=False))
r.to_csv("data/eval/v2/edge_topn.csv", index=False)
