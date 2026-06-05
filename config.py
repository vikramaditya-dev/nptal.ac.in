import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production-abc123')

    # ── Database (SQLite) ─────────────────────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, 'certificates.db')

    # ── Local temp folders (only used as staging before Cloudinary upload) ────
    CERT_FOLDER = os.path.join(BASE_DIR, 'static', 'certificates')
    QR_FOLDER   = os.path.join(BASE_DIR, 'static', 'qr')

    # ── Cloudinary (set these as env vars on Render) ──────────────────────────
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY    = os.environ.get('CLOUDINARY_API_KEY',    '')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

    # ── Base URL ──────────────────────────────────────────────────────────────
    
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # ── Admin Credentials ─────────────────────────────────────────────────────
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin@smartprep')
