import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CcsScraper:
    """Enhanced CCS scraper that retrieves detailed schedule information from the print view"""
    
    def __init__(self, headless=True, debug=False):
        """Initialize the scraper with options"""
        self.driver = None
        self.headless = headless
        self.debug = debug
        self.logged_in = False
        
    def setup_driver(self):
        """Setup Selenium WebDriver with appropriate options"""
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # More robust options
        options.add_argument('--disable-gpu')  # Required for Windows
        options.add_argument('--no-sandbox')  # Less secure but more stable
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource issues
        options.add_argument('--window-size=1920,1080')  # Consistent window size
        options.add_argument('--ignore-certificate-errors')  # Handle SSL issues
        options.add_argument('--disable-extensions')  # Disable extensions for reliability
        options.add_argument('--disable-popup-blocking')  # Allow popups we need
        
        # Improved performance options
        options.add_argument('--disable-features=NetworkService')  # More stable network
        options.add_argument('--disable-features=VizDisplayCompositor')  # Avoid GPU issues
        
        # Add custom user agent to avoid detection issues
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36')
        
        # Overcome connection refused errors
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Create Chrome WebDriver with increased timeouts
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Increase various timeouts
        self.driver.set_page_load_timeout(60)  # Longer page load timeout
        self.driver.set_script_timeout(60)  # Longer script timeout
        
        # Maximize window to ensure all elements are visible
        self.driver.maximize_window()
        
        return self.driver
        
    def login(self, username, password):
        """Login to CCS system"""
        if not self.driver:
            self.setup_driver()
            
        try:
            logger.info("Navigating to CCS login page")
            self.driver.get("https://ccs.ual.com/CCS/default.aspx")
            
            # Wait for the login page to load - increase timeout to 20 seconds
            logger.info("Waiting for login elements to appear")
            
            # Take a screenshot of the login page
            time.sleep(5)  # Give a moment for the page to render
            self.driver.save_screenshot("login_page.png")
            logger.info("Saved screenshot of login page")
            
            # Try the original IDs that we verified previously
            try:
                logger.info("Looking for username field with ID: ctl01_mHolder_txtUserID")
                username_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "ctl01_mHolder_txtUserID"))
                )
                
                logger.info("Looking for password field with ID: ctl01_mHolder_txtGlobalPassword")
                password_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "ctl01_mHolder_txtGlobalPassword"))
                )
                
                logger.info("Looking for login button with ID: ctl01_mHolder_loginButton")
                login_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "ctl01_mHolder_loginButton"))
                )
            except TimeoutException:
                # Fall back to looking for alternative IDs
                logger.warning("Could not find fields by verified IDs, trying alternative selectors")
                
                # Take a screenshot showing what we're working with
                self.driver.save_screenshot("login_page_alt.png")
                
                # Try to find elements by more general approaches
                username_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='text'][contains(@id, 'UserID') or contains(@id, 'Username')]"))
                )
                
                password_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='password'][contains(@id, 'Password')]"))
                )
                
                login_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' or @type='button'][contains(@id, 'login') or contains(@value, 'Login')]"))
                )
            
            # Enter username and password
            logger.info(f"Entering username: {username}")
            username_field.clear()
            username_field.send_keys(username)
            
            logger.info("Entering password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Take a screenshot before clicking login
            self.driver.save_screenshot("before_login.png")
            
            # Click login button
            logger.info("Clicking login button")
            login_button.click()
            
            # Wait for login to complete and dashboard to load
            logger.info("Waiting for login to complete")
            try:
                # Verify we're logged in by waiting for dashboard elements or My Schedule link
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'My Schedule')] | //div[contains(@class, 'dashboard')] | //div[contains(@class, 'welcome')]"))
                )
                logger.info("Login successful, CCS dashboard loaded")
                self.logged_in = True
                
                # Take a screenshot of the dashboard
                self.driver.save_screenshot("dashboard.png")
                
                # Extra time for the page to fully render if requested
                if self.debug:
                    logger.info("Debug mode: waiting 10 seconds for dashboard to fully load")
                    time.sleep(10)
                    self.driver.save_screenshot("dashboard_after_wait.png")
                
                return True
            except TimeoutException:
                logger.error("Login failed or dashboard didn't load properly")
                self.driver.save_screenshot("login_failure.png")
                return False
                
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}")
            self.driver.save_screenshot("login_exception.png")
            return False
    
    def navigate_to_my_schedule(self):
        """Navigate to My Schedule page"""
        if not self.logged_in:
            logger.error("Not logged in, cannot navigate to My Schedule")
            return False
            
        try:
            logger.info("Looking for My Schedule link")
            
            # First check if we're already on the My Schedule page
            current_url = self.driver.current_url
            if "#/myschedule" in current_url.lower():
                logger.info("Already on My Schedule page")
                return True
            
            # Take a screenshot before looking for the link
            self.driver.save_screenshot("before_my_schedule_click.png")
            
            # Try to find the My Schedule link using various strategies
            try:
                # First strategy: Look for the exact link based on user's screenshot
                schedule_link = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'My Schedule')][contains(@class, 'quick-link') or ancestor::div[contains(@class, 'quick-link')]]"))
                )
                logger.info("Found My Schedule in Quick Links")
            except TimeoutException:
                # Second strategy: Try more general link selectors
                try:
                    schedule_link = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'My Schedule')]"))
                    )
                    logger.info("Found My Schedule link by text")
                except TimeoutException:
                    # Third strategy: Try by href attribute
                    try:
                        schedule_link = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'schedule') or contains(@href, 'Schedule')]"))
                        )
                        logger.info("Found My Schedule link by href")
                    except TimeoutException:
                        # Final attempt: Look for any links with nav items
                        schedule_link = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".nav-item a, .sidebar a, .menu a"))
                        )
                        logger.info("Found a navigation link, attempting to use it")
            
            # Click the link
            logger.info("Clicking My Schedule link")
            schedule_link.click()
            
            # Wait for the My Schedule page to load
            logger.info("Waiting for My Schedule page to load")
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: "#/myschedule" in driver.current_url.lower() or 
                                   EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'My Schedule')] | //div[contains(@class, 'schedule')] | //div[contains(@class, 'calendar')]"))
                )
                logger.info("My Schedule page loaded successfully")
                
                # Take a screenshot of the My Schedule page
                self.driver.save_screenshot("my_schedule_page.png")
                return True
            except TimeoutException:
                logger.error("My Schedule page didn't load properly")
                self.driver.save_screenshot("my_schedule_failure.png")
                return False
                
        except Exception as e:
            logger.error(f"Exception navigating to My Schedule: {str(e)}")
            self.driver.save_screenshot("my_schedule_exception.png")
            return False
    
    def open_print_dialog(self):
        """Open the print dialog and select all options"""
        try:
            # First take a screenshot of the page where we're looking for the print button
            self.driver.save_screenshot("before_print.png")
            logger.info("Saved screenshot before looking for print button")
            
            # Look for the print button using the exact HTML structure provided by user:
            # <a placement="bottom" container="body"><i aria-hidden="true" class="icon-PrintSVG"></i>Print</a>
            logger.info("Looking for print button using exact user-provided HTML structure")
            
            try:
                # Strategy 1: Find by the exact structure with class "icon-PrintSVG"
                print_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[.//i[contains(@class, 'icon-PrintSVG')] and contains(text(), 'Print')]"))
                )
                logger.info("Found print button by exact user-provided structure")
            except TimeoutException:
                try:
                    # Strategy 2: Find by icon class alone
                    print_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, "//i[contains(@class, 'icon-PrintSVG')]/parent::a"))
                    )
                    logger.info("Found print button by icon class")
                except TimeoutException:
                    try:
                        # Strategy 3: Find by link with Print text
                        print_button = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Print')]"))
                        )
                        logger.info("Found print button by text")
                    except TimeoutException:
                        # Strategy 4: Most generic approach
                        print_button = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'print') or contains(text(), 'Print')]"))
                        )
                        logger.info("Found print button by generic selector")
            
            # Take a screenshot showing the located print button
            self.driver.save_screenshot("found_print_button.png")
            
            # Click the print button to open the dialog
            logger.info("Clicking print button")
            print_button.click()
            
            # Wait for print dialog to appear - based on exact user screenshot
            logger.info("Waiting for print options dialog")
            time.sleep(2)  # Brief pause to let dialog fully appear
            
            # Take a screenshot of what we have
            self.driver.save_screenshot("before_print_dialog_detection.png")
            
            try:
                # Wait for the print options dialog with title
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Printing Options')] | //h3[contains(text(), 'Printing Options')] | //h4[contains(text(), 'Printing Options')]"))
                )
                logger.info("Found print options dialog")
            except TimeoutException:
                logger.warning("Could not find print options dialog by title, trying alternatives")
                # Try to detect by presence of checkboxes
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox']"))
                )
                logger.info("Detected print dialog by checkboxes")
            
            # Take a screenshot of the print dialog
            self.driver.save_screenshot("print_dialog.png")
            logger.info("Print dialog opened and screenshot saved")
            
            # Check all the checkboxes in the dialog as shown in user's screenshot
            logger.info("Selecting all print options")
            
            # Select print options based on exact user's screenshot
            # Take screenshot before option selection
            self.driver.save_screenshot("before_option_selection.png")
            
            # First, find all options to understand their layout
            try:
                # Get all checkboxes and radio buttons for reference
                all_options = self.driver.find_elements(By.XPATH, "//input[@type='checkbox'] | //input[@type='radio']")
                logger.info(f"Found {len(all_options)} total checkbox/radio button options")
                
                for i, option in enumerate(all_options):
                    try:
                        option_id = option.get_attribute("id")
                        option_type = option.get_attribute("type")
                        option_checked = option.is_selected()
                        logger.info(f"Option {i}: id={option_id}, type={option_type}, checked={option_checked}")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Couldn't enumerate all options: {e}")
            
            # 1. Select "Letter Size" radio button (seen in screenshot)
            try:
                # Try different strategies to find the Letter Size radio button
                try:
                    # First try by label text which is visible in screenshot
                    letter_size = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='radio'][following-sibling::text()[contains(., 'Letter Size')] or preceding-sibling::text()[contains(., 'Letter Size')] or ancestor::label[contains(text(), 'Letter Size')]]")), 
                        "Could not find Letter Size radio by label"
                    )
                except:
                    try:
                        # Try by being the first radio button in Paper Size section
                        letter_size = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "(//div[contains(text(), 'Paper Size') or contains(@class, 'paper-size')]//input[@type='radio'])[1]")), 
                            "Could not find Letter Size as first radio in Paper Size section"
                        )
                    except:
                        # Last resort, use JavaScript to find by visible text near radio button
                        letter_size = self.driver.execute_script(
                            "return document.evaluate('//label[contains(text(), \'Letter Size\')]//input[@type=\'radio\'] | //input[@type=\'radio\'][../text()[contains(., \'Letter Size\')]]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;")
                
                if letter_size:
                    if not letter_size.is_selected():
                        letter_size.click()
                        logger.info("Selected 'Letter Size' option")
                        time.sleep(0.5)  # Brief pause between selections
                    else:
                        logger.info("Letter Size already selected")
                else:
                    logger.warning("Letter Size radio button was found but is null")
                    
                # Take a screenshot to verify selection
                self.driver.save_screenshot("after_letter_size_selection.png")
            except Exception as e:
                logger.warning(f"Could not select Letter Size radio: {e}")
                self.driver.save_screenshot("letter_size_selection_error.png")
            
            # Use JavaScript to check boxes more reliably
            checkbox_selectors = [
                # 2. Pairings checkbox
                {"name": "Pairings", "xpath": "//input[@type='checkbox'][following-sibling::text()[contains(., 'Pairings')] or preceding-sibling::text()[contains(., 'Pairings')] or ancestor::label[contains(text(), 'Pairings')]]"}, 
                
                # 3. Basic Information checkbox
                {"name": "Basic Information", "xpath": "//input[@type='checkbox'][following-sibling::text()[contains(., 'Basic Information')] or preceding-sibling::text()[contains(., 'Basic')] or ancestor::label[contains(text(), 'Basic')]]"}, 
                
                # 4. Layover Information checkbox
                {"name": "Layover Information", "xpath": "//input[@type='checkbox'][following-sibling::text()[contains(., 'Layover')] or preceding-sibling::text()[contains(., 'Layover')] or ancestor::label[contains(text(), 'Layover')]]"}, 
                
                # 5. Crew Information checkbox
                {"name": "Crew Information", "xpath": "//input[@type='checkbox'][following-sibling::text()[contains(., 'Crew Information')] or preceding-sibling::text()[contains(., 'Crew Information')] or ancestor::label[contains(text(), 'Crew')]]"}
            ]
            
            # Process each checkbox
            for selector in checkbox_selectors:
                try:
                    option_name = selector["name"]
                    option_xpath = selector["xpath"]
                    
                    # Try using standard Selenium method first
                    try:
                        checkbox = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, option_xpath))
                        )
                        
                        if not checkbox.is_selected():
                            checkbox.click()
                            logger.info(f"Checked '{option_name}' checkbox")
                            time.sleep(0.5)  # Brief pause between selections
                        else:
                            logger.info(f"'{option_name}' checkbox already checked")
                    except:
                        # Fallback to JavaScript execution
                        logger.warning(f"Using JavaScript fallback for {option_name}")
                        js_script = f"var el = document.evaluate('{option_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; if(el && !el.checked) {{ el.checked = true; return true; }} else {{ return false; }}"
                        result = self.driver.execute_script(js_script)
                        if result:
                            logger.info(f"JS: Checked '{option_name}' checkbox")
                        else:
                            logger.info(f"JS: '{option_name}' checkbox already checked or not found")
                    
                    # Take screenshot after each checkbox
                    self.driver.save_screenshot(f"after_{option_name.lower().replace(' ', '_')}_selection.png")
                except Exception as e:
                    logger.warning(f"Could not check {option_name} checkbox: {e}")
                    self.driver.save_screenshot(f"{option_name.lower().replace(' ', '_')}_selection_error.png")
            
            # 6. Select "Yes" radio button for "Include Crew Pictures"
            try:
                # Check if there's a Yes radio button near "Include Crew Pictures" text
                try:
                    crew_pics_yes = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='radio'][@value='Yes' or @id='crewPicturesYes'][following-sibling::text()[contains(., 'Yes')] or preceding-sibling::text()[contains(., 'Yes')] or ancestor::label[contains(text(), 'Yes')]]")),
                        "Could not find Yes radio by direct attributes"
                    )
                except:
                    # Look for radio button with Yes label after "Include Crew Pictures" text
                    try:
                        crew_pics_yes = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//text()[contains(., 'Include Crew Pictures')]/following::input[@type='radio'][following-sibling::text()[contains(., 'Yes')]]")),
                            "Could not find Yes radio after Include Crew Pictures text"
                        )
                    except:
                        # Last resort: try JavaScript to find it by nearby text
                        logger.warning("Using JavaScript to find Yes radio button")
                        crew_pics_yes = self.driver.execute_script(
                            "var yesRadios = document.querySelectorAll('input[type=\'radio\']'); " +
                            "for(var i=0; i<yesRadios.length; i++) { " +
                            "  var el = yesRadios[i]; " +
                            "  var text = el.parentElement.textContent || ''; " +
                            "  if(text.includes('Yes') && text.includes('Include Crew Pictures')) { " +
                            "    return el; " +
                            "  } " +
                            "} " +
                            "return null;"
                        )
                
                if crew_pics_yes:
                    if not crew_pics_yes.is_selected():
                        # Try direct click
                        try:
                            crew_pics_yes.click()
                            logger.info("Selected 'Yes' for Include Crew Pictures")
                        except:
                            # Try JavaScript click as fallback
                            self.driver.execute_script("arguments[0].click();", crew_pics_yes)
                            logger.info("Selected 'Yes' for Include Crew Pictures using JS")
                    else:
                        logger.info("'Yes' for Include Crew Pictures already selected")
                else:
                    logger.warning("'Yes' radio button not found or is null")
                    
                # Take screenshot after crew pictures selection
                self.driver.save_screenshot("after_crew_pictures_selection.png")
            except Exception as e:
                logger.warning(f"Could not select Yes for Crew Pictures: {e}")
                self.driver.save_screenshot("crew_pictures_selection_error.png")
                
                # Take screenshot after selecting options
                self.driver.save_screenshot("print_options_selected.png")
                logger.info("Print options selection complete")
                
            except Exception as e:
                logger.warning(f"Error selecting print options: {e}")
                self.driver.save_screenshot("print_options_error.png")
            
            # Wait for print options to settle
            time.sleep(2)
            
            # Take screenshot of final print options state
            self.driver.save_screenshot("print_options_final.png")
            
            # Click the print button in the dialog - based on user's screenshot showing gold/orange button
            logger.info("Looking for print/submit button in dialog")
            try:
                # Based on user's screenshot - gold/orange button with text "Print"
                print_submit = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Print']"))
                )
                logger.info("Found exact Print button from screenshot")
            except TimeoutException:
                try:
                    # Try by button text with more flexible matching
                    print_submit = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Print')] | //input[@type='button'][@value='Print'] | //input[@type='submit'][@value='Print']"))
                    )
                    logger.info("Found print button by text")
                except TimeoutException:
                    try:
                        # Try by gold/orange color or common print button classes
                        print_submit = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary, .btn-print, .print-btn, .gold-btn, .orange-btn"))
                        )
                        logger.info("Found print button by class/color")
                    except TimeoutException:
                        # Last resort - try any button that's not Cancel
                        print_submit = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[not(contains(text(), 'Cancel'))]"))
                        )
                        logger.info("Found non-cancel button (assuming print submit)")
            
            # Click the print/submit button
            logger.info("Clicking print/submit button")
            print_submit.click()
            
            # Wait for print preview to load (could be new tab/window)
            logger.info("Waiting for print preview to load")
            self.driver.save_screenshot("after_print_button_click.png")
            
            # Wait longer for potential dialog or popup to appear
            time.sleep(5)
            
            # Check if new window/tab opened
            try:
                original_window = self.driver.current_window_handle
                all_windows = self.driver.window_handles
                
                # If new window opened, switch to it
                if len(all_windows) > 1:
                    logger.info(f"Detected {len(all_windows)} windows/tabs, switching to print preview")
                    for window in all_windows:
                        if window != original_window:
                            self.driver.switch_to.window(window)
                            logger.info(f"Switched to new window/tab: {self.driver.current_url}")
                            
                            # Take screenshot of new window
                            self.driver.save_screenshot("print_preview_new_window.png")
                            break
                else:
                    # No new window, check if we're still on the same page
                    logger.info("No new window detected, checking for changes in current page")
                    self.driver.save_screenshot("still_on_same_page.png")
                    
                    # Check if we need to handle a browser print dialog that might be blocking
                    logger.info("Sending Escape key to dismiss any browser print dialogs")
                    from selenium.webdriver.common.keys import Keys
                    from selenium.webdriver.common.action_chains import ActionChains
                    
                    # Try to send Escape key to dismiss any native print dialog
                    try:
                        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(2)
                        self.driver.save_screenshot("after_escape_key.png")
                    except Exception as e:
                        logger.warning(f"Failed to send Escape key: {e}")
            except Exception as e:
                logger.warning(f"Error handling windows: {e}")
                self.driver.save_screenshot("window_handling_error.png")
            
            # Wait for print preview content to fully load
            logger.info("Waiting for print preview content to load")
            try:
                # Wait for any indicators that print preview is fully loaded
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//table | //div[contains(@class, 'print')] | //div[contains(@class, 'crew')]"))
                )
                logger.info("Print preview content detected")
            except TimeoutException:
                logger.warning("Could not detect specific print preview content, continuing anyway")
            
            # Take screenshot of the print preview
            self.driver.save_screenshot("print_preview_loaded.png")
            
            # Extract the HTML content from the print preview
            logger.info("Extracting HTML from print preview")
            html_content = self.driver.page_source
            
            # Save the HTML to a file for parsing
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"schedule_printview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Saved print preview HTML to {output_file}")
            
            # Return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to open print dialog: {str(e)}")
            return False
    
    def handle_print_preview_window(self):
        """Handle switching to print preview window/tab if needed"""
        try:
            # Check if we have multiple tabs/windows open
            all_windows = self.driver.window_handles
            
            if len(all_windows) > 1:
                # Get the current window handle
                current_window = self.driver.current_window_handle
                
                # Switch to the new window (assuming it's the print preview)
                for window in all_windows:
                    if window != current_window:
                        self.driver.switch_to.window(window)
                        logger.info(f"Switched to new window with URL: {self.driver.current_url}")
                        break
            
            return True
        except Exception as e:
            logger.error(f"Error handling print preview window: {e}")
            return False
            
    def get_print_html(self):
        """Extract the HTML from the print preview"""
        try:
            # Wait longer for the print preview to fully render
            time.sleep(5)
            
            # Get the HTML content
            html_content = self.driver.page_source
            
            # Save to a file with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, f"schedule_printview_{timestamp}.html")
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            logger.info(f"Saved print preview HTML to {output_file}")
            
            # Return the HTML content and file path
            return html_content, output_file
            
        except Exception as e:
            logger.error(f"Error extracting print HTML: {e}")
            return None, None
    
    def get_detailed_schedule(self, username, password, debug=False, pause_after_login=0):
        """Main method to retrieve the detailed schedule"""
        self.debug = debug
        
        try:
            # Setup and login
            if not self.login(username, password):
                logger.error("Login failed, cannot retrieve schedule")
                return None
                
            # Pause after login if requested (for debugging)
            if pause_after_login > 0:
                logger.info(f"Pausing for {pause_after_login} seconds after login (debug mode)")
                time.sleep(pause_after_login)
                
            # Navigate to My Schedule
            if not self.navigate_to_my_schedule():
                logger.error("Failed to navigate to My Schedule page")
                return None
                
            # Open print dialog and get HTML
            if not self.open_print_dialog():
                logger.error("Failed to open print dialog")
                return None
                
            # Extract the HTML from the print preview
            html_content, file_path = self.get_print_html()
            
            if not html_content:
                logger.error("Failed to extract HTML from print preview")
                return None
                
            logger.info("Successfully retrieved detailed schedule")
            return file_path
            
        except Exception as e:
            logger.error(f"Error retrieving detailed schedule: {e}")
            return None
        
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
