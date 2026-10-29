"""Check availability of public static NBA datasets (plain requests, default headers)."""
import requests, time, io, sys
def head(label, url):
    t=time.time()
    try:
        r = requests.head(url, allow_redirects=True, timeout=30)
        print(f"{label}: {r.status_code} len={r.headers.get('Content-Length')} {time.time()-t:.1f}s -> {r.url[:90]}")
        return r.status_code
    except Exception as e:
        print(f"{label}: FAIL {type(e).__name__}"); return None
REL = "https://github.com/sportsdataverse/hoopR-nba-data/releases/download"
for kind, name in [("nba_player_box","player_box_2025.parquet"), ("nba_team_box","team_box_2025.parquet"),
                   ("nba_schedules","nba_schedule_2025.parquet"), ("nba_player_box","player_box_2026.parquet"),
                   ("nba_player_box","player_box_2027.parquet")]:
    head(f"hoopR {kind}/{name}", f"{REL}/{kind}/{name}")
head("hoopR raw repo parquet", "https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/main/nba/player_box/parquet/player_box_2025.parquet")
head("cdn schedule", "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json")
head("cdn boxscore 2024-25 g1", "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022400061.json")
# download one player_box file to inspect schema
t=time.time()
r = requests.get(f"{REL}/nba_player_box/player_box_2025.parquet", timeout=120)
print("GET player_box_2025:", r.status_code, len(r.content), "bytes", f"{time.time()-t:.1f}s")
if r.status_code == 200:
    open("data/raw/hoopr/player_box_2025.parquet","wb").write(r.content)
    import pandas as pd
    df = pd.read_parquet("data/raw/hoopr/player_box_2025.parquet")
    print("shape", df.shape); print("cols", list(df.columns))
    print(df[["game_date","season_type","athlete_display_name","team_abbreviation","minutes","points","rebounds","assists","starter","did_not_play"]].head(8).to_string())
    print("season_type counts", df["season_type"].value_counts().to_dict())
    print("date range", df["game_date"].min(), df["game_date"].max())
