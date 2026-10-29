"""
odds_snapshot.py: snapshot NBA double-double prices from The Odds API and log them.

Cost: 1 credit per game per call for one market; up to ten named bookmakers bill as one region, so the
two-way books ride along with FanDuel and DraftKings at no extra cost. Reads ODDS_API_KEY from this
project's .env, falling back to the StrikeOut Bot .env. Writes data/odds/snapshots/{date}_{HHMM}_{kind}.json,
appends flat rows to data/odds/dd_prices.csv (column snapshot_kind: open or pretip) and one line per run to
data/odds/credits_log.csv (credits used this run, from the x-requests-last header, and credits remaining).

Importable: snapshot(books=..., date=..., event_ids=..., kind=...) is what tools/daily_run.py and
tools/pretip_snapshot.py call. The event listing call is free; only the per-event odds calls cost credits.

Run: python tools/odds_snapshot.py [--books fanduel,draftkings,...] [--kind open|pretip]
                                   [--events id1,id2] [--date YYYY-MM-DD] [--dry]
"""
import argparse
import collections
import csv
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [ROOT / ".env", Path(r"C:\Users\harri\Documents\StrikeOut Bot\mlb-k-predictor\.env")]
BASE = "https://api.the-odds-api.com/v4/sports/basketball_nba"
ET = ZoneInfo("America/New_York")
MARKET = "player_double_double"
# FanDuel and DraftKings (Yes-only boards), the books that have posted two-way double-double markets
# (theScore Bet espnbet, BetMGM, Hard Rock), the other DC-licensed books, and two exchange-style books.
# Ten keys bill as one region. The DC set that counts for the best available price is still Russ's call
# (master note, decision 4); tools/paper_common.py holds the working list.
DEFAULT_BOOKS = "fanduel,draftkings,betmgm,espnbet,hardrockbet,williamhill_us,fanatics,betrivers,ballybet,novig"
LOG_PATH = ROOT / "data" / "odds" / "dd_prices.csv"
CREDITS_PATH = ROOT / "data" / "odds" / "credits_log.csv"
SNAP_DIR = ROOT / "data" / "odds" / "snapshots"
COLUMNS = ["snapshot_et", "snapshot_kind", "game_date", "event_id", "away", "home", "commence_time", "book",
           "market", "market_last_update", "player", "side", "price", "implied"]


def load_key():
    if os.getenv("ODDS_API_KEY"):
        return os.environ["ODDS_API_KEY"]
    for p in ENV_CANDIDATES:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ODDS_API_KEY="):
                    return line.split("=", 1)[1].strip()
    sys.exit("ODDS_API_KEY not found")


def implied(american):
    a = float(american)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def et_date(commence_time):
    return datetime.fromisoformat(commence_time.replace("Z", "+00:00")).astimezone(ET).date().isoformat()


def list_events(key, date):
    """Events whose tip falls on `date` (ET). This call costs no credits."""
    r = requests.get(f"{BASE}/events", params={"apiKey": key}, timeout=30)
    r.raise_for_status()
    events = [e for e in r.json() if et_date(e["commence_time"]) == date]
    return events, r.headers.get("x-requests-remaining")


def migrate_log():
    """Add the snapshot_kind column to an older dd_prices.csv (rows before the column are open snapshots)."""
    if not LOG_PATH.exists():
        return
    with LOG_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "snapshot_kind" in (reader.fieldnames or []):
            return
        rows = list(reader)
    backup = LOG_PATH.with_name(f"dd_prices_backup_{datetime.now(ET).strftime('%Y%m%d_%H%M')}.csv")
    shutil.copy(LOG_PATH, backup)
    with LOG_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            r["snapshot_kind"] = "open"
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print(f"dd_prices.csv migrated to include snapshot_kind ({len(rows)} rows); backup {backup.name}")


def append_log(rows):
    migrate_log()
    new = not LOG_PATH.exists()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def log_credits(kind, date, n_events, n_requests, used_run, remaining, note=""):
    new = not CREDITS_PATH.exists()
    CREDITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CREDITS_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["logged_et", "kind", "game_date", "events", "requests", "credits_used_run",
                        "credits_remaining", "note"])
        w.writerow([datetime.now(ET).strftime("%Y-%m-%d %H:%M"), kind, date, n_events, n_requests, used_run,
                    remaining, note])


def snapshot(books=DEFAULT_BOOKS, market=MARKET, date=None, event_ids=None, kind="open", key=None, write=True,
             verbose=True):
    """Pull the double-double market for the games of `date` (ET, default today) and log the rows.

    event_ids restricts the pull (and the cost) to those Odds API events, used by the pre-tip snapshot.
    Returns a dict with rows (list of dicts in COLUMNS order), events, credits used in this run, credits
    remaining after the last call, the snapshot time and the json path.
    """
    key = key or load_key()
    now = datetime.now(ET)
    date = date or now.date().isoformat()
    events, remaining = list_events(key, date)
    if event_ids is not None:
        wanted = set(str(e) for e in event_ids)
        events = [e for e in events if e["id"] in wanted]
    if verbose:
        print(f"{len(events)} NBA games on {date} (ET) in this snapshot ({kind})")
    snap, rows, used_run, n_req = [], [], 0, 0
    stamp = now.strftime("%Y-%m-%d %H:%M")
    for e in events:
        r = requests.get(f"{BASE}/events/{e['id']}/odds",
                         params={"apiKey": key, "bookmakers": books, "markets": market, "oddsFormat": "american"},
                         timeout=30)
        n_req += 1
        remaining = r.headers.get("x-requests-remaining", remaining)
        try:
            used_run += int(float(r.headers.get("x-requests-last", 0) or 0))
        except ValueError:
            pass
        if r.status_code != 200:
            print("  ", e["away_team"], "@", e["home_team"], "HTTP", r.status_code, r.text[:160])
            continue
        j = r.json()
        snap.append(j)
        for bk in j.get("bookmakers", []):
            for m in bk.get("markets", []):
                for o in m.get("outcomes", []):
                    rows.append({"snapshot_et": stamp, "snapshot_kind": kind, "game_date": date,
                                 "event_id": e["id"], "away": e["away_team"], "home": e["home_team"],
                                 "commence_time": e["commence_time"], "book": bk["key"], "market": m["key"],
                                 "market_last_update": m.get("last_update"), "player": o.get("description"),
                                 "side": o.get("name"), "price": o.get("price"),
                                 "implied": round(implied(o["price"]), 4)})
    path = None
    if write:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        path = SNAP_DIR / f"{date}_{now.strftime('%H%M')}_{kind}.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        if rows:
            append_log(rows)
        log_credits(kind, date, len(events), n_req, used_run, remaining)
    if verbose:
        print(f"{len(rows)} price rows logged; credits used this run {used_run}; credits remaining {remaining}")
    return {"rows": rows, "events": events, "used_run": used_run, "remaining": remaining, "snapshot_et": stamp,
            "path": path, "requests": n_req}


def print_summary(rows, limit=60):
    by_book = collections.defaultdict(list)
    for r_ in rows:
        by_book[(r_["book"], r_["side"])].append(r_)
    for (bk, side), rs in sorted(by_book.items()):
        print(f"\n{bk} {side}: {len(rs)} players")
        for r_ in sorted(rs, key=lambda x: -x["implied"])[:limit]:
            print(f"  {r_['player']:<26} {r_['price']:>6}  implied {r_['implied']:.3f}  ({r_['away']} @ {r_['home']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default=DEFAULT_BOOKS)
    ap.add_argument("--market", default=MARKET)
    ap.add_argument("--kind", default="open", choices=["open", "pretip"])
    ap.add_argument("--events", default=None, help="comma-separated Odds API event ids to restrict the pull")
    ap.add_argument("--date", default=None, help="game date (ET), default today")
    ap.add_argument("--dry", action="store_true", help="list the games without spending credits")
    a = ap.parse_args()
    key = load_key()
    date = a.date or datetime.now(ET).date().isoformat()
    if a.dry:
        events, remaining = list_events(key, date)
        print(f"{len(events)} NBA games on {date} (ET); credits remaining {remaining}")
        for e in events:
            print(" ", e["id"], e["away_team"], "@", e["home_team"], e["commence_time"])
        return
    out = snapshot(books=a.books, market=a.market, date=date, kind=a.kind, key=key,
                   event_ids=a.events.split(",") if a.events else None)
    print_summary(out["rows"])


if __name__ == "__main__":
    main()
