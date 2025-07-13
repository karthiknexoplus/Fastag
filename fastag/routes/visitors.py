from flask import Blueprint, request, jsonify, send_from_directory
from fastag.utils.db import get_db
import os
from datetime import datetime

visitors_bp = Blueprint('visitors', __name__)

VISITOR_IMG_DIR = os.path.join('instance', 'visitor_images')
os.makedirs(VISITOR_IMG_DIR, exist_ok=True)

# --- Visitor Categories ---

@visitors_bp.route('/api/visitor-categories', methods=['GET'])
def list_visitor_categories():
    db = get_db()
    rows = db.execute("SELECT id, name FROM visitor_categories ORDER BY name").fetchall()
    return jsonify([{'id': r[0], 'name': r[1]} for r in rows])

@visitors_bp.route('/api/visitor-categories', methods=['POST'])
def create_visitor_category():
    name = request.form['name']
    db = get_db()
    db.execute("INSERT INTO visitor_categories (name) VALUES (?)", (name,))
    db.commit()
    cat_id = db.execute("SELECT id FROM visitor_categories WHERE name=?", (name,)).fetchone()[0]
    return jsonify({'status': 'success', 'category_id': cat_id})

# --- Beneficiaries (KYC Users) ---

@visitors_bp.route('/api/beneficiaries', methods=['GET'])
def list_beneficiaries():
    db = get_db()
    rows = db.execute("SELECT id, name, fastag_id FROM kyc_users ORDER BY name").fetchall()
    return jsonify([{'id': r[0], 'name': r[1], 'fastag_id': r[2]} for r in rows])

# --- Visitor Entry ---

@visitors_bp.route('/api/visitor-entry', methods=['POST'])
def visitor_entry():
    name = request.form['name']
    mobile = request.form.get('mobile')
    beneficiary_id = request.form['beneficiary_id']
    category_id = request.form['category_id']
    entry_image = request.files['entry_image']
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{entry_image.filename}"
    save_path = os.path.join(VISITOR_IMG_DIR, filename)
    entry_image.save(save_path)
    db = get_db()
    db.execute("""
        INSERT INTO visitors (name, mobile, beneficiary_id, category_id, entry_image_path, status)
        VALUES (?, ?, ?, ?, ?, 'in')
    """, (name, mobile, beneficiary_id, category_id, filename))
    db.commit()
    visitor_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({'status': 'success', 'visitor_id': visitor_id})

# --- Visitor Exit ---

@visitors_bp.route('/api/visitor-exit', methods=['POST'])
def visitor_exit():
    visitor_id = request.form['visitor_id']
    exit_image = request.files['exit_image']
    filename = f"exit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{exit_image.filename}"
    save_path = os.path.join(VISITOR_IMG_DIR, filename)
    exit_image.save(save_path)
    db = get_db()
    db.execute("""
        UPDATE visitors SET exit_time=CURRENT_TIMESTAMP, exit_image_path=?, status='out'
        WHERE id=?
    """, (filename, visitor_id))
    db.commit()
    return jsonify({'status': 'success'})

# --- List Visitors ---

@visitors_bp.route('/api/visitors', methods=['GET'])
def list_visitors():
    db = get_db()
    rows = db.execute("""
        SELECT v.id, v.name, v.mobile, ku.name, vc.name, v.entry_time, v.entry_image_path,
               v.exit_time, v.exit_image_path, v.status
        FROM visitors v
        LEFT JOIN kyc_users ku ON v.beneficiary_id = ku.id
        LEFT JOIN visitor_categories vc ON v.category_id = vc.id
        ORDER BY v.entry_time DESC
    """).fetchall()
    def img_url(path):
        return f"/api/visitor-image/{path}" if path else None
    return jsonify([
        {
            'id': r[0], 'name': r[1], 'mobile': r[2], 'beneficiary': r[3], 'category': r[4],
            'entry_time': r[5], 'entry_image_url': img_url(r[6]),
            'exit_time': r[7], 'exit_image_url': img_url(r[8]), 'status': r[9]
        } for r in rows
    ])

# --- Serve Visitor Images ---

@visitors_bp.route('/api/visitor-image/<filename>')
def visitor_image(filename):
    return send_from_directory(VISITOR_IMG_DIR, filename) 