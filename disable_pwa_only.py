#!/usr/bin/env python3
"""
Script to disable PWA-only mode
"""

import os

def disable_pwa_only():
    """Disable PWA-only mode"""
    os.environ['PWA_ONLY_MODE'] = 'false'
    print("✅ PWA-only mode DISABLED")
    print("🌐 All routes are now accessible")

if __name__ == "__main__":
    disable_pwa_only() 