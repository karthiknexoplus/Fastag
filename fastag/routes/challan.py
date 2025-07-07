from flask import Blueprint, render_template, request, jsonify
import requests

challan_bp = Blueprint('challan', __name__)

@challan_bp.route('/challan', methods=['GET', 'POST'])
def challan():
    challan_data = None
    error = None
    reg_no = ''
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip().upper()
        if not reg_no:
            error = 'Please enter a vehicle number.'
        else:
            try:
                # Step 1: Get request_id
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'origin': 'https://www.spinny.com',
                    'platform': 'web',
                    'priority': 'u=1, i',
                    'referer': 'https://www.spinny.com/',
                    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                }
                cookies = {
                    'platform': 'web',
                }
                req1 = requests.get(f'https://api.spinny.com/v3/api/challan/pending/request/?reg_no={reg_no}', headers=headers, cookies=cookies, timeout=10)
                req1.raise_for_status()
                data1 = req1.json()
                if not data1.get('is_success') or not data1.get('data'):
                    error = data1.get('message', 'No challan data found.')
                else:
                    request_id = data1['data'][0]['request_id']
                    # Step 2: Get challan details
                    req2 = requests.get(f'https://api.spinny.com/v3/api/challan/pending/?request_id={request_id}', headers=headers, cookies=cookies, timeout=10)
                    req2.raise_for_status()
                    data2 = req2.json()
                    if not data2.get('is_success') or not data2.get('data'):
                        error = data2.get('message', 'No challan data found.')
                    else:
                        challan_data = data2['data']
            except Exception as e:
                error = f'Error fetching challan: {str(e)}'
    return render_template('challan.html', challan_data=challan_data, error=error, reg_no=reg_no) 