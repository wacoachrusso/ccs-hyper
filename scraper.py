from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_schedule(username, password):
    """DEPRECATED: Scrapes the master schedule from the CCS website."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://ccs.flyfrontier.com/")
        
        # Login
        driver.find_element(By.ID, "Username").send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()
        
        # Navigate to Master Schedule
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "msLink"))
        ).click()
        
        # Wait for schedule to load and get page source
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sg-data-row"))
        )
        time.sleep(2) # Allow for any final JS rendering
        html_content = driver.page_source
        return html_content
    finally:
        driver.quit()
