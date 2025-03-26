import csv
import os
import pandas as pd
from collections import defaultdict
from openpyxl import Workbook, load_workbook

# ------------------------
# Normalization & Parsing
# ------------------------
team_name_mapping = {
    'manchester utd': 'man-utd',
    'manchester united': 'man-utd',
    'fulham': 'fulham',
    'ipswich town': 'ipswich',
    'liverpool': 'liverpool',
    'newcastle utd': 'newcastle',
    'newcastle united': 'newcastle',
    "nott'ham forest": 'forest',
    'nottingham forest': 'forest',
    'southampton': 'southampton',
    'west ham': 'west-ham',
    'west ham united': 'west-ham',
    'aston villa': 'aston-villa',
    'crystal palace': 'crystal-palace',
    'brentford': 'brentford',
    'manchester city': 'man-city',
    'leicester city': 'leicester',
    'chelsea': 'chelsea',
    'everton': 'everton',
    'tottenham': 'tottenham',
    'tottenham hotspur': 'tottenham',
    'wolves': 'wolves',
    'wolverhampton wanderers': 'wolves',
    'arsenal': 'arsenal',
    'brighton': 'brighton',
    'brighton & hove albion': 'brighton',
    'bournemouth': 'bournemouth',
    'afc bournemouth': 'bournemouth'
}
mapping = {k.lower(): v for k, v in team_name_mapping.items()}

def normalize_team_name(raw_name: str) -> str:
    lower_name = raw_name.strip().lower()
    return mapping.get(lower_name, lower_name.replace(" ", "-"))

def parse_result(result: str) -> tuple[int, int]:
    """Parse a result string like '2–1' into (home_goals, away_goals)."""
    if "–" not in result or "N/A" in result:
        return 0, 0
    home_goals, away_goals = map(int, result.split("–"))
    return home_goals, away_goals

def parse_stat(stat: str) -> float:
    """Parse a stat string (e.g., '19/35 (54%)' or '408') into a float."""
    if not stat or stat == '':
        return 0.0
    if '/' in stat:
        return float(stat.split('/')[0])
    try:
        return float(stat.replace('%', ''))
    except ValueError:
        return 0.0

# ------------------------
# Updated load_matches Function
# ------------------------
def load_matches(file_path: str) -> list[dict]:
    """
    Load matches from a CSV or XLSX file into a list of dictionaries.
    The function checks the file extension and uses the appropriate pandas function.
    """
    matches = []
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif ext == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        row_dict['team'] = normalize_team_name(str(row_dict.get('team', '')))
        row_dict['opponent'] = normalize_team_name(str(row_dict.get('opponent', '')))
        matches.append(row_dict)
    return matches

# ------------------------
# Grouping Matches (each match is 2 rows)
# ------------------------
def deduplicate_matches(rows: list[dict]) -> dict[str, dict]:
    """
    Group rows by match_id.
    We assume each match appears as two rows:
      - The 'home' row (first row encountered for a match_id)
      - The 'away' row (the second row)
    """
    match_groups = {}
    for row in rows:
        match_id = row['match_id']
        match_groups.setdefault(match_id, []).append(row)
    
    dedup = {}
    for match_id, group in match_groups.items():
        if len(group) >= 2:
            dedup[match_id] = {'home': group[0], 'away': group[1]}
        else:
            dedup[match_id] = {'home': group[0], 'away': None}
    return dedup

# ------------------------
# Helper to add extra columns for output rows
# ------------------------
def add_extra_columns(row: dict, role: str, team_of_interest: str = None) -> dict:
    """
    Add extra columns to a row:
      - "Perspective": "Home" or "Away"
      - "Adjusted_RESULT": For away rows, invert the RESULT (swap goals)
      - "Team_Perspective": "Yes" if row['team'] matches team_of_interest, else "No"
    """
    adjusted = row['RESULT']
    if role == "away":
        home_goals, away_goals = parse_result(row['RESULT'])
        adjusted = f"{away_goals}–{home_goals}"
    new_row = row.copy()
    new_row["Perspective"] = role.capitalize()
    new_row["Adjusted_RESULT"] = adjusted
    if team_of_interest:
        new_row["Team_Perspective"] = "Yes" if row["team"] == normalize_team_name(team_of_interest) else "No"
    else:
        new_row["Team_Perspective"] = ""
    return new_row

# ------------------------
# Analysis Functions using Grouped Matches
# ------------------------
def find_last_head_to_head_group(dedup_matches: dict, team1: str, team2: str) -> dict:
    """
    Find the most recent head-to-head match between team1 and team2.
    Returns the match group (both home and away rows) for that game.
    """
    team1 = normalize_team_name(team1)
    team2 = normalize_team_name(team2)
    groups = []
    for group in dedup_matches.values():
        home_team = group['home']['team'] if group['home'] else ""
        away_team = group['away']['team'] if group['away'] else ""
        if (home_team == team1 and away_team == team2) or (home_team == team2 and away_team == team1):
            groups.append(group)
    if not groups:
        return {}
    groups.sort(key=lambda g: int(g['home']['match_id']), reverse=True)
    return groups[0]

def get_last_five_match_groups(dedup_matches: dict, team: str) -> list:
    """
    Get the last five match groups in which the given team participated.
    Each group represents one game (two rows).
    """
    team = normalize_team_name(team)
    groups = []
    for group in dedup_matches.values():
        home_team = group['home']['team'] if group['home'] else ""
        away_team = group['away']['team'] if group['away'] else ""
        if team == home_team or team == away_team:
            groups.append(group)
    groups.sort(key=lambda g: int(g['home']['match_id']), reverse=True)
    return groups[:5]

def calculate_averages_dedup(dedup_matches: dict, team: str) -> dict:
    """
    Calculate average stats for a team over deduplicated matches.
    Home matches are taken from the home row.
    Away matches are taken from the away row (with the result inverted for clarity).
    """
    team = normalize_team_name(team)
    home_rows = []
    away_rows = []
    for group in dedup_matches.values():
        home_team = group['home']['team'] if group['home'] else ""
        away_team = group['away']['team'] if group['away'] else ""
        if team == home_team:
            home_rows.append(group['home'])
        elif group['away'] is not None and team == away_team:
            row = group['away'].copy()
            home_goals, away_goals = parse_result(row['RESULT'])
            row['RESULT'] = f"{away_goals}–{home_goals}"
            away_rows.append(row)
    
    stat_fields = [
        'Accurate passes', 'Aerial duels', 'Ball possession', 'Big chances', 'Big chances missed', 
        'Big chances scored', 'Big saves', 'Blocked shots', 'Clearances', 'Corner kicks', 'Crosses', 
        'Dispossessed', 'Dribbles', 'Duels', 'Errors lead to a goal', 'Errors lead to a shot', 
        'Expected goals', 'Final third entries', 'Final third phase', 'Fouled in final third', 
        'Fouls', 'Free kicks', 'Goal kicks', 'Goalkeeper saves', 'Goals prevented', 'Ground duels', 
        'High claims', 'Hit woodwork', 'Interceptions', 'Long balls', 'Offsides', 'Passes', 
        'Penalty saves', 'Punches', 'Recoveries', 'Red cards', 'Shots inside box', 'Shots off target', 
        'Shots on target', 'Shots outside box', 'Tackles', 'Tackles won', 'Through balls', 'Throw-ins', 
        'Total saves', 'Total shots', 'Total tackles', 'Touches in penalty area', 'Yellow cards'
    ]
    
    def compute_stats(rows):
        stats = defaultdict(lambda: {'sum': 0.0, 'count': 0})
        for row in rows:
            home_goals, away_goals = parse_result(row['RESULT'])
            stats['Goals scored']['sum'] += home_goals
            stats['Goals conceded']['sum'] += away_goals
            stats['Goals scored']['count'] += 1
            stats['Goals conceded']['count'] += 1
            for field in stat_fields:
                stats[field]['sum'] += parse_stat(str(row.get(field, '')))
                stats[field]['count'] += 1
        return {field: (stats[field]['sum'] / stats[field]['count'] if stats[field]['count'] > 0 else 0.0)
                for field in ['Goals scored', 'Goals conceded'] + stat_fields}
    
    return {
        'home': {'averages': compute_stats(home_rows), 'matches': len(home_rows)},
        'away': {'averages': compute_stats(away_rows), 'matches': len(away_rows)}
    }

# ------------------------
# Functions to Import External XLSX Tables
# ------------------------
def copy_sheet(src_sheet, dest_sheet):
    """Copy cell values from src_sheet to dest_sheet."""
    for row in src_sheet.iter_rows():
        for cell in row:
            dest_sheet[cell.coordinate].value = cell.value

def add_external_tables(workbook, external_file_paths: list):
    """
    For each external XLSX file, load its workbook and copy each worksheet
    into the final workbook as a new sheet.
    """
    for file_path in external_file_paths:
        wb_ext = load_workbook(file_path)
        for sheet in wb_ext.worksheets:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            new_sheet_title = f"Imported_{base_name}_{sheet.title}"
            # Ensure sheet title length is within Excel's limits (31 characters)
            new_sheet_title = new_sheet_title[:31]
            dest_sheet = workbook.create_sheet(title=new_sheet_title)
            copy_sheet(sheet, dest_sheet)

# ------------------------
# XLSX Output Function
# ------------------------
def write_period_output(period: str, rows: list[dict], team1: str, team2: str, output_filename: str, external_xlsx_paths: list):
    """
    Write the analysis for a given period to an XLSX file.
    For head-to-head and last 5 matches, both rows for each match are output
    with extra columns indicating perspective and adjusted result.
    At the end, external XLSX tables are imported as additional worksheets.
    """
    # Group rows by match_id
    dedup_matches = deduplicate_matches(rows)
    
    # --- Section 1: Head-to-Head Match ---
    head_to_head_group = find_last_head_to_head_group(dedup_matches, team1, team2)
    
    # --- Section 2: Last 5 Matches for team1 ---
    team1_groups = get_last_five_match_groups(dedup_matches, team1)
    
    # --- Section 3: Last 5 Matches for team2 ---
    team2_groups = get_last_five_match_groups(dedup_matches, team2)
    
    # --- Averages ---
    team1_averages = calculate_averages_dedup(dedup_matches, team1)
    team2_averages = calculate_averages_dedup(dedup_matches, team2)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Main Analysis"
    
    # Write period title
    ws.append([f"{period} Analysis"])
    ws.append([])  # blank row
    
    # Section 1: Head-to-Head Match
    ws.append(["Head-to-Head Match"])
    if head_to_head_group:
        home_aug = add_extra_columns(head_to_head_group['home'], "home")
        header = list(home_aug.keys())
        ws.append(header)
        ws.append(list(add_extra_columns(head_to_head_group['home'], "home").values()))
        if head_to_head_group['away']:
            ws.append(list(add_extra_columns(head_to_head_group['away'], "away").values()))
    else:
        ws.append(["No head-to-head match found."])
    ws.append([])
    
    # Section 2: Last 5 Matches for team1
    ws.append([f"Last 5 Matches for {normalize_team_name(team1)}"])
    if team1_groups:
        header = list(add_extra_columns(team1_groups[0]['home'], "home", team1).keys())
        ws.append(header)
        for group in team1_groups:
            ws.append(list(add_extra_columns(group['home'], "home", team1).values()))
            if group['away']:
                ws.append(list(add_extra_columns(group['away'], "away", team1).values()))
            ws.append([])  # blank row between matches
    else:
        ws.append([f"No matches found for {normalize_team_name(team1)}."])
    ws.append([])
    
    # Section 3: Last 5 Matches for team2
    ws.append([f"Last 5 Matches for {normalize_team_name(team2)} (each match shows two rows)"])
    if team2_groups:
        header = list(add_extra_columns(team2_groups[0]['home'], "home", team2).keys())
        ws.append(header)
        for group in team2_groups:
            ws.append(list(add_extra_columns(group['home'], "home", team2).values()))
            if group['away']:
                ws.append(list(add_extra_columns(group['away'], "away", team2).values()))
            ws.append([])
    else:
        ws.append([f"No matches found for {normalize_team_name(team2)}."])
    ws.append([])
    
    # Section 4: Averages
    ws.append(["Averages"])
    columns_order = ['Goals scored', 'Goals conceded'] + [
        'Accurate passes', 'Aerial duels', 'Ball possession', 'Big chances', 'Big chances missed', 
        'Big chances scored', 'Big saves', 'Blocked shots', 'Clearances', 'Corner kicks', 'Crosses', 
        'Dispossessed', 'Dribbles', 'Duels', 'Errors lead to a goal', 'Errors lead to a shot', 
        'Expected goals', 'Final third entries', 'Final third phase', 'Fouled in final third', 
        'Fouls', 'Free kicks', 'Goal kicks', 'Goalkeeper saves', 'Goals prevented', 'Ground duels', 
        'High claims', 'Hit woodwork', 'Interceptions', 'Long balls', 'Offsides', 'Passes', 
        'Penalty saves', 'Punches', 'Recoveries', 'Red cards', 'Shots inside box', 'Shots off target', 
        'Shots on target', 'Shots outside box', 'Tackles', 'Tackles won', 'Through balls', 'Throw-ins', 
        'Total saves', 'Total shots', 'Total tackles', 'Touches in penalty area', 'Yellow cards'
    ]
    
    ws.append([f"Averages for {normalize_team_name(team1)}"])
    for venue in ['home', 'away']:
        ws.append(["Venue", "Matches"] + columns_order)
        row = [venue.capitalize(), team1_averages[venue]['matches']] + [
            f"{team1_averages[venue]['averages'].get(col, 0.0):.2f}" for col in columns_order
        ]
        ws.append(row)
    ws.append([])
    
    ws.append([f"Averages for {normalize_team_name(team2)}"])
    for venue in ['home', 'away']:
        ws.append(["Venue", "Matches"] + columns_order)
        row = [venue.capitalize(), team2_averages[venue]['matches']] + [
            f"{team2_averages[venue]['averages'].get(col, 0.0):.2f}" for col in columns_order
        ]
        ws.append(row)
    
    # ------------------------
    # Import External XLSX Tables
    # ------------------------
    add_external_tables(wb, external_xlsx_paths)
    
    wb.save(output_filename)

# ------------------------
# Main: File Paths & Team Names set in Code
# ------------------------
def main():
    # Supply the CSV/XLSX file paths and team names here
    full_csv = "/Users/jd/Documents/PremierLeagueModel/matches_1ST.csv"         # Can be CSV or XLSX
    first_half_csv = "/Users/jd/Documents/PremierLeagueModel/matches_1ST.csv"     # Can be CSV or XLSX
    second_half_csv = "/Users/jd/Documents/PremierLeagueModel/matches_2ND.csv"    # Can be CSV or XLSX
    team1 = "man-utd"                    # First team name
    team2 = "leicester"                      # Second team name

    # List external XLSX files that you already have and want to import
    external_xlsx_paths = [
        "/Users/jd/Documents/PremierLeagueModel/leicester-man-utd-tiroslibres.xlsx",
        "/Users/jd/Documents/PremierLeagueModel/leicester-man-utd-tirostotales.xlsx",
        "/Users/jd/Documents/PremierLeagueModel/leicester-man-utdsaquesbanda.xlsx",
        "/Users/jd/Documents/PremierLeagueModel/man-utd-leicester-tiroslibres.xlsx",
        "/Users/jd/Documents/PremierLeagueModel/man-utd-leicester-tirostotales.xlsx",
        "/Users/jd/Documents/PremierLeagueModel/man-utd-leicestersaquesbanda.xlsx"
    ]
    
    # Load all three datasets (works with both XLSX and CSV)
    datasets = {
        'Full Match': load_matches(full_csv),
        'First Half': load_matches(first_half_csv),
        'Second Half': load_matches(second_half_csv)
    }
    
    # Process each period and write an output XLSX file
    for period, rows in datasets.items():
        output_filename = f"{period.replace(' ', '_').lower()},{team1}_vs_{team2}.xlsx"
        write_period_output(period, rows, team1, team2, output_filename, external_xlsx_paths)
        print(f"Output written to {output_filename}")

if __name__ == "__main__":
    main()
