import os
import sqlite3
import uuid
import io
import random
import string
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from config import Config
from utils.qr_generator import generate_qr_image

import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.config.from_object(Config)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# ── Cloudinary ────────────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name = app.config['CLOUDINARY_CLOUD_NAME'],
    api_key    = app.config['CLOUDINARY_API_KEY'],
    api_secret = app.config['CLOUDINARY_API_SECRET'],
    secure     = True
)

os.makedirs(app.config['CERT_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'],   exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id             INTEGER   PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT      NOT NULL UNIQUE,
            student_name   TEXT      NOT NULL,
            course_name    TEXT      NOT NULL,
            score          TEXT      NOT NULL,
            issue_date     TEXT      NOT NULL,
            image_url      TEXT      NOT NULL,
            qr_url         TEXT      NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_certificate_id():
    """
    NPTEL-style ID — no dashes, one long string.
    Example: SPAI26CS35S55050626404989372
        SPAI        = organisation prefix
        26          = 2-digit year
        CS35        = 4-char random course code
        S55         = 3-char random section code
        050626      = issue date DDMMYY
        404989372   = 9-digit random serial
    """
    yy          = str(date.today().year)[2:]
    course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    section     = 'S' + ''.join(random.choices(string.digits, k=2))
    datestamp   = date.today().strftime('%d%m%y')
    serial      = ''.join(random.choices(string.digits, k=9))
    return f"SPAI{yy}{course_code}{section}{datestamp}{serial}"

def upload_to_cloudinary(file_stream, public_id, resource_type='image'):
    result = cloudinary.uploader.upload(
        file_stream,
        public_id     = public_id,
        resource_type = resource_type,
        overwrite     = True,
        folder        = "certificates"
    )
    return result['secure_url']

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('admin_login'))

# ── Login / Logout ────────────────────────────────────────────────────────────

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

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    certs = db.execute("SELECT * FROM certificates ORDER BY id DESC").fetchall()
    db.close()
    return render_template('dashboard.html', certs=certs)

# ── Add Certificate ───────────────────────────────────────────────────────────

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

        cert_id   = generate_certificate_id()
        ext       = file.filename.rsplit('.', 1)[1].lower()
        public_id = f"cert_{cert_id}"

        # 1. Upload certificate file to Cloudinary
        resource_type = 'raw' if ext == 'pdf' else 'image'
        image_url = upload_to_cloudinary(file.stream, public_id, resource_type)

        # 2. QR points to /noc/E_Certificate/<cert_id>
        cert_url = f"{app.config['BASE_URL']}/noc/E_Certificate/{cert_id}"
        qr_image = generate_qr_image(cert_url)

        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_url = upload_to_cloudinary(qr_buffer, f"qr_{cert_id}", 'image')

        # 3. Save to DB
        db = get_db()
        db.execute("""
            INSERT INTO certificates
              (certificate_id, student_name, course_name, score, issue_date, image_url, qr_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cert_id, student_name, course_name, score, issue_date, image_url, qr_url))
        db.commit()
        db.close()

        flash(f'Certificate {cert_id} created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_certificate.html')

# ── Delete Certificate ────────────────────────────────────────────────────────

@app.route('/admin/delete/<certificate_id>', methods=['POST'])
@admin_required
def delete_certificate(certificate_id):
    db = get_db()
    cert = db.execute(
        "SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,)
    ).fetchone()

    if not cert:
        db.close()
        flash('Certificate not found.', 'error')
        return redirect(url_for('admin_dashboard'))

    db.execute("DELETE FROM certificates WHERE certificate_id = ?", (certificate_id,))
    db.commit()
    db.close()

    try:
        cloudinary.uploader.destroy(f"certificates/cert_{certificate_id}")
        cloudinary.uploader.destroy(f"certificates/qr_{certificate_id}")
    except Exception:
        pass

    flash(f'Certificate {certificate_id} deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── View Certificate  →  NPTEL-style path: /noc/E_Certificate/<id> ────────────

@app.route('/noc/E_Certificate/<certificate_id>')
def view_certificate(certificate_id):
    db   = get_db()
    cert = db.execute(
        "SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,)
    ).fetchone()
    db.close()

    if not cert:
        return render_template('not_found.html'), 404

    return render_template('certificate.html', cert=cert)

# ── Legacy redirects so old QR codes / links never break ─────────────────────
@app.route('/certificate/<certificate_id>')
@app.route('/verify/<certificate_id>')
def view_certificate_legacy(certificate_id):
    return redirect(
        url_for('view_certificate', certificate_id=certificate_id), 301
    )

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
