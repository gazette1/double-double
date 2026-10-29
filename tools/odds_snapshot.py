"""
odds_snapshot.py: snapshot NBA double-double prices from The Odds API and log them.
Cost: 1 credit per game per call (one market). Reads ODDS_API_KEY from this project's .env,
falling back to the StrikeOut Bot .env. Writes data/odds/snapshots/{date}_{HHMM}.json and
appends flat rows to data/odds/dd_prices.csv.
Run: python tools/odds_snapshot.py [--books fanduel,draftkings] [--dry]
"""
import argparse, csv, json, os, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [ROOT / ".env", Path(r"C:\Users\harri\Documents\StrikeOut Bot\mlb-k-predictor\.env")]
BASE = "https://api.the-odds-api.com/v4/sports/basketball_nba"
ET = timezone(timedelta(hours=-4))

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="fanduel,draftkings")
    ap.add_argument("--market", default="player_double_double")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    key = load_key()
    now = datetime.now(ET)
    today = now.date().isoformat()
    ev = requests.get(f"{BASE}/events", params={"apiKey": key}, timeout=30)
    ev.raise_for_status()
    events = [e for e in ev.json()
              if datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")).astimezone(ET).date().isoformat() == today]
    print(f"{len(events)} NBA games on {today} (ET)")
    if a.dry:
        for e in events: print(" ", e["away_team"], "@", e["home_team"], e["commence_time"])
        return
    snap, rows, remaining = [], [], None
    for e in events:
        r = requests.get(f"{BASE}/events/{e['id']}/odds",
                         params={"apiKey": key, "bookmakers": a.books, "markets": a.market, "oddsFormat": "american"},
                         timeout=30)
        remaining = r.headers.get("x-requests-remaining", remaining)
        if r.status_code != 200:
            print("  ", e["away_team"], "@", e["home_team"], "HTTP", r.status_code, r.text[:120]); continue
        j = r.json(); snap.append(j)
        for bk in j.get("bookmakers", []):
            for m in bk.get("markets", []):
                for o in m.get("outcomes", []):
                    rows.append({"snapshot_et": now.strftime("%Y-%m-%d %H:%M"), "game_date": today,
                                 "event_id": e["id"], "away": e["away_team"], "home": e["home_team"],
                                 "commence_time": e["commence_time"], "book": bk["key"], "market": m["key"],
                                 "market_last_update": m.get("last_update"), "player": o.get("description"),
                                 "side": o.get("name"), "price": o.get("price"), "implied": round(implied(o["price"]), 4)})
    out_dir = ROOT / "data" / "odds" / "snapshots"; out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{today}_{now.strftime('%H%M')}.json").write_text(json.dumps(snap), encoding="utf-8")
    log = ROOT / "data" / "odds" / "dd_prices.csv"
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["snapshot_et"])
        if new: w.writeheader()
        for r_ in rows: w.writerow(r_)
    print(f"{len(rows)} price rows logged; credits remaining: {remaining}")
    # summary by book
    import collections
    by_book = collections.defaultdict(list)
    for r_ in rows: by_book[(r_["book"], r_["side"])].append(r_)
    for (bk, side), rs in sorted(by_book.items()):
        print(f"\n{bk} {side}: {len(rs)} players")
        for r_ in sorted(rs, key=lambda x: -x["implied"])[:60]:
            print(f"  {r_['player']:<26} {r_['price']:>6}  implied {r_['implied']:.3f}  ({r_['away']} @ {r_['home']})")

if __name__ == "__main__":
    main()
