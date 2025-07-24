# Google OAuth Configuration Template
# Copy this file to your project root and fill in your actual Google OAuth credentials

import os

# Set your Google OAuth credentials as environment variables
# You can also set these directly in your system environment

# Get these from Google Cloud Console:
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project or select existing one
# 3. Enable Google+ API
# 4. Go to Credentials
# 5. Create OAuth 2.0 Client ID
# 6. Set authorized redirect URIs to: http://localhost:5000/google/callback (for development)
# 7. Copy the Client ID and Client Secret

os.environ['GOOGLE_CLIENT_ID'] = 'your-google-client-id-here'
os.environ['GOOGLE_CLIENT_SECRET'] = 'your-google-client-secret-here'

print("Google OAuth credentials configured!")
print("Make sure to:")
print("1. Replace 'your-google-client-id-here' with your actual Google Client ID")
print("2. Replace 'your-google-client-secret-here' with your actual Google Client Secret")
print("3. Set up authorized redirect URIs in Google Cloud Console")
print("4. For production, set these as environment variables instead of hardcoding") 