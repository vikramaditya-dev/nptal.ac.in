-- SQLite schema for Certificate Verification System
-- This is for reference only.
-- The app.py automatically creates the table on first run via init_db().

CREATE TABLE IF NOT EXISTS certificates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_id TEXT    NOT NULL UNIQUE,
    student_name   TEXT    NOT NULL,
    course_name    TEXT    NOT NULL,
    score          TEXT    NOT NULL,
    issue_date     TEXT    NOT NULL,
    image_path     TEXT    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
