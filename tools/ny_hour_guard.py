"""
ny_hour_guard.py: decide which pipeline step a scheduled run should perform from the America/New_York hour.

The GitHub Action (.github/workflows/daily_dd_discord.yml) fires at 19:00 and 20:00 UTC (one of them is 3 PM
Eastern on either side of the clock change) and at 22:40 and 23:40 UTC (one of them is 6:40 PM Eastern, before
the earliest usual tip). This script maps the hour to a step: 15 -> daily (grade yesterday, run today, post),
18 -> pretip (closing snapshot of the picked games), anything else -> none. A STEP environment variable
(workflow_dispatch input) overrides the clock. Writes step=<value> to GITHUB_OUTPUT when that file exists and
prints it.

Run: python tools/ny_hour_guard.py [--hour H]   (--hour overrides the clock for a local test)
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_common import now_et  # noqa: E402

STEP_BY_HOUR = {15: "daily", 18: "pretip"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hour", type=int, default=None)
    args = ap.parse_args()
    forced = (os.getenv("STEP") or "").strip().lower()
    hour = args.hour if args.hour is not None else now_et().hour
    step = forced if forced and forced != "auto" else STEP_BY_HOUR.get(hour, "none")
    print(f"New York hour {hour}; step={step}")
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"step={step}\n")


if __name__ == "__main__":
    main()
