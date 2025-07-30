#!/usr/bin/env python3
"""
Script to enable/disable PWA-only mode
When PWA-only mode is enabled, only /get-the-app and PWA routes work.
All other routes redirect to /get-the-app
"""

import os
import sys

def enable_pwa_only():
    """Enable PWA-only mode"""
    os.environ['PWA_ONLY_MODE'] = 'true'
    print("✅ PWA-only mode ENABLED")
    print("📱 Only /get-the-app and PWA routes will work")
    print("🌐 All other routes will redirect to /get-the-app")
    print("\nTo disable, run: python3 disable_pwa_only.py")

def disable_pwa_only():
    """Disable PWA-only mode"""
    os.environ['PWA_ONLY_MODE'] = 'false'
    print("✅ PWA-only mode DISABLED")
    print("🌐 All routes are now accessible")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "disable":
        disable_pwa_only()
    else:
        enable_pwa_only() 