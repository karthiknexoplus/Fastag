#!/usr/bin/env python3
"""
Send a test push notification to all FCM tokens saved in fcm_tokens.json
"""
import json
import requests

# TODO: Fill in your FCM server key here
FCM_SERVER_KEY = "YOUR_FCM_SERVER_KEY_HERE"

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"

# Load tokens
with open('fcm_tokens.json', 'r') as f:
    tokens = json.load(f)

if not tokens:
    print("No FCM tokens found. Please enable push notifications in your PWA first.")
    exit(1)

print(f"Found {len(tokens)} FCM token(s)")

# Prepare notification payload
payload = {
    "registration_ids": tokens,
    "notification": {
        "title": "FASTag Test Notification",
        "body": "This is a test push notification from your FASTag PWA!",
        "icon": "/static/icons/icon-192x192.png"
    }
}

headers = {
    "Authorization": f"key={FCM_SERVER_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(FCM_ENDPOINT, headers=headers, json=payload)

print(f"Response status: {response.status_code}")
print(response.text) 