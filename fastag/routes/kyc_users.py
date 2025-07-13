from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
from fastag.utils.db import get_db
import logging
import requests
import re
import urllib3

# Disable SSL warnings for this specific API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

kyc_users_bp = Blueprint('kyc_users', __name__)

@kyc_users_bp.route('/kyc_users', methods=['GET', 'POST'])
def kyc_users():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        fastag_id = request.form['fastag_id']
        vehicle_number = request.form['vehicle_number'].replace(' ', '').upper() if request.form['vehicle_number'] else ''
        contact_number = request.form['contact_number']
        address = request.form['address']
        # If fastag_id is empty, try to fetch it using the vehicle_number
        if not fastag_id and vehicle_number:
            try:
                api_url = url_for('kyc_users.fetch_fastag_by_vehicle', vehicle_number=vehicle_number, _external=True)
                resp = requests.get(api_url, timeout=10, verify=False)
                if resp.ok:
                    data = resp.json()
                    # Assign the first active FASTag ID if available
                    if data.get('success') and data.get('tags'):
                        fastag_id = data['tags'][0]['tag_id']
            except Exception as e:
                logging.error(f"Error auto-fetching FASTag ID for vehicle {vehicle_number}: {e}")
        try:
            db.execute('INSERT INTO kyc_users (name, fastag_id, vehicle_number, contact_number, address) VALUES (?, ?, ?, ?, ?)',
                       (name, fastag_id, vehicle_number, contact_number, address))
            db.commit()
            logging.info(f"KYC user added: {name} ({fastag_id})")
            flash('KYC user added!', 'success')
        except Exception as e:
            flash('Error adding KYC user: ' + str(e), 'danger')
    users = db.execute('SELECT * FROM kyc_users ORDER BY created_at DESC').fetchall()
    total_users = len(users)
    return render_template('kyc_users.html', users=users, total_users=total_users)

@kyc_users_bp.route('/api/kyc/fetch-vehicle/<fastag_id>')
def fetch_vehicle_by_fastag(fastag_id):
    """API endpoint to fetch vehicle number by FASTag ID"""
    try:
        # Use Axis Bank API to get vehicle information
        url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType=TagId&SearchValue={fastag_id.upper()}'
        headers = {
            'Cookie': 'axisbiconnect=1034004672.47873.0000'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ErrorMessage') == 'NONE' and data.get('npcitagDetails'):
            # Return ONLY ACTIVE tags for this FASTag ID
            tags = []
            for tag_detail in data['npcitagDetails']:
                # Only include tags with status "A" (Active)
                if tag_detail.get('TagStatus') == 'A':
                    tags.append({
                        'tag_id': tag_detail.get('TagID', ''),
                        'tid': tag_detail.get('TID', ''),
                        'vehicle_number': tag_detail.get('VRN', ''),
                        'status': tag_detail.get('TagStatus', ''),
                        'bank_name': tag_detail.get('BankId', ''),
                        'issue_date': tag_detail.get('IssueDate', ''),
                        'exception_code': tag_detail.get('ExceptionCode', ''),
                        'com_vehicle': tag_detail.get('ComVehicle', ''),
                        'vehicle_class': tag_detail.get('VehicleClass', ''),
                        'avc': tag_detail.get('AVC', '')
                    })
            
            return jsonify({
                'success': True,
                'fastag_id': fastag_id,
                'tags': tags,
                'total_tags': len(tags)
            })
        else:
            return jsonify({
                'success': False,
                'error': f"No vehicle information found for FASTag ID: {fastag_id}"
            })
            
    except Exception as e:
        logging.error(f"Error fetching vehicle by FASTag ID: {e}")
        return jsonify({
            'success': False,
            'error': f"API request failed: {str(e)}"
        }), 400

@kyc_users_bp.route('/api/kyc/fetch-fastag/<vehicle_number>')
def fetch_fastag_by_vehicle(vehicle_number):
    """API endpoint to fetch FASTag ID by vehicle number"""
    try:
        # Use Axis Bank API to get FASTag information
        url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType=VRN&SearchValue={vehicle_number.upper()}'
        headers = {
            'Cookie': 'axisbiconnect=1034004672.47873.0000'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('ErrorMessage') == 'NONE' and data.get('npcitagDetails'):
            # Return ONLY ACTIVE FASTag IDs for this vehicle number
            tags = []
            for tag_detail in data['npcitagDetails']:
                # Only include tags with status "A" (Active)
                if tag_detail.get('TagStatus') == 'A':
                    tags.append({
                        'tag_id': tag_detail.get('TagID', ''),
                        'tid': tag_detail.get('TID', ''),
                        'vehicle_number': tag_detail.get('VRN', ''),
                        'status': tag_detail.get('TagStatus', ''),
                        'bank_name': tag_detail.get('BankId', ''),
                        'issue_date': tag_detail.get('IssueDate', ''),
                        'exception_code': tag_detail.get('ExceptionCode', ''),
                        'com_vehicle': tag_detail.get('ComVehicle', ''),
                        'vehicle_class': tag_detail.get('VehicleClass', ''),
                        'avc': tag_detail.get('AVC', '')
                    })
            
            return jsonify({
                'success': True,
                'vehicle_number': vehicle_number,
                'tags': tags,
                'total_tags': len(tags)
            })
        else:
            return jsonify({
                'success': False,
                'error': f"No FASTag information found for vehicle: {vehicle_number}"
            })
            
    except Exception as e:
        logging.error(f"Error fetching FASTag by vehicle number: {e}")
        return jsonify({
            'success': False,
            'error': f"API request failed: {str(e)}"
        }), 400

@kyc_users_bp.route('/api/kyc_users', methods=['POST'])
def api_add_kyc_user():
    """API endpoint to add a KYC user (for mobile app)"""
    from fastag.utils.db import get_db
    import logging
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400
    data = request.get_json()
    required_fields = ["name", "fastag_id", "vehicle_number", "contact_number", "address"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO kyc_users (name, fastag_id, vehicle_number, contact_number, address) VALUES (?, ?, ?, ?, ?)',
            (data["name"], data["fastag_id"], data["vehicle_number"], data["contact_number"], data["address"])
        )
        db.commit()
        user_id = cursor.lastrowid
        logging.info(f"KYC user added via API: {data['name']} ({data['fastag_id']})")
        return jsonify({"success": True, "user_id": user_id}), 201
    except Exception as e:
        logging.error(f"Error adding KYC user via API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@kyc_users_bp.route('/api/kyc_users/<int:id>', methods=['GET'])
def api_get_kyc_user(id):
    """API endpoint to fetch a single KYC user by ID (for mobile app)"""
    db = get_db()
    user = db.execute('SELECT * FROM kyc_users WHERE id = ?', (id,)).fetchone()
    if user is None:
        return jsonify({"success": False, "error": f"No KYC user found with id {id}"}), 404
    # Convert sqlite3.Row to dict
    user_dict = dict(user)
    return jsonify({"success": True, "user": user_dict}), 200

@kyc_users_bp.route('/api/kyc_users', methods=['GET'])
def api_get_all_kyc_users():
    """API endpoint to fetch all KYC users as JSON (for mobile app)"""
    db = get_db()
    users = db.execute('SELECT * FROM kyc_users ORDER BY created_at DESC').fetchall()
    users_list = [dict(user) for user in users]
    return jsonify({"success": True, "users": users_list}), 200

@kyc_users_bp.route('/api/kyc_users/<int:id>', methods=['PUT'])
def api_edit_kyc_user(id):
    """API endpoint to edit a KYC user by ID (for mobile app)"""
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400
    data = request.get_json()
    required_fields = ["name", "fastag_id", "vehicle_number", "contact_number", "address"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE kyc_users SET name=?, fastag_id=?, vehicle_number=?, contact_number=?, address=? WHERE id=?',
            (data["name"], data["fastag_id"], data["vehicle_number"], data["contact_number"], data["address"], id)
        )
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": f"No KYC user found with id {id}"}), 404
        return jsonify({"success": True, "message": "KYC user updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@kyc_users_bp.route('/api/kyc_users/<int:id>', methods=['DELETE'])
def api_delete_kyc_user(id):
    """API endpoint to delete a KYC user by ID (for mobile app)"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM kyc_users WHERE id = ?', (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": f"No KYC user found with id {id}"}), 404
        return jsonify({"success": True, "message": "KYC user deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@kyc_users_bp.route('/kyc_users/edit/<int:id>', methods=['GET', 'POST'])
def edit_kyc_user(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    user = db.execute('SELECT * FROM kyc_users WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        fastag_id = request.form['fastag_id']
        vehicle_number = request.form['vehicle_number']
        contact_number = request.form['contact_number']
        address = request.form['address']
        try:
            db.execute('UPDATE kyc_users SET name=?, fastag_id=?, vehicle_number=?, contact_number=?, address=? WHERE id=?',
                       (name, fastag_id, vehicle_number, contact_number, address, id))
            db.commit()
            logging.info(f"KYC user updated: {name} ({fastag_id})")
            flash('KYC user updated!', 'success')
            return redirect(url_for('kyc_users.kyc_users'))
        except Exception as e:
            flash('Error updating KYC user: ' + str(e), 'danger')
    return render_template('edit_kyc_user.html', user=user)

@kyc_users_bp.route('/kyc_users/delete/<int:id>', methods=['POST'])
def delete_kyc_user(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('DELETE FROM kyc_users WHERE id = ?', (id,))
    db.commit()
    logging.info(f"KYC user deleted (ID {id})")
    flash('KYC user deleted!', 'info')
    return redirect(url_for('kyc_users.kyc_users')) 