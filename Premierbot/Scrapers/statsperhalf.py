from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Chrome options (you can uncomment headless mode if desired)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Open the target webpage (replace with your URL)
driver.get("https://www.sofascore.com/tournament/football/england/premier-league/17#id:61627")

# Wait for dynamic content to load completely
time.sleep(5)  # You may adjust this or use explicit waits as needed

# Get the fully rendered HTML
rendered_html = driver.page_source

# Save the HTML to a file
with open("C:/Users/svrub/Documents/Mis cosillas/apuestas/PremierLeagueModel/htmlscripts/rendered.html", "w", encoding="utf-8") as file:
    file.write(rendered_html)

# Close the browser
driver.quit()
