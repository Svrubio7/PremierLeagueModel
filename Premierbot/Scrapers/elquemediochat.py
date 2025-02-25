import time
import random
import requests
from bs4 import BeautifulSoup

# The base URL of the Premier League page on Sofascore
BASE_URL = "https://www.sofascore.com/tournament/football/england/premier-league/17#id:61627,tab:matches"

# Custom headers to look more like a normal browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/108.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

def get_all_match_ids():
    """
    Fetches the main league page, finds each 'round' container, and extracts
    the match IDs from the data-id attributes. Returns a list of match IDs.
    """
    all_match_ids = []
    
    # 1. Request the league page
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to load page. Status code: {response.status_code}")
        return all_match_ids
    
    # 2. Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Find each round container
    #    Adjust the class or selector below to match the actual HTML structure.
    #    For example, if "round-header" is the class for each round label:
    round_containers = soup.find_all("div", class_="round-header")
    
    for round_div in round_containers:
        # The match listings might be in a sibling or child container.
        # For example, if the matches are in the next sibling:
        matches_container = round_div.find_next_sibling("div")
        if not matches_container:
            continue
        
        # 4. Within the matches container, find elements with data-id
        match_divs = matches_container.find_all("div", attrs={"data-id": True})
        for match_div in match_divs:
            match_id = match_div["data-id"]
            all_match_ids.append(match_id)
    
    return all_match_ids

def scrape_match_statistics(match_ids):
    """
    Given a list of match IDs, builds the API URL for each match
    and fetches the JSON data. Waits randomly between requests to avoid blocks.
    """
    BASE_API = "https://www.sofascore.com/api/v1/event/{}/statistics"
    
    for i, match_id in enumerate(match_ids, start=1):
        url = BASE_API.format(match_id)
        print(f"Fetching stats for Match ID {match_id} ...")
        
        # Send the request
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            # Do something with the data (store it, print it, etc.)
            print(f"Match {match_id} data keys:", data.keys())
        else:
            print(f"Failed to fetch data for Match ID {match_id} (Status: {response.status_code})")
        
        # Sleep a random interval between 2 and 5 seconds (adjust as desired)
        if i < len(match_ids):  # Skip sleep after the last request
            sleep_time = random.uniform(2, 5)
            print(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

def main():
    # 1. Extract all match IDs by parsing the main page
    match_ids = get_all_match_ids()
    print(f"Found {len(match_ids)} match IDs.")

    if match_ids:
        # 2. Scrape stats for each match ID, with random delays
        scrape_match_statistics(match_ids)

if __name__ == "__main__":
    main()
