import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import random

# Load player list
df_players = pd.read_csv("data/rookie_10yr_vets_2004_2015.csv")
# df_players = df_players.iloc[:3]  
# Limit for testing 

headers = {"User-Agent": "Mozilla/5.0"}
output = []

BASE_STATS = ["pts_per_g", "ast_per_g", "trb_per_g", "stl_per_g", "blk_per_g", "mp_per_g", "games_started"]
ADV_STATS = ["per", "ts_pct", "usg_pct", "ws", "bpm"]  # Add more if desired

def extract_table(soup, table_id):
    # Some tables are inside HTML comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        if table_id in c:
            table_soup = BeautifulSoup(c, 'lxml')
            return table_soup.find("table", {"id": table_id})
    # Fallback if not in comment
    return soup.find("table", {"id": table_id})

# Begin scraping
for i, row in df_players.iterrows():
    name = row['name']
    url = row['url']
    rookie_year = row['rookie_year']
    rookie_age = row['rookie_age']
    print(f"[{i+1}/{len(df_players)}] {name} - checking profile...")

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "lxml")

        # Extract per-game table
        per_game_table = extract_table(soup, "per_game_stats")
        if not per_game_table:
            print(f"Skipping {name} (no per_game_stats table)")
            continue

        # Extract advanced stats table
        adv_table = extract_table(soup, "advanced")
        if not adv_table:
            print(f"Skipping {name} (no advanced table)")
            continue

        # Map season_str to per-game row
        per_game_rows = {}
        for r in per_game_table.tbody.find_all("tr"):
            th = r.find("th")
            if not th:
                continue
            season_str = th.text.strip()
            if "-" in season_str and season_str not in per_game_rows:
                per_game_rows[season_str] = r

        # Map season_str to advanced row
        adv_stats_rows = {}
        for r in adv_table.tbody.find_all("tr"):
            th = r.find("th")
            if not th:
                continue
            season_str = th.text.strip()
            if "-" in season_str and season_str not in adv_stats_rows:
                adv_stats_rows[season_str] = r

        # Use only overlapping seasons
        shared_seasons = sorted(list(set(per_game_rows.keys()) & set(adv_stats_rows.keys())))[:10]
        #print(f"{name} - using {len(shared_seasons)} seasons: {shared_seasons}")

        player_data = {"name": name, "rookie_year": rookie_year, "rookie_age": rookie_age}

        for season_idx, season in enumerate(shared_seasons):
            season_num = season_idx + 1
            tr = per_game_rows[season]
            adv_tr = adv_stats_rows[season]

            # Per-game stats
            for stat in BASE_STATS:
                td = tr.find("td", {"data-stat": stat})
                key = f"Y{season_num}_{stat}"
                player_data[key] = float(td.text) if td and td.text.strip() != '' else None

            # Advanced stats
            for stat in ADV_STATS:
                td = adv_tr.find("td", {"data-stat": stat})
                key = f"Y{season_num}_{stat}"
                player_data[key] = float(td.text) if td and td.text.strip() != '' else None

        output.append(player_data)
        time.sleep(random.uniform(5.0, 8.0))

    except Exception as e:
        print(f"Error with {name}: {e}")
        continue

# Save to CSV
df_output = pd.DataFrame(output)
df_output.to_csv("data/player_10yr_stats.csv", index=False)
print(f"\nDone. Saved {len(df_output)} players with 10 seasons.")
