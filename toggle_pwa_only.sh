#!/bin/bash

# Toggle PWA-only mode script
# This script sets the PWA_ONLY_MODE environment variable

if [ "$1" = "enable" ]; then
    export PWA_ONLY_MODE=true
    echo "✅ PWA-only mode ENABLED"
    echo "📱 Only /get-the-app and PWA routes will work"
    echo "🌐 All other routes will redirect to /get-the-app"
    echo ""
    echo "To run the app with this setting:"
    echo "PWA_ONLY_MODE=true python3 wsgi.py"
    echo ""
    echo "To disable: ./toggle_pwa_only.sh disable"
elif [ "$1" = "disable" ]; then
    export PWA_ONLY_MODE=false
    echo "✅ PWA-only mode DISABLED"
    echo "🌐 All routes are now accessible"
    echo ""
    echo "To run the app with this setting:"
    echo "PWA_ONLY_MODE=false python3 wsgi.py"
else
    echo "Usage: $0 [enable|disable]"
    echo ""
    echo "Examples:"
    echo "  $0 enable   - Enable PWA-only mode"
    echo "  $0 disable  - Disable PWA-only mode"
    echo ""
    echo "Current PWA_ONLY_MODE setting: ${PWA_ONLY_MODE:-false}"
fi 