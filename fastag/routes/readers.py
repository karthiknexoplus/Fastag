from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify, current_app
from fastag.utils.db import get_db
import logging

readers_bp = Blueprint('readers', __name__)

@readers_bp.route('/readers/<int:lane_id>', methods=['GET', 'POST'])
def readers(lane_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (lane_id,)).fetchone()
    readers = db.execute('SELECT * FROM readers WHERE lane_id = ?', (lane_id,)).fetchall()
    if request.method == 'POST':
        mac_address = request.form['mac_address']
        type_ = request.form['type']
        reader_ip = request.form['reader_ip']
        existing = db.execute('SELECT * FROM readers WHERE lane_id = ? AND type = ?', (lane_id, type_)).fetchone()
        if existing:
            flash(f'{type_.capitalize()} reader already exists for this lane.', 'danger')
        else:
            db.execute('INSERT INTO readers (lane_id, mac_address, type, reader_ip) VALUES (?, ?, ?, ?)',
                       (lane_id, mac_address, type_, reader_ip))
            db.commit()
            logging.info(f"Reader added: {mac_address} ({type_}) for lane {lane_id}")
            flash('Reader added!', 'success')
        return redirect(url_for('readers.readers', lane_id=lane_id))
    return render_template('readers.html', lane=lane, readers=readers)

@readers_bp.route('/readers/edit/<int:id>', methods=['GET', 'POST'])
def edit_reader(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    reader = db.execute('SELECT * FROM readers WHERE id = ?', (id,)).fetchone()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (reader['lane_id'],)).fetchone()
    if request.method == 'POST':
        mac_address = request.form['mac_address']
        type_ = request.form['type']
        reader_ip = request.form['reader_ip']
        existing = db.execute('SELECT * FROM readers WHERE lane_id = ? AND type = ? AND id != ?', (reader['lane_id'], type_, id)).fetchone()
        if existing:
            flash(f'{type_.capitalize()} reader already exists for this lane.', 'danger')
        else:
            db.execute('UPDATE readers SET mac_address = ?, type = ?, reader_ip = ? WHERE id = ?',
                       (mac_address, type_, reader_ip, id))
            db.commit()
            logging.info(f"Reader updated: {mac_address} ({type_}) for lane {reader['lane_id']}")
            flash('Reader updated!', 'success')
        return redirect(url_for('readers.readers', lane_id=reader['lane_id']))
    return render_template('edit_reader.html', reader=reader, lane=lane)

@readers_bp.route('/readers/delete/<int:id>', methods=['POST'])
def delete_reader(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    reader = db.execute('SELECT * FROM readers WHERE id = ?', (id,)).fetchone()
    db.execute('DELETE FROM readers WHERE id = ?', (id,))
    db.commit()
    logging.info(f"Reader deleted: {reader['mac_address']} (ID {id})")
    flash('Reader deleted!', 'info')
    return redirect(url_for('readers.readers', lane_id=reader['lane_id']))

@readers_bp.route('/readers/<int:id>/open-barrier', methods=['POST'])
def open_barrier(id):
    """
    Open the barrier for a specific reader (relay) from the web UI.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM readers")
    total_relays = cursor.fetchone()[0]
    relay_num = id  # Assuming relay number matches reader id (adjust if needed)
    if relay_num < 1 or relay_num > total_relays:
        return jsonify({"success": False, "error": "Invalid relay number"}), 400
    relay_controller = current_app.relay_controller
    try:
        relay_controller.turn_on(relay_num)
        import time
        time.sleep(2)
        relay_controller.turn_off(relay_num)
        return jsonify({"success": True, "activated": relay_num}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@readers_bp.route('/rfid/rfpower', methods=['GET'])
def rfid_rfpower_page():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('rfid_rfpower.html')

@readers_bp.route('/api/readers', methods=['POST'])
def api_add_reader():
    """API endpoint to add a reader (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    lane_id = data.get("lane_id")
    mac_address = data.get("mac_address")
    type_ = data.get("type")
    reader_ip = data.get("reader_ip")
    if not lane_id or not mac_address or not type_ or not reader_ip:
        return {"success": False, "error": "Missing lane_id, mac_address, type, or reader_ip"}, 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO readers (lane_id, mac_address, type, reader_ip) VALUES (?, ?, ?, ?)', (lane_id, mac_address, type_, reader_ip))
        db.commit()
        reader_id = cursor.lastrowid
        logging.info(f"Reader added via API: {mac_address} ({type_}) for lane {lane_id}")
        return {"success": True, "reader_id": reader_id}, 201
    except Exception as e:
        logging.error(f"Error adding reader via API: {e}")
        return {"success": False, "error": str(e)}, 500

@readers_bp.route('/api/readers/<int:id>', methods=['PUT'])
def api_edit_reader(id):
    """API endpoint to edit a reader (for mobile app)"""
    if not request.is_json:
        return {"success": False, "error": "Request must be JSON"}, 400
    data = request.get_json()
    lane_id = data.get("lane_id")
    mac_address = data.get("mac_address")
    type_ = data.get("type")
    reader_ip = data.get("reader_ip")
    if not lane_id or not mac_address or not type_ or not reader_ip:
        return {"success": False, "error": "Missing lane_id, mac_address, type, or reader_ip"}, 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE readers SET lane_id = ?, mac_address = ?, type = ?, reader_ip = ? WHERE id = ?', (lane_id, mac_address, type_, reader_ip, id))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Reader not found"}, 404
        logging.info(f"Reader updated via API: {mac_address} ({type_}) for lane {lane_id} (ID {id})")
        return {"success": True}, 200
    except Exception as e:
        logging.error(f"Error editing reader via API: {e}")
        return {"success": False, "error": str(e)}, 500

@readers_bp.route('/api/readers/<int:id>', methods=['DELETE'])
def api_delete_reader(id):
    """API endpoint to delete a reader (for mobile app)"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM readers WHERE id = ?', (id,))
        db.commit()
        if cursor.rowcount == 0:
            return {"success": False, "error": "Reader not found"}, 404
        logging.info(f"Reader deleted via API (ID {id})")
        return {"success": True}, 200
    except Exception as e:
        logging.error(f"Error deleting reader via API: {e}")
        return {"success": False, "error": str(e)}, 500

@readers_bp.route('/api/readers', methods=['GET'])
def api_view_readers():
    """API endpoint to view all readers (optionally filter by lane_id)"""
    lane_id = request.args.get('lane_id', type=int)
    try:
        db = get_db()
        if lane_id:
            readers = db.execute('SELECT id, lane_id, mac_address, type, reader_ip FROM readers WHERE lane_id = ?', (lane_id,)).fetchall()
        else:
            readers = db.execute('SELECT id, lane_id, mac_address, type, reader_ip FROM readers').fetchall()
        readers_list = [dict(r) for r in readers]
        return {"success": True, "readers": readers_list}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500 