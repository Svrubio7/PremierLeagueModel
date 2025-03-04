from bs4 import BeautifulSoup
from curl_cffi import requests
import csv
from rich import print
import random
import time

# 1. Extract match IDs from the 26 HTML files
data_ids = []
for i in range(1, 28):
    file_path = f"/Users/jd/Documents/PremierLeagueModel/PremierLeagueModel/htmlscripts/Dataids/round{i}.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        soup = BeautifulSoup(content, "html.parser")
        # Extract elements that have a "data-id" attribute.
        for element in soup.find_all(attrs={"data-id": True}):
            data_ids.append(element["data-id"])

print("Extracted data_ids:")
print(data_ids)

# 2. Import your merged team dictionary and build the results dictionary.
from matchdicts import all_match_dict            # all_match_dict: {match_id: {"home": team1, "away": team2}, ...}
from resultscraper import build_results_dict       # build_results_dict(csv_path) returns {(team, opponent): result, ...}

results_dict = build_results_dict("statspermatch_simple.csv")
# results_dict keys should be tuples like ("man-utd", "fulham") in lowercase.

# 3. Define headers for API requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def fetch_match_statistics(match_id: int):
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/statistics"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def process_period(data: dict, period_label: str):
    """
    Extract statistics for a given period (e.g., "ALL", "1ST", "2ND")
    from the JSON data. Returns two dictionaries: one for the home side,
    and one for the away side.
    """
    home_stats = {}
    away_stats = {}
    for period in data.get("statistics", []):
        if period.get("period") == period_label:
            for group in period.get("groups", []):
                for item in group.get("statisticsItems", []):
                    stat_name = item.get("name", "")
                    home_stats[stat_name] = item.get("home", "")
                    away_stats[stat_name] = item.get("away", "")
    return home_stats, away_stats

def main():
    stats_all = []
    stats_1st = []
    stats_2nd = []
    periods = ["ALL", "1ST", "2ND"]
    match_counter = 0

    for match_id in data_ids:
        match_counter += 1
        print(f"Processing match {match_counter} (ID {match_id})...")
        try:
            data = fetch_match_statistics(match_id)
        except Exception as e:
            print(f"Error fetching match {match_id}: {e}")
            continue

        # Lookup the actual team names using the merged dictionary.
        mid_str = str(match_id)
        if mid_str in all_match_dict:
            actual_home = all_match_dict[mid_str]["home"]  # e.g. "man-utd"
            actual_away = all_match_dict[mid_str]["away"]  # e.g. "fulham"
        else:
            actual_home = "unknown-home"
            actual_away = "unknown-away"

        # For each period, extract the statistics and create two rows (one for each side).
        for period in periods:
            home_stats, away_stats = process_period(data, period)
            if not (home_stats or away_stats):
                print(f"No data for period '{period}' in match {match_id}.")
                continue

            row_home = {
                "match_number": match_counter,
                "match_id": match_id,
                "team": actual_home,
                "opponent": actual_away
            }
            row_home.update(home_stats)

            row_away = {
                "match_number": match_counter,
                "match_id": match_id,
                "team": actual_away,
                "opponent": actual_home
            }
            row_away.update(away_stats)

            if period == "ALL":
                stats_all.extend([row_home, row_away])
            elif period == "1ST":
                stats_1st.extend([row_home, row_away])
            elif period == "2ND":
                stats_2nd.extend([row_home, row_away])
        
        sleep_time = random.uniform(2, 5)
        print(f"Sleeping for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)
    
    # Add the final match result (score) to each row.
    def add_results(rows):
        for row in rows:
            team = row["team"].lower()
            opponent = row["opponent"].lower()
            key_forward = (team, opponent)
            key_reverse = (opponent, team)
            if key_forward in results_dict:
                row["RESULT"] = results_dict[key_forward]
            elif key_reverse in results_dict:
                row["RESULT"] = results_dict[key_reverse]
            else:
                row["RESULT"] = ""
    
    add_results(stats_all)
    add_results(stats_1st)
    add_results(stats_2nd)
    
    # Write CSV files with the desired order of columns.
    def write_csv(filename, rows):
        if not rows:
            print(f"No data for {filename}. Skipping CSV creation.")
            return
        keys = set()
        for row in rows:
            keys.update(row.keys())
        # Priority columns appear first.
        priority_cols = ["match_number", "match_id", "team", "opponent", "RESULT"]
        ordered_keys = priority_cols + sorted(k for k in keys if k not in priority_cols)
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered_keys)
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV file '{filename}' created successfully.")
    
    write_csv("matches_ALL.csv", stats_all)
    write_csv("matches_1ST.csv", stats_1st)
    write_csv("matches_2ND.csv", stats_2nd)

if __name__ == "__main__":
    main()
