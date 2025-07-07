from flask import Blueprint, render_template, request, jsonify
import requests
import logging
import re
import urllib3

# Disable SSL warnings for this specific API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

bank_finder_bp = Blueprint('bank_finder', __name__)

@bank_finder_bp.route('/find-bank', methods=['GET', 'POST'])
def find_bank():
    bank_data = None
    error = None
    search_type = request.form.get('search_type', 'VRN')
    search_value = request.form.get('search_value', '').strip().upper()
    
    if request.method == 'POST':
        if not search_value:
            error = "Please enter a search value."
        elif search_type == 'VRN' and not re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$', search_value):
            error = "Please enter a valid vehicle registration number (e.g., TN66AT2938)."
        elif search_type == 'TagID' and not re.match(r'^[A-F0-9]{24}$', search_value):
            error = "Please enter a valid 24-character TagID (hexadecimal)."
        else:
            try:
                # API endpoint - EXACTLY like your curl
                url = f'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails?SearchType={search_type}&SearchValue={search_value}'
                headers = {
                    'Cookie': 'TS019079a3=01e33451e79286adff54e3e927f807bfcd9f7c80ddddd702e8b4f170cd048b04d65f9b970279e11be29a68140b39a5625463daed81'
                }
                
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                response.raise_for_status()
                
                # Print response details for debugging
                logging.info(f"Response status: {response.status_code}")
                logging.info(f"Response headers: {response.headers}")
                logging.info(f"Response text: {response.text}")
                
                bank_data = response.json()
                logging.info(f"Parsed JSON: {bank_data}")
                
                # Check if we got valid data
                if bank_data.get('ErrorMessage') != 'NONE' or not bank_data.get('npcitagDetails'):
                    error = f"No bank information found. Error: {bank_data.get('ErrorMessage', 'Unknown')}"
                    bank_data = None
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed: {e}")
                error = f"API request failed: {e}"
            except Exception as e:
                logging.error(f"Error processing bank data: {e}")
                error = f"Error processing bank data: {e}"
    
    return render_template('bank_finder.html', 
                         bank_data=bank_data, 
                         error=error, 
                         search_type=search_type,
                         search_value=search_value)

@bank_finder_bp.route('/api/bank/<search_type>/<search_value>')
def bank_api(search_type, search_value):
    """API endpoint for AJAX requests"""
    try:
        url = f'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails?SearchType={search_type}&SearchValue={search_value.upper()}'
        headers = {
            'Cookie': 'TS019079a3=01e33451e79286adff54e3e927f807bfcd9f7c80ddddd702e8b4f170cd048b04d65f9b970279e11be29a68140b39a5625463daed81'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 400 