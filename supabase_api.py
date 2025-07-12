"""
Supabase API endpoints for CCS Hyper.
This module provides all backend routes that interact with the Supabase database.
"""

from flask import Blueprint, request, jsonify
import logging
from supabase_client import SupabaseClient
from enhanced_parser import EnhancedParser
from enhanced_scraper import EnhancedScraper
from google_client import get_google_auth_url, get_credentials_from_code, create_google_calendar_service, add_events_to_calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask Blueprint
supabase_api_blueprint = Blueprint('supabase_api', __name__)

# Get Supabase client
try:
    supabase = SupabaseClient.get_client()
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

# --- User Authentication Routes ---

@supabase_api_blueprint.route('/auth/signup', methods=['POST'])
def signup():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password or not username:
        return jsonify({"error": "Email, password, and username are required"}), 400

    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username
                }
            }
        })
        return jsonify(res.data), 200
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return jsonify({"error": str(e)}), 400

@supabase_api_blueprint.route('/auth/login', methods=['POST'])
def login():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return jsonify(res.data), 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": str(e)}), 401

@supabase_api_blueprint.route('/auth/logout', methods=['POST'])
def logout():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500

    try:
        # The JWT is passed in the Authorization header
        # The client-side will handle removing the token
        # We can call this to invalidate the token on the server if needed
        # supabase.auth.sign_out()
        return jsonify({"message": "Logout successful"}), 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Data Syncing Routes ---

@supabase_api_blueprint.route('/sync/ccs', methods=['POST'])
def sync_from_ccs():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500

    data = request.get_json()
    html_content = data.get('html_content')
    user_id = data.get('user_id') # This should be securely obtained from the auth token

    if not html_content or not user_id:
        return jsonify({"error": "HTML content and user ID are required"}), 400

    try:
        parser = EnhancedParser(html_content)
        pairings_data = parser.parse()

        # Here you would insert/update the data in Supabase
        # This is a simplified example
        for pairing in pairings_data:
            # Check if pairing exists
            existing = supabase.table('pairings').select('id').eq('pairing_code', pairing['pairing_code']).eq('user_id', user_id).execute()
            
            if not existing.data:
                supabase.table('pairings').insert({
                    'user_id': user_id,
                    'pairing_code': pairing['pairing_code'],
                    'start_date': pairing['start_date'],
                    'end_date': pairing['end_date'],
                    # ... other fields
                }).execute()

        return jsonify({"message": f"Successfully synced {len(pairings_data)} pairings."}), 200
    except Exception as e:
        logger.error(f"CCS sync error: {e}")
        return jsonify({"error": "Failed to parse and sync schedule"}), 500

# --- Data Fetching Routes ---

@supabase_api_blueprint.route('/pairings', methods=['GET'])
def get_pairings():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500

    # In a real app, user_id would come from the validated JWT
    user_id = request.headers.get('Authorization').split(' ')[1] # Placeholder

    try:
        res = supabase.table('pairings').select('*').eq('user_id', user_id).order('start_date', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        logger.error(f"Error fetching pairings: {e}")
        return jsonify({"error": "Could not retrieve pairings"}), 500

# --- Google Calendar Integration ---

@supabase_api_blueprint.route('/calendar/auth', methods=['GET'])
def calendar_auth():
    auth_url = get_google_auth_url()
    return jsonify({"auth_url": auth_url})

@supabase_api_blueprint.route('/calendar/callback', methods=['GET'])
def calendar_callback():
    code = request.args.get('code')
    if not code:
        return "Authorization code not found.", 400

    try:
        credentials = get_credentials_from_code(code)
        # Securely store the user's credentials (e.g., in a private table in Supabase)
        # This is a simplified example, do not store tokens in client-side session
        # For demo, we'll just confirm it works and close the window
        return "<script>window.opener.postMessage('google_auth_success', '*'); window.close();</script>"
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        return "<script>window.opener.postMessage('google_auth_error', '*'); window.close();</script>"

@supabase_api_blueprint.route('/calendar/push', methods=['POST'])
def calendar_push():
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500

    data = request.get_json()
    user_id = data.get('user_id') # From auth token
    google_credentials = data.get('credentials') # Should be retrieved securely

    if not user_id or not google_credentials:
        return jsonify({"error": "User ID and Google credentials are required"}), 400

    try:
        # Fetch pairings from Supabase
        pairings_res = supabase.table('pairings').select('*').eq('user_id', user_id).execute()
        pairings = pairings_res.data

        # Create Google Calendar service
        service = create_google_calendar_service(google_credentials)

        # Add events
        count = add_events_to_calendar(service, pairings)

        return jsonify({"message": f"Successfully pushed {count} trips to your calendar."}), 200
    except Exception as e:
        logger.error(f"Calendar push error: {e}")
        return jsonify({"error": "Failed to push events to calendar"}), 500
