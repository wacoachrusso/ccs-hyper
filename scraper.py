from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def get_schedule(username, password):
    """Logs into the United CCS and scrapes the schedule."""
    print("--- Starting Scraper ---")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Headless mode can interfere with print-to-pdf
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Enable kiosk-printing to bypass the print dialog
    options.add_argument('--kiosk-printing')
    
    print("Installing/finding chromedriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Driver initialized.")
    
    try:
        # Login
        login_url = "https://ccs.ual.com/CCS/default.aspx" # This is a guess of the URL, please correct if wrong
        print(f"Navigating to {login_url}")
        driver.get(login_url)
        
        print("Finding username and password fields with correct IDs...")
        driver.find_element(By.ID, "ctl01_mHolder_txtUserID").send_keys(username)
        driver.find_element(By.ID, "ctl01_mHolder_txtGlobalPassword").send_keys(password)
        
        print("Clicking login button...")
        driver.find_element(By.ID, "ctl01_mHolder_loginButton").click()

        # Navigate to the Master Schedule page
        print("Login successful. Navigating to the Master Schedule page...")
        # Wait for a known element on the landing page (like 'Quick Links') before proceeding
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Quick Links')]")))
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Master Schedule"))).click()
        print("Master Schedule link clicked.")

        # Wait until the schedule grid appears (up to 20 s), then grab HTML immediately.
        print("Waiting for schedule grid to appear…")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "sg__day"))
            )
            print("Schedule grid detected – scraping now.")
        except TimeoutException:
            print("Schedule grid did not appear within 20 s – continuing anyway.")
        page_html = driver.page_source

        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(page_html)
        print("Saved page source to debug_page.html")

        # Return the HTML content so that the parser can process it.
        return page_html, "SUCCESS"

    except Exception as e:
        # Propagate a clearer error message
        print(f"An exception occurred in the scraper: {e}")
        # Return two None values to prevent the unpack error in the main app
        return None, f"An error occurred in the scraper: {e}"
    finally:
        driver.quit()
