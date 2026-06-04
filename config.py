import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production-abc123')

    # ── Database (SQLite) ─────────────────────────────────────────────────────
    BASE_DIR  = os.path.abspath(os.path.dirname(__file__))
    DATABASE  = os.path.join(BASE_DIR, 'certificates.db')

    # ── File Paths ────────────────────────────────────────────────────────────
    CERT_FOLDER = os.path.join(BASE_DIR, 'static', 'certificates')
    QR_FOLDER   = os.path.join(BASE_DIR, 'static', 'qr')

    # ── Base URL (change to your domain in production) ────────────────────────
    BASE_URL = os.environ.get('BASE_URL', 'http://verify.nptal.in')

    # ── Admin Credentials ─────────────────────────────────────────────────────
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin@smartprep')
