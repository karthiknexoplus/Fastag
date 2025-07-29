#!/usr/bin/env python3
"""
Send a test push notification to all FCM tokens using the HTTP v1 API and a Google service account.
"""
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import random

# TODO: Fill in your service account JSON file path and Firebase project ID
SERVICE_ACCOUNT_FILE = 'pwapush-4e4e4-5a979a55d9d3.json'
FIREBASE_PROJECT_ID = 'pwapush-4e4e4'

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

# List of 10 different push notification messages
MESSAGES = [
    {
        "title": "🚗 Onebee Parking Update",
        "body": "Dear Onebee User,\n\nExperience our world-class parking management system at your esteemed premises! ✨\n\nStay tuned for more updates from Onebee.\n\nBest Regards,\nTeam Onebee 🅿️🚦",
        "link": "https://www.onebee.in/"
    },
    {
        "title": "🅿️ Hassle-Free Parking Awaits!",
        "body": "Hello from Onebee!\n\nEnjoy seamless entry and exit at your location. Your convenience is our priority.\n\nKeep in touch for exciting features! 🚦",
        "link": "https://www.onebee.in/parking"
    },
    {
        "title": "✨ Welcome to Onebee!",
        "body": "Dear User,\n\nThank you for choosing Onebee for your parking needs. Discover smart, secure, and efficient parking today!\n\nTeam Onebee 🚗",
        "link": "https://www.onebee.in/welcome"
    },
    {
        "title": "🚦 Parking Just Got Smarter!",
        "body": "Hi!\n\nUnlock the power of technology with Onebee’s advanced parking management.\n\nStay tuned for more updates! ✨",
        "link": "https://www.onebee.in/smart"
    },
    {
        "title": "🔔 Onebee Notification",
        "body": "Dear User,\n\nYour parking experience is about to get even better. Watch this space for new features and offers!\n\nBest, Team Onebee 🅿️",
        "link": "https://www.onebee.in/updates"
    },
    {
        "title": "🌟 Premium Parking Experience",
        "body": "Hello!\n\nEnjoy premium parking services at your premises with Onebee.\n\nContact us for feedback or support! 🚗",
        "link": "https://www.onebee.in/support"
    },
    {
        "title": "🚗 Your Spot Awaits!",
        "body": "Dear Onebee User,\n\nYour reserved parking spot is ready. Enjoy a smooth and secure experience every time.\n\nTeam Onebee 🚦",
        "link": "https://www.onebee.in/reserve"
    },
    {
        "title": "💡 Did You Know?",
        "body": "Onebee offers real-time parking analytics and easy access control.\n\nExplore more on our website! 🌐",
        "link": "https://www.onebee.in/features"
    },
    {
        "title": "🎉 Thank You for Choosing Onebee!",
        "body": "We appreciate your trust in our parking solutions.\n\nStay connected for exclusive updates and offers! 🅿️",
        "link": "https://www.onebee.in/thankyou"
    },
    {
        "title": "🚀 Upgrade Your Parking!",
        "body": "Hi!\n\nUpgrade to Onebee’s smart parking for a seamless experience.\n\nVisit us for more info! ✨",
        "link": "https://www.onebee.in/upgrade"
    }
]

# Send a notification to each token
for token in tokens:
    msg = random.choice(MESSAGES)
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": msg["title"],
                "body": msg["body"]
            },
            "webpush": {
                "fcm_options": {
                    "link": msg["link"]
                }
            }
        }
    }
    response = requests.post(FCM_ENDPOINT, headers=headers, json=message)
    print(f"Token: {token[:20]}... Response: {response.status_code}")
    print(response.text) 