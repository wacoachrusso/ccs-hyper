import os
import sys
import logging
import time
from enhanced_scraper import CcsScraper
from getpass import getpass
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"ccs_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

def main():
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Ask for credentials
    print("\n=== CCS Hyper Schedule Extractor ===")
    print("Please enter your CCS credentials:")
    username = input("Username: ")
    password = getpass("Password: ")
    
    # Initialize scraper with headless=False to see the browser
    print("\nStarting browser automation...")
    scraper = None
    result_file = None
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"\n=== Attempt {attempt}/{MAX_ATTEMPTS} ===")
            print(f"\nAttempt {attempt}/{MAX_ATTEMPTS} to extract schedule data...")
            
            # Create a new scraper instance for each attempt
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
                    
            scraper = CcsScraper(headless=False, debug=True)
            
            # Run the extraction with increased timeouts for each retry
            result_file = scraper.get_detailed_schedule(
                username, 
                password, 
                debug=True, 
                pause_after_login=2
            )
            
            if result_file:
                logger.info(f"SUCCESS! Schedule data extracted on attempt {attempt}")
                print(f"\n✅ SUCCESS! Schedule data extracted successfully!")
                print(f"📄 Output file: {result_file}")
                break
            else:
                logger.warning(f"Attempt {attempt} failed, schedule data not extracted")
                if attempt < MAX_ATTEMPTS:
                    logger.info(f"Waiting 5 seconds before retry...")
                    time.sleep(5)
        
        except Exception as e:
            logger.error(f"Exception during attempt {attempt}: {str(e)}")
            if attempt < MAX_ATTEMPTS:
                logger.info(f"Waiting 5 seconds before retry...")
                time.sleep(5)
    
    if not result_file:
        logger.error(f"All {MAX_ATTEMPTS} attempts failed")
        print(f"\n❌ ERROR: Failed to extract schedule data after {MAX_ATTEMPTS} attempts.")
        print("Please check the logs for more details.")
    
    # Always close the browser
    if scraper:
        print("\nClosing browser...")
        try:
            scraper.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        
    print("\nTest completed.")

if __name__ == "__main__":
    main()
