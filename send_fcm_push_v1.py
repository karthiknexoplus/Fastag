#!/usr/bin/env python3
"""
Send a test push notification to all FCM tokens using the HTTP v1 API and a Google service account.
"""
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

# TODO: Fill in your service account JSON file path and Firebase project ID
SERVICE_ACCOUNT_FILE = 'path/to/your-service-account.json'
FIREBASE_PROJECT_ID = 'your-firebase-project-id'

FCM_ENDPOINT = f'https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send'

# Load tokens
with open('fcm_tokens.json', 'r') as f:
    tokens = json.load(f)

if not tokens:
    print("No FCM tokens found. Please enable push notifications in your PWA first.")
    exit(1)

print(f"Found {len(tokens)} FCM token(s)")

# Authenticate with service account
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
request = google.auth.transport.requests.Request()
credentials.refresh(request)
access_token = credentials.token

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json; UTF-8"
}

# Send a notification to each token
for token in tokens:
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": "FASTag Test Notification",
                "body": "This is a test push notification from your FASTag PWA!"
            },
            "webpush": {
                "fcm_options": {
                    "link": "https://your-pwa-url/"
                }
            }
        }
    }
    response = requests.post(FCM_ENDPOINT, headers=headers, json=message)
    print(f"Token: {token[:20]}... Response: {response.status_code}")
    print(response.text) 