-- mysql_queries.sql
-- ------------------
-- MySQL-equivalent schema and queries for the Job Market Tracker project.
--
-- The deployed version of this app uses PostgreSQL (via Neon.tech's free
-- tier), since Neon only supports Postgres. This file demonstrates the
-- same database logic written in MySQL syntax.

-- ============================================================
-- 1. Create table
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    adzuna_id           VARCHAR(255) UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    company             TEXT,
    location            TEXT,
    description         TEXT,
    skills_matched      TEXT,
    match_percentage    FLOAT,
    experience_level    VARCHAR(50),
    certification_note  TEXT,
    apply_link          TEXT,
    date_posted         VARCHAR(50),
    date_pulled         VARCHAR(50),
    applied             TINYINT DEFAULT 0,
    applied_date        VARCHAR(50)
);

-- ============================================================
-- 2. Insert a new job (skip if adzuna_id already exists)
-- ============================================================
-- In Python, you'd check for existence first (like the Postgres version),
-- OR use MySQL's own duplicate-handling:
INSERT IGNORE INTO jobs (
    adzuna_id, title, company, location, description,
    skills_matched, match_percentage, experience_level,
    certification_note, apply_link, date_posted, date_pulled,
    applied, applied_date
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NULL
);

-- ============================================================
-- 3. Mark a job as applied / not applied
-- ============================================================
UPDATE jobs
SET applied = %s,
    applied_date = %s
WHERE id = %s;

-- ============================================================
-- 4. Fetch jobs with filters
-- ============================================================
-- Note: Postgres uses ILIKE (case-insensitive LIKE).
-- MySQL's LIKE is case-insensitive by default for most collations,
-- so plain LIKE works the same way here.
SELECT * FROM jobs
WHERE (location LIKE CONCAT('%', %s, '%') OR %s IS NULL)
  AND (skills_matched LIKE CONCAT('%', %s, '%') OR %s IS NULL)
  AND (experience_level = %s OR %s IS NULL)
ORDER BY date_pulled DESC;

-- ============================================================
-- 5. Get distinct values for a column (used for filter dropdowns)
-- ============================================================
SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL;
