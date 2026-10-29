"""market_check.py: compare the latest logged FanDuel double-double prices with each player's realized double-double rates (last season, this season, last 10 games) and print league-wide double-doubles per night. Reads data/odds/dd_prices.csv and data/raw/hoopr. Run: python tools/market_check.py"""
import pandas as pd, numpy as np, requests
pd.set_option("display.width", 200)
root = r"C:\Users\harri\Documents\Double Double Bot"
pb = pd.concat([pd.read_parquet(f"{root}/data/raw/hoopr/player_box_{y}.parquet") for y in (2025, 2026, 2027)])
pb = pb.drop_duplicates(["game_id", "athlete_id"])
pb = pb[pb["minutes"].fillna(0) > 0].copy()
stats = ["points", "rebounds", "assists", "steals", "blocks"]
pb["dd"] = ((pb[stats] >= 10).sum(axis=1) >= 2).astype(int)
pb = pb.sort_values(["game_date_time", "game_id"])
# league-wide DDs per night (regular season 2025-26)
reg = pb[(pb.season == 2026) & (pb.season_type == 2)]
per_night = reg.groupby("game_date").agg(games=("game_id", "nunique"), dds=("dd", "sum"), players=("athlete_id", "size"))
print("2025-26 regular season: nights", len(per_night), "| DDs per night mean %.1f | DDs per game %.2f | DD rate among played %.3f" % (per_night.dds.mean(), (per_night.dds/per_night.games).mean(), reg.dd.mean()))
print("DDs per night by slate size:"); print(per_night.groupby(pd.cut(per_night.games, [0,3,6,9,12,16]), observed=False).dds.agg(["count","mean"]).round(1).to_string())
# concentration: how many DDs by the top players
pc = reg.groupby("athlete_display_name").dd.agg(["sum","count","mean"]).sort_values("sum", ascending=False)
print("\nTop 15 DD producers 2025-26 (count, games, rate):"); print(pc.head(15).round(3).to_string())
print("share of all DDs from top 10 players: %.1f%%, top 30: %.1f%%" % (100*pc["sum"].head(10).sum()/pc["sum"].sum(), 100*pc["sum"].head(30).sum()/pc["sum"].sum()))
# tonight's FanDuel prices vs history
px = pd.read_csv(f"{root}/data/odds/dd_prices.csv")
fd = px[px.book == "fanduel"].copy()
dk = px[px.book == "draftkings"][["player","price","implied"]].rename(columns={"price":"dk_price","implied":"dk_implied"})
def hist(name):
    d = pb[pb.athlete_display_name == name]
    if d.empty: return pd.Series({"g_2526": 0, "dd_2526": np.nan, "g_2627": 0, "dd_2627": np.nan, "dd_last10": np.nan, "min_last10": np.nan, "reb_l10": np.nan, "ast_l10": np.nan, "pts_l10": np.nan})
    s1 = d[d.season == 2026]; s2 = d[d.season == 2027]; l10 = d.tail(10)
    return pd.Series({"g_2526": len(s1), "dd_2526": s1.dd.mean() if len(s1) else np.nan, "g_2627": len(s2), "dd_2627": s2.dd.mean() if len(s2) else np.nan,
                      "dd_last10": l10.dd.mean(), "min_last10": l10.minutes.mean(), "reb_l10": l10.rebounds.mean(), "ast_l10": l10.assists.mean(), "pts_l10": l10.points.mean()})
h = fd.player.apply(hist)
out = pd.concat([fd[["player","price","implied"]].reset_index(drop=True), h.reset_index(drop=True)], axis=1).merge(dk, on="player", how="left")
out["edge_vs_l10"] = out.dd_last10 - out.implied
print("\nTonight FanDuel Yes prices vs history (implied = FD implied prob; dd_* = realized DD rates):")
print(out.sort_values("implied", ascending=False).round(3).to_string(index=False))
# ESPN scoreboard with explicit date
r = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard", params={"dates": "20261029"}, timeout=30)
print("\nESPN scoreboard 2026-10-29:", [e["shortName"] for e in r.json().get("events", [])])
