"""
pull_shot_quality.py: per-game shot attempts by closest-defender distance from stats.nba.com, through nba_api.

Russ, 2026-10-30: look at "open 3s taken (for assist)" among the advanced stats. The LeagueDashPlayerPtShot
endpoint, filtered to one game date and one closest-defender band, returns each player's attempts in that band
for that game: FGA, FG3A, FG3M and the share of his attempts the band holds. Two bands are pulled, "4-6 Feet -
Open" and "6+ Feet - Wide Open", so a player's own open looks and his teammates' open looks (the passer's
assist chances) can be built later by tools/build_shot_features.py. Regular season only, league years 2024 to
2027 (2023-24 onward, the same span as the tracking layer).

stats.nba.com throttles in 30 to 45 minute blocks, so the loop is the one from pull_tracking.py: one file per
request under data/raw/shots/, short retries (10 s, 30 s), a long wait after a failed request, a pass ends after
two consecutive failures, later passes pick up what is missing, and each pass consolidates into shots_{Y}.parquet.

Run: PYTHONUTF8=1 python tools/pull_shot_quality.py [--seasons 2024 2025 2026 2027] [--sleep 1.5] [--timeout 60]
                                                   [--passes 4] [--block-fails 2] [--block-wait 600] [--pass-wait 1200]
"""
import argparse
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import LeagueDashPlayerPtShot

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "shots"
BANDS = {"open": "4-6 Feet - Open", "wide": "6+ Feet - Wide Open"}
LOG = OUT / "pull_log.txt"


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def season_str(y):
    return f"{y - 1}-{str(y)[-2:]}"


def game_dates(y):
    pb = pd.read_parquet(RAW / "hoopr" / f"player_box_{y}.parquet", columns=["game_date", "season_type"])
    pb = pb[pb["season_type"] == 2]
    return sorted(pd.to_datetime(pb["game_date"]).dt.normalize().unique())


def fetch(band, y, d, timeout):
    ds = d.strftime("%m/%d/%Y")
    ep = LeagueDashPlayerPtShot(season=season_str(y), season_type_all_star="Regular Season", per_mode_simple="Totals",
                                close_def_dist_range_nullable=BANDS[band], date_from_nullable=ds,
                                date_to_nullable=ds, timeout=timeout)
    df = ep.get_data_frames()[0]
    df.insert(0, "band", band)
    df.insert(0, "game_date", d)
    df.insert(0, "season", y)
    return df


def fetch_with_retry(band, y, d, timeout, sleeps=(10, 30)):
    err = None
    for i, pause in enumerate(list(sleeps) + [None]):
        try:
            return fetch(band, y, d, timeout), None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:80]}"
            if pause is None:
                break
            time.sleep(pause)
    return None, err


def path_for(band, y, d):
    return OUT / f"{band}_{y}_{d:%Y%m%d}.parquet"


def pending(seasons):
    todo = []
    for y in seasons:
        for d in game_dates(y):
            for band in BANDS:
                if not path_for(band, y, d).exists():
                    todo.append((y, band, d))
    return todo


def consolidate(y):
    files = sorted(OUT.glob(f"*_{y}_*.parquet"))
    if not files:
        return 0
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df.to_parquet(OUT / f"shots_{y}.parquet", index=False)
    return len(df)


def run_pass(todo, args, t0):
    failed, consecutive, done = [], 0, 0
    for y, band, d in todo:
        df, err = fetch_with_retry(band, y, d, args.timeout)
        if df is None:
            failed.append((y, band, d, err))
            consecutive += 1
            log(f"FAILED {band} {y} {d:%Y-%m-%d}: {err}")
            if consecutive >= args.block_fails:
                log(f"  {consecutive} consecutive failed requests, ending this pass early")
                return failed, False
            log(f"  waiting {args.block_wait} s before the next request")
            time.sleep(args.block_wait)
            continue
        consecutive = 0
        df.to_parquet(path_for(band, y, d), index=False)
        done += 1
        if done % 50 == 0:
            log(f"  {done} requests done this pass, {time.time() - t0:.0f} s elapsed")
        time.sleep(args.sleep)
    return failed, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026, 2027])
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--passes", type=int, default=4)
    ap.add_argument("--block-fails", type=int, default=2)
    ap.add_argument("--block-wait", type=int, default=600)
    ap.add_argument("--pass-wait", type=int, default=1200)
    ap.add_argument("--consolidate-only", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if not args.consolidate_only:
        for p in range(1, args.passes + 1):
            todo = pending(args.seasons)
            if not todo:
                break
            log(f"pass {p}: {len(todo)} requests pending")
            failed, complete = run_pass(todo, args, t0)
            for y in sorted({y for y, _, _ in todo}):
                log(f"consolidated {y}: {consolidate(y):,} rows")
            if not pending(args.seasons):
                break
            if p < args.passes:
                log(f"  {len(pending(args.seasons))} still missing; waiting {args.pass_wait} s before pass {p + 1}")
                time.sleep(args.pass_wait)
    for y in args.seasons:
        log(f"final {y}: {consolidate(y):,} rows")
    left = pending(args.seasons)
    log(f"done in {time.time() - t0:.0f} s; {len(left)} requests still missing")
    raise SystemExit(1 if left else 0)


if __name__ == "__main__":
    main()
