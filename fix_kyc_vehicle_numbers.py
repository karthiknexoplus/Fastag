import sqlite3
import requests
import logging
from fastag.config import DATABASE

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_active_fastag_id(vehicle_number):
    url = f"http://127.0.0.1:5000/api/kyc/fetch-fastag/{vehicle_number}"
    try:
        resp = requests.get(url, timeout=10, verify=False)
        if resp.ok:
            data = resp.json()
            if data.get('success') and data.get('tags'):
                return data['tags'][0]['tag_id']
    except Exception as e:
        logging.error(f"Error fetching FASTag ID for {vehicle_number}: {e}")
    return None

def main():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Find users with spaces in vehicle_number
    cur.execute("SELECT * FROM kyc_users WHERE vehicle_number LIKE '% %'")
    users = cur.fetchall()
    logging.info(f"Found {len(users)} users with spaces in vehicle_number.")
    for user in users:
        old_vrn = user['vehicle_number']
        cleaned_vrn = old_vrn.replace(' ', '').upper()
        fastag_id = fetch_active_fastag_id(cleaned_vrn)
        logging.info(f"User ID {user['id']}: {old_vrn} -> {cleaned_vrn}, FASTag: {fastag_id}")
        # Update only if something changed
        cur.execute(
            "UPDATE kyc_users SET vehicle_number=?, fastag_id=? WHERE id=?",
            (cleaned_vrn, fastag_id or user['fastag_id'], user['id'])
        )
    conn.commit()
    conn.close()
    logging.info("Done updating KYC users.")

if __name__ == "__main__":
    main() 