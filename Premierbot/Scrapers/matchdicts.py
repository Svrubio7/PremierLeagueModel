from bs4 import BeautifulSoup

team_name_mapping = {
    'Manchester Utd': 'man-utd',
    'Fulham': 'fulham',
    'Ipswich Town': 'ipswich',
    'Liverpool': 'liverpool',
    'Newcastle Utd': 'newcastle',
    "Nott'ham Forest": 'forest',
    'Southampton': 'southampton',
    'West Ham': 'west-ham',
    'Aston Villa': 'aston-villa',
    'Crystal Palace': 'crystal-palace',
    'Brentford': 'brentford',
    'Manchester City': 'man-city',
    'Leicester City': 'leicester',
    'Chelsea': 'chelsea',
    'Everton': 'everton',
    'Brentford': 'brentford',
    'Watford': 'watford',
    'Tottenham': 'tottenham',
    'Wolves': 'wolves',
    'Arsenal': 'arsenal',
    'Brighton': 'brighton',
    }

mapping = {k.lower(): v for k, v in team_name_mapping.items()}

def normalize_team_name(raw_name:str) -> str:
    lower_name = raw_name.strip().lower()
    return mapping.get(lower_name, lower_name.replace(" ", "-"))

def build_match_team_dict(file_path: str) -> dict:
    """
    Reads an HTML file from the given path and returns a dictionary:
      {
        "12436965": {"home": "southampton", "away": "brighton-and-hove-albion"},
        ...
      }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    match_dict = {}
    for a_tag in soup.find_all("a", attrs={"data-testid": "event_cell"}):
        match_id = a_tag.get("data-id", "")
        if not match_id:
            continue

        left_div = a_tag.find("div", attrs={"data-testid": "left_team"})
        right_div = a_tag.find("div", attrs={"data-testid": "right_team"})
        if not left_div or not right_div:
            continue

        raw_home_team = left_div.get_text(strip=True).lower().replace(" ", "-")
        raw_away_team = right_div.get_text(strip=True).lower().replace(" ", "-")
        home_team = normalize_team_name(raw_home_team)
        away_team = normalize_team_name(raw_away_team)

        match_dict[match_id] = {"home": home_team, "away": away_team}

    return match_dict

# Merge dictionaries from rounds 1 to 26
all_match_dict = {}
for i in range(1, 29):
    path = f"/Users/jd/Documents/PremierLeagueModel/PremierLeagueModel/htmlscripts/Dataids/round{i}.txt"
    round_dict = build_match_team_dict(path)
    all_match_dict.update(round_dict)

print("Merged match team dictionary:")
print(all_match_dict)
