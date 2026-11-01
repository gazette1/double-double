"""
grade.py: next-morning grading of the paper picks (master note, Bot design step 5).

For the date (default yesterday, ET): refresh the hoopR files, read data/paper/picks_{date}.csv, grade every
pick from the box score (double-double = at least two of points, rebounds, assists, steals, blocks at 10 or
more; void when the player never took the court, FanDuel's settlement rule), pay the flat paper stake at the
logged open price (FanDuel when quoted, else the best bettable book) and at the FanDuel close, compute fair
closing line value under both de-vig methods, replace that date's rows in data/paper/ledger.csv and write
data/paper/discord_grade_{date}.md in the strikeout bot's results layout (not posted).
The five names tools/top_post.py posted (data/paper/top_{date}.csv) are graded the same way at the FanDuel price
into data/paper/ledger_top.csv, so the next post can carry the record (Russ, 2026-10-29: five names, like strikeout).

Closing line value, in probability points, positive favors the pick:
  clv_fd_pts     = FanDuel closing implied minus FanDuel open implied (raw line movement at the book)
  fair_clv_mult  = fair closing probability (multiplicative de-vig of the two-way close) minus the open implied
                   price logged at the book we would bet: positive means the bet was +EV against the close
  fair_clv_power = the same under the power de-vig
  ev_close_mult  = fair_close_mult divided by the open implied price, minus 1 (expected return per unit at close)
The gate (design step 6): mean fair CLV positive under both methods over at least 100 picks at logged prices.
Box scores: hoopR (refreshed about 11:30 UTC) first, the ESPN summary endpoint when hoopR lacks the game.

Run: PYTHONUTF8=1 python tools/grade.py [--date YYYY-MM-DD] [--no-pull]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pull_hoopr  # noqa: E402
from common import DD_STATS, load_player_box  # noqa: E402
from paper_common import (LEDGER_PATH, append_run_log, espn_box_scores, fmt_price, grade_summary_path,  # noqa: E402
                          now_et, picks_path, profit_per_unit, tee_stdout, yesterday_et)

GATE_PICKS = 100
RESULT_COLUMNS = ["minutes", "points", "rebounds", "assists", "steals", "blocks", "dd", "box_source", "result",
                  "won", "profit_open", "profit_close", "clv_fd_pts", "fair_clv_mult", "fair_clv_power",
                  "ev_close_mult", "ev_close_power", "fair_move_mult", "graded_at", "note"]
EMOJI = {"win": "✅", "loss": "❌", "void": "⚪", "pending": "⏳"}
TOP_LEDGER_PATH = LEDGER_PATH.with_name("ledger_top.csv")


def log(msg, t0):
    print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)


def season_of(date):
    d = pd.Timestamp(date)
    return d.year + 1 if d.month >= 8 else d.year


def box_scores_for(picks, date, no_pull, t0):
    """Box rows for the picked games: hoopR when it has the game, else the ESPN summary."""
    season = season_of(date)
    if not no_pull:
        for kind in pull_hoopr.KINDS:
            p, status = pull_hoopr.fetch(kind, season, force=True)
            log(f"hoopR {kind}_{season}: {status}", t0)
    raw = load_player_box([season])
    cols = ["game_id", "athlete_id", "minutes", "points", "rebounds", "assists", "steals", "blocks", "did_not_play",
            "reason"]
    have = raw[raw["game_id"].isin(picks["game_id"].astype(int))][cols].copy()
    have["box_source"] = "hoopr"
    have["final"] = True
    missing = sorted(set(picks["game_id"].astype(int)) - set(have["game_id"]))
    frames = [have]
    for gid in missing:
        df, final = espn_box_scores(gid)
        df["box_source"] = "espn"
        df["final"] = final
        frames.append(df[cols + ["box_source", "final"]])
        log(f"game {gid} not in hoopR yet; ESPN summary {'final' if final else 'not final'} with {len(df)} rows", t0)
    box = pd.concat(frames, ignore_index=True)
    box["dd"] = ((box[DD_STATS] >= 10).sum(axis=1) >= 2).astype(float)
    return box


def grade_rows(picks, box):
    out = picks.copy()
    for c in RESULT_COLUMNS:
        if c not in out:
            out[c] = np.nan
    b = box.drop_duplicates(["game_id", "athlete_id"]).set_index(["game_id", "athlete_id"])
    game_final = box.groupby("game_id")["final"].first().to_dict()
    rows = []
    for r in out.itertuples():
        key = (int(r.game_id), int(r.athlete_id))
        rec = {}
        final = bool(game_final.get(int(r.game_id), False))
        if key in b.index:
            x = b.loc[key]
            for c in ["minutes", "points", "rebounds", "assists", "steals", "blocks", "dd"]:
                rec[c] = float(x[c]) if pd.notna(x[c]) else np.nan
            rec["box_source"] = x["box_source"]
            played = pd.notna(x["minutes"]) and float(x["minutes"]) > 0 and not bool(x["did_not_play"])
        else:
            played = False
            rec["box_source"] = "none"
        status = str(getattr(r, "status", "open"))
        if not final and key not in b.index:
            result = "pending"
        elif status == "void_out" or not played:
            result = "void"
        else:
            result = "win" if rec.get("dd", 0) >= 1 else "loss"
        rec["result"] = result
        won = {"win": True, "loss": False}.get(result)
        rec["won"] = won
        stake = float(getattr(r, "stake", 1.0) or 1.0)
        open_price = getattr(r, "book_price", np.nan)
        close_price = getattr(r, "fd_close_price", np.nan)
        rec["profit_open"] = 0.0 if result == "void" else (stake * profit_per_unit(open_price, won)
                                                          if won is not None else np.nan)
        rec["profit_close"] = 0.0 if result == "void" else (stake * profit_per_unit(close_price, won)
                                                           if won is not None else np.nan)
        q_open = getattr(r, "book_implied", np.nan)
        rec["clv_fd_pts"] = getattr(r, "fd_close_implied", np.nan) - getattr(r, "fd_implied", np.nan)
        rec["fair_clv_mult"] = getattr(r, "fair_close_mult", np.nan) - q_open
        rec["fair_clv_power"] = getattr(r, "fair_close_power", np.nan) - q_open
        rec["ev_close_mult"] = getattr(r, "fair_close_mult", np.nan) / q_open - 1 if pd.notna(q_open) else np.nan
        rec["ev_close_power"] = getattr(r, "fair_close_power", np.nan) / q_open - 1 if pd.notna(q_open) else np.nan
        rec["fair_move_mult"] = getattr(r, "fair_close_mult", np.nan) - getattr(r, "fair_mult", np.nan)
        rec["graded_at"] = now_et().strftime("%Y-%m-%d %H:%M")
        notes = []
        if pd.isna(open_price):
            notes.append("no price logged")
        if pd.isna(getattr(r, "fair_close_mult", np.nan)):
            notes.append("no two-way close")
        if result == "void":
            notes.append("ruled out before tip" if status == "void_out" else "did not play")
        rec["note"] = "; ".join(notes)
        rows.append(rec)
    res = pd.DataFrame(rows, index=out.index)
    for c in res.columns:
        out[c] = res[c]
    return out


def grade_top(date, no_pull, t0, box=None):
    """Grade the five names top_post.py posted for the date, at the FanDuel open price, into ledger_top.csv."""
    path = LEDGER_PATH.parent / f"top_{date}.csv"
    if not path.exists():
        return None
    top = pd.read_csv(path)
    if top.empty:
        return None
    top["book_price"] = top["fd_price"]
    top["book_implied"] = top["fd_implied"]
    top["stake"] = 1.0
    if box is None:
        box = box_scores_for(top, date, no_pull, t0)
    else:
        missing = set(top["game_id"].astype(int)) - set(box["game_id"].astype(int))
        if missing:
            extra = box_scores_for(top[top["game_id"].isin(missing)], date, True, t0)
            box = pd.concat([box, extra], ignore_index=True)
    graded = grade_rows(top, box)
    if TOP_LEDGER_PATH.exists():
        led = pd.read_csv(TOP_LEDGER_PATH)
        led = led[led["date"].astype(str) != str(date)]
        led = pd.concat([led, graded], ignore_index=True, sort=False)
    else:
        led = graded.copy()
    led = led.sort_values(["date", "rank"])
    led.to_csv(TOP_LEDGER_PATH, index=False)
    w, l = int((graded["result"] == "win").sum()), int((graded["result"] == "loss").sum())
    pend = int((graded["result"] == "pending").sum())
    units = graded["profit_open"].sum() if graded["profit_open"].notna().any() else float("nan")
    unit_txt = f"{units:+.2f} units at FanDuel prices" if units == units else "no prices logged"
    decided = graded[graded["result"].isin(["win", "loss"])]
    exp_hits = float(decided["p_cal"].sum())
    log(f"top five {date}: {w}-{l} against {exp_hits:.2f} expected hits, {pend} pending, {unit_txt}; "
        f"{TOP_LEDGER_PATH.name} now {len(led)} rows", t0)
    ld = led[led["result"].isin(["win", "loss"])]
    if len(ld):
        sw, se = int((ld["result"] == "win").sum()), float(ld["p_cal"].sum())
        sd = float(np.sqrt((ld["p_cal"] * (1 - ld["p_cal"])).sum()))
        z = (sw - se) / sd if sd > 0 else float("nan")
        log(f"five-name record to date: {sw}-{len(ld) - sw}, expected {se:.1f} hits, z {z:+.2f} "
            f"(luck against model bias; a z beyond 2 for a run of 100 legs means the model, not the dice)", t0)
    append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "grade_top",
                    "picks": len(graded), "wins": w, "losses": l, "pending": pend, "expected_hits": round(exp_hits, 2),
                    "units_open": round(units, 2) if units == units else np.nan})
    return graded


def update_ledger(graded, date):
    if LEDGER_PATH.exists():
        led = pd.read_csv(LEDGER_PATH)
        led = led[led["date"].astype(str) != str(date)]
        led = pd.concat([led, graded], ignore_index=True, sort=False)
    else:
        led = graded.copy()
    led = led.sort_values(["date", "rank"], na_position="last")
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    led.to_csv(LEDGER_PATH, index=False)
    return led


def season_block(led):
    """Season-to-date line in the strikeout bot's rolling-stats style, plus the CLV gate. Only edge-selected
    picks at logged prices count; backfill picks without prices are reported apart."""
    sel = led["selection"].astype(str)
    edge, other = led[sel == "edge"], led[sel != "edge"]
    decided = edge[edge["result"].isin(["win", "loss"])]
    w, l = int((decided["result"] == "win").sum()), int((decided["result"] == "loss").sum())
    priced = decided[decided["profit_open"].notna() & decided["book_price"].notna()]
    units = float(priced["profit_open"].sum()) if len(priced) else 0.0
    hr = 100.0 * w / max(w + l, 1)
    clv = edge[edge["fair_clv_mult"].notna() & edge["fair_clv_power"].notna() & edge["result"].isin(["win", "loss"])]
    n_clv = len(clv)
    extra = ""
    if len(other):
        wo = int((other["result"] == "win").sum())
        lo = int((other["result"] == "loss").sum())
        extra = f" Backfill picks without prices, not counted: {wo}-{lo}."
    line = (f"📈 **Season:** {w}-{l} ({hr:.0f}%) · {units:+.2f}u at the open price on {len(priced)} priced picks"
            f" · fair CLV mean {clv['fair_clv_mult'].mean():+.3f} / {clv['fair_clv_power'].mean():+.3f} on {n_clv} "
            f"picks with a two-way close" if n_clv else
            f"📈 **Season:** {w}-{l} ({hr:.0f}%) · {units:+.2f}u at the open price on {len(priced)} priced picks · "
            f"no picks with a two-way close yet")
    if n_clv >= GATE_PICKS:
        ok = clv["fair_clv_mult"].mean() > 0 and clv["fair_clv_power"].mean() > 0
        gate = f"Gate ({GATE_PICKS} picks, fair CLV positive under both de-vig methods): {'met' if ok else 'not met'}."
    else:
        gate = f"Gate: {GATE_PICKS - n_clv} more picks with a two-way close needed before the CLV test reads."
    return line + "\n_" + gate + extra + "_"


def discord_results(date, graded, led, note_backfill):
    decided = graded[graded["result"].isin(["win", "loss"])]
    w, l = int((decided["result"] == "win").sum()), int((decided["result"] == "loss").sum())
    units = graded["profit_open"].sum() if graded["profit_open"].notna().any() else np.nan
    head = f"**{w}-{l}**"
    if w + l:
        head += f" ({100.0 * w / (w + l):.0f}%)"
    if pd.notna(units):
        head += f" · {units:+.2f}u at the open price"
    lines = [f"🏀 DD results: {date}", "", head]
    for r in graded.sort_values("rank").itertuples():
        stat = (f"{r.points:.0f} pts {r.rebounds:.0f} reb {r.assists:.0f} ast" if pd.notna(r.points) else "no box score")
        if pd.notna(r.steals) and r.steals >= 10:
            stat += f" {r.steals:.0f} stl"
        if pd.notna(r.blocks) and r.blocks >= 10:
            stat += f" {r.blocks:.0f} blk"
        price = f"Yes {fmt_price(r.book_price)}" if pd.notna(r.book_price) else "no price logged"
        clv = (f" · fair CLV {r.fair_clv_mult:+.3f} / {r.fair_clv_power:+.3f}" if pd.notna(r.fair_clv_mult) else "")
        tag = f" ({r.note})" if isinstance(r.note, str) and r.note and r.result in ("void", "pending") else ""
        lines.append(f"{EMOJI.get(r.result, '•')} **{r.player}** ({r.team} vs {r.opp}) {price} · model {r.p_cal:.2f}"
                     f" · {stat}{clv}{tag}")
    lines += ["", season_block(led)]
    if note_backfill:
        lines.append("_Backfill day: picks were the top probabilities without logged prices, graded to test the path. "
                     "They count in the record but not in units or CLV._")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="game date to grade (ET), default yesterday")
    ap.add_argument("--no-pull", action="store_true", help="skip the hoopR refresh")
    args = ap.parse_args()
    t0 = time.time()
    date = args.date or yesterday_et()
    tee_stdout("grade", date)
    path = picks_path(date)
    picks = pd.read_csv(path) if path.exists() else pd.DataFrame()  # no file: no run that day, nothing to grade
    if picks.empty:
        why = "No plays were posted for this date" if path.exists() else "No run was made for this date"
        text = f"🏀 DD results: {date}\n\n{why}, nothing to grade.\n"
        grade_summary_path(date).parent.mkdir(parents=True, exist_ok=True)
        grade_summary_path(date).write_text(text, encoding="utf-8")
        append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "grade", "picks": 0,
                        "seconds": round(time.time() - t0, 1)})
        print(text)
        grade_top(date, args.no_pull, t0)
        return
    box = box_scores_for(picks, date, args.no_pull, t0)
    graded = grade_rows(picks, box)
    grade_top(date, args.no_pull, t0, box)
    pending = int((graded["result"] == "pending").sum())
    if pending:
        log(f"{pending} picks are in games that are not final; re-run later to grade them", t0)
    led = update_ledger(graded, date)
    backfill = bool((graded["selection"].astype(str).str.contains("no prices")).any())
    text = discord_results(date, graded, led, backfill)
    grade_summary_path(date).parent.mkdir(parents=True, exist_ok=True)
    grade_summary_path(date).write_text(text, encoding="utf-8")
    assert "—" not in text
    append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "grade",
                    "picks": len(graded), "wins": int((graded["result"] == "win").sum()),
                    "losses": int((graded["result"] == "loss").sum()), "voids": int((graded["result"] == "void").sum()),
                    "pending": pending, "units_open": float(graded["profit_open"].sum()) if graded["profit_open"].notna().any() else np.nan,
                    "ledger_rows": len(led), "seconds": round(time.time() - t0, 1)})
    print()
    print(text)
    log(f"ledger {LEDGER_PATH.name} now {len(led)} rows; wrote {grade_summary_path(date).name}", t0)


if __name__ == "__main__":
    main()
