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
        site_id = request.form.get('site_id') or os.urandom(4).hex().upper()
        db.execute('INSERT INTO locations (name, address, site_id) VALUES (?, ?, ?)', (name, address, site_id))
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
        db.execute('UPDATE locations SET name = ?, address = ? WHERE id = ?', (name, address, id))
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