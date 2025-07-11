from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from scraper import get_schedule
from parser import parse_schedule
from ics import Calendar, Event
from google_client import get_flow, save_credentials, build_calendar_service
import os
import arrow
import re

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

# --- Web pages ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync', methods=['POST'])
def sync():
    username = request.form['username']
    password = request.form['password']
    
    try:
        html_content, status = get_schedule(username, password)

        if status != "SUCCESS" or not html_content:
            error_message = status if status != "SUCCESS" else "Scraper returned no data."
            raise ValueError(error_message)

        # Save the raw HTML for debugging
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Parse the schedule
        schedule_data = parse_schedule(html_content)
        print(f"Parsed {len(schedule_data)} events from schedule.")

        if not schedule_data:
            return jsonify({'error': 'Could not find any schedule data to parse. Please check debug_page.html.'}), 404

        return jsonify({'events': schedule_data})

    except Exception as e:
        print(f"Error in /sync: {e}")
        return jsonify({'error': str(e)}), 500

# --- Google OAuth routes ---
@app.route('/authorize')
def authorize():
    # Step 1: Start OAuth flow
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return jsonify({'auth_url': auth_url})


@app.route('/oauth2callback')
def oauth2callback():
    # Step 2: Google redirected back with code
    flow = get_flow()
    flow.fetch_token(code=request.args.get('code'))
    creds = flow.credentials
    save_credentials(creds)
    return render_template('close_popup.html')  # simple page telling user they can close window


@app.route('/push', methods=['POST'])
def push_to_google():
    """Parse schedule and insert events into the user's Google Calendar.
    
    This function will first delete existing events created by CCS Hyper
    and then add selected events to ensure schedule changes are reflected.
    
    Options:
    - preserve_past: If true, past trips will not be deleted (default: false)
    - selected_events: If provided, only these events will be inserted (optional)
    """
    creds_service = build_calendar_service()
    if not creds_service:
        return jsonify({'error': 'Not authorised with Google yet.'}), 403

    events_data = request.get_json()
    if not events_data or 'events' not in events_data:
        return jsonify({'error': 'No event data provided'}), 400
    
    # Get sync options
    preserve_past = events_data.get('preserve_past', False)
    selected_indices = events_data.get('selected_indices', None)
    
    events = events_data['events']
    if not events:
        return jsonify({'error': 'No schedule data found'}), 404
        
    # If specific events were selected, only use those
    if selected_indices is not None:
        try:
            selected_indices = [int(i) for i in selected_indices]
            events = [events[i] for i in selected_indices if i < len(events)]
            if not events:
                return jsonify({'error': 'No events selected for sync'}), 400
        except Exception as e:
            return jsonify({'error': f'Invalid selected_indices: {e}'}), 400

    # Constants for event identification
    calendar_id = 'primary'
    APP_EVENT_PREFIX = "TRIP:" # How we identify our app's events
    
    # Step 1: Find and delete all existing events created by our app
    # Set time bounds for search
    now = arrow.now()
    
    # If preserving past trips, only delete future trips
    if preserve_past:
        time_min = now.isoformat()
        print("Preserving past trips - only deleting future trips")
    else:
        # Otherwise look from 2 months ago to clean up all trips
        time_min = now.shift(months=-2).isoformat()
        
    # Always look up to a year ahead
    time_max = now.shift(years=1).isoformat()
    
    # Search for events with our prefix in the title
    print("Searching for existing events to clean up...")
    deleted = 0
    page_token = None
    
    try:
        while True:
            events_result = creds_service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                q=APP_EVENT_PREFIX,  # Search for our event prefix
                singleEvents=True,
                pageToken=page_token
            ).execute()
            
            old_events = events_result.get('items', [])
            
            # Delete each event created by our app
            for old_event in old_events:
                if old_event.get('summary', '').startswith(APP_EVENT_PREFIX):
                    try:
                        creds_service.events().delete(
                            calendarId=calendar_id,
                            eventId=old_event['id']
                        ).execute()
                        deleted += 1
                    except Exception as e:
                        print(f"Failed to delete event {old_event.get('id')}: {e}")
            
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break
                
        print(f"Deleted {deleted} old events")
    except Exception as e:
        print(f"Error during event cleanup: {e}")

    # Step 2: Insert new events
    inserted = 0
    for event in events:
        try:
            # Make sure all our events have the prefix so we can find them later
            if 'summary' in event and not event['summary'].startswith(APP_EVENT_PREFIX):
                event['summary'] = f"{APP_EVENT_PREFIX} {event['summary']}"
                
            # Add a custom property to identify our app's events
            if 'extendedProperties' not in event:
                event['extendedProperties'] = {
                    'private': {'createdBy': 'CCS-Hyper'}
                }
            else:
                if 'private' not in event['extendedProperties']:
                    event['extendedProperties']['private'] = {'createdBy': 'CCS-Hyper'}
                else:
                    event['extendedProperties']['private']['createdBy'] = 'CCS-Hyper'
                    
            creds_service.events().insert(calendarId=calendar_id, body=event).execute()
            inserted += 1
        except Exception as e:
            print(f"Google insert failed for event {event.get('summary')}: {e}")

    return jsonify({'inserted': inserted, 'deleted': deleted})


if __name__ == '__main__':
    app.run(debug=True, port=5001) # Using a different port to avoid conflict with the previous run
