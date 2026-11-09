"""
ci_gate.py: decide which step a scheduled GitHub Action run performs. Standard library only, so it runs before
the dependencies are installed and a run outside every window ends in seconds.

Replaces ny_hour_guard.py. Russ, 2026-11-08: "this shouldnt rely on claude coder being open to run it should run
everyday like how the strikeout did". GitHub starts scheduled runs late: this repository's crons on the hour
(19:00 and 20:00 UTC) started 5 to 9 hours late and the StrikeOut repository's 13:00 UTC cron starts 3 to 9 hours
late, while crons off the hour mark started within minutes to an hour. The old guard asked whether the New York
hour was exactly 15, so every late run did nothing and the Action never posted. This gate asks whether the New
York clock is inside the step's window and whether the checkout already shows the step done today. Several crons
cover each window: the first run inside it does the step, later runs find it done and stop.

  daily   14:50 to 19:00 ET, no sent post_top row for today in data/paper/run_log.csv, today's daily run not done:
          grade yesterday, daily run, post.
  post    same window, no post yet, today's daily run done (a live row with games and a board file): post only,
          so a failed send retries without another price snapshot.
  pretip  18:30 to 19:30 ET, data/paper/picks_{date}.csv holds at least one pick and data/paper/
          discord_pretip_{date}.md is not written yet: closing snapshot of the picked games.
  none    anything else, including a day with no games (a live row with zero games and no post).
A STEP environment variable other than auto (the workflow_dispatch input) overrides the decision.
Writes step= and date= to GITHUB_OUTPUT when it is set, and prints the decision.

Run: python3 tools/ci_gate.py [--now "YYYY-MM-DD HH:MM"]   (--now simulates the New York clock for a local test)
"""
import argparse
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
PAPER = Path(__file__).resolve().parents[1] / "data" / "paper"
DAILY_WINDOW = ((14, 50), (19, 0))     # the 3 PM post, until the first usual tip
PRETIP_WINDOW = ((18, 30), (19, 30))   # closing snapshot of the picked games


def in_window(now, window):
    return window[0] <= (now.hour, now.minute) < window[1]


def read_rows(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def posted_today(rows, date):
    """A sent, unlabeled post_top row; a test post carries a label and does not count."""
    return any(len(r) >= 4 and r[1] == date and r[2] == "post_top" and r[3] == "True"
               and (len(r) < 5 or r[4] == "") for r in rows)


def games_in(row):
    try:
        return float(row[3])
    except (IndexError, ValueError):
        return 0.0


def decide(now, forced="", paper=PAPER):
    """Return (step, date, reason) for a run that starts at the New York time `now`."""
    date = now.strftime("%Y-%m-%d")
    clock = now.strftime("%H:%M")
    if forced and forced != "auto":
        return forced, date, f"forced by the STEP input: {forced}"
    rows = read_rows(paper / "run_log.csv")
    if in_window(now, DAILY_WINDOW) and not posted_today(rows, date):
        live = [r for r in rows if len(r) > 3 and r[1] == date and r[2] == "live"]
        if live and not any(games_in(r) > 0 for r in live):
            return "none", date, f"{clock} ET: no games to price today"
        if live and (paper / f"board_{date}.csv").exists():
            return "post", date, f"{clock} ET: today's daily run is done, the post is not sent yet"
        return "daily", date, f"{clock} ET: inside the daily window and nothing posted yet"
    if in_window(now, PRETIP_WINDOW):
        picks = paper / f"picks_{date}.csv"
        n = max(len(read_rows(picks)) - 1, 0)
        if n and not (paper / f"discord_pretip_{date}.md").exists():
            return "pretip", date, f"{clock} ET: {n} pick(s) without a closing snapshot"
        return "none", date, f"{clock} ET: inside the pre-tip window, {n} pick(s), " + ("snapshot done" if n else "none to snapshot")
    if in_window(now, DAILY_WINDOW):
        return "none", date, f"{clock} ET: today's post is already in the run log"
    return "none", date, f"{clock} ET: outside the daily and pre-tip windows"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", default=None, help='simulate the New York clock, "YYYY-MM-DD HH:MM"')
    args = ap.parse_args()
    now = datetime.strptime(args.now, "%Y-%m-%d %H:%M").replace(tzinfo=ET) if args.now else datetime.now(ET)
    step, date, why = decide(now, (os.getenv("STEP") or "").strip().lower())
    print(f"step={step} date={date} ({why})")
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"step={step}\ndate={date}\n")


if __name__ == "__main__":
    main()
