# google_oauth_env_setup.py
import os

def load_existing_env():
    """Load existing environment variables from .env file"""
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def save_env_file(env_vars):
    """Save environment variables to .env file"""
    with open('.env', 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

# Load existing environment variables
existing_env = load_existing_env()

print("=== Google OAuth & Feature Flag Setup ===\n")

# Check for existing Google credentials
existing_client_id = existing_env.get('GOOGLE_CLIENT_ID', '')
existing_client_secret = existing_env.get('GOOGLE_CLIENT_SECRET', '')

if existing_client_id and existing_client_secret:
    print(f"Existing Google credentials found:")
    print(f"Client ID: {existing_client_id[:20]}...")
    print(f"Client Secret: {existing_client_secret[:10]}...")
    
    update_google = input("\nDo you want to update Google credentials? (y/n): ").lower().strip()
    
    if update_google in ['y', 'yes']:
        client_id = input("Enter your new Google Client ID: ")
        client_secret = input("Enter your new Google Client Secret: ")
        existing_env['GOOGLE_CLIENT_ID'] = client_id
        existing_env['GOOGLE_CLIENT_SECRET'] = client_secret
        print("✓ Google credentials updated!")
    else:
        print("✓ Keeping existing Google credentials")
else:
    print("No existing Google credentials found.")
    client_id = input("Enter your Google Client ID: ")
    client_secret = input("Enter your Google Client Secret: ")
    existing_env['GOOGLE_CLIENT_ID'] = client_id
    existing_env['GOOGLE_CLIENT_SECRET'] = client_secret
    print("✓ Google credentials added!")

# Check for existing FASTag feature flag
existing_fastag_enabled = existing_env.get('FASTAG_FEATURES_ENABLED', '')

if existing_fastag_enabled:
    print(f"\nExisting FASTag feature flag: {existing_fastag_enabled}")
    update_fastag = input("Do you want to update FASTag feature flag? (y/n): ").lower().strip()
    
    if update_fastag in ['y', 'yes']:
        enable_fastag_features = input("Enable FASTag features? (y/n): ").lower().strip()
        fastag_enabled = "true" if enable_fastag_features in ['y', 'yes', '1'] else "false"
        existing_env['FASTAG_FEATURES_ENABLED'] = fastag_enabled
        print("✓ FASTag feature flag updated!")
    else:
        print("✓ Keeping existing FASTag feature flag")
else:
    print("\nNo existing FASTag feature flag found.")
    enable_fastag_features = input("Enable FASTag features? (y/n): ").lower().strip()
    fastag_enabled = "true" if enable_fastag_features in ['y', 'yes', '1'] else "false"
    existing_env['FASTAG_FEATURES_ENABLED'] = fastag_enabled
    print("✓ FASTag feature flag added!")

# Save all environment variables
save_env_file(existing_env)

print(f"\n✓ .env file updated with your configuration!")
print(f"FASTAG_FEATURES_ENABLED = {existing_env.get('FASTAG_FEATURES_ENABLED', 'true')}") 