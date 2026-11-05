"""
daily_run.py: the morning paper-trade run of the Double Double Bot (master note, Bot design steps 1 to 3).

1. Refresh the hoopR box-score files of the current season (tools/pull_hoopr.py).
2. Pull the slate from the ESPN scoreboard (explicit dates parameter), the injury report and the rosters of
   the teams playing.
3. Build point-in-time features for every rostered player through build_dataset.build_table, the same code
   path as the historical table: the day's games are appended to the cleaned box-score history as pending rows
   with placeholder stats (every window is exclusive, so a row's placeholders never enter its own features),
   and players listed Out or Doubtful get no row, which is what the abs_ teammate-absence features read.
4. Predict calibrated probabilities with the production model (C_full plus Platt) and the season-rate proxy.
5. Log prices with tools/odds_snapshot.py (FanDuel, DraftKings and the two-way books), derive fair
   probabilities from the two-way quotes under multiplicative and power de-vig, compute edge = p minus fair and
   the FanDuel edge = p minus the FanDuel implied probability.
6. Select by edge under the design thresholds (constants below; a player on the second night of a back-to-back,
   team_b2b or b2b, is never a pick: Russ, 2026-11-04) and write data/paper/picks_{date}.csv,
   board_{date}.csv (every scored or priced player) and discord_{date}.md (Discord text, not posted).

Backfill: --date with a past date rebuilds that day as of its morning: history strictly before the date, the
day's rows from the actual lineups (so the abs_ features are lineup-known, as in the backtest). --no-odds skips
the price snapshot (no credits); selection then falls back to the three highest probabilities and the files say
so. Paper stakes only, one unit per pick.

Run: PYTHONUTF8=1 python tools/daily_run.py [--date YYYY-MM-DD] [--no-pull] [--no-odds] [--no-retrain]
                                             [--books a,b,c] [--max-picks 3] [--verify] [--dry-run]
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.special import expit, logit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dataset as bd  # noqa: E402
import odds_snapshot as osn  # noqa: E402
import pull_hoopr  # noqa: E402
from common import MIN_PRIOR_GAMES, PLAYER_COLS, SEASONS, load_player_box  # noqa: E402
from paper_common import (BEST_BOOKS, BOOK_LABEL, ET, EXCLUDE_B2B, PROD_DIR, TEAM_ABBR, TEAM_NAME_TO_ID,  # noqa: E402
                          append_run_log, board_path, espn_injuries, espn_roster, espn_scoreboard, fmt_price, is_out,
                          logged_price_rows, match_names, now_et, on_back_to_back, picks_path, price_board,
                          summary_path, tee_stdout, today_et, write_text)
from train_eval import baseline_a  # noqa: E402

# Selection thresholds (Bot design step 3). Edges are probability points.
P_MIN = 0.35            # minimum calibrated probability
MARGIN_FLOOR = 0.03     # floor of the edge bar when the measured FanDuel one-sided margin is smaller
MARGIN_FAIR_MIN = 0.20  # the FanDuel margin is measured on players whose fair probability is at least this
BOOK_EDGE_MIN = 0.02    # p minus the implied price at the book we would bet (FanDuel if quoted), model-error buffer
NEAR_LOCK_P = 0.80      # near-lock caution: p at or above this ...
BIG_SPREAD = 10.0       # ... in a game with a spread of 10 or more needs twice the bar
EARLY_SEASON_GAMES = 5  # a team's first five games: the bar rises by EARLY_EXTRA
EARLY_EXTRA = 0.03
MAX_PICKS = 3
STAKE = 1.0             # paper units per pick
STALE_DAYS = 7          # retrain when the production manifest is older than this
ROOT = Path(__file__).resolve().parent.parent
PICK_COLUMNS = ["date", "game_id", "event_id", "tip_et", "away_abbr", "home_abbr", "team", "opp", "home", "player",
                "athlete_id", "position", "injury_status", "team_game_num", "spread_team", "spread_detail",
                "p_raw", "p_cal", "p_proxy", "fd_price", "fd_implied", "dk_price", "dk_implied", "best_price",
                "best_book", "best_implied", "book_used", "book_price", "book_implied", "n_twoway", "twoway_books",
                "fair_mult", "fair_power", "edge_mult", "edge_power", "fd_edge", "book_edge", "margin_slate", "bar",
                "flags", "rank", "stake", "selection", "status", "open_snapshot_et", "model_trained_at"]


def log(msg, t0):
    print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)


def season_of(date):
    d = pd.Timestamp(date)
    return d.year + 1 if d.month >= 8 else d.year


# --------------------------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------------------------
def ensure_model(no_retrain, t0):
    manifest_path = PROD_DIR / "manifest.json"
    stale = True
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        age = (now_et().replace(tzinfo=None) - datetime.strptime(m["trained_at"], "%Y-%m-%d %H:%M")).days
        stale = age >= STALE_DAYS
        log(f"production model trained {m['trained_at']} (cutoff {m['train_cutoff']}, {age} days old)", t0)
    if stale and not no_retrain:
        log("retraining the production model (weekly schedule)", t0)
        subprocess.run([sys.executable, str(ROOT / "tools" / "train_production.py")], check=True)
    elif stale:
        log("WARNING: production model is stale or missing and --no-retrain was given", t0)
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = json.loads((PROD_DIR / "features.json").read_text(encoding="utf-8"))
    booster = lgb.Booster(model_file=str(PROD_DIR / m["files"]["model"]))
    platt = json.loads((PROD_DIR / m["files"]["platt"]).read_text(encoding="utf-8"))
    return m, spec, booster, platt


def predict(live, spec, booster, platt, league_rate):
    X = live[spec["features"]].copy()
    X["position"] = pd.Categorical(X["position"].astype(object), categories=spec["position_categories"])
    p_raw = booster.predict(X)
    p_cal = expit(platt["a"] * logit(np.clip(p_raw, 1e-6, 1 - 1e-6)) + platt["b"])
    return p_raw, p_cal, baseline_a(live, league_rate)


# --------------------------------------------------------------------------------------------
# Slate, rosters, pending rows
# --------------------------------------------------------------------------------------------
def live_rosters(games, t0):
    """Roster rows for the teams playing, with injury status from the roster and the league report."""
    inj = espn_injuries()
    teams = sorted({g["home_id"] for g in games} | {g["away_id"] for g in games})
    frames = []
    for tid in teams:
        r = espn_roster(tid)
        if r.empty:
            log(f"WARNING: empty ESPN roster for team {tid}", t0)
        frames.append(r)
    ro = pd.concat(frames, ignore_index=True)
    by_id = inj.dropna(subset=["athlete_id"]).drop_duplicates("athlete_id").set_index("athlete_id")
    ro["report_status"] = ro["athlete_id"].map(by_id["status"])
    ro["injury_status"] = ro["report_status"].fillna(ro["injury_status"])
    ro["injury_note"] = ro["athlete_id"].map(by_id["injury_type"].astype(str) + ", " + by_id["return_date"].astype(str))
    log(f"rosters: {len(ro)} players on {len(teams)} teams; injury report {len(inj)} players league-wide, "
        f"{int(ro['injury_status'].map(is_out).sum())} of tonight's players Out or Doubtful", t0)
    return ro, inj


def backfill_rosters(games, date):
    """Actual lineups of a past date (players with minutes) from the raw box scores, status unknown."""
    raw = load_player_box([season_of(date)])
    day = raw[(raw["game_date"] == pd.Timestamp(date)) & (raw["minutes"] > 0)]
    ro = day[["team_id", "athlete_id", "athlete_display_name", "athlete_position_abbreviation"]].rename(
        columns={"athlete_display_name": "player", "athlete_position_abbreviation": "position"}).drop_duplicates()
    ro["roster_status"] = "played"
    ro["injury_status"] = None
    ro["injury_note"] = None
    return ro.reset_index(drop=True)


def pending_rows(games, rosters, pb_hist, date):
    """One placeholder row per game, team and available player, in the raw player-box column layout."""
    last = pb_hist.sort_values("game_date").drop_duplicates("athlete_id", keep="last").set_index("athlete_id")
    season = season_of(date)
    rows = []
    for g in games:
        for side, tid, opp in [("home", g["home_id"], g["away_id"]), ("away", g["away_id"], g["home_id"])]:
            team_ro = rosters[rosters["team_id"] == tid]
            for r in team_ro.itertuples():
                if is_out(r.injury_status):
                    continue
                aid = int(r.athlete_id)
                pos = last["athlete_position_abbreviation"].get(aid) if aid in last.index else None
                rows.append({
                    "game_id": g["game_id"], "season": season, "season_type": g["season_type"],
                    "game_date": pd.Timestamp(date), "game_date_time": pd.Timestamp(g["tip_et"]).tz_convert(ET),
                    "athlete_id": aid, "athlete_display_name": r.player,
                    "athlete_position_abbreviation": pos if isinstance(pos, str) else r.position,
                    "team_id": tid, "team_abbreviation": TEAM_ABBR.get(tid), "opponent_team_id": opp,
                    "home_away": side, "minutes": 1.0, "points": 0.0, "rebounds": 0.0, "offensive_rebounds": 0.0,
                    "defensive_rebounds": 0.0, "assists": 0.0, "steals": 0.0, "blocks": 0.0, "turnovers": 0.0,
                    "fouls": 0.0, "field_goals_attempted": 0.0, "free_throws_attempted": 0.0, "starter": False,
                    "did_not_play": False, "reason": None, "team_score": np.nan, "opponent_team_score": np.nan,
                })
    pend = pd.DataFrame(rows, columns=PLAYER_COLS)
    pend = pend.drop_duplicates("athlete_id", keep="first").reset_index(drop=True)
    return pend


def build_live_table(pb, tb, pend, verify, t0):
    """Append the pending rows to the history and run the shared feature build; return the pending rows."""
    pb = pb.copy()
    pb["game_date_time"] = pb["game_date_time"].dt.tz_convert(ET)
    pend = pend.copy()
    pend["game_date_time"] = pd.to_datetime(pend["game_date_time"]).dt.tz_convert(ET)
    allpb = pd.concat([pb, pend], ignore_index=True)
    allpb["starter"] = allpb["starter"].astype(bool)
    allpb["did_not_play"] = allpb["did_not_play"].astype(bool)
    info = {}
    ds, p, feats, meta_cols = bd.build_table(allpb, tb, info, t0, verify=verify)
    live = ds[ds["game_id"].isin(set(pend["game_id"])) & ds["athlete_id"].isin(set(pend["athlete_id"]))].copy()
    for c in ["minutes", "points", "rebounds", "assists", "steals", "blocks", "starter", "dd", "td"]:
        live[c] = np.nan
    n_before = len(live)
    skipped = live[live["games_played_career"] < MIN_PRIOR_GAMES][["athlete_display_name", "team_abbreviation",
                                                                   "games_played_career"]]
    live = live[live["games_played_career"] >= MIN_PRIOR_GAMES].reset_index(drop=True)
    log(f"live rows {len(live)} of {n_before} pending players ({len(skipped)} with fewer than {MIN_PRIOR_GAMES} "
        f"prior games skipped; {len(pend) - n_before} without any box-score history)", t0)
    return live, feats, skipped


# --------------------------------------------------------------------------------------------
# Prices and selection
# --------------------------------------------------------------------------------------------
def event_to_game(events, games):
    out = {}
    by_pair = {(g["home_id"], g["away_id"]): g for g in games}
    for e in events:
        h, a = TEAM_NAME_TO_ID.get(e["home_team"]), TEAM_NAME_TO_ID.get(e["away_team"])
        g = by_pair.get((h, a))
        if g is not None:
            out[e["id"]] = g["game_id"]
    return out


def attach_prices(live, rosters, snap, games, t0):
    """Merge the price board onto the live rows by (game, athlete) through name matching inside each game."""
    board = price_board(snap["rows"], BEST_BOOKS)
    e2g = event_to_game(snap["events"], games)
    if board.empty:
        log("no price rows returned", t0)
        return live.assign(event_id=None), board, []
    board["game_id"] = board["event_id"].map(e2g)
    unmatched = []
    board["athlete_id"] = np.nan
    gteams = {g["game_id"]: (g["home_id"], g["away_id"]) for g in games}
    for gid, grp in board.groupby("game_id"):
        if pd.isna(gid):
            continue
        teams = gteams.get(int(gid), ())
        cand = pd.concat([rosters[rosters["team_id"].isin(teams)][["athlete_id", "player"]],
                          live[live["game_id"] == gid][["athlete_id", "athlete_display_name"]].rename(
                              columns={"athlete_display_name": "player"})], ignore_index=True)
        mapping, misses = match_names(grp["player"].tolist(), cand)
        board.loc[grp.index, "athlete_id"] = grp["player"].map(mapping)
        unmatched += misses
    if unmatched:
        log(f"price rows without a roster match: {unmatched}", t0)
    keep = ["game_id", "athlete_id", "event_id", "fd_price", "fd_implied", "dk_price", "dk_implied", "best_price",
            "best_book", "best_implied", "n_twoway", "twoway_books", "fair_mult", "fair_power", "fair_mult_min",
            "fair_mult_max", "twoway_hold_mean", "n_books_yes", "books_yes", "yes_quotes", "no_quotes"]
    pb_ = board.dropna(subset=["athlete_id", "game_id"]).copy()
    pb_["athlete_id"] = pb_["athlete_id"].astype(int)
    pb_["game_id"] = pb_["game_id"].astype(int)
    merged = live.merge(pb_[keep], on=["game_id", "athlete_id"], how="left")
    assert len(merged) == len(live)
    return merged, board, unmatched


def select_picks(live, games, no_odds, max_picks):
    df = live.copy()
    gmap = {g["game_id"]: g for g in games}
    df["spread_home"] = df["game_id"].map(lambda g: gmap[g]["spread_home"])
    df["spread_detail"] = df["game_id"].map(lambda g: gmap[g]["spread_detail"])
    df["spread_team"] = np.where(df["home"] == 1, df["spread_home"], -df["spread_home"])
    for c in ["fd_implied", "fair_mult", "fair_power", "best_implied", "n_twoway"]:
        if c not in df:
            df[c] = np.nan
    df["edge_mult"] = df["p_cal"] - df["fair_mult"]
    df["edge_power"] = df["p_cal"] - df["fair_power"]
    df["fd_edge"] = df["p_cal"] - df["fd_implied"]
    use_fd = df["fd_implied"].notna()
    df["book_used"] = np.where(use_fd, "fanduel", df.get("best_book", pd.Series(index=df.index, dtype=object)))
    df["book_price"] = np.where(use_fd, df.get("fd_price", np.nan), df.get("best_price", np.nan))
    df["book_implied"] = np.where(use_fd, df["fd_implied"], df["best_implied"])
    df["book_edge"] = df["p_cal"] - df["book_implied"]
    # FanDuel's one-sided margin tonight, measured where picks can occur (fair at least MARGIN_FAIR_MIN): the
    # margin is concentrated on the favorites and near zero on longshots, so a whole-board median understates it.
    both = df["fd_implied"].notna() & df["fair_mult"].notna() & (df["fair_mult"] >= MARGIN_FAIR_MIN)
    margin_slate = float((df.loc[both, "fd_implied"] - df.loc[both, "fair_mult"]).median()) if both.any() else np.nan
    bar = max(margin_slate, MARGIN_FLOOR) if np.isfinite(margin_slate) else MARGIN_FLOOR
    df["margin_slate"] = margin_slate
    df["bar"] = bar
    early = df["team_game_num"].fillna(99) <= EARLY_SEASON_GAMES
    df.loc[early, "bar"] = df.loc[early, "bar"] + EARLY_EXTRA
    near_lock = (df["p_cal"] >= NEAR_LOCK_P) & (df["spread_team"].abs() >= BIG_SPREAD)
    df.loc[near_lock, "bar"] = df.loc[near_lock, "bar"] * 2

    df["b2b_out"] = on_back_to_back(df) if EXCLUDE_B2B else False
    reasons = []
    for r in df.itertuples():
        why = []
        if r.b2b_out:
            why.append("second night of a back-to-back")
        if r.p_cal < P_MIN:
            why.append(f"p below {P_MIN:.2f}")
        if no_odds:
            why.append("no prices logged")
        else:
            if not (r.n_twoway >= 1):
                why.append("no two-way quote")
            elif r.edge_mult < r.bar or r.edge_power < r.bar:
                why.append(f"edge {r.edge_mult:+.3f}/{r.edge_power:+.3f} below bar {r.bar:.3f}")
            if pd.isna(r.book_implied):
                why.append("no price at a bettable book")
            elif r.book_edge < BOOK_EDGE_MIN:
                why.append(f"price edge {r.book_edge:+.3f} below {BOOK_EDGE_MIN:.2f}")
        reasons.append("; ".join(why))
    df["why_not"] = reasons
    flags = []
    for r in df.itertuples():
        f = []
        if r.team_game_num <= EARLY_SEASON_GAMES:
            f.append("early season")
        if (r.p_cal >= NEAR_LOCK_P) and (abs(r.spread_team) >= BIG_SPREAD):
            f.append("near-lock in 10-point spread")
        if isinstance(r.injury_status, str) and r.injury_status:
            f.append(f"listed {r.injury_status}")
        flags.append("; ".join(f))
    df["flags"] = flags

    if no_odds:
        df["selection"] = "probability (no prices logged)"
        ranked = df[(df["p_cal"] >= P_MIN) & ~df["b2b_out"]].sort_values(["p_cal", "p_raw"], ascending=False)
    else:
        df["selection"] = "edge"
        ranked = df[df["why_not"] == ""].sort_values(["edge_mult", "p_cal"], ascending=False)
    picks = ranked.head(max_picks).copy()
    picks["rank"] = np.arange(1, len(picks) + 1)
    picks["stake"] = STAKE
    picks["status"] = "open"
    df["pick"] = df["athlete_id"].isin(picks["athlete_id"]) & df["game_id"].isin(picks["game_id"])
    return df, picks, margin_slate, bar


# --------------------------------------------------------------------------------------------
# Discord text (strikeout bot layout, voice rules applied)
# --------------------------------------------------------------------------------------------
def discord_text(date, games, board, picks, margin_slate, bar, no_odds, credits, n_scored, model_m, unscored=None):
    n_games = len(games)
    lines = [f"🏀 DD picks: {date} ({n_games} games, {n_scored} players scored)", ""]
    if picks.empty:
        priced = board[board["fair_mult"].notna()] if not no_odds else board
        if no_odds:
            lines.append("No prices logged for this date, so no edge picks.")
        elif priced.empty:
            lines.append("No two-way double-double quotes tonight, so no fair price and no picks.")
        else:
            lines.append("No plays tonight. Closest by edge against the fair price, with the blocking rule:")
            for r in priced.sort_values("edge_mult", ascending=False).head(3).itertuples():
                px = f"FD {fmt_price(r.fd_price)}" if pd.notna(r.fd_price) else f"{fmt_price(r.best_price)} {r.best_book}"
                lines.append(f"• {r.athlete_display_name} ({r.team}) model {r.p_cal:.2f}, fair {r.fair_mult:.2f} / "
                             f"{r.fair_power:.2f}, {px}, edge {r.edge_mult:+.3f} / {r.edge_power:+.3f}: {r.why_not}")
    for r in picks.itertuples():
        side = "vs" if r.home == 1 else "at"
        price_txt = (f"Yes **{fmt_price(r.book_price)}** {BOOK_LABEL.get(r.book_used, str(r.book_used))}"
                     if not no_odds and pd.notna(r.book_price) else "no price logged")
        fair_txt = (f"fair {r.fair_mult:.2f} / {r.fair_power:.2f} · edge **{r.edge_mult:+.3f}** / {r.edge_power:+.3f}"
                    f" · FD edge {r.fd_edge:+.3f}" if not no_odds and pd.notna(r.fair_mult) else
                    f"proxy {r.p_proxy:.2f}")
        spread_txt = f" · spread {r.spread_detail}" if isinstance(r.spread_detail, str) else ""
        flag_txt = f"  _({r.flags})_" if isinstance(r.flags, str) and r.flags else ""
        lines.append(f"🟢 **{r.player}** ({r.team} {side} {r.opp}) {price_txt}")
        lines.append(f"   model **{r.p_cal:.2f}** · {fair_txt}{spread_txt}{flag_txt}")
    lines.append("")
    if not no_odds:
        margin_txt = f"{margin_slate:.3f}" if np.isfinite(margin_slate) else "not measurable"
        lines.append(f"_Bar: edge above {bar:.3f} under both de-vig methods ({bar + EARLY_EXTRA:.3f} in a team's "
                     f"first {EARLY_SEASON_GAMES} games, doubled for near-locks in {BIG_SPREAD:.0f}-point spreads); "
                     f"FanDuel one-sided margin tonight {margin_txt} on players with fair at least "
                     f"{MARGIN_FAIR_MIN:.2f}, floor {MARGIN_FLOOR:.2f}; p at least {P_MIN:.2f}; price edge at least "
                     f"{BOOK_EDGE_MIN:.2f} at the book._")
        if unscored is not None and len(unscored):
            items = []
            for r in unscored.itertuples():
                px = f"FD {fmt_price(r.fd_price)}" if pd.notna(r.fd_price) else f"DK {fmt_price(r.dk_price)}"
                fair = f", fair {r.fair_mult:.2f}" if pd.notna(r.fair_mult) else ""
                items.append(f"{r.player} ({px}{fair})")
            lines.append(f"_Priced but not scored (fewer than {MIN_PRIOR_GAMES} prior games, no history, or listed "
                         f"out): " + "; ".join(items) + "._")
        passed = board[(board["p_cal"] >= 0.55) & ~board["pick"]].sort_values("p_cal", ascending=False).head(4)
        if len(passed):
            items = []
            for r in passed.itertuples():
                px = f"FD {fmt_price(r.fd_price)}" if pd.notna(r.fd_price) else "no FD price"
                fair = f"fair {r.fair_mult:.2f}" if pd.notna(r.fair_mult) else "no two-way quote"
                items.append(f"{r.athlete_display_name} p {r.p_cal:.2f}, {px}, {fair}")
            lines.append("_Passed on the favorites: " + "; ".join(items) + "._")
        remaining = credits.get("remaining")
        credit_txt = (f"Credits used {credits.get('used_run', 0)}, remaining {remaining}." if remaining is not None
                      else "Prices replayed from the logged snapshot, no credits used.")
        lines.append(f"_{credit_txt} Paper stakes only, {STAKE:.0f} unit per pick. Model trained "
                     f"{model_m['trained_at']} through {model_m['train_cutoff']}._")
    else:
        lines.append(f"_Backfill run without prices: picks are the top probabilities, for grading the code path "
                     f"only. Model trained {model_m['trained_at']} through {model_m['train_cutoff']}._")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="game date (ET); a past date runs as a backfill")
    ap.add_argument("--no-pull", action="store_true", help="skip the hoopR refresh")
    ap.add_argument("--no-odds", action="store_true", help="skip the price snapshot (no credits)")
    ap.add_argument("--no-retrain", action="store_true", help="do not retrain a stale production model")
    ap.add_argument("--books", default=osn.DEFAULT_BOOKS)
    ap.add_argument("--max-picks", type=int, default=MAX_PICKS)
    ap.add_argument("--verify", action="store_true", help="run the window recomputation check in the build")
    ap.add_argument("--reuse-prices", action="store_true",
                    help="re-run with the logged open snapshot of the date instead of a new API call (no credits)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and predict only: no prices, no files, no run-log row (a check of the live path)")
    args = ap.parse_args()
    t0 = time.time()
    date = args.date or today_et()
    today = today_et()
    assert date <= today, "cannot run a future date"
    live_mode = date == today
    tee_stdout("dryrun" if args.dry_run else "daily", date)
    log(f"daily run for {date} ({'live' if live_mode else 'backfill'})", t0)

    if not args.no_pull:
        # every season is needed for the feature history (a fresh checkout, as in the GitHub Action, has none);
        # only the current season is re-downloaded when the file already exists
        season = season_of(date if live_mode else today)
        for y in SEASONS:
            for kind in pull_hoopr.KINDS:
                p, status = pull_hoopr.fetch(kind, y, force=(y == season))
                if status != "cached":
                    log(f"hoopR {kind}_{y}: {status}", t0)
    model_m, spec, booster, platt = ensure_model(args.no_retrain or args.dry_run, t0)

    games = espn_scoreboard(date)
    if live_mode:
        started = [g for g in games if g["status_state"] != "pre"]
        if started:
            log("games already started or finished, left out: " + ", ".join(
                f"{g['away_abbr']} at {g['home_abbr']} ({g['status_name']})" for g in started), t0)
        games = [g for g in games if g["status_state"] == "pre"]
    if not games:
        write_text(summary_path(date), f"🏀 DD picks: {date}\n\nNo NBA games left to price on this date.\n")
        picks_path(date).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=PICK_COLUMNS).to_csv(picks_path(date), index=False)
        log("no games to price; empty picks file and summary written", t0)
        return
    log(f"slate: {len(games)} games: " + ", ".join(f"{g['away_abbr']} at {g['home_abbr']} "
        f"{g['tip_et'].strftime('%H:%M')} ({g['spread_detail']})" for g in games), t0)

    pb, tb, info = bd.load_clean()
    cutoff = pd.Timestamp(date)
    pb = pb[pb["game_date"] < cutoff]
    tb = tb[tb["game_date"] < cutoff]
    log(f"history through {pb['game_date'].max().date()}: {len(pb)} player rows", t0)
    rosters, inj = live_rosters(games, t0) if live_mode else (backfill_rosters(games, date), None)
    pend = pending_rows(games, rosters, pb, date)
    log(f"pending rows {len(pend)} for {pend['game_id'].nunique()} games", t0)
    live, feats, skipped = build_live_table(pb, tb, pend, args.verify, t0)
    if len(skipped):
        log("skipped (fewer than 5 prior games): " + ", ".join(
            f"{r.athlete_display_name} ({r.team_abbreviation}, {int(r.games_played_career)})" for r in skipped.itertuples()), t0)

    p_raw, p_cal, p_proxy = predict(live, spec, booster, platt, model_m["league_dd_rate_train"])
    live["p_raw"], live["p_cal"], live["p_proxy"] = p_raw, p_cal, p_proxy
    status_map = rosters.drop_duplicates("athlete_id").set_index("athlete_id")["injury_status"]
    live["injury_status"] = live["athlete_id"].map(status_map)
    log(f"predicted {len(live)} players; top: " + ", ".join(
        f"{r.athlete_display_name} {r.p_cal:.2f}" for r in live.sort_values("p_cal", ascending=False).head(6).itertuples()), t0)
    if EXCLUDE_B2B:
        b2b_teams = sorted(live.loc[on_back_to_back(live), "team_abbreviation"].dropna().unique())
        log("second night of a back-to-back, left out of the five and the picks: "
            + (", ".join(b2b_teams) if b2b_teams else "no team"), t0)
    if args.dry_run:
        gs = [c for c in spec["features"] if c.startswith("gs_")]
        cover = {c: round(float(live[c].notna().mean()), 3) for c in gs}
        log(f"dry run: {len(live)} players scored with {len(spec['features'])} features; game-state coverage {cover}", t0)
        show = ["athlete_display_name", "team_abbreviation", "p_cal", "team_b2b", "b2b"] + gs
        print(live.sort_values("p_cal", ascending=False)[show].head(12).round(3).to_string(index=False))
        log("dry run: nothing written", t0)
        return

    credits = {}
    unmatched = []
    if args.no_odds:
        live["event_id"] = None
        board_px = pd.DataFrame()
        snapshot_et = None
    else:
        if args.reuse_prices:
            rows, events = logged_price_rows(date, "open")
            assert rows, f"no logged open snapshot for {date} to reuse"
            snap = {"rows": rows, "events": events, "used_run": 0, "remaining": None,
                    "snapshot_et": rows[0]["snapshot_et"]}
            log(f"reusing the logged open snapshot of {snap['snapshot_et']} ({len(rows)} rows, 0 credits)", t0)
        else:
            snap = osn.snapshot(books=args.books, date=date, kind="open")
        credits = {"used_run": snap["used_run"], "remaining": snap["remaining"]}
        snapshot_et = snap["snapshot_et"]
        live, board_px, unmatched = attach_prices(live, rosters, snap, games, t0)
        n_px = int(live["fd_implied"].notna().sum()) if "fd_implied" in live else 0
        n_two = int((live["n_twoway"].fillna(0) >= 1).sum()) if "n_twoway" in live else 0
        log(f"prices: {n_px} scored players with a FanDuel quote, {n_two} with a two-way quote; "
            f"books in the snapshot: {sorted(set(r['book'] for r in snap['rows']))}", t0)

    board, picks, margin_slate, bar = select_picks(live, games, args.no_odds, args.max_picks)
    gmap = {g["game_id"]: g for g in games}
    board["date"] = date
    board["tip_et"] = board["game_id"].map(lambda g: gmap[g]["tip_et"].strftime("%Y-%m-%d %H:%M"))
    board["away_abbr"] = board["game_id"].map(lambda g: gmap[g]["away_abbr"])
    board["home_abbr"] = board["game_id"].map(lambda g: gmap[g]["home_abbr"])
    board["team"] = board["team_abbreviation"]
    board["opp"] = board["opponent_team_id"].map(TEAM_ABBR)
    board["player"] = board["athlete_display_name"]
    board["open_snapshot_et"] = snapshot_et
    board["model_trained_at"] = model_m["trained_at"]
    picks = board[board["pick"]].merge(picks[["game_id", "athlete_id", "rank", "stake", "status"]],
                                       on=["game_id", "athlete_id"], how="inner").sort_values("rank")
    for c in PICK_COLUMNS:
        if c not in picks:
            picks[c] = np.nan
        if c not in board:
            board[c] = np.nan
    board_cols = [c for c in PICK_COLUMNS if c not in ("rank", "stake", "status")] + \
                 ["why_not", "pick", "fair_mult_min", "fair_mult_max", "twoway_hold_mean", "n_books_yes", "books_yes",
                  "yes_quotes", "no_quotes", "team_b2b", "b2b"]
    for c in board_cols:
        if c not in board:
            board[c] = np.nan
    board_out = board[board_cols].sort_values(["p_cal"], ascending=False)
    board_path(date).parent.mkdir(parents=True, exist_ok=True)
    board_out.to_csv(board_path(date), index=False)
    picks[PICK_COLUMNS].to_csv(picks_path(date), index=False)
    extra = pd.DataFrame()
    if not args.no_odds and not board_px.empty:
        extra = board_px[board_px["athlete_id"].isna() | ~board_px.set_index(["game_id", "athlete_id"]).index.isin(
            board.set_index(["game_id", "athlete_id"]).index)]
        if len(extra):
            extra.to_csv(board_path(date).with_name(f"priced_unscored_{date}.csv"), index=False)
            log(f"{len(extra)} priced players without a model row (no history, fewer than 5 games, or Out) saved "
                f"to priced_unscored_{date}.csv", t0)

    text = discord_text(date, games, board, picks, margin_slate, bar, args.no_odds, credits, len(live), model_m,
                        unscored=extra)
    write_text(summary_path(date), text)
    append_run_log({"run_et": now_et().strftime("%Y-%m-%d %H:%M"), "date": date, "mode": "live" if live_mode else
                    "backfill", "games": len(games), "pending_players": len(pend), "scored": len(live),
                    "priced_fd": int(live["fd_implied"].notna().sum()) if "fd_implied" in live else 0,
                    "twoway": int((live["n_twoway"].fillna(0) >= 1).sum()) if "n_twoway" in live else 0,
                    "picks": len(picks), "margin_slate": margin_slate, "bar": bar,
                    "credits_used": credits.get("used_run"), "credits_remaining": credits.get("remaining"),
                    "unmatched_names": "; ".join(unmatched), "model_trained_at": model_m["trained_at"],
                    "seconds": round(time.time() - t0, 1)})
    print()
    print(text)
    log(f"wrote {picks_path(date).name} ({len(picks)} picks), {board_path(date).name} ({len(board_out)} rows), "
        f"{summary_path(date).name}", t0)


if __name__ == "__main__":
    main()
