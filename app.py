from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
import uuid

app = Flask(__name__, instance_relative_config=True)
app.secret_key = os.urandom(24)

# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

DB_PATH = os.path.join(app.instance_path, 'fastag.db')

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            site_id TEXT UNIQUE NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS lanes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            lane_name TEXT NOT NULL,
            FOREIGN KEY(location_id) REFERENCES locations(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane_id INTEGER NOT NULL,
            mac_address TEXT NOT NULL,
            type TEXT CHECK(type IN ('entry', 'exit')) NOT NULL,
            reader_ip TEXT NOT NULL,
            FOREIGN KEY(lane_id) REFERENCES lanes(id),
            UNIQUE(lane_id, type)
        )''')
        conn.commit()

init_db()

def log_activity(username, action):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO activity_log (username, action, timestamp) VALUES (?, ?, ?)',
                  (username, action, datetime.now().isoformat()))
        conn.commit()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('locations'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username = ?', (username,))
            row = c.fetchone()
        if row and check_password_hash(row[0], password):
            session['user'] = username
            log_activity(username, 'login')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
                conn.commit()
            log_activity(username, 'signup')
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'danger')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    username = session.get('user')
    session.pop('user', None)
    if username:
        log_activity(username, 'logout')
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/locations', methods=['GET', 'POST'])
def locations():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        site_id = str(uuid.uuid4())[:8].upper()
        db.execute('INSERT INTO locations (name, address, site_id) VALUES (?, ?, ?)', (name, address, site_id))
        db.commit()
        flash('Location added!', 'success')
        return redirect(url_for('locations'))
    locations = db.execute('SELECT * FROM locations').fetchall()
    return render_template('locations.html', locations=locations)

@app.route('/lanes', methods=['GET', 'POST'])
def lanes():
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
        flash('Lane added!', 'success')
        return redirect(url_for('lanes', location_id=location_id))
    return render_template('lanes.html', lanes=lanes, locations=locations, selected_location=selected_location, readers_map=readers_map)

@app.route('/locations/edit/<int:id>', methods=['GET', 'POST'])
def edit_location(id):
    db = get_db()
    loc = db.execute('SELECT * FROM locations WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        db.execute('UPDATE locations SET name = ?, address = ? WHERE id = ?', (name, address, id))
        db.commit()
        flash('Location updated!', 'success')
        return redirect(url_for('locations'))
    return render_template('edit_location.html', loc=loc)

@app.route('/locations/delete/<int:id>', methods=['POST'])
def delete_location(id):
    db = get_db()
    db.execute('DELETE FROM locations WHERE id = ?', (id,))
    db.commit()
    flash('Location deleted!', 'info')
    return redirect(url_for('locations'))

@app.route('/lanes/edit/<int:id>', methods=['GET', 'POST'])
def edit_lane(id):
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (id,)).fetchone()
    locations = db.execute('SELECT * FROM locations').fetchall()
    if request.method == 'POST':
        location_id = request.form['location_id']
        lane_name = request.form['lane_name']
        db.execute('UPDATE lanes SET location_id = ?, lane_name = ? WHERE id = ?', (location_id, lane_name, id))
        db.commit()
        flash('Lane updated!', 'success')
        return redirect(url_for('lanes', location_id=location_id))
    return render_template('edit_lane.html', lane=lane, locations=locations)

@app.route('/lanes/delete/<int:id>', methods=['POST'])
def delete_lane(id):
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (id,)).fetchone()
    db.execute('DELETE FROM lanes WHERE id = ?', (id,))
    db.execute('DELETE FROM readers WHERE lane_id = ?', (id,))
    db.commit()
    flash('Lane and its readers deleted!', 'info')
    return redirect(url_for('lanes', location_id=lane['location_id']))

@app.route('/readers/<int:lane_id>', methods=['GET', 'POST'])
def readers(lane_id):
    db = get_db()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (lane_id,)).fetchone()
    readers = db.execute('SELECT * FROM readers WHERE lane_id = ?', (lane_id,)).fetchall()
    if request.method == 'POST':
        mac_address = request.form['mac_address']
        type_ = request.form['type']
        reader_ip = request.form['reader_ip']
        # Enforce max 1 entry and 1 exit per lane
        existing = db.execute('SELECT * FROM readers WHERE lane_id = ? AND type = ?', (lane_id, type_)).fetchone()
        if existing:
            flash(f'{type_.capitalize()} reader already exists for this lane.', 'danger')
        else:
            db.execute('INSERT INTO readers (lane_id, mac_address, type, reader_ip) VALUES (?, ?, ?, ?)',
                       (lane_id, mac_address, type_, reader_ip))
            db.commit()
            flash('Reader added!', 'success')
        return redirect(url_for('readers', lane_id=lane_id))
    return render_template('readers.html', lane=lane, readers=readers)

@app.route('/readers/edit/<int:id>', methods=['GET', 'POST'])
def edit_reader(id):
    db = get_db()
    reader = db.execute('SELECT * FROM readers WHERE id = ?', (id,)).fetchone()
    lane = db.execute('SELECT * FROM lanes WHERE id = ?', (reader['lane_id'],)).fetchone()
    if request.method == 'POST':
        mac_address = request.form['mac_address']
        type_ = request.form['type']
        reader_ip = request.form['reader_ip']
        # Enforce max 1 entry and 1 exit per lane
        existing = db.execute('SELECT * FROM readers WHERE lane_id = ? AND type = ? AND id != ?', (reader['lane_id'], type_, id)).fetchone()
        if existing:
            flash(f'{type_.capitalize()} reader already exists for this lane.', 'danger')
        else:
            db.execute('UPDATE readers SET mac_address = ?, type = ?, reader_ip = ? WHERE id = ?',
                       (mac_address, type_, reader_ip, id))
            db.commit()
            flash('Reader updated!', 'success')
        return redirect(url_for('readers', lane_id=reader['lane_id']))
    return render_template('edit_reader.html', reader=reader, lane=lane)

@app.route('/readers/delete/<int:id>', methods=['POST'])
def delete_reader(id):
    db = get_db()
    reader = db.execute('SELECT * FROM readers WHERE id = ?', (id,)).fetchone()
    db.execute('DELETE FROM readers WHERE id = ?', (id,))
    db.commit()
    flash('Reader deleted!', 'info')
    return redirect(url_for('readers', lane_id=reader['lane_id']))

if __name__ == '__main__':
    app.run(debug=True) 