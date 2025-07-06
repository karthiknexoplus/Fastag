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
        lanes = db.execute('SELECT * FROM lanes WHERE location_id = ?', (selected_location,)).fetchall()
        lane_ids = [lane['id'] for lane in lanes]
        if lane_ids:
            qmarks = ','.join('?'*len(lane_ids))
            readers = db.execute(f'SELECT lane_id, COUNT(*) as count FROM readers WHERE lane_id IN ({qmarks}) GROUP BY lane_id', lane_ids).fetchall()
            readers_map = {row['lane_id']: row['count'] for row in readers}
    if request.method == 'POST':
        location_id = request.form['location_id']
        lane_name = request.form['lane_name']
        db.execute('INSERT INTO lanes (location_id, lane_name) VALUES (?, ?)', (location_id, lane_name))
        db.commit()
        logging.info(f"Lane added: {lane_name} (Location {location_id})")
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
        location_id = request.form['location_id']
        lane_name = request.form['lane_name']
        db.execute('UPDATE lanes SET location_id = ?, lane_name = ? WHERE id = ?', (location_id, lane_name, id))
        db.commit()
        logging.info(f"Lane updated: {lane_name} (ID {id})")
        flash('Lane updated!', 'success')
        return redirect(url_for('lanes.lanes', location_id=location_id))
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