"""
pull_hoopr.py: download the sportsdataverse hoopR-nba-data bulk files (ESPN box scores).
Season key = season END year (2025 = 2024-25). Files land in data/raw/hoopr/.
Run: python tools/pull_hoopr.py            # default seasons
     python tools/pull_hoopr.py --force    # re-download everything
"""
import argparse, sys, time
from pathlib import Path
import requests, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "hoopr"
BASE = "https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/main/nba"
KINDS = {"player_box": "player_box/parquet/player_box_{y}.parquet",
         "team_box": "team_box/parquet/team_box_{y}.parquet",
         "schedule": "schedules/parquet/nba_schedule_{y}.parquet"}

def fetch(kind, year, force=False):
    dest = OUT / f"{kind}_{year}.parquet"
    if dest.exists() and not force:
        return dest, "cached"
    url = f"{BASE}/{KINDS[kind].format(y=year)}"
    r = requests.get(url, timeout=180)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    dest.write_bytes(r.content)
    return dest, f"{len(r.content)/1e6:.1f} MB"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=list(range(2018, 2028)))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for y in a.seasons:
        for kind in KINDS:
            t = time.time()
            p, status = fetch(kind, y, a.force)
            line = f"{kind}_{y}: {status} ({time.time()-t:.1f}s)"
            if p is not None and kind == "player_box":
                df = pd.read_parquet(p)
                line += f" rows={len(df)} dates {df['game_date'].min()} .. {df['game_date'].max()}"
            print(line, flush=True)
