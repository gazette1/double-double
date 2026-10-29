#!/usr/bin/env python
"""Pull coaching staffs per team and league year from stats.nba.com (CommonTeamRoster, Coaches frame) through nba_api.

Russ (2026-10-29): track coaches and lead assistants the way rosters are tracked, because staffs change teams and
carry their characteristics with them.

The Coaches frame for league year Y is a snapshot taken at the end of that league year, and it includes hires made in
May and June after the season (the 2021-22 Kings frame lists Mike Brown, hired May 2022). So the staff that opened
season Y is best read from the snapshot of Y-1, the snapshot of Y shows the staff after any in-season change, and the
dates of in-season changes come from data/raw/coaches/midseason_changes.csv (curated, with a verified flag).

One request per team per league year, about 1 second each. Resumable; block-aware waits like pull_tracking.py.
Output: data/raw/coaches/staff_{Y}_{TEAM_ID}.parquet per request, and data/raw/coaches/coaches_snapshots.parquet
consolidated (season = end-year key of the league year, TEAM_ID, TEAM_ABBR, COACH_ID, COACH_NAME, IS_ASSISTANT,
COACH_TYPE, SORT_SEQUENCE, SUB_SORT_SEQUENCE).
Usage: PYTHONUTF8=1 python tools/pull_coaches.py --seasons 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026 2027
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.static import teams as nba_teams

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "coaches"
LOG = OUT / "pull_log.txt"


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def season_str(y):
    return f"{y - 1}-{str(y)[-2:]}"


def fetch(y, team_id, timeout):
    frames = CommonTeamRoster(team_id=team_id, season=season_str(y), timeout=timeout).get_data_frames()
    df = frames[1].copy()
    df.insert(0, "season", y)
    return df


def fetch_with_retry(y, team_id, timeout, sleeps=(10, 30)):
    last = None
    for attempt in range(len(sleeps) + 1):
        try:
            return fetch(y, team_id, timeout), None
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
            if attempt < len(sleeps):
                time.sleep(sleeps[attempt])
    return None, last


def pending(seasons, team_ids):
    return [(y, t) for y in seasons for t in team_ids if not (OUT / f"staff_{y}_{t}.parquet").exists()]


def consolidate(abbr):
    files = sorted(OUT.glob("staff_*.parquet"))
    frames = [pd.read_parquet(f) for f in files]
    frames = [f for f in frames if len(f)]
    if not frames:
        return 0
    df = pd.concat(frames, ignore_index=True)
    df.insert(2, "TEAM_ABBR", df["TEAM_ID"].map(abbr))
    df.to_parquet(OUT / "coaches_snapshots.parquet", index=False)
    return len(df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=list(range(2017, 2028)))
    ap.add_argument("--sleep", type=float, default=1.2)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--block-wait", type=int, default=600)
    ap.add_argument("--pass-wait", type=int, default=1200)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    teams = nba_teams.get_teams()
    abbr = {t["id"]: t["abbreviation"] for t in teams}
    team_ids = sorted(abbr)
    t0 = time.time()
    remaining = pending(args.seasons, team_ids)
    for p in range(1, args.passes + 1):
        if not remaining:
            break
        log(f"pass {p}/{args.passes}: {len(remaining)} requests pending")
        consecutive, n_done = 0, 0
        for y, tid in remaining:
            df, err = fetch_with_retry(y, tid, args.timeout)
            n_done += 1
            if df is None:
                consecutive += 1
                log(f"FAILED {y} {abbr[tid]}: {err}")
                if consecutive >= 2:
                    log("  2 consecutive failed requests, ending this pass early")
                    break
                time.sleep(args.block_wait)
                continue
            consecutive = 0
            df.to_parquet(OUT / f"staff_{y}_{tid}.parquet", index=False)
            if n_done % 30 == 0 or n_done == len(remaining):
                log(f"  {n_done}/{len(remaining)} done, {(time.time() - t0) / 60:.1f} min elapsed")
            time.sleep(args.sleep)
        remaining = pending(args.seasons, team_ids)
        log(f"pass {p} done: {len(remaining)} still pending; consolidated {consolidate(abbr)} staff rows")
        if remaining and p < args.passes:
            log(f"waiting {args.pass_wait} s for the service block to clear")
            time.sleep(args.pass_wait)
    log(f"finished in {(time.time() - t0) / 60:.1f} min with {len(remaining)} requests still missing")
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
