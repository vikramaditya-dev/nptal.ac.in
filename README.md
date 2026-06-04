# Certificate Verification System — SQLite Edition

This project has been converted from MySQL to SQLite.  
**No external database service is required.**

---

## What Changed

| File | Change |
|------|--------|
| `app.py` | Replaced `mysql.connector` with built-in `sqlite3`; switched `%s` placeholders to `?`; added `init_db()` for auto-table creation; uses `conn.row_factory = sqlite3.Row` for dict-like row access |
| `config.py` | Removed all `DB_HOST / DB_USER / DB_PASSWORD / DB_NAME` variables; added `DATABASE` path pointing to `certificates.db` |
| `requirements.txt` | Removed `mysql-connector-python` |
| `database/schema.sql` | Converted to SQLite syntax (for reference only — app auto-creates the table) |

Everything else (templates, static files, routes, QR generation, admin login, file uploads) is **100% unchanged**.

---

## Local Development

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run with Flask dev server
python app.py

# Or run with gunicorn (production-like)
gunicorn app:app
```

The `certificates.db` file is created automatically in the project root on first run.

---

## Deploy on Render

1. Push this folder to a GitHub repository.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Connect your GitHub repo.
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add **Environment Variables** (optional — defaults are set in `config.py`):
   - `SECRET_KEY` — a long random string
   - `ADMIN_USERNAME` — admin username
   - `ADMIN_PASSWORD` — admin password
   - `BASE_URL` — your Render app URL, e.g. `https://your-app.onrender.com`

> **Note on Render persistence:** Render's free tier uses an ephemeral filesystem.  
> The `certificates.db` file and uploaded images will be lost on redeploy/restart.  
> For persistent storage, upgrade to a paid plan and use a Render Disk, or store files externally (e.g., AWS S3).

---

## Admin Credentials (default)

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin@smartprep` |

Change these via environment variables in production.
