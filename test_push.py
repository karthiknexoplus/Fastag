#!/usr/bin/env python3
"""
Test script to send push notifications to all saved subscriptions
"""
import json
import sys
import os
import argparse

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    print("pywebpush not installed. Install with: pip install pywebpush")
    sys.exit(1)

def load_private_key(key_path):
    try:
        with open(key_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Failed to load private key from {key_path}: {e}")
        return None

def send_test_notification(key_path):
    # Load VAPID private key (try PKCS#8 first, then EC)
    vapid_private = load_private_key(key_path)
    if not vapid_private:
        print(f"Could not load VAPID private key from {key_path}")
        return
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
    parser = argparse.ArgumentParser(description="Send test push notifications to all saved subscriptions.")
    parser.add_argument('--key', type=str, default='vapid_private.pem', help='Path to VAPID private key (PEM)')
    args = parser.parse_args()
    send_test_notification(args.key) 