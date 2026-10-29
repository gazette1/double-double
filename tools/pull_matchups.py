#!/usr/bin/env python
"""Pull season-level defender versus offensive-player matchup totals from stats.nba.com (LeagueSeasonMatchups).

One request per defensive team per season (30 per season). Each row is one defender-offender pair with
matchup minutes, partial possessions, points, assists, field goals and turnovers recorded while that defender
was the matched defender. These are full-season totals, so in a backtest they are only used as the prior
season's profile; the current season's file is point-in-time at the moment it is pulled.

Output: data/raw/matchups/<Y>_<TEAM_ID>.parquet per team and data/raw/matchups/matchups_<Y>.parquet per
season (Y = season end year, the hoopR key). Resumable: existing team files are skipped.

Usage: PYTHONUTF8=1 python tools/pull_matchups.py --seasons 2023 2024 2025 2026 2027
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import LeagueSeasonMatchups

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "matchups"
LOG = OUT / "pull_log.txt"
TEAM_IDS = list(range(1610612737, 1610612767))


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def season_str(y):
    return f"{y - 1}-{str(y)[-2:]}"


def fetch(y, team_id, timeout):
    ep = LeagueSeasonMatchups(season=season_str(y), season_type_playoffs="Regular Season",
                              per_mode_simple="Totals", def_team_id_nullable=team_id, timeout=timeout)
    df = ep.get_data_frames()[0]
    df.insert(0, "season", y)
    df.insert(1, "DEF_TEAM_ID", team_id)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025, 2026, 2027])
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    failures = []
    for y in args.seasons:
        for tid in TEAM_IDS:
            path = OUT / f"{y}_{tid}.parquet"
            if path.exists():
                continue
            err = None
            for attempt, pause in enumerate((0, 10, 30, 60)):
                if pause:
                    time.sleep(pause)
                try:
                    df = fetch(y, tid, args.timeout)
                    df.to_parquet(path, index=False)
                    err = None
                    break
                except Exception as e:
                    err = f"{type(e).__name__}: {str(e)[:120]}"
            if err:
                failures.append((y, tid, err))
                log(f"FAILED {y} {tid}: {err}")
            time.sleep(args.sleep)
        files = sorted(OUT.glob(f"{y}_*.parquet"))
        if files:
            df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            df.to_parquet(OUT / f"matchups_{y}.parquet", index=False)
            log(f"season {y}: {len(files)} team files, {len(df)} matchup rows, {(time.time() - t0) / 60:.1f} min")
    log(f"finished with {len(failures)} failures")
    for f in failures:
        log(f"  failed: {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
