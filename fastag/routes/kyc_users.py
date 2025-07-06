from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from fastag.utils.db import get_db
import logging

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