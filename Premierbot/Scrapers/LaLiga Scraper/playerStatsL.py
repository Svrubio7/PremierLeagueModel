from curl_cffi import requests
import csv
from rich import print
import random
import time
from statsPerHalfL import data_ids
from matchDictsL import all_match_dict

# Reuse your existing headers.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def fetch_player_statistics(match_id: int):
    """
    Fetch player statistics for the given match ID.
    Adjust the endpoint URL if needed.
    """
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/lineups"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def process_player_data(data: dict, match_id: int, match_info: dict):
    """
    Process the JSON response from the player stats API.
    
    Iterates over both home and away players, extracts key player details
    and in-match statistics, and returns a list of player records.
    Missing or empty numeric fields are set to 0.
    """
    players_stats = []
    # Define keys that should remain as-is (identifiers or textual fields).
    non_numeric_keys = {
        "match_id", "round", "side", "teamId", "player_id",
        "player_name", "player_slug", "position", "jerseyNumber",
        "height", "country", "dateOfBirthTimestamp", "shirtNumber",
        "substitute"
    }
    
    for side in ["home", "away"]:
        if side in data:
            for entry in data[side].get("players", []):
                row = {}
                # Add match context.
                row["match_id"] = match_id
                row["round"] = match_info.get("round", "unknown")
                row["side"] = side
                row["teamId"] = entry.get("teamId")
                
                # Extract player basic info.
                player = entry.get("player", {})
                row["player_id"] = player.get("id")
                row["player_name"] = player.get("name")
                row["player_slug"] = player.get("slug")
                row["position"] = player.get("position")
                row["jerseyNumber"] = player.get("jerseyNumber")
                row["height"] = player.get("height")
                row["country"] = player.get("country", {}).get("name")
                row["dateOfBirthTimestamp"] = player.get("dateOfBirthTimestamp")
                row["marketValue"] = player.get("proposedMarketValueRaw", {}).get("value")
                
                # Additional team details.
                row["shirtNumber"] = entry.get("shirtNumber")
                row["substitute"] = entry.get("substitute")
                
                # Extract statistics.
                stats = entry.get("statistics", {})
                for stat_key, stat_value in stats.items():
                    if stat_key == "ratingVersions" and isinstance(stat_value, dict):
                        row["rating_original"] = stat_value.get("original")
                        row["rating_alternative"] = stat_value.get("alternative")
                    else:
                        row[stat_key] = stat_value
                        
                # For every key not in non_numeric_keys, if the value is None or empty, set it to 0.
                for key, value in row.items():
                    if key not in non_numeric_keys:
                        if value is None or (isinstance(value, str) and value.strip() == ""):
                            row[key] = 0

                players_stats.append(row)
    return players_stats

def write_csv(filename, rows):
    if not rows:
        print(f"No data for {filename}. Skipping CSV creation.")
        return
    keys = set()
    for row in rows:
        keys.update(row.keys())
    # Ensure key columns appear first.
    priority_cols = ["match_id", "round", "side", "teamId", "player_id", "player_name", "position"]
    ordered_keys = priority_cols + sorted(k for k in keys if k not in priority_cols)
    
    for row in rows:
        for key in ordered_keys:
            if key not in row or row[key] is None or (isinstance(row[key], str) and row[key]. strip() == ""):
                row[key] = 0
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV file '{filename}' created successfully.")

def main():
    all_players_stats = []
    match_counter = 0
    for match_id in data_ids:
        match_counter += 1
        print(f"Processing player stats for match {match_counter} (ID {match_id})...")
        try:
            data = fetch_player_statistics(match_id)
        except Exception as e:
            print(f"Error fetching player stats for match {match_id}: {e}")
            continue
        
        # Retrieve match info from your dictionary.
        mid_str = str(match_id)
        match_info = all_match_dict.get(mid_str, {})
        
        players_stats = process_player_data(data, match_id, match_info)
        all_players_stats.extend(players_stats)
        
        # Optionally, sleep a random time to avoid overloading the API.
        # sleep_time = random.uniform(1, 3)
        # print(f"Sleeping for {sleep_time:.2f} seconds...")
        # time.sleep(sleep_time)
    
    write_csv("player_statsBundesliga.csv", all_players_stats)

if __name__ == "__main__":
    main()
