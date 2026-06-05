-- SQLite schema for Certificate Verification System (Cloudinary edition)
-- Tables are auto-created by app.py on first run.

CREATE TABLE IF NOT EXISTS certificates (
    id             INTEGER   PRIMARY KEY AUTOINCREMENT,
    certificate_id TEXT      NOT NULL UNIQUE,
    student_name   TEXT      NOT NULL,
    course_name    TEXT      NOT NULL,
    score          TEXT      NOT NULL,
    issue_date     TEXT      NOT NULL,
    image_url      TEXT      NOT NULL,   -- Cloudinary permanent URL
    qr_url         TEXT      NOT NULL,   -- Cloudinary permanent URL
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
