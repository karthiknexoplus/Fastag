from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from fastag.utils.db import get_db

tariff_bp = Blueprint('tariff', __name__)

@tariff_bp.route('/tariff/<int:lane_id>', methods=['GET', 'POST'])
def manage_tariff(lane_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (lane_id,)).fetchone()
    if not lane or lane['lane_type'].lower() != 'exit':
        flash('Tariffs can only be managed for Exit lanes.', 'danger')
        return redirect(url_for('lanes.lanes'))
    if request.method == 'POST':
        from_minutes = int(request.form['from_minutes'])
        to_minutes = int(request.form['to_minutes'])
        amount = float(request.form['amount'])
        db.execute('INSERT INTO tariffs (lane_id, from_minutes, to_minutes, amount) VALUES (?, ?, ?, ?)',
                   (lane_id, from_minutes, to_minutes, amount))
        db.commit()
        flash('Tariff slab added!', 'success')
        return redirect(url_for('tariff.manage_tariff', lane_id=lane_id))
    tariffs = db.execute('SELECT * FROM tariffs WHERE lane_id = ? ORDER BY from_minutes', (lane_id,)).fetchall()
    return render_template('manage_tariff.html', lane=lane, tariffs=tariffs)

@tariff_bp.route('/tariff/<int:lane_id>/delete/<int:tariff_id>', methods=['POST'])
def delete_tariff(lane_id, tariff_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('DELETE FROM tariffs WHERE id = ?', (tariff_id,))
    db.commit()
    flash('Tariff slab deleted!', 'info')
    return redirect(url_for('tariff.manage_tariff', lane_id=lane_id)) 