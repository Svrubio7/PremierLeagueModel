from curl_cffi import requests
import csv
from rich import print
import random
import time
from statsperhalf import data_ids
from matchdicts import all_match_dict
from resultscraper import build_results_dict

# Load the results CSV into a dictionary. 
# (Assumes build_results_dict returns keys as tuples (team, opponent) in lowercase.)
results_dict = build_results_dict("statspermatch_simple.csv")

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
    """Extract statistics for the given period."""
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

def add_results(rows):
    match_counts = {}
    unmatched = []
    print("results_dict keys:", list(results_dict.keys()))
    
    for row in rows:
        team = row["team"]
        opponent = row["opponent"]
        key_forward = (team, opponent)
        key_reverse = (opponent, team)
        
        print(f"Trying: {key_forward}")
        
        if key_forward not in match_counts:
            match_counts[key_forward] = 0
        if key_reverse not in match_counts:
            match_counts[key_reverse] = 0
        
        if key_forward in results_dict:
            match_index = match_counts[key_forward]
            if match_index < len(results_dict[key_forward]):
                match_data = results_dict[key_forward][match_index]
                row["RESULT"] = match_data["result"]
                row["REFEREE"] = match_data["referee"]
                match_counts[key_forward] += 1
                print(f"Matched {key_forward}: {match_data}")
            else:
                row["RESULT"] = "N/A (No more matches)"
                row["REFEREE"] = "N/A"
                unmatched.append((team, opponent, row["match_id"], "forward"))
        elif key_reverse in results_dict:
            match_index = match_counts[key_reverse]
            if match_index < len(results_dict[key_reverse]):
                match_data = results_dict[key_reverse][match_index]
                row["RESULT"] = match_data["result"]
                row["REFEREE"] = match_data["referee"]
                match_counts[key_reverse] += 1
                print(f"Matched {key_reverse}: {match_data}")
            else:
                row["RESULT"] = "N/A (No more matches)"
                row["REFEREE"] = "N/A"
                unmatched.append((team, opponent, row["match_id"], "reverse"))
        else:
            row["RESULT"] = "N/A (Not found)"
            row["REFEREE"] = "N/A"
            unmatched.append((team, opponent, row["match_id"], "not found"))
    
    if unmatched:
        print(f"Warning: {len(unmatched)} matches not matched:")
        for team, opp, mid, reason in unmatched[:5]:
            print(f"  - {team} vs {opp} (match_id: {mid}, reason: {reason})")
            
            
def write_csv(filename, rows):
    if not rows:
        print(f"No data for {filename}. Skipping CSV creation.")
        return
    keys = set()
    for row in rows:
        keys.update(row.keys())
    # Ensure these columns appear first.
    priority_cols = ["match_number", "match_id", "team", "opponent", "RESULT"]
    ordered_keys = priority_cols + sorted(k for k in keys if k not in priority_cols)
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV file '{filename}' created successfully.")

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

        # Retrieve canonical team names from all_match_dict.
        mid_str = str(match_id)
        if mid_str in all_match_dict:
            actual_home = all_match_dict[mid_str]["home"]
            actual_away = all_match_dict[mid_str]["away"]
        else:
            actual_home = "unknown-home"
            actual_away = "unknown-away"

        for period in periods:
            home_stats, away_stats = process_period(data, period)
            if not (home_stats or away_stats):
                print(f"No data for period '{period}' in match {match_id}.")
                continue

            # Build two rows: one for the home side and one for the away side.
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
        
        '''sleep_time = random.uniform(2, 4)
        print(f"Sleeping for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)'''
    
    # Merge results (final score) into each row using the canonical ordering.
    add_results(stats_all)
    add_results(stats_1st)
    add_results(stats_2nd)  # Note: careful with variable names (2ND vs. 2nd)

    write_csv("matches_ALL.csv", stats_all)
    write_csv("matches_1ST.csv", stats_1st)
    write_csv("matches_2ND.csv", stats_2nd)

if __name__ == "__main__":
    main()
