"""
top_post.py: the five most likely double-doubles tonight, in the StrikeOut Bot's post format.

Russ, 2026-10-29, after seeing the first edge-rule post: "All these numbers are confusing. I just want 5 dudes
sent to phone like strikeout. Most likely to double double based on the data and today's games." This reads the
board daily_run.py wrote for the date, drops players listed out or doubtful and players on the second night of a
back-to-back (Russ, 2026-11-04: "no back to backs with players"; the board's team_b2b and b2b flags, switch
EXCLUDE_B2B in paper_common), ranks the rest by the calibrated model probability and writes two files in
data/paper:
  discord_top_{date}.md  the post: one line per player with team, opponent, tip time, model percent and the
                         FanDuel price, a green mark when the model sits above FanDuel's implied probability and
                         a yellow one when it sits below, plus the edge-rule value play when there is one
  top_{date}.csv         the same players with the fields needed to grade them (grade.py grades them at the
                         FanDuel price into ledger_top.csv; the next post carries last night's result and the
                         season record of these posts)
post_discord.py --kind top sends the post. The edge-rule picks file and board are unchanged, so the price log
and the 100-pick gate keep running underneath.

Run: PYTHONUTF8=1 python tools/top_post.py [--date YYYY-MM-DD] [--n 5]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_common import EXCLUDE_B2B, PAPER_DIR, on_back_to_back, today_et  # noqa: E402

SKIP_STATUS = {"out", "doubtful"}
TOP_LEDGER = PAPER_DIR / "ledger_top.csv"
KEEP_COLS = ["date", "game_id", "tip_et", "team", "opp", "home", "player", "athlete_id", "position",
             "injury_status", "p_cal", "fd_price", "fd_implied", "dk_price", "best_price", "best_book",
             "fair_mult", "fair_power", "pick", "model_trained_at", "open_snapshot_et"]


def fmt_price(x):
    if pd.isna(x):
        return "no FD line"
    return f"FD {int(round(float(x))):+d}"


def tip_label(s):
    try:
        return pd.Timestamp(s).strftime("%I:%M %p").lstrip("0") + " ET"
    except (ValueError, TypeError):
        return ""


def rank(board, n):
    b = board[board["p_cal"].notna()].copy()
    status = b["injury_status"].fillna("").astype(str).str.lower() if "injury_status" in b else ""
    if len(b) and isinstance(status, pd.Series):
        b = b[~status.isin(SKIP_STATUS)]
    if EXCLUDE_B2B:
        b = b[~on_back_to_back(b)]
    b = b.sort_values(["p_cal", "player"], ascending=[False, True]).head(n)
    b.insert(0, "rank", range(1, len(b) + 1))
    return b


def record_line(date):
    """One line: the most recent graded five before this date, and the season record of the five-name posts."""
    if not TOP_LEDGER.exists():
        return None
    led = pd.read_csv(TOP_LEDGER)
    led = led[led["result"].isin(["win", "loss"]) & (led["date"].astype(str) < str(date))]
    if led.empty:
        return None
    last_date = led["date"].astype(str).max()
    last = led[led["date"].astype(str) == last_date]
    w, l = int((last["result"] == "win").sum()), int((last["result"] == "loss").sum())
    hits = ", ".join(last.loc[last["result"] == "win", "player"].astype(str))
    units = last["profit_open"].sum() if last["profit_open"].notna().any() else None
    u = f", {units:+.1f}u at FanDuel prices" if units is not None else ""
    sw, sl = int((led["result"] == "win").sum()), int((led["result"] == "loss").sum())
    prev = (pd.Timestamp(date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    when = "Last night" if last_date == prev else last_date
    hit_txt = f" (hit: {hits})" if hits else ""
    return f"_{when}: {w}-{l}{u}{hit_txt} · season {sw}-{sl}_"


def post_text(date, board, top, record=None):
    n_games = board["game_id"].nunique() if "game_id" in board else 0
    lines = [f"🏀 Top Double-Double Plays: {date} ({n_games} games)",
             f"**Tonight's {len(top)} most likely double-doubles, ranked by the model**", ""]
    for r in top.itertuples():
        side = "vs" if r.home == 1 else "at"
        above = pd.notna(r.fd_implied) and r.p_cal >= r.fd_implied
        mark = "🟢" if above else "🟡"
        status = f" _({r.injury_status.lower()})_" if isinstance(r.injury_status, str) and r.injury_status else ""
        lines.append(f"{mark} **{r.player}** ({r.team} {side} {r.opp}, {tip_label(r.tip_et)}){status}")
        lines.append(f"   model **{r.p_cal * 100:.0f}%** · {fmt_price(r.fd_price)}")
    if "pick" in board:
        picks = board[board["pick"].astype(str).str.lower() == "true"]
        extra = picks[~picks["player"].isin(top["player"])]
        if len(extra):
            names = "; ".join(f"{r.player} ({fmt_price(r.fd_price)})" for r in extra.itertuples())
            lines += ["", f"_Value play by the edge rule: {names}_"]
    lines.append("")
    if record:
        lines.append(record)
    back = " Players on the second night of a back-to-back are left out." if EXCLUDE_B2B else ""
    lines.append(f"_🟢 model above the FanDuel price · 🟡 below it.{back} Paper picks, graded the next day._")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()
    date = args.date or today_et()
    path = PAPER_DIR / f"board_{date}.csv"
    if not path.exists():
        sys.exit(f"no board for {date}: {path}")
    board = pd.read_csv(path)
    top = rank(board, args.n)
    if top.empty:
        sys.exit(f"no scored players on the board for {date}")
    text = post_text(date, board, top, record_line(date))
    (PAPER_DIR / f"discord_top_{date}.md").write_text(text, encoding="utf-8")
    top[[c for c in ["rank"] + KEEP_COLS if c in top]].to_csv(PAPER_DIR / f"top_{date}.csv", index=False)
    print(text)


if __name__ == "__main__":
    main()
