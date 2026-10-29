"""
paper_common.py: shared pieces of the paper-trade pipeline (tools/daily_run.py, tools/pretip_snapshot.py,
tools/grade.py): paths, Eastern time, ESPN public JSON (scoreboard, injuries, rosters, box scores), price
de-vigging (multiplicative and power), the price board built from logged Odds API rows, player-name matching
between the Odds API and ESPN, and the plain-text summary helpers. No stats.nba.com calls anywhere.
"""
import difflib
import json
import re
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = ROOT / "data" / "paper"
PROD_DIR = ROOT / "data" / "models" / "production"
ODDS_DIR = ROOT / "data" / "odds"
LEDGER_PATH = PAPER_DIR / "ledger.csv"
RUN_LOG_PATH = PAPER_DIR / "run_log.csv"
ET = ZoneInfo("America/New_York")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
CURRENT_SEASON = 2027  # season end year of 2026-27; update each October

# ESPN team ids (the hoopR team_id) by the names The Odds API uses
TEAM_NAME_TO_ID = {
    "Atlanta Hawks": 1, "Boston Celtics": 2, "New Orleans Pelicans": 3, "Chicago Bulls": 4,
    "Cleveland Cavaliers": 5, "Dallas Mavericks": 6, "Denver Nuggets": 7, "Detroit Pistons": 8,
    "Golden State Warriors": 9, "Houston Rockets": 10, "Indiana Pacers": 11, "Los Angeles Clippers": 12,
    "LA Clippers": 12, "Los Angeles Lakers": 13, "Miami Heat": 14, "Milwaukee Bucks": 15,
    "Minnesota Timberwolves": 16, "Brooklyn Nets": 17, "New York Knicks": 18, "Orlando Magic": 19,
    "Philadelphia 76ers": 20, "Phoenix Suns": 21, "Portland Trail Blazers": 22, "Sacramento Kings": 23,
    "San Antonio Spurs": 24, "Oklahoma City Thunder": 25, "Utah Jazz": 26, "Washington Wizards": 27,
    "Toronto Raptors": 28, "Memphis Grizzlies": 29, "Charlotte Hornets": 30,
}
TEAM_ABBR = {1: "ATL", 2: "BOS", 3: "NO", 4: "CHI", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET", 9: "GS", 10: "HOU",
             11: "IND", 12: "LAC", 13: "LAL", 14: "MIA", 15: "MIL", 16: "MIN", 17: "BKN", 18: "NY", 19: "ORL",
             20: "PHI", 21: "PHX", 22: "POR", 23: "SAC", 24: "SA", 25: "OKC", 26: "UTAH", 27: "WSH", 28: "TOR",
             29: "MEM", 30: "CHA"}
# Books Russ can bet from DC, the working set for the best available price (decision 4 in the master note).
BEST_BOOKS = ["fanduel", "draftkings", "betmgm", "williamhill_us", "fanatics", "espnbet", "hardrockbet"]
BOOK_LABEL = {"fanduel": "FD", "draftkings": "DK", "betmgm": "MGM", "williamhill_us": "CZR", "fanatics": "FAN",
              "espnbet": "SCORE", "hardrockbet": "HR", "betrivers": "BR", "ballybet": "BALLY", "novig": "NOVIG"}
OUT_STATUSES = {"out", "doubtful", "suspended", "injured reserve", "ir"}


# --------------------------------------------------------------------------------------------
# Time and files
# --------------------------------------------------------------------------------------------
def now_et():
    return datetime.now(ET)


def today_et():
    return now_et().date().isoformat()


def yesterday_et():
    return (now_et().date() - timedelta(days=1)).isoformat()


def picks_path(date):
    return PAPER_DIR / f"picks_{date}.csv"


def board_path(date):
    return PAPER_DIR / f"board_{date}.csv"


def summary_path(date):
    return PAPER_DIR / f"discord_{date}.md"


def grade_summary_path(date):
    return PAPER_DIR / f"discord_grade_{date}.md"


def check_voice(text):
    """Russ's voice rules for anything written: no em-dash, no exclamation point."""
    bad = [ch for ch in ("—", "!") if ch in text]
    assert not bad, f"voice rule violation, characters {bad}"
    return text


def write_text(path, text):
    check_voice(text)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def append_run_log(row):
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row])
    header = not RUN_LOG_PATH.exists()
    df.to_csv(RUN_LOG_PATH, mode="a", header=header, index=False)


class _Tee:
    def __init__(self, path, stream):
        self.f = open(path, "a", encoding="utf-8")
        self.stream = stream

    def write(self, s):
        self.stream.write(s)
        self.f.write(s)

    def flush(self):
        self.stream.flush()
        self.f.flush()


def tee_stdout(name, date):
    """Copy everything printed from here on into data/paper/logs/{name}_{date}.txt (appending)."""
    import sys
    path = PAPER_DIR / "logs" / f"{name}_{date}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = _Tee(path, sys.stdout)
    print(f"----- {name} {date}, started {now_et().strftime('%Y-%m-%d %H:%M')} ET -----")
    return path


def logged_price_rows(date, kind="open", latest_only=True):
    """Rows of data/odds/dd_prices.csv for one game date and snapshot kind, as the snapshot() output shape,
    plus the event list rebuilt from them (team names, ids, tip times). Zero credits; used for re-runs."""
    path = ODDS_DIR / "dd_prices.csv"
    if not path.exists():
        return [], []
    df = pd.read_csv(path, dtype={"event_id": str})
    if "snapshot_kind" not in df:
        df["snapshot_kind"] = "open"
    df = df[(df["game_date"] == date) & (df["snapshot_kind"] == kind)]
    if df.empty:
        return [], []
    if latest_only:
        df = df[df["snapshot_et"] == df["snapshot_et"].max()]
    rows = df.to_dict(orient="records")
    ev = df.drop_duplicates("event_id")
    events = [{"id": r.event_id, "home_team": r.home, "away_team": r.away, "commence_time": r.commence_time}
              for r in ev.itertuples()]
    return rows, events


# --------------------------------------------------------------------------------------------
# ESPN public JSON
# --------------------------------------------------------------------------------------------
def espn_get(path, params=None, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(f"{ESPN}/{path}", params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"ESPN {path} failed: {last}")


def espn_scoreboard(date):
    """Games on an ET date (YYYY-MM-DD). The scoreboard needs the explicit dates parameter."""
    j = espn_get("scoreboard", {"dates": date.replace("-", "")})
    games = []
    for e in j.get("events", []):
        c = e["competitions"][0]
        home = next(x for x in c["competitors"] if x["homeAway"] == "home")
        away = next(x for x in c["competitors"] if x["homeAway"] == "away")
        odds = (c.get("odds") or [{}])[0]
        tip_utc = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        games.append({
            "game_id": int(e["id"]), "tip_utc": tip_utc, "tip_et": tip_utc.astimezone(ET),
            "status_state": e["status"]["type"]["state"], "status_name": e["status"]["type"]["name"],
            "completed": bool(e["status"]["type"].get("completed", False)),
            "home_id": int(home["team"]["id"]), "away_id": int(away["team"]["id"]),
            "home_abbr": home["team"]["abbreviation"], "away_abbr": away["team"]["abbreviation"],
            "home_name": home["team"].get("displayName"), "away_name": away["team"].get("displayName"),
            "home_score": float(home["score"]) if str(home.get("score", "")).strip() else np.nan,
            "away_score": float(away["score"]) if str(away.get("score", "")).strip() else np.nan,
            "spread_home": odds.get("spread", np.nan) if odds else np.nan,  # negative = home favored
            "spread_detail": odds.get("details") if odds else None,
            "over_under": odds.get("overUnder", np.nan) if odds else np.nan,
            "odds_provider": (odds.get("provider") or {}).get("name") if odds else None,
            "season_type": int((e.get("season") or {}).get("type", 2)),
            "neutral_site": bool(c.get("neutralSite", False)),
        })
    return games


def _athlete_id_from_links(athlete):
    if athlete.get("id"):
        return int(athlete["id"])
    for link in athlete.get("links", []) or []:
        m = re.search(r"/id/(\d+)", link.get("href", ""))
        if m:
            return int(m.group(1))
    return None


def espn_injuries():
    """League injury report: one row per listed player with status (Out, Day-To-Day, ...)."""
    j = espn_get("injuries")
    rows = []
    for t in j.get("injuries", []):
        for i in t.get("injuries", []):
            a = i.get("athlete", {}) or {}
            d = i.get("details") or {}
            rows.append({"team_id": int(t.get("id")) if str(t.get("id", "")).isdigit() else None,
                         "athlete_id": _athlete_id_from_links(a), "player": a.get("displayName"),
                         "status": i.get("status"), "injury_type": d.get("type"), "injury_detail": d.get("detail"),
                         "return_date": d.get("returnDate"), "comment": i.get("shortComment"),
                         "listed": i.get("date")})
    cols = ["team_id", "athlete_id", "player", "status", "injury_type", "injury_detail", "return_date", "comment",
            "listed"]
    return pd.DataFrame(rows, columns=cols)


def espn_roster(team_id):
    """Current roster with ESPN athlete ids (equal to the hoopR athlete_id) and per-player injury status."""
    j = espn_get(f"teams/{team_id}/roster")
    rows = []
    for a in j.get("athletes", []):
        inj = a.get("injuries") or []
        rows.append({"team_id": int(team_id), "athlete_id": int(a["id"]), "player": a.get("displayName"),
                     "position": (a.get("position") or {}).get("abbreviation"),
                     "roster_status": (a.get("status") or {}).get("name"),
                     "injury_status": inj[0].get("status") if inj else None})
    return pd.DataFrame(rows, columns=["team_id", "athlete_id", "player", "position", "roster_status",
                                       "injury_status"])


def espn_box_scores(game_id):
    """Player box score of one game from the summary endpoint; final flag from the header status."""
    j = espn_get("summary", {"event": game_id})
    status = ((j.get("header", {}).get("competitions") or [{}])[0].get("status", {}).get("type", {}))
    final = status.get("name") == "STATUS_FINAL" or bool(status.get("completed"))
    rows = []
    for block in j.get("boxscore", {}).get("players", []):
        team = block.get("team", {})
        for st in block.get("statistics", []):
            keys = st.get("keys", [])
            for a in st.get("athletes", []):
                vals = dict(zip(keys, a.get("stats", [])))

                def num(k):
                    v = vals.get(k)
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return np.nan
                dnp = bool(a.get("didNotPlay", False))
                rows.append({"game_id": int(game_id), "athlete_id": int(a["athlete"]["id"]),
                             "player": a["athlete"].get("displayName"), "team_abbr": team.get("abbreviation"),
                             "minutes": np.nan if dnp else num("minutes"), "points": num("points"),
                             "rebounds": num("rebounds"), "assists": num("assists"), "steals": num("steals"),
                             "blocks": num("blocks"), "starter": bool(a.get("starter", False)), "did_not_play": dnp,
                             "reason": a.get("reason")})
    df = pd.DataFrame(rows, columns=["game_id", "athlete_id", "player", "team_abbr", "minutes", "points", "rebounds",
                                     "assists", "steals", "blocks", "starter", "did_not_play", "reason"])
    return df, final


# --------------------------------------------------------------------------------------------
# Prices
# --------------------------------------------------------------------------------------------
def implied(american):
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else -a / (-a + 100.0)


def american(p):
    """Break-even American price for probability p."""
    p = float(p)
    if not (0 < p < 1):
        return np.nan
    return -100.0 * p / (1 - p) if p >= 0.5 else 100.0 * (1 - p) / p


def fmt_price(a):
    if a is None or (isinstance(a, float) and np.isnan(a)):
        return "n/a"
    a = int(round(float(a)))
    return f"+{a}" if a > 0 else f"{a}"


def profit_per_unit(american_price, won):
    """Flat one-unit stake: profit on a win at the American price, minus one on a loss."""
    if won is None or american_price is None or (isinstance(american_price, float) and np.isnan(american_price)):
        return np.nan
    a = float(american_price)
    return (a / 100.0 if a > 0 else 100.0 / -a) if won else -1.0


def power_exponent(qs, lo=0.05, hi=60.0, iters=200):
    """k with sum(q_i ** k) = 1 for implied probabilities q_i (k above 1 when the book holds a margin)."""
    qs = np.asarray(qs, dtype=np.float64)

    def f(k):
        return np.sum(qs ** k) - 1.0
    flo, fhi = f(lo), f(hi)
    if flo < 0:
        return lo
    if fhi > 0:
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def devig_pair(q_yes, q_no):
    """Fair Yes probability from a two-way quote under the multiplicative and the power method."""
    q_yes, q_no = float(q_yes), float(q_no)
    mult = q_yes / (q_yes + q_no)
    k = power_exponent([q_yes, q_no])
    power = q_yes ** k
    return mult, power, q_yes + q_no - 1.0


def price_board(rows, best_books=None):
    """One row per (event, player) from flat Odds API rows: FanDuel and DraftKings Yes prices, the best
    available Yes price among best_books, and the fair probability from every book that quotes both sides
    (mean across two-way books under each de-vig method, with the range and the book list)."""
    best_books = best_books or BEST_BOOKS
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()
    df["price"] = df["price"].astype(float)
    df["implied"] = df["price"].map(implied)
    out = []
    for (eid, player), g in df.groupby(["event_id", "player"], sort=False):
        yes = g[g["side"] == "Yes"].drop_duplicates("book").set_index("book")
        no = g[g["side"] == "No"].drop_duplicates("book").set_index("book")
        rec = {"event_id": eid, "player": player, "away": g["away"].iloc[0], "home": g["home"].iloc[0],
               "commence_time": g["commence_time"].iloc[0], "snapshot_et": g["snapshot_et"].max(),
               "n_books_yes": int(len(yes)), "books_yes": ",".join(sorted(yes.index))}
        for bk, lab in [("fanduel", "fd"), ("draftkings", "dk")]:
            rec[f"{lab}_price"] = float(yes.loc[bk, "price"]) if bk in yes.index else np.nan
            rec[f"{lab}_implied"] = float(yes.loc[bk, "implied"]) if bk in yes.index else np.nan
        cand = yes[yes.index.isin(best_books)]
        if len(cand):
            b = cand["implied"].idxmin()
            rec.update({"best_price": float(cand.loc[b, "price"]), "best_implied": float(cand.loc[b, "implied"]),
                        "best_book": b})
        else:
            rec.update({"best_price": np.nan, "best_implied": np.nan, "best_book": None})
        two = sorted(set(yes.index) & set(no.index))
        mults, powers, holds = [], [], []
        for bk in two:
            m, pw, h = devig_pair(yes.loc[bk, "implied"], no.loc[bk, "implied"])
            mults.append(m)
            powers.append(pw)
            holds.append(h)
        rec.update({"n_twoway": len(two), "twoway_books": ",".join(two),
                    "fair_mult": float(np.mean(mults)) if two else np.nan,
                    "fair_power": float(np.mean(powers)) if two else np.nan,
                    "fair_mult_min": float(np.min(mults)) if two else np.nan,
                    "fair_mult_max": float(np.max(mults)) if two else np.nan,
                    "twoway_hold_mean": float(np.mean(holds)) if two else np.nan,
                    "yes_quotes": json.dumps({bk: float(yes.loc[bk, "price"]) for bk in yes.index}),
                    "no_quotes": json.dumps({bk: float(no.loc[bk, "price"]) for bk in no.index})})
        out.append(rec)
    return pd.DataFrame(out)


# --------------------------------------------------------------------------------------------
# Name matching (Odds API names against ESPN names)
# --------------------------------------------------------------------------------------------
_SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")
_PUNCT = re.compile("[.'’-]")


def norm_name(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = _PUNCT.sub(" ", s)
    s = _SUFFIX.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_names(names, candidates, cutoff=0.86):
    """Map each Odds API name to an athlete_id from candidates (DataFrame with athlete_id, player).
    Exact normalized match first, then the closest fuzzy match above the cutoff. Returns dict and misses."""
    cand = candidates.drop_duplicates("athlete_id").copy()
    cand["key"] = cand["player"].map(norm_name)
    by_key = {}
    for r in cand.itertuples():
        by_key.setdefault(r.key, []).append(int(r.athlete_id))
    mapping, misses = {}, []
    for n in names:
        k = norm_name(n)
        ids = by_key.get(k)
        if ids and len(ids) == 1:
            mapping[n] = ids[0]
            continue
        close = difflib.get_close_matches(k, list(by_key), n=1, cutoff=cutoff)
        if close and len(by_key[close[0]]) == 1:
            mapping[n] = by_key[close[0]][0]
        else:
            misses.append(n)
    return mapping, misses


def is_out(status):
    return str(status or "").strip().lower() in OUT_STATUSES
