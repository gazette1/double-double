#!/usr/bin/env python
"""Pull per-game NBA tracking and hustle box scores from stats.nba.com through nba_api.

One request per game date per measure with DateFrom = DateTo = that date and PerMode = Totals, so every
returned row is one player-game (GP = 1). Measures: reb (LeagueDashPtStats Rebounding: rebound chances,
contested rebounds), pass (LeagueDashPtStats Passing: passes, potential assists), hustle
(LeagueHustleStatsPlayer: box outs, deflections, screen assists). Regular season only.

Resumable: a date already saved under data/raw/tracking/<measure>/ is skipped. After each season the
per-date files are consolidated into data/raw/tracking/<measure>_<Y>.parquet (Y = season end year, the
hoopR key). Game dates come from the hoopR player box scores already on disk, so the pull covers exactly
the dates the feature dataset knows about.

Usage: PYTHONUTF8=1 python tools/pull_tracking.py --seasons 2024 2025 2026 2027 --measures reb pass hustle

stats.nba.com throttles by hanging requests until they time out, in stretches of 30 to 45 minutes. The puller
waits --block-wait seconds after a failed request, ends a pass after --block-fails consecutive failures, waits
--pass-wait seconds, and re-runs the missing dates for up to --passes passes. Existing date files are skipped.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import LeagueDashPtStats, LeagueHustleStatsPlayer

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "tracking"
LOG = OUT / "pull_log.txt"
NBA_TEAMS = {"ATL", "BKN", "BOS", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GS", "HOU", "IND", "LAC", "LAL",
             "MEM", "MIA", "MIL", "MIN", "NO", "NY", "OKC", "ORL", "PHI", "PHX", "POR", "SA", "SAC", "TOR",
             "UTAH", "WSH"}
MEASURE_NAMES = {"reb": "Rebounding", "pass": "Passing"}


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def season_str(y):
    return f"{y - 1}-{str(y)[-2:]}"


def game_dates(y):
    """Regular-season game dates for hoopR season key y, excluding All-Star weekend dates."""
    pb = pd.read_parquet(RAW / "hoopr" / f"player_box_{y}.parquet",
                         columns=["game_date", "season_type", "team_abbreviation"])
    pb = pb[pb["season_type"] == 2]
    pb["d"] = pd.to_datetime(pb["game_date"]).dt.normalize()
    real = pb.groupby("d")["team_abbreviation"].apply(lambda s: s.isin(NBA_TEAMS).any())
    return sorted(d.date() for d, ok in real.items() if ok)


def fetch(measure, y, d, timeout):
    s = season_str(y)
    ds = d.strftime("%m/%d/%Y")
    if measure == "hustle":
        ep = LeagueHustleStatsPlayer(per_mode_time="Totals", season=s, season_type_all_star="Regular Season",
                                     date_from_nullable=ds, date_to_nullable=ds, timeout=timeout)
    else:
        ep = LeagueDashPtStats(pt_measure_type=MEASURE_NAMES[measure], per_mode_simple="Totals",
                               player_or_team="Player", season=s, season_type_all_star="Regular Season",
                               date_from_nullable=ds, date_to_nullable=ds, timeout=timeout)
    df = ep.get_data_frames()[0]
    df.insert(0, "game_date", pd.Timestamp(d))
    df.insert(1, "season", y)
    return df


def fetch_with_retry(measure, y, d, timeout, sleeps=(10, 30)):
    """Up to len(sleeps) + 1 attempts with short pauses. The long waits for a service block live in run_pass."""
    last = None
    for attempt in range(len(sleeps) + 1):
        try:
            df = fetch(measure, y, d, timeout)
            if len(df) == 0 and attempt == 0:
                time.sleep(5)
                continue  # one re-check for an empty day before accepting it
            return df, None
        except Exception as e:  # timeouts, connection errors, JSON decode errors
            last = f"{type(e).__name__}: {str(e)[:120]}"
            if attempt < len(sleeps):
                time.sleep(sleeps[attempt])
    return None, last


def consolidate(measure, y):
    files = sorted((OUT / measure).glob(f"{y}_*.parquet"))
    if not files:
        return 0
    frames = [pd.read_parquet(f) for f in files]
    frames = [f for f in frames if len(f)]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    df.to_parquet(OUT / f"{measure}_{y}.parquet", index=False)
    return len(df)


def pending(seasons, measures):
    """(season, date, measure) triples whose file does not exist yet."""
    todo = []
    for y in seasons:
        for d in game_dates(y):
            for m in measures:
                if not (OUT / m / f"{y}_{d:%Y-%m-%d}.parquet").exists():
                    todo.append((y, d, m))
    return todo


def run_pass(todo, args, t0):
    """One pass over the pending requests.

    stats.nba.com answers with long hangs (read timeouts) for stretches of 30 to 45 minutes once it decides to
    throttle a client, and keeps hanging while requests keep coming. So after a failed request this waits
    args.block_wait seconds, and after args.block_fails consecutive failures it ends the pass so main can
    wait longer before the next pass.
    """
    failed, consecutive, n_done = [], 0, 0
    for y, d, m in todo:
        df, err = fetch_with_retry(m, y, d, args.timeout)
        n_done += 1
        if df is None:
            failed.append((y, m, d, err))
            consecutive += 1
            log(f"FAILED {m} {y} {d:%Y-%m-%d}: {err}")
            if consecutive >= args.block_fails:
                log(f"  {consecutive} consecutive failed requests, ending this pass early")
                return failed, False
            log(f"  waiting {args.block_wait} s before the next request")
            time.sleep(args.block_wait)
            continue
        consecutive = 0
        df.to_parquet(OUT / m / f"{y}_{d:%Y-%m-%d}.parquet", index=False)
        if len(df) == 0:
            log(f"empty {m} {y} {d:%Y-%m-%d}")
        if n_done % 30 == 0 or n_done == len(todo):
            log(f"  {n_done}/{len(todo)} done, {(time.time() - t0) / 60:.1f} min elapsed")
        time.sleep(args.sleep)
    return failed, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025, 2026, 2027])
    ap.add_argument("--measures", nargs="+", default=["reb", "pass", "hustle"])
    ap.add_argument("--sleep", type=float, default=1.5, help="seconds between requests")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--passes", type=int, default=4, help="passes over the missing dates")
    ap.add_argument("--block-fails", type=int, default=2, help="consecutive failed requests that end a pass")
    ap.add_argument("--block-wait", type=int, default=600, help="seconds to wait after a failed request")
    ap.add_argument("--pass-wait", type=int, default=1200, help="seconds to wait between passes")
    ap.add_argument("--initial-wait", type=int, default=0, help="seconds to wait before the first request")
    ap.add_argument("--consolidate-only", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for m in args.measures:
        (OUT / m).mkdir(exist_ok=True)

    if args.consolidate_only:
        for y in args.seasons:
            for m in args.measures:
                log(f"consolidated {m} {y}: {consolidate(m, y)} rows")
        return 0

    if args.initial_wait:
        log(f"initial wait of {args.initial_wait} s before the first request")
        time.sleep(args.initial_wait)
    t0 = time.time()
    touched = set()
    remaining = pending(args.seasons, args.measures)
    for p in range(1, args.passes + 1):
        if not remaining:
            log("nothing pending")
            break
        touched.update(y for y, _, _ in remaining)
        log(f"pass {p}/{args.passes}: {len(remaining)} requests pending")
        failed, completed = run_pass(remaining, args, t0)
        for y in sorted(touched):
            for m in args.measures:
                log(f"consolidated {m} {y}: {consolidate(m, y)} rows")
        remaining = pending(args.seasons, args.measures)
        log(f"pass {p} done: {len(failed)} failed requests, {len(remaining)} still pending, "
            f"{(time.time() - t0) / 60:.1f} min elapsed")
        if remaining and p < args.passes:
            log(f"waiting {args.pass_wait} s for the service block to clear")
            time.sleep(args.pass_wait)
    log(f"finished in {(time.time() - t0) / 60:.1f} min with {len(remaining)} requests still missing")
    for y, d, m in remaining[:60]:
        log(f"  missing: {m} {y} {d:%Y-%m-%d}")
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
