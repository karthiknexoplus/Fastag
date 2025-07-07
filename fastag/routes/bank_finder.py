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
            error = f"Please enter a valid 24-character TagID (hexadecimal). Current value: {search_value} (length: {len(search_value)})"
        else:
            try:
                # Use Axis Bank API
                url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType={search_type}&SearchValue={search_value}'
                headers = {
                    'Cookie': 'axisbiconnect=1034004672.47873.0000'
                }
                
                response = requests.get(url, headers=headers, timeout=15, verify=False)
                response.raise_for_status()
                
                # Print response details for debugging
                logging.info(f"API URL: {url}")
                logging.info(f"Search Type: {search_type}")
                logging.info(f"Search Value: {search_value}")
                logging.info(f"Response status: {response.status_code}")
                logging.info(f"Response headers: {dict(response.headers)}")
                logging.info(f"Response text: {response.text}")
                
                bank_data = response.json()
                logging.info(f"Parsed JSON: {bank_data}")
                
                # Check if we got valid data
                if bank_data.get('ErrorMessage') != 'NONE' or not bank_data.get('npcitagDetails'):
                    error = f"No bank information found. Error: {bank_data.get('ErrorMessage', 'Unknown')}. Response: {bank_data}"
                    bank_data = None
                else:
                    logging.info(f"Successfully found bank data: {bank_data}")
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed: {e}")
                error = f"API request failed: {e}. Network connectivity issue detected."
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
        url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType={search_type}&SearchValue={search_value.upper()}'
        headers = {
            'Cookie': 'axisbiconnect=1034004672.47873.0000'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bank_finder_bp.route('/debug-tag-search/<tag_id>')
def debug_tag_search(tag_id):
    """Debug route to test Tag ID search specifically"""
    try:
        url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType=TagID&SearchValue={tag_id.upper()}'
        headers = {
            'Cookie': 'axisbiconnect=1034004672.47873.0000'
        }
        
        logging.info(f"Debug Tag Search - URL: {url}")
        logging.info(f"Debug Tag Search - Tag ID: {tag_id}")
        logging.info(f"Debug Tag Search - Tag ID length: {len(tag_id)}")
        logging.info(f"Debug Tag Search - Tag ID regex match: {bool(re.match(r'^[A-F0-9]{24}$', tag_id.upper()))}")
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        logging.info(f"Debug Tag Search - Response status: {response.status_code}")
        logging.info(f"Debug Tag Search - Response headers: {dict(response.headers)}")
        logging.info(f"Debug Tag Search - Response text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logging.info(f"Debug Tag Search - Parsed JSON: {data}")
                return jsonify({
                    "status": "success",
                    "tag_id": tag_id,
                    "tag_id_length": len(tag_id),
                    "regex_match": bool(re.match(r'^[A-F0-9]{24}$', tag_id.upper())),
                    "response": data
                })
            except Exception as e:
                logging.error(f"Debug Tag Search - JSON parse error: {e}")
                return jsonify({
                    "status": "json_error",
                    "tag_id": tag_id,
                    "response_text": response.text,
                    "error": str(e)
                })
        else:
            return jsonify({
                "status": "http_error",
                "tag_id": tag_id,
                "status_code": response.status_code,
                "response_text": response.text
            })
            
    except Exception as e:
        logging.error(f"Debug Tag Search - Exception: {e}")
        return jsonify({
            "status": "exception",
            "tag_id": tag_id,
            "error": str(e)
        }) 