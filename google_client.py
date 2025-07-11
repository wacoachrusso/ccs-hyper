"""Helper functions for Google Calendar OAuth flow and service creation."""
import os
import datetime as dt
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Full access to manage events (insert / update / delete)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Accept either filename so users don't have to rename files
DEFAULT_CLIENT_SECRETS_FILE = "client_secret.json"
ALTERNATE_CLIENT_SECRETS_FILE = "credentials.json"
if os.path.exists(DEFAULT_CLIENT_SECRETS_FILE):
    CLIENT_SECRETS_FILE = DEFAULT_CLIENT_SECRETS_FILE
elif os.path.exists(ALTERNATE_CLIENT_SECRETS_FILE):
    CLIENT_SECRETS_FILE = ALTERNATE_CLIENT_SECRETS_FILE
else:
    # Fall back to default name; an explicit error will be raised later if file truly missing
    CLIENT_SECRETS_FILE = DEFAULT_CLIENT_SECRETS_FILE
TOKEN_FILE = "token.json"  # For single-user desktop use. Replace with per-user storage in production.


def get_flow() -> Flow:
    """Return an OAuth 2.0 Flow object configured for installed-app flow."""
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://127.0.0.1:5001/oauth2callback",  # matches Flask route
    )


def save_credentials(creds: Credentials) -> None:
    """Save credentials to TOKEN_FILE (in JSON)."""
    with open(TOKEN_FILE, "w", encoding="utf-8") as token:
        token.write(creds.to_json())


def load_credentials() -> Optional[Credentials]:
    """Load credentials from TOKEN_FILE if they exist and are valid.

    Refreshes the access token automatically if needed.
    Returns None if no valid credentials are available.
    """
    if not os.path.exists(TOKEN_FILE):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
    return creds


def build_calendar_service() -> Optional[object]:
    """Return a shiny Calendar v3 service instance or None if not authorised."""
    creds = load_credentials()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
