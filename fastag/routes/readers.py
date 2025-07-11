from flask import Blueprint, render_template, redirect, url_for, request, session, flash
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