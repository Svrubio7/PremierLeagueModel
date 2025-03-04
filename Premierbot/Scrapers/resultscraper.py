import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import csv

base_url = "https://fbref.com"
main_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
headers = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/88.0.4324.150 Safari/537.36")
}

# Fetch the main schedule page
response = requests.get(main_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find all table rows
matches = soup.find_all("tr")
match_data = []

for match in matches:
    # Skip spacer or header rows
    row_classes = match.get("class", [])
    if "spacer" in row_classes or "partial_table_header" in row_classes:
        continue

    home_team_el = match.find("td", {"data-stat": "home_team"})
    away_team_el = match.find("td", {"data-stat": "away_team"})
    score_el = match.find("td", {"data-stat": "score"})
    
    # Only process rows that have all three elements
    if not (home_team_el and away_team_el and score_el):
        continue

    home_team = home_team_el.text.strip()
    away_team = away_team_el.text.strip()
    score = score_el.text.strip()

    match_data.append({
        "TEAM": home_team,
        "RIVAL": away_team,
        "RESULT": score
    })
    match_data.append({
        "TEAM": away_team,
        "RIVAL": home_team,
        "RESULT": score
    })
    
    # Optional small delay (not critical for a single page)
    time.sleep(random.uniform(0.5, 1.5))

# Convert the data to a DataFrame and save to CSV
df = pd.DataFrame(match_data)
csv_filename = "statspermatch_simple.csv"
df.to_csv(csv_filename, index=False)

print("\nExtracted Match Data:")
print(df)
print(f"\n✅ Data saved to {csv_filename}")

def build_results_dict(csv_path: str) -> dict:
    results = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_raw = row["TEAM"].strip()
            rival_raw = row["RIVAL"].strip()
            result = row["RESULT"].strip()
            
            # normalize team names
            team_norm = team_raw.lower().replace(" ", "-")
            rival_norm = rival_raw.lower().replace(" ", "-")
            
            results[(team_norm, rival_norm)] = result
    return results
    
