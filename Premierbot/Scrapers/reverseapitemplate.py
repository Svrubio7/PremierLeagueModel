from curl_cffi import requests
import csv
from rich import print
import random
import time
from statsperhalf import data_ids

from matchdicts import all_match_dict

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def new_session():
    session = requests.Session(impersonate_chrome=True)
    return session

def fetch_match_statistics(match_id: int):
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/statistics"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def process_period(data: dict, period_label: str):
    """
    Extracts statistics for a given period (e.g., "ALL", "1ST", "2ND")
    from the JSON data. Returns two dictionaries: one for the Home team and
    one for the Away team, mapping statistic names to their values.
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
        
        # For each period, extract statistics if available
        for period in periods:
            home_stats, away_stats = process_period(data, period)
            if not (home_stats or away_stats):
                print(f"No data for period '{period}' in match {match_id}.")
                continue
            
            # Build rows with the counter, match id, and "team" set to "Home"/"Away"
            row_home = {"match_number": match_counter, "match_id": match_id, "team": "Home"}
            row_home.update(home_stats)
            row_away = {"match_number": match_counter, "match_id": match_id, "team": "Away"}
            row_away.update(away_stats)
            
            if period == "ALL":
                stats_all.extend([row_home, row_away])
            elif period == "1ST":
                stats_1st.extend([row_home, row_away])
            elif period == "2ND":
                stats_2nd.extend([row_home, row_away])
        
        # Sleep a random interval
        sleep_time = random.uniform(2, 5)
        print(f"Sleeping for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)
    
    # ### NEW ###
    # Function to replace "Home"/"Away" with actual team names
    def replace_teams(rows):
        for row in rows:
            # Convert the match_id to string for dictionary lookup
            mid_str = str(row["match_id"])
            if mid_str in all_match_dict:
                if row["team"] == "Home":
                    row["team"] = all_match_dict[mid_str]["home"]
                elif row["team"] == "Away":
                    row["team"] = all_match_dict[mid_str]["away"]
    
    # ### NEW ###
    # Replace "Home"/"Away" in all three lists
    replace_teams(stats_all)
    replace_teams(stats_1st)
    replace_teams(stats_2nd)
    
    def write_csv(filename, rows):
        if not rows:
            print(f"No data for {filename}. Skipping CSV creation.")
            return
        # Collect all keys from all rows
        keys = set()
        for row in rows:
            keys.update(row.keys())
        # "match_number", "match_id", "team" come first
        ordered_keys = ["match_number", "match_id", "team"] + sorted(k for k in keys if k not in ["match_number", "match_id", "team"])
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered_keys)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"CSV file '{filename}' created successfully.")
    
    # Write the final CSVs
    write_csv("matches_ALL.csv", stats_all)
    write_csv("matches_1ST.csv", stats_1st)
    write_csv("matches_2ND.csv", stats_2nd)

if __name__ == "__main__":
    main()
