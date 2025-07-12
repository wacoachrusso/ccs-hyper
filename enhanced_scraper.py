import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedScraper:
    """
    Scrapes the detailed 'Print View' schedule from CCS.
    This view contains all necessary flight, crew, and pairing details.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def login(self):
        logger.info("Logging into CCS...")
        self.driver.get("https://ccs.flyfrontier.com/")
        self.driver.find_element(By.ID, "Username").send_keys(self.username)
        self.driver.find_element(By.ID, "Password").send_keys(self.password)
        self.driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "msLink")))
        logger.info("Login successful.")

    def navigate_to_print_view(self):
        logger.info("Navigating to the detailed print view schedule...")
        # This sequence might need adjustment based on the actual CCS navigation
        self.driver.find_element(By.ID, "msLink").click() # Go to My Schedule
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "print_button"))).click() # Click Print
        
        # Switch to the new window/tab that opens
        original_window = self.driver.current_window_handle
        WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))

        for window_handle in self.driver.window_handles:
            if window_handle != original_window:
                self.driver.switch_to.window(window_handle)
                break
        
        # In the print preview, select all details
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "check_all_crew"))).click()
        self.driver.find_element(By.ID, "check_all_flights").click()
        self.driver.find_element(By.ID, "print_preview_button").click()
        logger.info("Print preview generated.")

    def get_schedule_html(self):
        """Executes the scraping process and returns the HTML content."""
        try:
            self.login()
            self.navigate_to_print_view()
            # Wait for the final content to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pairing-details"))
            )
            time.sleep(3) # Extra wait for any JS rendering
            html = self.driver.page_source
            logger.info("Successfully scraped schedule HTML.")
            return html
        except Exception as e:
            logger.error(f"An error occurred during scraping: {e}", exc_info=True)
            return None
        finally:
            self.driver.quit()
