"""
pretip_snapshot.py: the pre-tip step of the paper trade (master note, Bot design step 4).

Re-snapshots prices for the games that hold picks only (one credit per such game), re-reads the ESPN injury
report and rosters, marks any pick whose player is now listed Out or Doubtful as ruled out, and records the
closing price: FanDuel, the best bettable book, and the fair probability from the two-way quotes under both
de-vig methods. Running it again before tip overwrites the closing columns with the newer snapshot, so the last
run before tip is the close. Picks file: data/paper/picks_{date}.csv (closing columns added in place).

Run: PYTHONUTF8=1 python tools/pretip_snapshot.py [--date YYYY-MM-DD] [--books a,b,c]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import odds_snapshot as osn  # noqa: E402
from paper_common import (BEST_BOOKS, append_run_log, espn_injuries, espn_roster, espn_scoreboard,  # noqa: E402
                          fmt_price, is_out, match_names, now_et, picks_path, price_board, summary_path, tee_stdout,
                          today_et, write_text)

CLOSE_COLUMNS = ["close_snapshot_et", "fd_close_price", "fd_close_implied", "dk_close_price", "dk_close_implied",
                 "best_close_price", "best_close_book", "best_close_implied", "n_twoway_close", "twoway_books_close",
                 "fair_close_mult", "fair_close_power", "injury_status_close", "ruled_out", "game_state_at_close"]


def log(msg, t0):
    print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="game date (ET), default today")
    ap.add_argument("--books", default=osn.DEFAULT_BOOKS)
    args = ap.parse_args()
    t0 = time.time()
    date = args.date or today_et()
    tee_stdout("pretip", date)
    path = picks_path(date)
    if not path.exists():
        sys.exit(f"no picks file for {date}: {path}")
    picks = pd.read_csv(path)
    if picks.empty:
        log(f"picks file for {date} has no picks; nothing to snapshot", t0)
        return
    for c in CLOSE_COLUMNS:
        if c not in picks:
            picks[c] = np.nan

    games = {g["game_id"]: g for g in espn_scoreboard(date)}
    picks["game_state_at_close"] = picks["game_id"].map(lambda g: games.get(int(g), {}).get("status_state"))
    started = picks["game_state_at_close"].isin(["in", "post"])
    if started.any():
        log(f"WARNING: {int(started.sum())} picks are in games that already started; their closing price is the "
            f"last pre-game quote the API still serves, if any", t0)

    # injuries and rosters for the picked teams
    inj = espn_injuries().dropna(subset=["athlete_id"]).drop_duplicates("athlete_id").set_index("athlete_id")
    teams = set()
    for gid in picks["game_id"].unique():
        g = games.get(int(gid))
        if g:
            teams |= {g["home_id"], g["away_id"]}
    rosters = pd.concat([espn_roster(t) for t in sorted(teams)], ignore_index=True) if teams else pd.DataFrame()
    ro_status = rosters.drop_duplicates("athlete_id").set_index("athlete_id")["injury_status"] if len(rosters) else {}
    status = picks["athlete_id"].map(inj["status"]) if len(inj) else pd.Series(np.nan, index=picks.index)
    status = status.fillna(picks["athlete_id"].map(ro_status)) if len(rosters) else status
    picks["injury_status_close"] = status
    picks["ruled_out"] = picks["injury_status_close"].map(is_out)

    # prices for the picked games only
    event_ids = sorted(set(str(e) for e in picks["event_id"].dropna().unique()))
    credits = {}
    if event_ids:
        snap = osn.snapshot(books=args.books, date=date, event_ids=event_ids, kind="pretip")
        credits = {"used_run": snap["used_run"], "remaining": snap["remaining"]}
        board = price_board(snap["rows"], BEST_BOOKS)
        if not board.empty:
            cand = pd.concat([rosters[["athlete_id", "player"]] if len(rosters) else pd.DataFrame(),
                              picks[["athlete_id", "player"]]], ignore_index=True)
            mapping, misses = match_names(board["player"].tolist(), cand)
            board["athlete_id"] = board["player"].map(mapping)
            board["event_id"] = board["event_id"].astype(str)
            picks["event_id"] = picks["event_id"].astype(str)
            m = picks[["event_id", "athlete_id"]].merge(board, on=["event_id", "athlete_id"], how="left")
            picks["close_snapshot_et"] = snap["snapshot_et"]
            picks["fd_close_price"] = m["fd_price"].to_numpy()
            picks["fd_close_implied"] = m["fd_implied"].to_numpy()
            picks["dk_close_price"] = m["dk_price"].to_numpy()
            picks["dk_close_implied"] = m["dk_implied"].to_numpy()
            picks["best_close_price"] = m["best_price"].to_numpy()
            picks["best_close_book"] = m["best_book"].to_numpy()
            picks["best_close_implied"] = m["best_implied"].to_numpy()
            picks["n_twoway_close"] = m["n_twoway"].to_numpy()
            picks["twoway_books_close"] = m["twoway_books"].to_numpy()
            picks["fair_close_mult"] = m["fair_mult"].to_numpy()
            picks["fair_close_power"] = m["fair_power"].to_numpy()
            log(f"closing quotes matched for {int(m['fd_price'].notna().sum())} of {len(picks)} picks (FanDuel), "
                f"{int((m['n_twoway'].fillna(0) >= 1).sum())} with two-way quotes", t0)
    else:
        log("picks carry no Odds API event ids (backfill without prices); only the injury check runs", t0)

    picks.loc[picks["ruled_out"], "status"] = "void_out"
    picks.to_csv(path, index=False)

    lines = [f"🏀 DD pre-tip check: {date}", ""]
    for r in picks.itertuples():
        mark = "⚪" if r.ruled_out else "🟢"
        close = (f"close FD {fmt_price(r.fd_close_price)} (open {fmt_price(r.fd_price)}), fair close "
                 f"{r.fair_close_mult:.2f} / {r.fair_close_power:.2f}" if pd.notna(r.fair_close_mult) else
                 (f"close FD {fmt_price(r.fd_close_price)} (open {fmt_price(r.fd_price)})" if pd.notna(r.fd_close_price)
                  else "no closing quote"))
        state = f", game {r.game_state_at_close}" if isinstance(r.game_state_at_close, str) else ""
        note = f" · listed {r.injury_status_close}" if isinstance(r.injury_status_close, str) else ""
        lines.append(f"{mark} **{r.player}** ({r.team} vs {r.opp}) {'ruled out, void' if r.ruled_out else 'stands'}"
                     f" · {close}{note}{state}")
    lines.append("")
    lines.append(f"_Credits used {credits.get('used_run', 0)}, remaining {credits.get('remaining')}._")
    text = "\n".join(lines) + "\n"
    write_text(summary_path(date).with_name(f"discord_pretip_{date}.md"), text)
    append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "pretip",
                    "games": len(event_ids), "picks": len(picks), "ruled_out": int(picks["ruled_out"].sum()),
                    "credits_used": credits.get("used_run"), "credits_remaining": credits.get("remaining"),
                    "seconds": round(time.time() - t0, 1)})
    print()
    print(text)


if __name__ == "__main__":
    main()
