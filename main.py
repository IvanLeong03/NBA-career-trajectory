import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.basketball-reference.com"
rookie_years = range(2004, 2017)
# players who played their first season in 15-16 will have player 10 seasons as of July 2025
players = []

headers = {"User-Agent": "Mozilla/5.0"}

for year in rookie_years:
    url = f"{BASE_URL}/leagues/NBA_{year}_rookies.html"
    print(f"Scraping rookies from {year}...")
    
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, 'lxml')

    table = soup.find("table", {"id": "rookies"})
    if not table:
        print(f"Table not found for {year}")
        continue


    for row in table.tbody.find_all("tr"):
        player_cell = row.find("td", {"data-stat": "player"})
        if not player_cell or not player_cell.a:
            continue  # skip rows without a real player link

        name = player_cell.text.strip()
        link = player_cell.a["href"]

        # Safe to grab these now — since you know it's a valid player
        player_age = row.find("td", {"data-stat": "age"})
        years_played = row.find("td", {"data-stat": "years"})

        players.append({
            "name": name,
            "url": BASE_URL + link,
            "rookie_year": year,
            "rookie_age": player_age.text.strip() if player_age else None,
            "years_played": years_played.text.strip() if years_played else None
        })

    time.sleep(1.5)  # Be nice to the server
    
# Save to CSV
df_players = pd.DataFrame(players)
# Convert 'years_played' to integer for filtering
df_players["years_played"] = pd.to_numeric(df_players["years_played"], errors="coerce")

# Filter for players who played at least 10 seasons
df_10yr_vets = df_players[df_players["years_played"] >= 10].copy()

# Save filtered dataset
df_10yr_vets.to_csv("data/rookie_10yr_vets_2004_2015.csv", index=False)
print(f"Saved {len(df_10yr_vets)} players with 10+ seasons.")