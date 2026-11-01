"""
fallback_post.py: the 3 PM chain by hand when the GitHub Action has not posted.

Russ, 2026-11-01, to the question whether the paper-trade session should run the 3 PM post as a fallback: "Yes.
Schedule a one-shot fallback in this session for 3:10 PM Eastern today that runs grade, daily run, top post and
the Discord post only if the run log has no post for today yet." The Action (.github/workflows/daily_dd_discord.yml)
owns the post since 2026-11-01; this script defers to it and acts only when it has not posted.

From the project root:
  1. git pull --ff-only, so the local run log carries whatever the Action committed back.
  2. Every POLL_MINUTES until the cap, one decision from the run log and the public GitHub API:
       posted   a sent, unlabeled post_top row for the date in data/paper/run_log.csv, or an Action run that day
                whose "Post the five most likely double-doubles to Discord" step concluded success
       active   an Action run that day queued or in progress
       failed   an Action run created at or after the post slot that completed without a successful post step
     posted: stop. active: wait (until the cap, then stop without posting). failed, or nothing by the deadline:
     run the chain by hand.
  3. The chain by hand: grade.py (yesterday), daily_run.py, top_post.py, post_discord.py --kind top --post --once,
     then commit data/paper, data/odds and data/models/production and push, as the Action does, so the pre-tip
     step and tomorrow's grade find the files. The Action's own post step carries --once, so a run that starts
     after this push skips its post.
The API is read without a token (60 requests an hour, enough at the polling rate); GH_TOKEN is used when set.
Everything printed also goes to data/paper/logs/fallback_{date}.txt.

Run: PYTHONUTF8=1 python tools/fallback_post.py [--date YYYY-MM-DD] [--check] [--now] [--no-pull]
                                                 [--deadline 15:40] [--cap 16:30]
  --check   print the decision and exit (nothing run, nothing posted)
  --now     one pass: posted or active stops, anything else runs the chain
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_common import ET, append_run_log, now_et, tee_stdout, today_et  # noqa: E402
from post_discord import posted_in_run_log  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPO = "gazette1/double-double"
WORKFLOW = "daily_dd_discord.yml"
POST_STEP = "Post the five most likely double-doubles to Discord"
API = "https://api.github.com"
POLL_MINUTES = 4
SLOT_HOUR = 15          # the post slot, New York hour
DEADLINE = "15:40"      # no Action run at all by then: run the chain by hand
CAP = "16:30"           # stop waiting on a run still in progress
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}
CHAIN = [("grade", ["tools/grade.py"]),
         ("daily_run", ["tools/daily_run.py"]),
         ("top_post", ["tools/top_post.py"]),
         ("post", ["tools/post_discord.py", "--kind", "top", "--post", "--once"])]


def sh(args, timeout=1800):
    """Run a command in the project root, print its output, return the CompletedProcess."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    if out.strip():
        print(out.rstrip())
    return r


def api(path, params=None):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"{API}{path}", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def action_runs(date):
    """Runs of the workflow created on this New York date, newest first, with the post step's conclusion."""
    data = api(f"/repos/{REPO}/actions/workflows/{WORKFLOW}/runs", {"per_page": 20})
    runs = []
    for w in data.get("workflow_runs", []):
        created = datetime.fromisoformat(w["created_at"].replace("Z", "+00:00")).astimezone(ET)
        if created.strftime("%Y-%m-%d") != date:
            continue
        post_step = None
        if w["status"] == "completed":
            for job in api(f"/repos/{REPO}/actions/runs/{w['id']}/jobs").get("jobs", []):
                for step in job.get("steps", []):
                    if step.get("name") == POST_STEP:
                        post_step = step.get("conclusion")
        runs.append({"id": w["id"], "event": w["event"], "status": w["status"], "conclusion": w["conclusion"],
                     "created_et": created, "post_step": post_step})
    return runs


def describe(r):
    return (f"run {r['id']} ({r['event']}, created {r['created_et']:%H:%M} ET): {r['status']}"
            f"{', ' + r['conclusion'] if r['conclusion'] else ''}, post step {r['post_step'] or 'not finished'}")


def decide(date, runs, now, deadline):
    if posted_in_run_log(date, "top"):
        return "posted", "the run log holds today's post"
    hit = [r for r in runs if r["post_step"] == "success"]
    if hit:
        return "posted", "the Action posted: " + describe(hit[0])
    active = [r for r in runs if r["status"] in ACTIVE]
    if active:
        return "active", describe(active[0])
    slot = now.replace(hour=SLOT_HOUR, minute=0, second=0, microsecond=0) - timedelta(minutes=10)
    failed = [r for r in runs if r["status"] == "completed" and r["created_et"] >= slot and r["post_step"] != "success"]
    if failed:
        return "failed", describe(failed[0])
    if now >= deadline:
        return "missing", f"no Action run for the slot by {now:%H:%M} ET"
    return "wait", f"no run for the slot yet; {len(runs)} run(s) today, none active"


def run_chain(date):
    for name, argv in CHAIN:
        print(f"=== {name}")
        r = sh([sys.executable, *argv])
        print(f"{name} exit={r.returncode}")
        if r.returncode != 0:
            print("stopping the chain; nothing committed")
            return False
    return True


def commit_and_push(date, when):
    sh(["git", "add", "data/paper", "data/odds", "data/models/production"])
    if sh(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("nothing to commit")
        return
    msg = (f"paper trade {date} fallback by hand from the paper-trade session\n\n"
           f"The Action had not posted by {when} ET; grade, daily run, five-name post and the Discord send ran here.\n\n"
           "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
    sh(["git", "commit", "-m", msg])
    sh(["git", "pull", "--rebase"])
    r = sh(["git", "push"])
    print("push exit", r.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--deadline", default=DEADLINE)
    ap.add_argument("--cap", default=CAP)
    args = ap.parse_args()
    date = args.date or today_et()
    tee_stdout("fallback", date)
    day = datetime.strptime(date, "%Y-%m-%d")
    deadline = datetime.combine(day, datetime.strptime(args.deadline, "%H:%M").time(), tzinfo=ET)
    cap = datetime.combine(day, datetime.strptime(args.cap, "%H:%M").time(), tzinfo=ET)
    print(f"fallback for {date}: deadline {deadline:%H:%M}, cap {cap:%H:%M}, poll every {POLL_MINUTES} min")
    if not args.no_pull and not args.check:
        print("=== git pull --ff-only")
        sh(["git", "pull", "--ff-only"])
    while True:
        now = now_et()
        try:
            runs = action_runs(date)
        except Exception as e:  # noqa: BLE001
            print(f"[{now:%H:%M}] GitHub API unavailable ({e}); deciding from the run log alone")
            runs = []
        decision, why = decide(date, runs, now, deadline)
        print(f"[{now:%H:%M}] {decision}: {why}")
        if args.check:
            return
        if decision == "posted":
            append_run_log({"run_et": now.strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "fallback", "decision": decision})
            return
        if decision == "active":
            if now >= cap:
                print("a run is still in progress at the cap; not posting, to avoid a duplicate")
                return
            if args.now:
                return
        elif decision in ("failed", "missing") or args.now:
            print(f"running the chain by hand ({decision})")
            ok = run_chain(date)
            append_run_log({"run_et": now.strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "fallback",
                            "decision": f"chain_{'ok' if ok else 'failed'}"})
            if ok:
                commit_and_push(date, now.strftime("%H:%M"))
            return
        time.sleep(POLL_MINUTES * 60)


if __name__ == "__main__":
    main()
