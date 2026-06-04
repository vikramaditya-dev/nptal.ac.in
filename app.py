import os
import sqlite3
import uuid
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from config import Config
from utils.qr_generator import generate_qr

app = Flask(__name__)
app.config.from_object(Config)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Ensure folders exist
os.makedirs(app.config['CERT_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

# ---------------- DATABASE CONNECTION ---------------- #

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # Dict-like access to rows
    return conn

def init_db():
    """Initialize the SQLite database with required tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT    NOT NULL UNIQUE,
            student_name   TEXT    NOT NULL,
            course_name    TEXT    NOT NULL,
            score          TEXT    NOT NULL,
            issue_date     TEXT    NOT NULL,
            image_path     TEXT    NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Auto-initialize DB on startup
with app.app_context():
    init_db()

# ---------------- HELPERS ---------------- #

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_certificate_id():
    year = date.today().year
    unique = uuid.uuid4().hex[:6].upper()
    return f"SPAI{year}-{unique}"

# ---------------- HOME ---------------- #

@app.route('/')
def home():
    return redirect(url_for('admin_login'))

# ---------------- ADMIN LOGIN ---------------- #

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == app.config['ADMIN_USERNAME'] and
                request.form['password'] == app.config['ADMIN_PASSWORD']):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ---------------- ADMIN ACCESS CONTROL ---------------- #

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ---------------- DASHBOARD ---------------- #

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM certificates ORDER BY id DESC")
    certs = cursor.fetchall()
    db.close()
    return render_template('dashboard.html', certs=certs)

# ---------------- ADD CERTIFICATE ---------------- #

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_certificate():
    if request.method == 'POST':
        student_name = request.form['student_name'].strip()
        course_name  = request.form['course_name'].strip()
        score        = request.form['score'].strip()
        issue_date   = request.form['issue_date']
        file         = request.files.get('certificate_image')

        if not file or file.filename == '':
            flash('Please upload a certificate image.', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Allowed file types: PNG, JPG, JPEG, PDF', 'error')
            return redirect(request.url)

        cert_id = generate_certificate_id()

        filename = secure_filename(f"{cert_id}_{file.filename}")
        img_path = os.path.join(app.config['CERT_FOLDER'], filename)
        file.save(img_path)

        # Public URL for QR
        cert_url = f"{app.config['BASE_URL']}/certificate/{cert_id}"

        qr_filename = f"{cert_id}.png"
        qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
        generate_qr(cert_url, qr_path)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO certificates
            (certificate_id, student_name, course_name, score, issue_date, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cert_id,
            student_name,
            course_name,
            score,
            issue_date,
            f"certificates/{filename}"
        ))

        db.commit()
        db.close()

        flash(f'Certificate {cert_id} created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_certificate.html')

# ---------------- DELETE CERTIFICATE ---------------- #

@app.route('/admin/delete/<certificate_id>', methods=['POST'])
@admin_required
def delete_certificate(certificate_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT image_path FROM certificates WHERE certificate_id = ?",
        (certificate_id,)
    )
    cert = cursor.fetchone()

    if not cert:
        db.close()
        flash('Certificate not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    cursor.execute(
        "DELETE FROM certificates WHERE certificate_id = ?",
        (certificate_id,)
    )
    db.commit()
    db.close()

    certificate_path = os.path.join(app.static_folder, cert['image_path'])
    qr_path = os.path.join(app.config['QR_FOLDER'], f"{certificate_id}.png")

    for path in (certificate_path, qr_path):
        if os.path.exists(path):
            os.remove(path)

    flash(f'Certificate {certificate_id} deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# ---------------- VIEW CERTIFICATE (QR Target) ---------------- #

@app.route('/certificate/<certificate_id>')
def view_certificate(certificate_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM certificates WHERE certificate_id = ?",
        (certificate_id,)
    )

    cert = cursor.fetchone()
    db.close()

    if not cert:
        return render_template('not_found.html'), 404

    return render_template('certificate.html', cert=cert)

# ---------------- RUN APP ---------------- #

if __name__ == '__main__':
    app.run(debug=True)
