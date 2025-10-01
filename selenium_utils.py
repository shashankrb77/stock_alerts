# selenium_utils.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

def fetch_single_table(url, wait_time, keyword):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(wait_time)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()
    all_tables = soup.find_all("table")
    company_tables = [table for table in all_tables if keyword.lower() in table.get_text(strip=True).lower()]
    if len(company_tables) == 1:
        return company_tables[0]
    raise Exception(f"Expected exactly one table containing the word '{keyword}', but found {len(company_tables)}.")
