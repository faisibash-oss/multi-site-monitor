import os
import socket
import sys
import time

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CREDENTIALS_FILE = "credentials.json"
RETRYABLE_ERRORS = (socket.timeout, TimeoutError, ConnectionError, httplib2.HttpLib2Error)


def call_with_retry(func, attempts=3, delay=2):
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except RETRYABLE_ERRORS as exc:
            if attempt == attempts:
                raise
            print(f"Network error ({exc}), retrying ({attempt}/{attempts - 1})...")
            time.sleep(delay)


def get_credentials(token_file):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "aireadypage"
    token_file = f"token_{label}.json"

    print(f"Running for site label: {label} (token file: {token_file})")

    creds = get_credentials(token_file)
    service = build("searchconsole", "v1", credentials=creds)

    site_list = call_with_retry(lambda: service.sites().list().execute())
    entries = site_list.get("siteEntry", [])

    if not entries:
        print("No verified Search Console properties found for this account.")
        return

    print("Verified Search Console properties:")
    for entry in entries:
        print(f"- {entry['siteUrl']} (permission: {entry['permissionLevel']})")


if __name__ == "__main__":
    main()
