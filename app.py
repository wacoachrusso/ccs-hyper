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
    """Parse schedule and insert events into the user's Google Calendar."""
    creds_service = build_calendar_service()
    if not creds_service:
        return jsonify({'error': 'Not authorised with Google yet.'}), 403

    events_data = request.get_json()
    if not events_data or 'events' not in events_data:
        return jsonify({'error': 'No event data provided'}), 400
    events = events_data['events']
    if not events:
        return jsonify({'error': 'No schedule data found'}), 404

    calendar_id = 'primary'
    inserted = 0
    for event in events:
        try:
            creds_service.events().insert(calendarId=calendar_id, body=event).execute()
            inserted += 1
        except Exception as e:
            print(f"Google insert failed for event {event.get('summary')}: {e}")

    return jsonify({'inserted': inserted})


if __name__ == '__main__':
    app.run(debug=True, port=5001) # Using a different port to avoid conflict with the previous run
