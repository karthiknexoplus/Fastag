from flask import Blueprint, render_template, request, jsonify
import requests
import logging
import re

vehicle_finder_bp = Blueprint('vehicle_finder', __name__)

@vehicle_finder_bp.route('/find-vehicle', methods=['GET', 'POST'])
def find_vehicle():
    vehicle_data = None
    error = None
    
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip().upper()
        
        if not reg_no:
            error = "Please enter a vehicle registration number."
        elif not re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$', reg_no):
            error = "Please enter a valid vehicle registration number (e.g., KA03KD1578)."
        else:
            try:
                # API endpoint and headers
                url = f'https://www.acko.com/api/app/vehicleInfo/?regNo={reg_no}'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.acko.com/',
                    'Origin': 'https://www.acko.com'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                vehicle_data = response.json()
                
                # Check if we got valid data
                if not vehicle_data.get('registration_number'):
                    error = "Vehicle information not found for this registration number."
                    vehicle_data = None
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed: {e}")
                error = "Unable to fetch vehicle information. Please try again later."
            except Exception as e:
                logging.error(f"Error processing vehicle data: {e}")
                error = "An error occurred while processing the request."
    
    return render_template('vehicle_finder.html', vehicle_data=vehicle_data, error=error)

@vehicle_finder_bp.route('/api/vehicle/<reg_no>')
def vehicle_api(reg_no):
    """API endpoint for AJAX requests"""
    try:
        url = f'https://www.acko.com/api/app/vehicleInfo/?regNo={reg_no.upper()}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 400 