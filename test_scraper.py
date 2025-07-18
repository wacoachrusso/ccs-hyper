import os
import sys
import logging
from enhanced_scraper import CcsScraper
from getpass import getpass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    scraper = CcsScraper(headless=False, debug=True)
    
    try:
        # Run the extraction
        print("\nAttempting to extract schedule data...")
        result_file = scraper.get_detailed_schedule(username, password, debug=True, pause_after_login=2)
        
        if result_file:
            print(f"\n✅ SUCCESS! Schedule data extracted successfully!")
            print(f"📄 Output file: {result_file}")
        else:
            print("\n❌ ERROR: Failed to extract schedule data.")
            print("Please check the logs for more details.")
    
    except Exception as e:
        print(f"\n❌ ERROR: An exception occurred: {str(e)}")
    
    finally:
        # Always close the browser
        print("\nClosing browser...")
        scraper.close()
        
    print("\nTest completed.")

if __name__ == "__main__":
    main()
