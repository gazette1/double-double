"""
post_discord.py: post the headline of a paper-trade summary to the StrikeOut Bot's Discord channel.

Russ, 2026-10-29: "link to the strikeouts discord send the first couple lines everyday at 3pm." The format is
the strikeout bot's send_discord (tools/daily_picks.py): one embed, title plus description, posted with
requests.post. The headline is everything in the summary file above the first footer line (the lines that start
with an underscore): the date and slate line, then the picks with model probability, price and edge, or the
no-play line with the closest names. The full summary stays in the saved file.

Dry run by default: prints the title and body and sends nothing. --post reads DISCORD_WEBHOOK_URL from the
environment, this project's .env, or the StrikeOut Bot .env, and posts once; the value is never printed.
--ny-hour H exits quietly unless the America/New_York hour is H (the schedule guard; the GitHub Action runs at
19:00 and 20:00 UTC so that one of them is 3 PM Eastern on either side of the clock change).
--label adds a bracketed tag to the title, for the one manual test post.
--once does nothing when data/paper/run_log.csv already holds a sent, unlabeled post of this kind for the date
(the Action's daily step and tools/fallback_post.py both use it, so a late Action run after a post by hand
does not post twice).

Russ, 2026-10-29 evening, after the first edge-rule post: "All these numbers are confusing. I just want 5 dudes sent
to phone like strikeout." So the daily post is now --kind top: the five names tools/top_post.py ranks by model
probability, sent whole (it is short). --kind picks still posts the edge-rule headline when wanted.

Run: PYTHONUTF8=1 python tools/post_discord.py [--date YYYY-MM-DD] [--kind top|picks|pretip|grade] [--post]
                                                [--full] [--ny-hour 15] [--label test] [--once]
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odds_snapshot import ENV_CANDIDATES  # noqa: E402
from paper_common import PAPER_DIR, RUN_LOG_PATH, append_run_log, now_et, today_et, yesterday_et  # noqa: E402

FILES = {"top": "discord_top_{date}.md", "picks": "discord_{date}.md", "pretip": "discord_pretip_{date}.md",
         "grade": "discord_grade_{date}.md"}
COLORS = {"top": 0x1ABC9C, "picks": 0x95A5A6, "pretip": 0xF39C12, "grade": 0x3498DB}
FULL_KINDS = {"top"}  # short posts that go out whole, legend line included
TIMEOUT = 15


def webhook_url():
    if os.getenv("DISCORD_WEBHOOK_URL"):
        return os.environ["DISCORD_WEBHOOK_URL"]
    for p in ENV_CANDIDATES:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("DISCORD_WEBHOOK_URL="):
                    return line.split("=", 1)[1].strip()
    return None


def posted_in_run_log(date, kind):
    """True when the run log holds a sent, unlabeled post of this kind for the date (test posts do not count)."""
    if not RUN_LOG_PATH.exists():
        return False
    mode = f"post_{kind}"
    with open(RUN_LOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 5 and row[1] == date and row[2] == mode and row[3] == "True" and row[4] == "":
                return True
    return False


def headline(text):
    """Title and the lines above the first footer line (footers start with an underscore)."""
    lines = text.strip().splitlines()
    kept = []
    for ln in lines:
        if ln.startswith("_"):
            break
        kept.append(ln)
    while kept and not kept[-1].strip():
        kept.pop()
    title = kept[0] if kept else "DD picks"
    return title, "\n".join(kept[1:]).strip()


def send_discord(url, title, body, color):
    payload = {"embeds": [{"title": title[:256], "description": body[:4000], "color": color}]}
    r = requests.post(url, json=payload, timeout=TIMEOUT)
    ok = r.status_code in (200, 204)
    print(f"Discord: HTTP {r.status_code} ({'sent' if ok else 'failed'})")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="game date; default today for picks and pretip, yesterday for grade")
    ap.add_argument("--kind", default="top", choices=sorted(FILES))
    ap.add_argument("--post", action="store_true", help="send to the webhook (default is a dry run)")
    ap.add_argument("--full", action="store_true", help="post the whole summary instead of the headline")
    ap.add_argument("--ny-hour", type=int, default=None, help="do nothing unless the New York hour equals this")
    ap.add_argument("--label", default=None, help="tag added to the title, for example test")
    ap.add_argument("--once", action="store_true", help="do nothing if the run log already holds this post")
    args = ap.parse_args()
    if args.ny_hour is not None and now_et().hour != args.ny_hour:
        print(f"New York hour is {now_et().hour}, not {args.ny_hour}; nothing to do")
        return
    date = args.date or (yesterday_et() if args.kind == "grade" else today_et())
    if args.once and posted_in_run_log(date, args.kind):
        print(f"{args.kind} post for {date} already sent (run log); nothing to do")
        return
    path = PAPER_DIR / FILES[args.kind].format(date=date)
    if not path.exists():
        sys.exit(f"no summary file {path}")
    text = path.read_text(encoding="utf-8")
    if args.full or args.kind in FULL_KINDS:
        title, _, body = text.strip().partition("\n")
        body = body.strip()
    else:
        title, body = headline(text)
    if args.label:
        title = f"[{args.label}] {title}"
    print(title)
    print(body)
    if not args.post:
        print("\n[dry run] nothing sent; add --post to send")
        return
    url = webhook_url()
    if not url:
        sys.exit("DISCORD_WEBHOOK_URL not found")
    ok = send_discord(url, title, body, COLORS[args.kind])
    append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": f"post_{args.kind}",
                    "posted": ok, "label": args.label or "", "chars": len(body)})


if __name__ == "__main__":
    main()
