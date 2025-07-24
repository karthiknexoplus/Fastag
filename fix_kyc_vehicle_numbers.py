import sqlite3
import requests
import logging
# Set your database path here. Adjust if needed.
DATABASE = "instance/fastag.db"

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_active_fastag_id(vehicle_number):
    url = f"https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType=VRN&SearchValue={vehicle_number.upper()}"
    headers = {
        'Cookie': 'axisbiconnect=1034004672.47873.0000'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.ok:
            data = resp.json()
            if data.get('ErrorMessage') == 'NONE' and data.get('npcitagDetails'):
                for tag_detail in data['npcitagDetails']:
                    if tag_detail.get('TagStatus') == 'A':
                        return tag_detail.get('TagID', None)
    except Exception as e:
        logging.error(f"Error fetching FASTag ID for {vehicle_number}: {e}")
    return None

def main():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Find users with empty/null fastag_id or fastag_id not starting with '34161'
    cur.execute("SELECT * FROM kyc_users WHERE fastag_id IS NULL OR fastag_id = '' OR fastag_id NOT LIKE '34161%'")
    users = cur.fetchall()
    logging.info(f"Found {len(users)} users with missing or invalid fastag_id.")
    print("Users to process (id, name, vehicle_number, fastag_id):")
    for user in users:
        print(user['id'], user['name'], user['vehicle_number'], user['fastag_id'])
    updated = 0
    for user in users:
        old_vrn = user['vehicle_number']
        cleaned_vrn = old_vrn.replace(' ', '').upper() if old_vrn else ''
        if not cleaned_vrn:
            logging.info(f"User ID {user['id']}: No vehicle number, skipping.")
            continue
        fastag_id = fetch_active_fastag_id(cleaned_vrn)
        if fastag_id and fastag_id.startswith('34161'):
            logging.info(f"User ID {user['id']}: {old_vrn} -> {cleaned_vrn}, FASTag: {fastag_id} (UPDATED)")
            cur.execute(
                "UPDATE kyc_users SET vehicle_number=?, fastag_id=? WHERE id=?",
                (cleaned_vrn, fastag_id, user['id'])
            )
            updated += 1
        else:
            logging.info(f"User ID {user['id']}: {old_vrn} -> {cleaned_vrn}, FASTag: NOT FOUND or does not start with 34161 (SKIPPED)")
    conn.commit()
    # Count users without fastag_id or not starting with 34161
    cur.execute("SELECT COUNT(*) FROM kyc_users WHERE fastag_id IS NULL OR fastag_id = '' OR fastag_id NOT LIKE '34161%'")
    missing_fastag_count = cur.fetchone()[0]
    conn.close()
    logging.info(f"Done. Updated {updated} KYC users.")
    print(f"Number of vehicles without valid FASTag ID: {missing_fastag_count}")
    print(f"Expected: 34161")

if __name__ == "__main__":
    main() 