"""
config.py
---------
Loads all secrets and settings from environment variables.

Why this file exists:
  - We NEVER want API keys typed directly into our code.
  - Instead, keys live in a local ".env" file (which is excluded from
    GitHub via .gitignore) and this file reads them safely.
  - If a key is missing, we fail loudly with a clear error instead of
    silently breaking later.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file into the environment.
# This does nothing on a server where the variables are already set
# (e.g. Streamlit Cloud secrets), so it's safe everywhere.
load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Postgres connection string from Neon.tech (free tier).
# Looks like: postgresql://user:password@ep-xxxx.neon.tech/neondb?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL")

# List of skills used to score how well a job matches your profile.
# Edit this list to match your own skillset.
MY_SKILLS = [
    "python", "sql", "power bi", "dax", "pandas", "matplotlib",
    "scikit-learn", "xgboost", "random forest", "mongodb",
    "machine learning", "data analysis", "excel",
]

# Keywords used to detect if a job description mentions a certification
# requirement. Edit/extend this list as needed.
CERTIFICATION_KEYWORDS = [
    "certified", "certification", "certificate required",
    "pmp", "cfa", "aws certified", "azure certified",
    "google certified", "oracle certified",
]

def validate_config():
    """Raise a clear error early if required secrets are missing."""
    missing = []
    if not ADZUNA_APP_ID:
        missing.append("ADZUNA_APP_ID")
    if not ADZUNA_APP_KEY:
        missing.append("ADZUNA_APP_KEY")
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}.\n"
            f"Create a '.env' file (see .env.example) and set these values."
        )
