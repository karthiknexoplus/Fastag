from flask import Blueprint, render_template, request, jsonify
import requests
import logging
import re

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
                # API endpoint and headers
                url = f'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails?SearchType={search_type}&SearchValue={search_value}'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Cookie': 'TS019079a3=01e33451e7f6a9a64bbb5a6e970573e2c7ccf2f153dd52c79a5c8d34e25b94ef891ed412dcbc16ae837736ae9657086368e5a88d3c'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                bank_data = response.json()
                
                # Check if we got valid data
                if bank_data.get('ErrorMessage') != 'NONE' or not bank_data.get('npcitagDetails'):
                    error = "No bank information found for this search."
                    bank_data = None
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed: {e}")
                error = "Unable to fetch bank information. Please try again later."
            except Exception as e:
                logging.error(f"Error processing bank data: {e}")
                error = "An error occurred while processing the request."
    
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Cookie': 'TS019079a3=01e33451e7f6a9a64bbb5a6e970573e2c7ccf2f153dd52c79a5c8d34e25b94ef891ed412dcbc16ae837736ae9657086368e5a88d3c'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 400 