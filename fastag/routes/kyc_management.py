from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from fastag.utils.db import get_db
import logging

kyc_management_bp = Blueprint('kyc_management', __name__)

# Define available roles
AVAILABLE_ROLES = {
    'tenant': {'name': 'Tenant', 'color': '#1976d2', 'description': 'Basic access - vehicle finder, fuel price, balance'},
    'service_engineer': {'name': 'Service Engineer', 'color': '#f57c00', 'description': 'Technical access - reader settings, barrier control'},
    'manager': {'name': 'Manager', 'color': '#7b1fa2', 'description': 'Management access - reports, analytics, user management'},
    'superuser': {'name': 'Superuser', 'color': '#388e3c', 'description': 'Full access - all features and system settings'}
}

@kyc_management_bp.route('/kyc-management')
def kyc_management():
    """KYC users management page"""
    db = get_db()
    
    # Get all KYC users with their roles
    users = db.execute('''
        SELECT 
            ku.id,
            ku.name,
            ku.vehicle_number,
            ku.contact_number,
            ku.fastag_id,
            ku.address,
            ku.created_at,
            COALESCE(ku.user_role, 'tenant') as role,
            COALESCE(ku.is_active, 1) as is_active
        FROM kyc_users ku
        ORDER BY ku.created_at DESC
    ''').fetchall()
    
    return render_template('kyc_management.html', 
                         users=users,
                         roles=AVAILABLE_ROLES)

@kyc_management_bp.route('/api/kyc-users', methods=['GET'])
def get_kyc_users():
    """Get all KYC users API"""
    db = get_db()
    users = db.execute('''
        SELECT 
            ku.id,
            ku.name,
            ku.vehicle_number,
            ku.contact_number,
            ku.fastag_id,
            ku.address,
            ku.created_at,
            COALESCE(ku.user_role, 'tenant') as role,
            COALESCE(ku.is_active, 1) as is_active
        FROM kyc_users ku
        ORDER BY ku.created_at DESC
    ''').fetchall()
    
    return jsonify({
        'success': True,
        'users': [
            {
                'id': user[0],
                'name': user[1],
                'vehicle_number': user[2],
                'contact_number': user[3],
                'fastag_id': user[4],
                'address': user[5],
                'created_at': user[6],
                'role': user[7],
                'is_active': bool(user[8])
            } for user in users
        ]
    })

@kyc_management_bp.route('/api/kyc-users/<int:user_id>', methods=['PUT'])
def update_kyc_user(user_id):
    """Update KYC user role and status"""
    data = request.get_json()
    role = data.get('role')
    is_active = data.get('is_active', True)
    
    if not role or role not in AVAILABLE_ROLES:
        return jsonify({'error': 'Invalid role'}), 400
    
    db = get_db()
    
    try:
        # Update user role and status
        db.execute('''
            UPDATE kyc_users 
            SET user_role = ?, is_active = ?
            WHERE id = ?
        ''', (role, is_active, user_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'User role updated to {AVAILABLE_ROLES[role]["name"]}'
        })
        
    except Exception as e:
        db.rollback()
        logging.exception(f"Error updating KYC user: {e}")
        return jsonify({'error': 'Failed to update user'}), 500

@kyc_management_bp.route('/api/kyc-users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    db = get_db()
    
    try:
        # Get current status
        current = db.execute('SELECT is_active FROM kyc_users WHERE id = ?', (user_id,)).fetchone()
        if not current:
            return jsonify({'error': 'User not found'}), 404
        
        new_status = not current[0]  # Toggle the status
        
        # Update status
        db.execute('UPDATE kyc_users SET is_active = ? WHERE id = ?', (new_status, user_id))
        db.commit()
        
        return jsonify({
            'success': True,
            'is_active': new_status,
            'message': f'User {"activated" if new_status else "deactivated"} successfully'
        })
        
    except Exception as e:
        db.rollback()
        logging.exception(f"Error toggling user status: {e}")
        return jsonify({'error': 'Failed to update user status'}), 500 