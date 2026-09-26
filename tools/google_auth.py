"""
Google OAuth helper for WAT framework tools.

Manages authentication flow using Google's OAuth 2.0 installed-app pattern.
Caches credentials in token.json and refreshes as needed.

Usage:
    from tools.google_auth import get_credentials

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/presentations'
    ]
    credentials = get_credentials(scopes)
    # Now use credentials with googleapiclient services
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_credentials(scopes, credentials_file="credentials.json", token_file="token.json"):
    """
    Get Google API credentials, using cached token if available.

    Falls back to OAuth flow if:
    - No cached token exists
    - Token is expired and cannot be refreshed

    Args:
        scopes: List of OAuth scopes (e.g.,
                ['https://www.googleapis.com/auth/spreadsheets'])
        credentials_file: Path to downloaded OAuth client secret JSON
                         (download from Google Cloud Console)
        token_file: Path to cache refreshed tokens

    Returns:
        google.oauth2.credentials.Credentials object ready to use with services

    Raises:
        FileNotFoundError: If credentials_file does not exist
    """
    creds = None
    project_root = Path(__file__).parent.parent

    credentials_path = project_root / credentials_file
    token_path = project_root / token_file

    # Load cached token if it exists
    if token_path.exists():
        creds = UserCredentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"OAuth credentials file not found: {credentials_path}\n"
                    "Download it from Google Cloud Console and save it as "
                    "'credentials.json' in the project root."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), scopes
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds
