import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import os
import random

df_players = pd.read_csv("data/rookie_10yr_vets_2006_2015.csv")
df_players = df_players.iloc[:3]  # Limit for testing

headers = {"User-Agent": "Mozilla/5.0"}
output = []

def extract_table(soup, table_id):
    # Some tables are inside HTML comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        if table_id in c:
            table_soup = BeautifulSoup(c, 'lxml')
            return table_soup.find("table", {"id": table_id})
    # Fallback if not in comment
    return soup.find("table", {"id": table_id})

for i, row in df_players.iterrows():
    name = row['name']
    url = row['url']
    rookie_year = row['rookie_year']
    rookie_age = row['rookie_age']
    print(f"[{i+1}/{len(df_players)}] {name} - checking profile...")

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "lxml")
        
        # Try to find "Experience: X years" in the sidebar
        info_box = soup.find("div", {"id": "meta"})
        exp_text = info_box.get_text() if info_box else ""
        
        exp_years = None
        for line in exp_text.splitlines():
            if "Experience:" in line or "Career Length:" in line:
                try:
                    exp_years = int(line.strip().split(":")[1].strip().split()[0])
                    break
                except:
                    pass

        # extract per game stats            
        per_game_table = extract_table(soup, "per_game_stats")
        if not per_game_table:
            print(f"Skipping {name} (no per_game_stats table)")
            continue

        rows = per_game_table.tbody.find_all("tr")
                
        seen_years = set()
        unique_rows = []

        for r in rows:
            th = r.find("th")
            if not th:
                continue
            season_str = th.text.strip()
            if len(season_str) < 4:
                continue
            season_year = season_str[:4]  # e.g., '2018' from '2018-19'

            if season_year not in seen_years:
                seen_years.add(season_year)
                unique_rows.append(r)    
                
        valid_rows = unique_rows[:10]
        
        player_data = {"name": name, "rookie_year": rookie_year, "rookie_age": rookie_age}
        for season_idx, tr in enumerate(valid_rows[:10]):  # Only first 10 seasons
            season_num = season_idx + 1
            for stat in ["pts_per_g", "ast_per_g", "trb_per_g", "stl_per_g", "blk_per_g", "mp_per_g"]:
                td = tr.find("td", {"data-stat": stat})
                key = f"Y{season_num}_{stat}"
                player_data[key] = float(td.text) if td and td.text.strip() != '' else None
        output.append(player_data)

        time.sleep(random.uniform(5.5, 8.5))

    except Exception as e:
        print(f"Error with {name}: {e}")
        continue

# Save structured data
df_output = pd.DataFrame(output)
df_output.to_csv("data/player_10yr_stats.csv", index=False)
print(f"\nDone. Saved {len(df_output)} players with 10 seasons.")
