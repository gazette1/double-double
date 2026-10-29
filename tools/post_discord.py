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

Run: PYTHONUTF8=1 python tools/post_discord.py [--date YYYY-MM-DD] [--kind picks|pretip|grade] [--post]
                                                [--full] [--ny-hour 15] [--label test]
"""
import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odds_snapshot import ENV_CANDIDATES  # noqa: E402
from paper_common import PAPER_DIR, append_run_log, now_et, today_et, yesterday_et  # noqa: E402

FILES = {"picks": "discord_{date}.md", "pretip": "discord_pretip_{date}.md", "grade": "discord_grade_{date}.md"}
COLORS = {"picks": 0x1ABC9C, "pretip": 0xF39C12, "grade": 0x3498DB}
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
    ap.add_argument("--kind", default="picks", choices=sorted(FILES))
    ap.add_argument("--post", action="store_true", help="send to the webhook (default is a dry run)")
    ap.add_argument("--full", action="store_true", help="post the whole summary instead of the headline")
    ap.add_argument("--ny-hour", type=int, default=None, help="do nothing unless the New York hour equals this")
    ap.add_argument("--label", default=None, help="tag added to the title, for example test")
    args = ap.parse_args()
    if args.ny_hour is not None and now_et().hour != args.ny_hour:
        print(f"New York hour is {now_et().hour}, not {args.ny_hour}; nothing to do")
        return
    date = args.date or (yesterday_et() if args.kind == "grade" else today_et())
    path = PAPER_DIR / FILES[args.kind].format(date=date)
    if not path.exists():
        sys.exit(f"no summary file {path}")
    text = path.read_text(encoding="utf-8")
    if args.full:
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
