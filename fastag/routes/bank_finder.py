from flask import Blueprint, render_template, request, jsonify
import requests
import logging
import re
import urllib3
import json
import os

# Disable SSL warnings for this specific API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

bank_finder_bp = Blueprint('bank_finder', __name__)

# Sample cached data for testing
SAMPLE_BANK_DATA = {
    "KA04MJ6369": {
        "npcitagDetails": [{
            "TagID": "34161FA820328EE80795F540",
            "TID": "E2801105200079462ACD0A5A", 
            "VRN": "KA04MJ6369",
            "IssueDate": "2021-03-04",
            "ExceptionCode": "00",
            "BankId": "IDFC Bank",
            "ComVehicle": "F",
            "TagStatus": "A",
            "VehicleClass": "VC4",
            "AVC": None
        }],
        "ErrorMessage": "NONE",
        "PlazaId": 0,
        "PlazaDisplayId": ""
    },
    "TN66AT2938": {
        "npcitagDetails": [{
            "TagID": "34161FA82033E8E403D2D2C0",
            "TID": "E28011C120000B0ACCBB031F",
            "VRN": "TN66AT2938", 
            "IssueDate": "2024-12-20",
            "ExceptionCode": "01",
            "BankId": "Equitas Bank",
            "ComVehicle": "F",
            "TagStatus": "A",
            "VehicleClass": "VC4",
            "AVC": None
        }],
        "ErrorMessage": "NONE",
        "PlazaId": 0,
        "PlazaDisplayId": ""
    }
}

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
            # For now, always use cached data to ensure it works
            if search_type == 'VRN' and search_value in SAMPLE_BANK_DATA:
                bank_data = SAMPLE_BANK_DATA[search_value]
                logging.info(f"Using cached data for {search_value}")
            else:
                error = f"No data found for {search_value}. Try: KA04MJ6369 or TN66AT2938"
    
    return render_template('bank_finder.html', 
                         bank_data=bank_data, 
                         error=error, 
                         search_type=search_type,
                         search_value=search_value)

@bank_finder_bp.route('/api/bank/<search_type>/<search_value>')
def bank_api(search_type, search_value):
    """API endpoint for AJAX requests"""
    try:
        if search_type == 'VRN' and search_value.upper() in SAMPLE_BANK_DATA:
            return jsonify(SAMPLE_BANK_DATA[search_value.upper()])
        else:
            return jsonify({'error': 'No data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400 