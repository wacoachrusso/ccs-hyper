"""Helper functions for Google Calendar OAuth flow and service creation."""

import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CLIENT_SECRETS_FILE = 'credentials.json' # Standard name
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
REDIRECT_URI = 'http://localhost:5001/api/google-callback' # Should match your setup

def get_google_auth_url():
    """Get the Google authentication URL for the user to visit."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    except FileNotFoundError:
        logger.error(f"'{CLIENT_SECRETS_FILE}' not found. Please add your Google API credentials.")
        raise
    except Exception as e:
        logger.error(f"Error creating auth URL: {e}")
        raise

def get_credentials_from_code(code):
    """Exchange an authorization code for credentials."""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    return flow.credentials

def create_google_calendar_service(credentials):
    """Create a Google Calendar service object from credentials."""
    # If credentials are a dict, convert them back to a Credentials object
    if isinstance(credentials, dict):
        credentials = Credentials(**credentials)
    
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    return service

def get_user_info(service):
    """Get user's email address from the service object."""
    user_info_service = build('oauth2', 'v2', credentials=service._credentials)
    user_info = user_info_service.userinfo().get().execute()
    return user_info

def add_events_to_calendar(service, pairings):
    """Adds a list of pairing events to the user's 'CCS Hyper' calendar."""
    # Find or create the 'CCS Hyper' calendar
    calendar_list = service.calendarList().list().execute()
    ccs_calendar_id = None
    for calendar_entry in calendar_list.get('items', []):
        if calendar_entry['summary'] == 'CCS Hyper':
            ccs_calendar_id = calendar_entry['id']
            break
    
    if not ccs_calendar_id:
        new_calendar = {'summary': 'CCS Hyper', 'timeZone': 'America/New_York'}
        created_calendar = service.calendars().insert(body=new_calendar).execute()
        ccs_calendar_id = created_calendar['id']
        logger.info("Created 'CCS Hyper' calendar")

    # Clear old events (optional, implement based on user preference)
    # ...

    # Add new events
    count = 0
    for pairing in pairings:
        event = {
            'summary': f"Trip: {pairing['pairing_code']}",
            'description': pairing.get('description', ''),
            'start': {
                'date': pairing['start_date'],
                'timeZone': 'America/New_York',
            },
            'end': {
                'date': pairing['end_date'],
                'timeZone': 'America/New_York',
            },
            'reminders': {'useDefault': False},
        }
        service.events().insert(calendarId=ccs_calendar_id, body=event).execute()
        count += 1
    
    logger.info(f"Successfully added {count} trips to the calendar")
    return count
