#!/usr/bin/env python3
"""
Test script for PWA-only mode
This script tests various routes to ensure they redirect to /get-the-app when PWA-only mode is enabled
"""

import os
import requests
import sys

def test_pwa_only_mode():
    """Test PWA-only mode functionality"""
    
    # Set PWA-only mode
    os.environ['PWA_ONLY_MODE'] = 'true'
    print("🔒 PWA-only mode ENABLED")
    print("=" * 50)
    
    # Base URL - change this to your server URL
    base_url = "http://localhost:5000"  # Change to your server URL
    
    # Routes that should be DISABLED (redirect to /get-the-app)
    disabled_routes = [
        "/",
        "/home", 
        "/login",
        "/signup",
        "/logout",
        "/audit-log",
        "/watchlist",
        "/onboarding",
        "/locations",
        "/lanes",
        "/readers/1",
        "/kyc_users",
        "/analytics/dashboard",
        "/analytics/reports",
        "/analytics/barrier-events",
        "/pricing",
        "/find-vehicle",
        "/admin/restart_readers"
    ]
    
    # Routes that should be ENABLED (PWA routes)
    enabled_routes = [
        "/get-the-app",
        "/pwa-login",
        "/pwa-dashboard",
        "/pwa/vehicle-finder"
    ]
    
    print("❌ Testing DISABLED routes (should redirect to /get-the-app):")
    print("-" * 50)
    
    for route in disabled_routes:
        try:
            response = requests.get(f"{base_url}{route}", allow_redirects=False, timeout=5)
            if response.status_code == 302 and '/get-the-app' in response.headers.get('Location', ''):
                print(f"✅ {route} - Correctly redirected to /get-the-app")
            else:
                print(f"❌ {route} - NOT redirected (Status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  {route} - Error: {e}")
    
    print("\n✅ Testing ENABLED routes (should work normally):")
    print("-" * 50)
    
    for route in enabled_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {route} - Working normally")
            else:
                print(f"❌ {route} - Not working (Status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  {route} - Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 PWA-only mode test completed!")
    print("\nTo disable PWA-only mode:")
    print("  export PWA_ONLY_MODE=false")
    print("  python3 wsgi.py")

if __name__ == "__main__":
    test_pwa_only_mode() 