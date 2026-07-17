import os
import json
import logging

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from utils.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID,
    GOOGLE_REDIRECT_URI, CREDENTIALS_DIR, GOOGLE_AUTH_URI, GOOGLE_TOKEN_URI
)

logger = logging.getLogger(__name__)

# The scopes define the permissions the bot is asking for.
# Be specific and request only what you need.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
]

def get_google_auth_url(user_id: str) -> str:
    """Generates the Google OAuth2 authorization URL."""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "project_id": GOOGLE_PROJECT_ID,
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    flow.access_type = 'offline'
    flow.prompt = 'consent'
    flow.state = user_id

    authorization_url, _ = flow.authorization_url()
    return authorization_url

def save_google_credentials(user_id: str, code: str):
    """Exchanges the authorization code for credentials and saves them."""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "project_id": GOOGLE_PROJECT_ID,
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(code=code)
    creds_data = {
        'token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'token_uri': flow.credentials.token_uri,
        'client_id': flow.credentials.client_id,
        'client_secret': flow.credentials.client_secret,
        'scopes': flow.credentials.scopes
    }

    creds_path = os.path.join(CREDENTIALS_DIR, f"{user_id}.json")
    with open(creds_path, 'w') as f:
        json.dump(creds_data, f)
    logger.info(f"Saved credentials for user {user_id} to {creds_path}")

def get_credentials_for_user(user_id: str) -> Credentials:
    """Loads and returns credentials for a specific user, refreshing if necessary."""
    creds_path = os.path.join(CREDENTIALS_DIR, f"{user_id}.json")
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"No credentials found for user {user_id}. Please re-authorize via /start.")

    creds = Credentials.from_authorized_user_file(creds_path, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        logger.info(f"Credentials for user {user_id} expired. Refreshing...")
        creds.refresh(Request())
        creds_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        with open(creds_path, 'w') as f:
            json.dump(creds_data, f)
        logger.info(f"Refreshed and saved credentials for user {user_id}.")

    return creds

def get_google_service(user_id: str, service_name: str, version: str):
    """Builds and returns an authorized Google API service client."""
    credentials = get_credentials_for_user(user_id)
    service = build(service_name, version, credentials=credentials, static_discovery=False)
    return service
