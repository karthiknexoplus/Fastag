from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from fastag.utils.db import get_db
import logging
import os

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/locations', methods=['GET', 'POST'])
def locations():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        org_id = request.form.get('org_id')
        plaza_id = request.form.get('plaza_id')
        agency_id = request.form.get('agency_id')
        acquirer_id = request.form.get('acquirer_id')
        geo_code = request.form.get('geo_code')
        site_id = request.form.get('site_id') or os.urandom(4).hex().upper()
        db.execute('INSERT INTO locations (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, site_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, site_id))
        db.commit()
        logging.info(f"Location added: {name} ({site_id})")
        flash('Location added!', 'success')
        return redirect(url_for('locations.locations'))
    locations = db.execute('SELECT * FROM locations').fetchall()
    return render_template('locations.html', locations=locations)

@locations_bp.route('/locations/edit/<int:id>', methods=['GET', 'POST'])
def edit_location(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    loc = db.execute('SELECT * FROM locations WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        org_id = request.form.get('org_id')
        plaza_id = request.form.get('plaza_id')
        agency_id = request.form.get('agency_id')
        acquirer_id = request.form.get('acquirer_id')
        geo_code = request.form.get('geo_code')
        db.execute('UPDATE locations SET name = ?, address = ?, org_id = ?, plaza_id = ?, agency_id = ?, acquirer_id = ?, geo_code = ? WHERE id = ?',
                   (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, id))
        db.commit()
        logging.info(f"Location updated: {name} (ID {id})")
        flash('Location updated!', 'success')
        return redirect(url_for('locations.locations'))
    return render_template('edit_location.html', loc=loc)

@locations_bp.route('/locations/delete/<int:id>', methods=['POST'])
def delete_location(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('DELETE FROM locations WHERE id = ?', (id,))
    db.commit()
    logging.info(f"Location deleted (ID {id})")
    flash('Location deleted!', 'info')
    return redirect(url_for('locations.locations'))

@locations_bp.route('/api/locations', methods=['POST'])
def api_add_location():
    """API endpoint to add a location (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    name = data.get("name")
    address = data.get("address")
    org_id = data.get("org_id")
    plaza_id = data.get("plaza_id")
    agency_id = data.get("agency_id")
    acquirer_id = data.get("acquirer_id")
    geo_code = data.get("geo_code")
    if not name or not address:
        return {"success": False, "error": "Missing name or address"}, 400
    site_id = data.get("site_id") or os.urandom(4).hex().upper()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO locations (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, site_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, site_id))
        db.commit()
        # Fetch updated list
        locations = db.execute('SELECT * FROM locations').fetchall()
        locations_list = [dict(l) for l in locations]
        logging.info(f"Location added via API: {name} ({site_id})")
        return {"success": True, "locations": locations_list}, 200
    except Exception as e:
        logging.error(f"Error adding location via API: {e}")
        return {"success": False, "error": str(e)}, 500

@locations_bp.route('/api/locations/<int:id>', methods=['PUT'])
def api_edit_location(id):
    """API endpoint to edit a location (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    name = data.get("name")
    address = data.get("address")
    org_id = data.get("org_id")
    plaza_id = data.get("plaza_id")
    agency_id = data.get("agency_id")
    acquirer_id = data.get("acquirer_id")
    geo_code = data.get("geo_code")
    if not name or not address:
        return {"success": False, "error": "Missing name or address"}, 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE locations SET name = ?, address = ?, org_id = ?, plaza_id = ?, agency_id = ?, acquirer_id = ?, geo_code = ? WHERE id = ?',
                       (name, address, org_id, plaza_id, agency_id, acquirer_id, geo_code, id))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Location not found"}, 404
        # Fetch updated list
        locations = db.execute('SELECT * FROM locations').fetchall()
        locations_list = [dict(l) for l in locations]
        logging.info(f"Location updated via API: {name} (ID {id})")
        return {"success": True, "locations": locations_list}, 200
    except Exception as e:
        logging.error(f"Error editing location via API: {e}")
        return {"success": False, "error": str(e)}, 500

@locations_bp.route('/api/locations/<int:id>', methods=['DELETE'])
def api_delete_location(id):
    """API endpoint to delete a location (for mobile app)"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM locations WHERE id = ?', (id,))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Location not found"}, 404
        # Fetch updated list
        locations = db.execute('SELECT * FROM locations').fetchall()
        locations_list = [dict(l) for l in locations]
        logging.info(f"Location deleted via API (ID {id})")
        return {"success": True, "locations": locations_list}, 200
    except Exception as e:
        logging.error(f"Error deleting location via API: {e}")
        return {"success": False, "error": str(e)}, 500

@locations_bp.route('/api/locations', methods=['GET'])
def api_view_locations():
    """API endpoint to view all locations"""
    try:
        db = get_db()
        locations = db.execute('SELECT * FROM locations').fetchall()
        locations_list = [dict(l) for l in locations]
        return {"success": True, "locations": locations_list}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500 