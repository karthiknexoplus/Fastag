# google_oauth_env_setup.py
client_id = input("Enter your Google Client ID: ")
client_secret = input("Enter your Google Client Secret: ")

# Add feature flag for hifield mode
enable_fastag_features = input("Enable FASTag features? (y/n): ").lower().strip()
fastag_enabled = "true" if enable_fastag_features in ['y', 'yes', '1'] else "false"

with open('.env', 'w') as f:
    f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
    f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
    f.write(f"FASTAG_FEATURES_ENABLED={fastag_enabled}\n")

print(".env file created with your Google OAuth credentials and feature flags.") 