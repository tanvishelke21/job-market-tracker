"""
app.py
------
Streamlit dashboard for browsing scraped/pulled jobs, filtering them,
and tracking which ones you've applied to.

Run with:
    streamlit run app.py

Each job is shown as a single card containing: title, company, location,
match %, skills, certification note, a short description, a direct
"Apply" button/link, and an "Applied" checkbox right next to it — ticking
the box saves the status back into the database immediately.
"""

import streamlit as st
from database import init_db, get_jobs, get_distinct_values, mark_applied

st.set_page_config(page_title="Job Market Dashboard", layout="wide")

init_db()

st.title("📊 Job Market Dashboard")
st.caption("Live job postings scored against your skillset — filter, review, and track what you've applied to.")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

locations = ["All"] + get_distinct_values("location")
selected_location = st.sidebar.selectbox("Location", locations)

skill_filter = st.sidebar.text_input("Skill contains (e.g. 'python')")

experience_options = ["All", "Entry-level", "Mid-level", "Senior"]
selected_experience = st.sidebar.selectbox("Experience level", experience_options)

# Shows only jobs whose date_pulled (when fetch_jobs.py added them) is within
# the last 24 hours — i.e. "what's new since yesterday".
last_24h_only = st.sidebar.checkbox("🕐 Only show jobs added in the last 24 hours")

certification_only = st.sidebar.checkbox("Only show jobs requiring a certification")

applied_status = st.sidebar.radio("Applied status", ["All", "Applied", "Not Applied"])

min_match = st.sidebar.slider("Minimum match %", 0, 100, 0)

# ---------------- Fetch filtered jobs ----------------
jobs = get_jobs(
    location=None if selected_location == "All" else selected_location,
    skill=skill_filter or None,
    experience_level=None if selected_experience == "All" else selected_experience,
    certification_only=certification_only,
    applied_status=applied_status,
    last_24h=last_24h_only,
)
jobs = [j for j in jobs if (j["match_percentage"] or 0) >= min_match]

st.write(f"**{len(jobs)} job(s) found**")

# ---------------- Job cards ----------------
for job in jobs:
    with st.container(border=True):
        col_main, col_action = st.columns([4, 1])

        with col_main:
            st.subheader(f"{job['title']} — {job['company']}")
            st.write(f"📍 {job['location']}  |  🎯 Match: {job['match_percentage']}%  |  📈 {job['experience_level']}")

            if job["skills_matched"]:
                st.write(f"**Matched skills:** {job['skills_matched']}")

            if job["certification_note"]:
                st.write(f"**Certification mentioned:** {job['certification_note']}")

            with st.expander("Job description"):
                st.write(job["description"])

        with col_action:
            if job["apply_link"]:
                st.link_button("🔗 Apply", job["apply_link"], use_container_width=True)

            is_applied = bool(job["applied"])
            new_status = st.checkbox(
                "Applied" if not is_applied else f"✅ Applied ({job['applied_date'][:10]})",
                value=is_applied,
                key=f"applied_{job['id']}",
            )
            if new_status != is_applied:
                mark_applied(job["id"], applied=new_status)
                st.rerun()
