"""
fetch_jobs.py
-------------
Pulls live job postings from the Adzuna API, scores each one against your
skillset, detects certification requirements, and saves NEW postings into
the SQLite database.

Run this manually whenever you want fresh postings:
    python fetch_jobs.py

Or schedule it (Windows Task Scheduler / cron / GitHub Actions) to run
automatically, e.g. every morning. Since insert_job() skips duplicates,
you can safely run this as often as you like.

NOTE: Adapt SEARCH_KEYWORDS / SEARCH_COUNTRY / SEARCH_LOCATION below to
match your own job search, and plug in your own matching logic if you
already have a more advanced one (e.g. TF-IDF or embeddings).
"""

import requests
from bs4 import BeautifulSoup

from config import (
    ADZUNA_APP_ID, ADZUNA_APP_KEY, MY_SKILLS,
    CERTIFICATION_KEYWORDS, validate_config,
)
from database import init_db, insert_job

# --- Search settings: edit these to match what you're looking for ---
SEARCH_COUNTRY = "in"          # Adzuna country code, e.g. "in" for India
SEARCH_KEYWORDS = "data analyst"
SEARCH_LOCATION = "Pune"
RESULTS_PER_PAGE = 20
PAGES_TO_FETCH = 2

ADZUNA_URL = f"https://api.adzuna.com/v1/api/jobs/{SEARCH_COUNTRY}/search"


def score_match(description: str):
    """
    Very simple keyword-based match score: what % of MY_SKILLS appear
    in the job description, plus the list of matched skills.
    Replace this with your own scoring logic (e.g. the one you already
    built with SMOTE/GridSearchCV features) if you have something fancier.
    """
    text = description.lower()
    matched = [skill for skill in MY_SKILLS if skill in text]
    match_percentage = round(100 * len(matched) / len(MY_SKILLS), 1)
    return match_percentage, ", ".join(matched)


def detect_certification(description: str):
    """Return a short note if the description mentions a certification, else None."""
    text = description.lower()
    found = [kw for kw in CERTIFICATION_KEYWORDS if kw in text]
    return ", ".join(found) if found else None


def guess_experience_level(title: str, description: str):
    """Very rough heuristic — tune this to your own needs."""
    text = f"{title} {description}".lower()
    if "senior" in text or "5+ years" in text or "lead" in text:
        return "Senior"
    if "fresher" in text or "entry" in text or "0-1 year" in text or "trainee" in text:
        return "Entry-level"
    return "Mid-level"


def resolve_direct_apply_url(adzuna_url: str, session: requests.Session) -> str:
    """
    Adzuna's API only ever gives us a link to an Adzuna-hosted page
    (redirect_url), not the employer's real application page. Clicking
    "Apply" on Adzuna's own site normally shows an extra "Apply for this
    job" step, sometimes followed by an email-capture popup ("Receive
    similar jobs by email") before you actually reach the real posting.

    This function tries to skip straight to the real posting by:
      1. Following redirect_url. For some postings Adzuna 302-redirects
         straight to the real employer/job-board page — if so, we're done.
      2. If we're still on an Adzuna page, parsing its HTML for the
         outbound link (e.g. the "No thanks, take me to the job" link, or
         an "Apply" link) and using that instead.

    This is best-effort scraping of a page Adzuna intentionally designed
    to route traffic through their own site, so:
      - It can silently stop working if Adzuna changes their page layout.
      - It roughly doubles the number of HTTP requests fetch_jobs.py makes,
        so it will run slower than before.
    If anything goes wrong, or no better link is found, we simply fall
    back to the original Adzuna URL — so "Apply" in the dashboard never
    breaks, it just occasionally lands on Adzuna's page instead of the
    employer's.
    """
    if not adzuna_url:
        return adzuna_url

    try:
        resp = session.get(adzuna_url, timeout=15, allow_redirects=True)
        final_url = resp.url

        # Already left Adzuna's domain entirely -> nothing more to do.
        if "adzuna." not in final_url:
            return final_url

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=True)

        # Prefer the explicit bypass link from the email-capture popup.
        for link in links:
            if "take me to the job" in link.get_text(strip=True).lower():
                href = link["href"]
                if href.startswith("http") and "adzuna." not in href:
                    return href

        # Otherwise take the first plausible outbound "apply" link.
        for link in links:
            href = link["href"]
            if not href.startswith("http") or "adzuna." in href:
                continue
            if "apply" in link.get_text(strip=True).lower():
                return href

        # Couldn't find a better link — fall back to Adzuna's own page.
        return final_url

    except Exception:
        # Network error, timeout, parsing issue, etc. -> don't break the
        # pipeline, just use the original Adzuna link.
        return adzuna_url


def fetch_page(page: int):
    """Fetch a single page of results from the Adzuna API."""
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": SEARCH_KEYWORDS,
        "where": SEARCH_LOCATION,
        "results_per_page": RESULTS_PER_PAGE,
    }
    response = requests.get(f"{ADZUNA_URL}/{page}", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def run():
    validate_config()
    init_db()

    new_count = 0
    # Reuse one session across requests (faster, and plays nicer with the
    # site we're resolving links against than opening a fresh connection
    # every time).
    session = requests.Session()

    for page in range(1, PAGES_TO_FETCH + 1):
        results = fetch_page(page)
        for posting in results:
            description = posting.get("description", "")
            match_percentage, matched_skills = score_match(description)

            direct_apply_link = resolve_direct_apply_url(
                posting.get("redirect_url"), session
            )

            job = {
                "adzuna_id": posting.get("id"),
                "title": posting.get("title", "").strip(),
                "company": posting.get("company", {}).get("display_name", "Unknown"),
                "location": posting.get("location", {}).get("display_name", "Unknown"),
                "description": description,
                "skills_matched": matched_skills,
                "match_percentage": match_percentage,
                "experience_level": guess_experience_level(posting.get("title", ""), description),
                "certification_note": detect_certification(description),
                "apply_link": direct_apply_link,
                "date_posted": posting.get("created"),
            }

            was_new = insert_job(job)
            if was_new:
                new_count += 1

    print(f"Done. {new_count} new job(s) added to the database.")


if __name__ == "__main__":
    run()
