import requests

def find_challan(vehicle_number):
    """
    Fetch challan details for a given vehicle number using Spinny API.
    Returns a list of challans or an error message.
    """
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://www.spinny.com',
        'platform': 'web',
        'referer': 'https://www.spinny.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }
    try:
        # Step 1: Get request_id for the vehicle number
        url1 = f'https://api.spinny.com/v3/api/challan/pending/request/?reg_no={vehicle_number}'
        resp1 = requests.get(url1, headers=headers, timeout=10)
        data1 = resp1.json()
        if not data1.get('is_success') or not data1.get('data'):
            return {'error': data1.get('message', 'No challan info found.')}
        request_id = data1['data'][0]['request_id']

        # Step 2: Get challan details using request_id
        url2 = f'https://api.spinny.com/v3/api/challan/pending/?request_id={request_id}'
        resp2 = requests.get(url2, headers=headers, timeout=10)
        data2 = resp2.json()
        if not data2.get('is_success') or not data2.get('data'):
            return {'error': data2.get('message', 'No challan info found.')}
        challans = data2['data']
        return {'challans': challans}
    except Exception as e:
        return {'error': f'Error fetching challan: {e}'}

if __name__ == "__main__":
    vehicle_number = input("Enter vehicle number: ").strip().upper()
    if not vehicle_number:
        print("Vehicle number is required.")
    else:
        result = find_challan(vehicle_number)
        if 'challans' in result:
            print(f"\nChallans for {vehicle_number}:")
            for i, challan in enumerate(result['challans'], 1):
                print(f"\nChallan #{i}:")
                for k, v in challan.items():
                    print(f"  {k}: {v}")
        else:
            print("Error:", result['error']) 