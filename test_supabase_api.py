import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://127.0.0.1:5000/supabase"

# --- Test Data ---
# This should be a valid JWT from a test user in your Supabase project
TEST_JWT = os.getenv("TEST_USER_JWT")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TEST_JWT}"
}

# --- Helper Functions ---
def print_test_result(test_name, success, response):
    status = "PASSED" if success else "FAILED"
    print(f"--- Test: {test_name} --- [{status}] ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response Text: {response.text}")
    print("--------------------------------------------------\n")

# --- Test Cases ---

def test_get_user():
    """Tests the /user endpoint to retrieve authenticated user data."""
    response = requests.get(f"{BASE_URL}/user", headers=HEADERS)
    success = response.status_code == 200 and 'id' in response.json()
    print_test_result("Get User", success, response)

def test_sync_schedule():
    """Tests the /sync-schedule endpoint."""
    # This test requires a valid CCS schedule HTML file.
    # For this example, we'll simulate a failure case without the file.
    response = requests.post(f"{BASE_URL}/sync-schedule", headers=HEADERS, json={})
    success = response.status_code == 400 # Expecting bad request without content
    print_test_result("Sync Schedule (No Content)", success, response)

def test_get_pairings():
    """Tests the /pairings endpoint."""
    response = requests.get(f"{BASE_URL}/pairings", headers=HEADERS)
    success = response.status_code == 200 and isinstance(response.json(), list)
    print_test_result("Get Pairings", success, response)

if __name__ == "__main__":
    if not TEST_JWT:
        print("ERROR: TEST_USER_JWT environment variable not set. Cannot run authenticated tests.")
    else:
        print("Starting Supabase API tests...\n")
        test_get_user()
        test_sync_schedule()
        test_get_pairings()
