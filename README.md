# Job Market Trend Tracker

An end-to-end job search tool: a pipeline pulls live postings from the Adzuna API,
scores them against your skillset, and stores everything in a local SQLite
database. That same database powers:

- **A Streamlit dashboard** (`app.py`) — filter jobs by location, skill, experience
  level, and certification requirement, see a match %, and mark jobs as "Applied"
  with one click.
- **A Power BI report** — for polished, shareable trend visuals (jobs over time,
  match % distribution, top locations, etc.).

Because both read from the same database, running the pipeline once updates
both dashboards.

## Project structure

```
job-market-tracker/
├── config.py         # Loads API keys + settings from environment variables
├── database.py        # SQLite schema, insert/read/update logic
├── fetch_jobs.py       # Pulls postings from Adzuna, scores + saves new ones
├── app.py             # Streamlit dashboard
├── requirements.txt
├── .env.example        # Template for your local secrets file
└── .gitignore
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Get free Adzuna API credentials at https://developer.adzuna.com/
3. Copy the env template and fill in your real keys:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   ADZUNA_APP_ID=your_real_id
   ADZUNA_APP_KEY=your_real_key
   ```
4. Pull jobs into the database:
   ```bash
   python fetch_jobs.py
   ```
5. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```

Run `python fetch_jobs.py` again anytime (or schedule it, e.g. daily) — only
genuinely new postings get added, so nothing duplicates.

## Connecting Power BI to the same database

1. Install the **SQLite ODBC driver** (search "sqliteodbc" — Christian Werner's
   driver is the standard one) so Windows/Power BI can read `.db` files.
2. In Power BI Desktop: **Get Data → More → ODBC** → pick the SQLite DSN you
   configured → select the `jobs` table.
3. Build your visuals (jobs over time, match % distribution, top skills, etc.)
4. Click **Refresh** anytime after running `fetch_jobs.py` to pull in new postings.

## How the "Applied" and filters work

- Every job row has an `applied` flag and `applied_date` in the database.
- Ticking the checkbox in the Streamlit card calls `mark_applied()`, which
  updates that row immediately — no separate save step.
- Filters (location, skill, experience level, certification, applied status,
  minimum match %) are all applied as a SQL query in `database.get_jobs()`,
  so they stay fast even as your job list grows.

## Uploading this project to GitHub (and keeping your API key safe)

**The rule: your real API key should only ever live in your local `.env` file,
which is never committed.** Here's how that's already set up, plus the exact
steps to push:

1. **Confirm your `.gitignore` is in place first** (it already excludes `.env`
   and `*.db` in this project — don't delete those lines).

2. **Double-check no key is hardcoded anywhere** — search for it before pushing:
   ```bash
   grep -r "ADZUNA" --include="*.py" .
   ```
   You should only see `os.getenv(...)` calls in `config.py`, never an actual key.

3. **Initialize git and make your first commit:**
   ```bash
   cd job-market-tracker
   git init
   git add .gitignore
   git add .
   git status
   ```
   At this point, check the `git status` output carefully — `.env` and any
   `.db` file should **not** appear in the list of files to be committed. If
   they do, stop and check your `.gitignore`.

4. **Commit and push:**
   ```bash
   git commit -m "Initial commit: job market tracker with Streamlit dashboard"
   ```
   Create a new empty repository on GitHub (no README/license, so it stays empty),
   then:
   ```bash
   git remote add origin https://github.com/tanvishelke21/job-market-tracker.git
   git branch -M main
   git push -u origin main
   ```

5. **If you have an OLDER version of this project where a key was already
   committed to git history**, adding `.gitignore` now is not enough — the key
   is still visible in old commits. Easiest fix for a personal project: delete
   the old `.git` folder and start a fresh repo (steps above), **and rotate
   (regenerate) your Adzuna key** from your Adzuna dashboard, since the old one
   should be treated as exposed.

6. **Deploying the Streamlit app publicly?** Don't use `.env` on the server.
   Instead use Streamlit Cloud's **Secrets** manager (Settings → Secrets) and
   paste the same `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` values there — Streamlit
   automatically exposes them the same way environment variables would.

## Ideas to make the dashboard even better

A few optional additions — happy to build any of these if you want them, just
say yes/no:

- A "Notes" text box per job (e.g. why you applied, referral contact)
- A weekly email/summary of new high-match jobs
- Sorting by match % or date posted
- A simple bar chart at the top of the Streamlit app (jobs by location) so you
  don't need Power BI open just to see the shape of your search
- A "Saved for later" status in addition to Applied
