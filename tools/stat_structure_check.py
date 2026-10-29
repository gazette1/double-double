"""stat_structure_check.py: measures, from the ESPN game logs, (1) within-player correlations among points, rebounds, assists and minutes, (2) the same partial correlations controlling for minutes, (3) variance-to-mean dispersion of rebounds, assists and points, (4) realized joint double-double rates versus independence for mid-range players, (5) the home-arena assist-rate excess by season (scorekeeper effect). Regular season 2021-22 to 2025-26. All-Star rosters are excluded from the arena table. Run: python tools/stat_structure_check.py"""
import pandas as pd, numpy as np
pd.set_option("display.width", 200)
root = r"C:\Users\harri\Documents\Double Double Bot"
pb = pd.concat([pd.read_parquet(f"{root}/data/raw/hoopr/player_box_{y}.parquet") for y in range(2022, 2027)])
pb = pb.drop_duplicates(["game_id", "athlete_id"])
pb = pb[(pb["minutes"].fillna(0) > 0) & (pb.season_type == 2)].copy()
for c in ["points","rebounds","assists","minutes"]: pb[c] = pb[c].astype(float)
# player-seasons with >= 40 games and meaningful DD chance (mean reb>=6 or ast>=5) to focus on relevant players
g = pb.groupby(["season","athlete_id"])
agg = g.agg(n=("game_id","size"), pts=("points","mean"), reb=("rebounds","mean"), ast=("assists","mean"), mins=("minutes","mean"))
keep = agg[(agg.n >= 40) & ((agg.reb >= 6) | (agg.ast >= 5))].index
d = pb.set_index(["season","athlete_id"]).loc[keep].reset_index()
print("player-seasons kept:", len(keep), "rows:", len(d))
# 1) within-player raw correlations (demean per player-season)
for c in ["points","rebounds","assists","minutes"]:
    d[c+"_dm"] = d[c] - d.groupby(["season","athlete_id"])[c].transform("mean")
print("\nWithin-player raw correlations (demeaned):")
print(d[["points_dm","rebounds_dm","assists_dm","minutes_dm"]].corr().round(3).to_string())
# 2) partial correlations given minutes: residualize each stat on minutes within player-season
def resid(group, c):
    x = group["minutes"].values; y = group[c].values
    if np.std(x) < 1e-9: return y - y.mean()
    b = np.cov(x, y, bias=True)[0,1] / np.var(x); a = y.mean() - b * x.mean()
    return y - (a + b * x)
for c in ["points","rebounds","assists"]:
    d[c+"_res"] = d.groupby(["season","athlete_id"], group_keys=False).apply(lambda gr: pd.Series(resid(gr, c), index=gr.index))
print("\nPartial correlations controlling for minutes (within player-season):")
print(d[["points_res","rebounds_res","assists_res"]].corr().round(3).to_string())
# 3) dispersion: variance / mean for rebounds and assists per player-season (Poisson = 1)
disp = d.groupby(["season","athlete_id"]).agg(reb_var=("rebounds","var"), reb_mean=("rebounds","mean"), ast_var=("assists","var"), ast_mean=("assists","mean"), pts_var=("points","var"), pts_mean=("points","mean"))
disp["reb_vmr"] = disp.reb_var/disp.reb_mean; disp["ast_vmr"] = disp.ast_var/disp.ast_mean; disp["pts_vmr"] = disp.pts_var/disp.pts_mean
print("\nVariance-to-mean ratio (median across player-seasons): reb %.2f, ast %.2f, pts %.2f" % (disp.reb_vmr.median(), disp.ast_vmr.median(), disp.pts_vmr.median()))
print("Share of player-seasons with reb VMR > 1.2: %.2f, ast: %.2f" % ((disp.reb_vmr>1.2).mean(), (disp.ast_vmr>1.2).mean()))
# 4) independence check for the DD event: compare realized P(pts>=10 & reb>=10) vs product of marginals, by player-season
d["p10"] = d.points>=10; d["r10"] = d.rebounds>=10; d["a10"] = d.assists>=10
ps = d.groupby(["season","athlete_id"]).agg(p=("p10","mean"), r=("r10","mean"), a=("a10","mean"), pr=("p10", lambda s: (s & d.loc[s.index,"r10"]).mean()), pa=("p10", lambda s: (s & d.loc[s.index,"a10"]).mean()), n=("p10","size"))
ps["pr_indep"] = ps.p*ps.r; ps["pa_indep"] = ps.p*ps.a
mid = ps[(ps.r.between(0.25,0.75)) & (ps.p.between(0.25,0.95))]
print("\nPoints+rebounds DD: player-seasons with mid-range rates n=%d | realized joint mean %.3f vs independence %.3f (ratio %.3f)" % (len(mid), mid.pr.mean(), mid.pr_indep.mean(), mid.pr.mean()/mid.pr_indep.mean()))
mida = ps[(ps.a.between(0.25,0.75)) & (ps.p.between(0.25,0.95))]
print("Points+assists DD: player-seasons with mid-range rates n=%d | realized joint mean %.3f vs independence %.3f (ratio %.3f)" % (len(mida), mida.pa.mean(), mida.pa_indep.mean(), mida.pa.mean()/mida.pa_indep.mean()))
# 5) arena scorekeeper assist effect: team assist rate (AST/FGM) at each arena minus that team's own road rate elsewhere
tb = pd.concat([pd.read_parquet(f"{root}/data/raw/hoopr/team_box_{y}.parquet") for y in range(2022, 2027)])
tb = tb[tb.season_type == 2].drop_duplicates(["game_id","team_id"]).copy()
tb["ast_rate"] = tb.assists / tb.field_goals_made
sched = pd.concat([pd.read_parquet(f"{root}/data/raw/hoopr/schedule_{y}.parquet")[["id","home_id","neutral_site"]] for y in range(2022, 2027)]).drop_duplicates("id")
sched["id"] = sched["id"].astype(int)
tb = tb.merge(sched.rename(columns={"id":"game_id","home_id":"arena_team"}), on="game_id", how="left")
tb = tb[(tb.neutral_site != True) & (~tb.team_abbreviation.isin(["STARS","STRIPES","CHK","SHQ","LEB","GIA","KEN","CAN","OGG","RIS","SHA","WLD","USA","LBN","CND"]))]
road = tb[tb.team_home_away == "away"].groupby(["season","team_id"]).ast_rate.mean().rename("road_rate")
tb = tb.merge(road, on=["season","team_id"], how="left")
tb["excess"] = tb.ast_rate - tb.road_rate
arena = tb.groupby(["season","arena_team"]).excess.mean().unstack(0)
arena.index = arena.index.map(dict(zip(tb.arena_team, tb.team_abbreviation.where(tb.team_home_away=="home"))).get)
print("\nArena assist-rate excess (AST/FGM at arena minus teams' own road rate), by season:")
print(arena.round(3).sort_values(2026, ascending=False).to_string())
print("\nYear-over-year correlation of arena effects:"); print(arena.corr().round(2).to_string())
print("Arena effect in assists per game at league ~ 42 FGM: top %.2f, bottom %.2f (2025-26)" % (arena[2026].max()*42, arena[2026].min()*42))
