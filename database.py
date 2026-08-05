"""
database.py
-----------
All Postgres (Neon) database logic lives here: creating the table, inserting
new jobs (without duplicating ones we already have), reading jobs back with
filters, and marking a job as "Applied".

Uses Postgres instead of local SQLite so data survives restarts/redeploys on
Render, Streamlit Cloud, and GitHub Actions runners.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from config import DATABASE_URL


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id                  SERIAL PRIMARY KEY,
            adzuna_id           TEXT UNIQUE NOT NULL,
            title               TEXT NOT NULL,
            company             TEXT,
            location            TEXT,
            description         TEXT,
            skills_matched      TEXT,
            match_percentage    REAL,
            experience_level    TEXT,
            certification_note  TEXT,
            apply_link          TEXT,
            date_posted         TEXT,
            date_pulled         TEXT,
            applied             INTEGER DEFAULT 0,
            applied_date        TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def insert_job(job: dict) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM jobs WHERE adzuna_id = %s", (job["adzuna_id"],))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False

    cur.execute("""
        INSERT INTO jobs (
            adzuna_id, title, company, location, description,
            skills_matched, match_percentage, experience_level,
            certification_note, apply_link, date_posted, date_pulled,
            applied, applied_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NULL)
    """, (
        job["adzuna_id"], job["title"], job["company"], job["location"],
        job["description"], job["skills_matched"], job["match_percentage"],
        job["experience_level"], job["certification_note"],
        job["apply_link"], job["date_posted"],
        datetime.now().isoformat(timespec="seconds"),
    ))
    conn.commit()
    cur.close()
    conn.close()
    return True


def mark_applied(job_id: int, applied: bool = True):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE jobs SET applied = %s, applied_date = %s WHERE id = %s",
        (
            1 if applied else 0,
            datetime.now().isoformat(timespec="seconds") if applied else None,
            job_id,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_jobs(location=None, skill=None, experience_level=None,
             certification_only=False, applied_status="All", last_24h=False):
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if location:
        query += " AND location ILIKE %s"
        params.append(f"%{location}%")

    if skill:
        query += " AND skills_matched ILIKE %s"
        params.append(f"%{skill}%")

    if experience_level:
        query += " AND experience_level = %s"
        params.append(experience_level)

    if certification_only:
        query += " AND certification_note IS NOT NULL AND certification_note != ''"

    if applied_status == "Applied":
        query += " AND applied = 1"
    elif applied_status == "Not Applied":
        query += " AND applied = 0"

    if last_24h:
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat(timespec="seconds")
        query += " AND date_pulled >= %s"
        params.append(cutoff)

    query += " ORDER BY date_pulled DESC"

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]


def get_distinct_values(column: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT {column} FROM jobs WHERE {column} IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return sorted({row[0] for row in rows if row[0]})
