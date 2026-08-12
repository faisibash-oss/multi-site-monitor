#!/usr/bin/env python3
"""
ga4_auth_test.py

GA4 (Google Analytics Data API) OAuth flow, mirroring gsc_auth_test.py:
  - reuses the same credentials.json OAuth client (adds the GA4 read-only scope)
  - takes a site label as a CLI arg
  - saves a per-site token file: token_ga4_<site>.json
    (deliberately NOT token_<site>.json, since that name is already
    taken by the GSC token for the same site)
  - wraps the API test call in the same retry pattern used for the
    intermittent httplib2 timeouts on the GSC side

Usage:
    python ga4_auth_test.py aireadypage
    python ga4_auth_test.py tracycarpetcare
    python ga4_auth_test.py hypicsmodapk
GA4 property IDs are NOT hardcoded here — they're read from config.json
(gitignored, same as credentials.json and the token files) so they never
get staged or pushed.
"""

import argparse
import json
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
CREDENTIALS_FILE = "credentials.json"
CONFIG_FILE = "config.json"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def load_property_ids() -> dict:
    if not os.path.exists(CONFIG_FILE):
        sys.exit(
            f"Missing {CONFIG_FILE}. Copy config.json.example to {CONFIG_FILE} "
            "and fill in each site's GA4 property ID (Admin > Property Settings)."
        )
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return config.get("ga4_property_ids", {})


GA4_PROPERTY_IDS = load_property_ids()


def token_path(site: str) -> str:
    return f"token_ga4_{site}.json"


def get_credentials(site: str) -> Credentials:
    """Load, refresh, or create OAuth credentials for the given site."""
    creds = None
    path = token_path(site)

    if os.path.exists(path):
        creds = Credentials.from_authorized_user_file(path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(f"Missing {CREDENTIALS_FILE} — same OAuth client used for GSC.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            print("\nOpen this URL in the browser where you're already signed in:\n", flush=True)
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(path, "w") as f:
            f.write(creds.to_json())

    return creds


def with_retries(func, *args, **kwargs):
    """Same retry wrapper pattern as the GSC script, for intermittent timeouts."""
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except (httplib2.error.ServerNotFoundError, TimeoutError, ConnectionError) as e:
            last_err = e
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed ({e}); retrying in {RETRY_DELAY_SECONDS}s...")
            time.sleep(RETRY_DELAY_SECONDS)
    raise last_err


def test_ga4_connection(site: str) -> None:
    property_id = GA4_PROPERTY_IDS.get(site)
    if not property_id:
        sys.exit(f"No GA4 property ID set for '{site}' — fill in GA4_PROPERTY_IDS first.")

    creds = get_credentials(site)
    service = build("analyticsdata", "v1beta", credentials=creds)

    def run_report():
        return service.properties().runReport(
            property=f"properties/{property_id}",
            body={
                "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                "metrics": [{"name": "activeUsers"}],
            },
        ).execute()

    try:
        result = with_retries(run_report)
    except HttpError as e:
        sys.exit(f"GA4 API error for {site}: {e}")

    rows = result.get("rows", [])
    users = rows[0]["metricValues"][0]["value"] if rows else "0"
    print(f"[{site}] OAuth OK — token saved to {token_path(site)}")
    print(f"[{site}] Active users (last 7 days): {users}")


def main():
    parser = argparse.ArgumentParser(description="GA4 OAuth test, per-site.")
    parser.add_argument("site", choices=list(GA4_PROPERTY_IDS.keys()))
    args = parser.parse_args()
    test_ga4_connection(args.site)


if __name__ == "__main__":
    main()
