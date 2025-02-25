from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import requests

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.sofascore.com/tournament/football/england/premier-league/17#id:61627,tab:matches")
# Wait for JavaScript to load (adjust time or use WebDriverWait)
time.sleep(5)

html = driver.page_source

from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find the round containers
round_containers = soup.find_all("div", class_="round-header")
all_match_ids = []

for round_div in round_containers:
    matches_container = round_div.find_next_sibling("div")
    if matches_container:
        match_divs = matches_container.find_all("div", attrs={"data-id": True})
        for match_div in match_divs:
            match_id = match_div["data-id"]
            all_match_ids.append(match_id)
            

print("All match IDs:", all_match_ids)

driver.quit()