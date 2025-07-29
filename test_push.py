#!/usr/bin/env python3
"""
Test script to send push notifications to all saved subscriptions
"""
import json
import sys
import os

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    print("pywebpush not installed. Install with: pip install pywebpush")
    sys.exit(1)

def send_test_notification():
    # Load VAPID private key
    with open('vapid_private.pem', 'r') as f:
        vapid_private = f.read()
    
    # Load subscriptions
    subs_file = 'push_subscriptions.json'
    if not os.path.exists(subs_file):
        print(f"No subscriptions found in {subs_file}")
        print("Please enable push notifications in the PWA first.")
        return
    
    with open(subs_file, 'r') as f:
        subscriptions = json.load(f)
    
    if not subscriptions:
        print("No subscriptions found. Please enable push notifications in the PWA first.")
        return
    
    print(f"Found {len(subscriptions)} subscription(s)")
    
    # Send test notification
    message = {
        "title": "FASTag Test Notification",
        "body": "This is a test push notification from your FASTag PWA!",
        "url": "/"
    }
    
    success_count = 0
    for i, sub in enumerate(subscriptions):
        try:
            webpush(
                sub,
                json.dumps(message),
                vapid_private_key=vapid_private,
                vapid_claims={"sub": "mailto:test@fastag.com"}
            )
            print(f"✓ Notification sent to subscription {i+1}")
            success_count += 1
        except WebPushException as ex:
            print(f"✗ Failed to send to subscription {i+1}: {ex}")
        except Exception as e:
            print(f"✗ Error with subscription {i+1}: {e}")
    
    print(f"\nSent {success_count}/{len(subscriptions)} notifications successfully!")

if __name__ == "__main__":
    send_test_notification() 