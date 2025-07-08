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
        vehicle_number = request.form['vehicle_number']
        contact_number = request.form['contact_number']
        address = request.form['address']
        try:
            db.execute('INSERT INTO kyc_users (name, fastag_id, vehicle_number, contact_number, address) VALUES (?, ?, ?, ?, ?)',
                       (name, fastag_id, vehicle_number, contact_number, address))
            db.commit()
            logging.info(f"KYC user added: {name} ({fastag_id})")
            flash('KYC user added!', 'success')
        except Exception as e:
            flash('Error adding KYC user: ' + str(e), 'danger')
    users = db.execute('SELECT * FROM kyc_users ORDER BY created_at DESC').fetchall()
    return render_template('kyc_users.html', users=users)

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
            # Extract vehicle number from the first tag detail
            tag_detail = data['npcitagDetails'][0]
            vehicle_number = tag_detail.get('VRN', '')
            return jsonify({
                'success': True,
                'vehicle_number': vehicle_number,
                'fastag_id': fastag_id
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
            # Extract FASTag ID from the first tag detail
            tag_detail = data['npcitagDetails'][0]
            fastag_id = tag_detail.get('TagID', '')
            return jsonify({
                'success': True,
                'fastag_id': fastag_id,
                'vehicle_number': vehicle_number
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