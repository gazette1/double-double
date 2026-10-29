"""
common.py: shared paths, loading, target, and helper functions for the v1 double-double pipeline.

Season key = season END year (2025 = 2024-25). Raw ESPN box scores live in data/raw/hoopr/ and are
treated as data only. Used by tools/build_dataset.py and tools/train_eval.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "hoopr"
FEATURES_DIR = ROOT / "data" / "features"
DATASET_PATH = FEATURES_DIR / "dataset_v1.parquet"
FEATURE_LIST_PATH = FEATURES_DIR / "dataset_v1_features.json"
MODELS_DIR = ROOT / "data" / "models" / "v1"
EVAL_DIR = ROOT / "data" / "eval" / "v1"
DOCS_DIR = ROOT / "docs"

SEASONS = list(range(2018, 2028))
TEST_SEASONS = [2023, 2024, 2025, 2026]
SEED = 42
NBA_TEAM_IDS = set(range(1, 31))  # ESPN ids of the 30 franchises; All-Star and Rising Stars teams use other ids
MIN_PRIOR_GAMES = 5

PLAYER_COLS = [
    "game_id", "season", "season_type", "game_date", "game_date_time", "athlete_id",
    "athlete_display_name", "athlete_position_abbreviation", "team_id", "team_abbreviation",
    "opponent_team_id", "home_away", "minutes", "points", "rebounds", "offensive_rebounds",
    "defensive_rebounds", "assists", "steals", "blocks", "turnovers", "fouls",
    "field_goals_attempted", "free_throws_attempted", "starter", "did_not_play", "reason",
    "team_score", "opponent_team_score",
]
TEAM_COLS = [
    "game_id", "season", "season_type", "game_date", "game_date_time", "team_id",
    "team_abbreviation", "team_home_away", "opponent_team_id", "team_score", "opponent_team_score",
    "field_goals_attempted", "free_throws_attempted", "offensive_rebounds", "defensive_rebounds",
    "assists", "turnovers",
]
DD_STATS = ["points", "rebounds", "assists", "steals", "blocks"]


def load_raw(kind, cols, seasons=SEASONS):
    """Concatenate one raw hoopR file type across seasons, keeping only `cols`."""
    frames = []
    for y in seasons:
        path = RAW / f"{kind}_{y}.parquet"
        frames.append(pd.read_parquet(path, columns=cols))
    df = pd.concat(frames, ignore_index=True)
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def load_player_box(seasons=SEASONS):
    return load_raw("player_box", PLAYER_COLS, seasons)


def load_team_box(seasons=SEASONS):
    return load_raw("team_box", TEAM_COLS, seasons)


def add_targets(df):
    """dd = at least two of points, rebounds, assists, steals, blocks >= 10; td = at least three."""
    tens = (df[DD_STATS] >= 10).sum(axis=1)
    df["dd"] = (tens >= 2).astype(np.int8)
    df["td"] = (tens >= 3).astype(np.int8)
    return df


def exhibition_mask(df, team_col="team_id", opp_col="opponent_team_id"):
    """True for All-Star, Rising Stars, and other games involving a non-franchise team id."""
    return ~df[team_col].isin(NBA_TEAM_IDS) | ~df[opp_col].isin(NBA_TEAM_IDS)


def drop_alias_duplicates(pb):
    """Remove second ESPN athlete ids: rows of one game and team sharing a display name.

    Keeps the row with the most minutes, then the athlete_id with more rows overall. In the raw files
    this affects 36 (game, team, name) groups, mostly 2018-19 (Isaiah Canaan and Corey Brewer listed
    twice with identical stat lines).
    """
    key = ["game_id", "team_id", "athlete_display_name"]
    dup = pb.duplicated(key, keep=False)
    if not dup.any():
        return pb, 0
    n_rows = pb.groupby("athlete_id")["game_id"].transform("size")
    order = pb.assign(_m=pb["minutes"].fillna(-1.0), _n=n_rows)
    order = order.sort_values(key + ["_m", "_n", "athlete_id"], ascending=[True, True, True, False, False, True])
    keep_idx = order.drop_duplicates(key, keep="first").index
    out = pb.loc[pb.index.isin(keep_idx)]
    return out, int(len(pb) - len(out))


def same_date_conflict_games(rows):
    """Game ids to drop when a team has more than one game on the same date.

    Keeps the game with the latest tip time for that team and date. In the raw files this
    affects one 2019-20 game with a corrupted timestamp.
    """
    tg = rows[["game_id", "team_id", "game_date", "game_date_time"]].drop_duplicates(["game_id", "team_id"])
    tg = tg.sort_values(["team_id", "game_date", "game_date_time", "game_id"])
    dup = tg.duplicated(["team_id", "game_date"], keep="last")
    return set(tg.loc[dup, "game_id"].tolist())


def within_group_index(keys):
    """0-based position of each row inside its group; rows must already be sorted by group then time."""
    keys = np.asarray(keys)
    n = len(keys)
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    start = np.r_[True, keys[1:] != keys[:-1]]
    group_start_pos = np.maximum.accumulate(np.where(start, np.arange(n), 0))
    return np.arange(n) - group_start_pos


def prior_cumsum(values, keys):
    """Exclusive cumulative sum inside groups (sum of all earlier rows of the same group).

    values: (n, m) float array, rows sorted by group then time, no NaN.
    keys: (n,) group labels aligned with values.
    """
    values = np.asarray(values, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    if np.isnan(values).any():
        raise ValueError("prior_cumsum expects no NaN values")
    keys = np.asarray(keys)
    total = np.cumsum(values, axis=0)
    excl = total - values  # sum of all earlier rows, ignoring groups
    start = np.r_[True, keys[1:] != keys[:-1]]
    # subtract the running total at each group's first row so sums restart per group
    offset = np.where(start[:, None], excl, np.nan)
    offset = pd.DataFrame(offset).ffill().to_numpy()
    return excl - offset


def window_from_prior(prior, k, n_window):
    """Sums over the last n_window earlier rows of the same group, plus the count of those rows.

    prior: exclusive within-group cumsums (n, m). k: within-group index (number of earlier rows).
    """
    s = prior.copy()
    idx = np.nonzero(k >= n_window)[0]
    s[idx] -= prior[idx - n_window]
    cnt = np.minimum(k, n_window).astype(np.float64)
    return s, cnt


def window_sums_nan(values, keys, k, n_window):
    """Window sums and per-column counts over the last n_window earlier rows, skipping NaN values.

    n_window=None gives the full exclusive history of the group (used for season to date).
    """
    values = np.asarray(values, dtype=np.float64)
    valid = ~np.isnan(values)
    P = prior_cumsum(np.where(valid, values, 0.0), keys)
    C = prior_cumsum(valid.astype(np.float64), keys)
    if n_window is None:
        return P, C
    S, _ = window_from_prior(P, k, n_window)
    N, _ = window_from_prior(C, k, n_window)
    return S, N


def safe_div(num, den):
    num = np.asarray(num, dtype=np.float64)
    den = np.asarray(den, dtype=np.float64)
    out = np.full(np.broadcast(num, den).shape, np.nan)
    np.divide(num, den, out=out, where=den > 0)
    return out


def american_odds(p):
    """Break-even American price for win probability p (negative when p >= 0.5)."""
    p = np.asarray(p, dtype=np.float64)
    out = np.full(p.shape, np.nan)
    fav = (p >= 0.5) & (p < 1)
    dog = (p > 0) & (p < 0.5)
    out[fav] = -100.0 * p[fav] / (1 - p[fav])
    out[dog] = 100.0 * (1 - p[dog]) / p[dog]
    return out


def fmt_value(v, digits=4):
    if v is None:
        return ""
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return ""
        if float(v).is_integer() and abs(v) >= 1000:
            return f"{int(v)}"
        return f"{v:.{digits}f}"
    return str(v)


def to_markdown(df, digits=4, digits_map=None):
    """Plain markdown table without extra dependencies; formats each column by its dtype."""
    digits_map = digits_map or {}
    cols = list(df.columns)
    cells = {}
    for c in cols:
        s = df[c]
        d = digits_map.get(c, digits)
        if pd.api.types.is_bool_dtype(s):
            cells[c] = [str(bool(v)) for v in s]
        elif pd.api.types.is_integer_dtype(s):
            cells[c] = [str(int(v)) for v in s]
        elif pd.api.types.is_float_dtype(s):
            cells[c] = ["" if pd.isna(v) else f"{v:.{d}f}" for v in s]
        else:
            cells[c] = [fmt_value(v, d) for v in s]
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for i in range(len(df)):
        lines.append("| " + " | ".join(cells[c][i] for c in cols) + " |")
    return "\n".join(lines)
