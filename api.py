from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging

from scraper import scrape_schedule
from parser import parse_and_group_schedule
from google_client import get_google_auth_url, get_google_credentials, create_google_calendar_service, get_user_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/sync-schedule', methods=['POST'])
def sync_schedule():
    logger.info("Received request to /api/sync-schedule")
    if 'scheduleFile' not in request.files:
        logger.warning("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['scheduleFile']
    if file.filename == '':
        logger.warning("No selected file")
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved to {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Use the new parser
            trips, month, year = parse_and_group_schedule(html_content)
            session['trips_data'] = trips
            session['month'] = month
            session['year'] = year
            
            logger.info(f"Parsed {len(trips)} trips for {month}/{year}")
            
            auth_url = get_google_auth_url()
            return jsonify({"auth_url": auth_url, "trips_found": len(trips)})
        except Exception as e:
            logger.error(f"Error processing schedule file: {e}", exc_info=True)
            return jsonify({"error": "Failed to process schedule file."}), 500

@app.route('/api/google-callback')
def google_callback():
    logger.info("Received request to /api/google-callback")
    try:
        credentials = get_google_credentials(request.url)
        session['google_credentials'] = credentials_to_dict(credentials)
        
        service = create_google_calendar_service(credentials)
        user_info = get_user_info(service)
        session['user_email'] = user_info.get('email', 'Unknown User')
        
        logger.info(f"Google authentication successful for {session['user_email']}")
        return "<script>window.opener.postMessage('auth_success', '*'); window.close();</script>"
    except Exception as e:
        logger.error(f"Error during Google callback: {e}", exc_info=True)
        return "<script>window.opener.postMessage('auth_error', '*'); window.close();</script>"

@app.route('/api/push-to-calendar', methods=['POST'])
def push_to_calendar():
    logger.info("Received request to /api/push-to-calendar")
    if 'google_credentials' not in session or 'trips_data' not in session:
        logger.warning("Session data missing for calendar push")
        return jsonify({"error": "Authentication or trip data is missing. Please sync again."}), 400

    try:
        credentials = session['google_credentials']
        service = create_google_calendar_service(credentials)
        trips = session['trips_data']
        month = session['month']
        year = session['year']
        
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

        # Clear old events from the calendar for the specific month/year
        time_min = f"{year}-{month:02d}-01T00:00:00Z"
        time_max = f"{year}-{month:02d}-31T23:59:59Z"
        events_result = service.events().list(calendarId=ccs_calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True).execute()
        for event in events_result.get('items', []):
            service.events().delete(calendarId=ccs_calendar_id, eventId=event['id']).execute()
        logger.info(f"Cleared old events for {month}/{year} from 'CCS Hyper' calendar")

        # Add new events
        for trip in trips:
            event = {
                'summary': f"Trip: {trip['pairing_code']}",
                'description': trip['description'],
                'start': {
                    'date': trip['start_date'],
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'date': trip['end_date'],
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                },
            }
            service.events().insert(calendarId=ccs_calendar_id, body=event).execute()
        
        logger.info(f"Successfully added {len(trips)} trips to the calendar")
        return jsonify({"message": f"Successfully added {len(trips)} trips to your 'CCS Hyper' calendar.", "user": session.get('user_email')})

    except Exception as e:
        logger.error(f"Error pushing to calendar: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while adding events to your calendar."}), 500

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run(debug=True, port=5001)
