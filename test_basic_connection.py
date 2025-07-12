import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
BASE_URL = "http://127.0.0.1:5000"

def test_health_check():
    """Tests the basic health check endpoint."""
    endpoint = f"{BASE_URL}/health"
    try:
        logger.info(f"Pinging health check endpoint: {endpoint}")
        response = requests.get(endpoint, timeout=5)
        
        if response.status_code == 200:
            logger.info("Health check PASSED. Server is up and running.")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"Health check FAILED. Status Code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Health check FAILED. Could not connect to the server at {BASE_URL}.")
        logger.error(f"Error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during health check: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting connection tests...")
    test_health_check()
