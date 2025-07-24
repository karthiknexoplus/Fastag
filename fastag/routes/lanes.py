from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from fastag.utils.db import get_db
import logging

lanes_bp = Blueprint('lanes', __name__)

@lanes_bp.route('/lanes', methods=['GET', 'POST'])
def lanes():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    locations = db.execute('SELECT * FROM locations').fetchall()
    selected_location = request.args.get('location_id')
    lanes = []
    readers_map = {}
    if selected_location:
        lanes = db.execute('''
            SELECT l.*, r.reader_id, r.reader_ip
            FROM lanes l
            LEFT JOIN readers r ON l.id = r.lane_id
            WHERE l.location_id = ?
        ''', (selected_location,)).fetchall()
        lane_ids = [lane['id'] for lane in lanes]
        if lane_ids:
            qmarks = ','.join('?'*len(lane_ids))
            readers = db.execute(f'SELECT lane_id, COUNT(*) as count FROM readers WHERE lane_id IN ({qmarks}) GROUP BY lane_id', lane_ids).fetchall()
            readers_map = {row['lane_id']: row['count'] for row in readers}
    if request.method == 'POST':
        location_id = request.form['location_id']
        plaza_id = request.form['plaza_id']
        plaza_name = request.form['plaza_name']
        lane_id_val = request.form['lane_id']
        lane_type = request.form['lane_type']
        lane_desc = request.form['lane_desc']
        lane_direction = request.form['lane_direction']
        plaza_lane_direction = request.form['plaza_lane_direction']
        db.execute('INSERT INTO lanes (location_id, plaza_id, plaza_name, lane_id, lane_type, lane_desc, lane_direction, plaza_lane_direction) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (location_id, plaza_id, plaza_name, lane_id_val, lane_type, lane_desc, lane_direction, plaza_lane_direction))
        db.commit()
        logging.info(f"Lane added: {lane_id_val} (Location {location_id})")
        flash('Lane added!', 'success')
        return redirect(url_for('lanes.lanes', location_id=location_id))
    return render_template('lanes.html', lanes=lanes, locations=locations, selected_location=selected_location, readers_map=readers_map)

@lanes_bp.route('/lanes/edit/<int:id>', methods=['GET', 'POST'])
def edit_lane(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (id,)).fetchone()
    locations = db.execute('SELECT * FROM locations').fetchall()
    if request.method == 'POST':
        plaza_id = request.form['plaza_id']
        plaza_name = request.form['plaza_name']
        lane_id_val = request.form['lane_id']
        lane_type = request.form['lane_type']
        lane_desc = request.form['lane_desc']
        lane_direction = request.form['lane_direction']
        plaza_lane_direction = request.form['plaza_lane_direction']
        db.execute('UPDATE lanes SET plaza_id = ?, plaza_name = ?, lane_id = ?, lane_type = ?, lane_desc = ?, lane_direction = ?, plaza_lane_direction = ? WHERE id = ?',
                   (plaza_id, plaza_name, lane_id_val, lane_type, lane_desc, lane_direction, plaza_lane_direction, id))
        db.commit()
        logging.info(f"Lane updated: {lane_id_val} (ID {id})")
        flash('Lane updated!', 'success')
        return redirect(url_for('lanes.lanes', location_id=lane['location_id']))
    return render_template('edit_lane.html', lane=lane, locations=locations)

@lanes_bp.route('/lanes/delete/<int:id>', methods=['POST'])
def delete_lane(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (id,)).fetchone()
    db.execute('DELETE FROM lanes WHERE id = ?', (id,))
    db.execute('DELETE FROM readers WHERE lane_id = ?', (id,))
    db.commit()
    logging.info(f"Lane deleted (ID {id}) and its readers.")
    flash('Lane and its readers deleted!', 'info')
    return redirect(url_for('lanes.lanes', location_id=lane['location_id']))

@lanes_bp.route('/api/lanes', methods=['POST'])
def api_add_lane():
    """API endpoint to add a lane (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    location_id = data.get("location_id")
    lane_id_val = data.get("lane_id")
    if not location_id or not lane_id_val:
        return {"success": False, "error": "Missing location_id or lane_id"}, 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO lanes (location_id, plaza_id, plaza_name, lane_id, lane_type, lane_desc, lane_direction, plaza_lane_direction) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (location_id, data.get('plaza_id'), data.get('plaza_name'), data.get('lane_id'), data.get('lane_type'), data.get('lane_desc'), data.get('lane_direction'), data.get('plaza_lane_direction')))
        db.commit()
        lane_id_db = cursor.lastrowid
        logging.info(f"Lane added via API: {data.get('lane_id')} (Location {location_id})")
        return {"success": True, "lane_id": lane_id_db}, 201
    except Exception as e:
        logging.error(f"Error adding lane via API: {e}")
        return {"success": False, "error": str(e)}, 500

@lanes_bp.route('/api/lanes/<int:id>', methods=['PUT'])
def api_edit_lane(id):
    """API endpoint to edit a lane (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    location_id = data.get("location_id")
    lane_id_val = data.get("lane_id")
    if not location_id or not lane_id_val:
        return {"success": False, "error": "Missing location_id or lane_id"}, 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE lanes SET plaza_id = ?, plaza_name = ?, lane_id = ?, lane_type = ?, lane_desc = ?, lane_direction = ?, plaza_lane_direction = ? WHERE id = ?',
                       (data.get('plaza_id'), data.get('plaza_name'), data.get('lane_id'), data.get('lane_type'), data.get('lane_desc'), data.get('lane_direction'), data.get('plaza_lane_direction'), id))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Lane not found"}, 404
        logging.info(f"Lane updated via API: {data.get('lane_id')} (ID {id})")
        return {"success": True}, 200
    except Exception as e:
        logging.error(f"Error editing lane via API: {e}")
        return {"success": False, "error": str(e)}, 500

@lanes_bp.route('/api/lanes/<int:id>', methods=['DELETE'])
def api_delete_lane(id):
    """API endpoint to delete a lane (for mobile app)"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM lanes WHERE id = ?', (id,))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Lane not found"}, 404
        logging.info(f"Lane deleted via API (ID {id})")
        return {"success": True}, 200
    except Exception as e:
        logging.error(f"Error deleting lane via API: {e}")
        return {"success": False, "error": str(e)}, 500

@lanes_bp.route('/api/lanes', methods=['GET'])
def api_view_lanes():
    """API endpoint to view all lanes (optionally filter by location_id)"""
    location_id = request.args.get('location_id', type=int)
    try:
        db = get_db()
        if location_id:
            lanes = db.execute('SELECT * FROM lanes WHERE location_id = ?', (location_id,)).fetchall()
        else:
            lanes = db.execute('SELECT * FROM lanes').fetchall()
        lanes_list = [dict(l) for l in lanes]
        return {"success": True, "lanes": lanes_list}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500 