# google_oauth_env_setup.py
client_id = input("Enter your Google Client ID: ")
client_secret = input("Enter your Google Client Secret: ")

with open('.env', 'w') as f:
    f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
    f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")

print(".env file created with your Google OAuth credentials.") 