# selenium_utils.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import glob
from bs4 import BeautifulSoup

def fetch_single_table(url, wait_time, keyword):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--incognito')

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

def download_csv_with_year_filter(url, year):

    anchor_email_id = os.getenv("ANCHOR_EMAIL_ID")
    anchor_password = os.getenv("ANCHOR_PASSWORD")

    # Create download directory if it doesn't exist
    download_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(download_dir, exist_ok=True)

    # Delete all existing CSV files in the download directory
    existing_files = glob.glob(os.path.join(download_dir, '*.csv'))
    for file in existing_files:
        os.remove(file)
        print(f"Deleted existing file: {file}")

    # Configure Chrome options for download
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--incognito')

    prefs = {
        "download.default_directory": os.path.abspath(download_dir)
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Enable download behavior - this is what actually makes downloads work in headless mode
    driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': os.path.abspath(download_dir)}}
    driver.execute("send_command", params)

    try:
        driver.get(url)

        # Use the provided year
        year_text = f"Year {year}"

        # Wait for and click on dropdown with current year text
        wait = WebDriverWait(driver, 10)

        # Try to find dropdown by text content (could be a select element, button, or div)
        year_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{year_text}')]"))
        )
        year_element.click()
        print(f"Clicked on element containing: {year_text}")

        # Wait for 2 seconds
        time.sleep(2)

        # Find and click the Export to CSV button
        export_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='Export to CSV']"))
        )
        export_button.click()
        print("Clicked Export to CSV button")

        # Check if login popup appears
        print("Checking for login popup...")
        try:
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            print("✓ Login popup found!")

            # Fill in credentials
            username_field.clear()
            username_field.send_keys(anchor_email_id)
            print("Entered email")

            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(anchor_password)
            print("Entered password")

            # Click the Log in now button
            login_button = driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Log in now')]")
            login_button.click()
            print("Clicked Log in now button")
        except Exception as login_error:
            print(f"✗ Login popup not found or error occurred: {str(login_error)}")
            print("Continuing without login...")

        # Wait for download to complete
        time.sleep(3)

        # Find the most recently downloaded CSV file
        list_of_files = glob.glob(os.path.join(download_dir, '*.csv'))
        if not list_of_files:
            raise Exception("No CSV file found in download directory")

        latest_file = max(list_of_files, key=os.path.getctime)
        print(f"Downloaded CSV file: {latest_file}")

        return latest_file

    except Exception as e:
        print(f"Error during CSV download: {str(e)}")
        raise
    finally:
        driver.quit()
