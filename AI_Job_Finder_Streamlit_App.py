import streamlit as st
import pandas as pd
import requests
import pdfplumber
from io import BytesIO
from datetime import datetime
import os

st.set_page_config(page_title="AI Job Finder", layout="wide")

st.title("🤖 AI Job Finder - India Remote Jobs")

# -----------------------------
# CONFIG
# -----------------------------

TARGET_ROLES = [
    "business analyst",
    "data analyst",
    "reporting analyst",
    "operations analyst",
    "workforce analyst",
    "program coordinator",
    "project coordinator",
    "pmo analyst"
]

SKILLS = [
    "sql",
    "power bi",
    "tableau",
    "excel",
    "stakeholder management",
    "dashboard",
    "kpi",
    "analytics",
    "reporting",
    "process improvement",
    "requirements gathering",
    "project management",
    "data analysis",
    "power query",
    "vba",
    "python"
]

SALARY_MAP = {
    "business analyst": "₹10-16 LPA",
    "data analyst": "₹9-18 LPA",
    "operations analyst": "₹10-15 LPA",
    "reporting analyst": "₹10-16 LPA",
    "workforce analyst": "₹12-18 LPA",
    "pmo analyst": "₹10-18 LPA",
    "project coordinator": "₹8-14 LPA"
}

TRACKER_FILE = "applied_jobs.csv"

# -----------------------------
# RESUME PARSER
# -----------------------------

def extract_pdf_text(file):
    text = ""

    with pdfplumber.open(BytesIO(file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text.lower()

    return text

def extract_skills(text):
    found = []

    for skill in SKILLS:
        if skill.lower() in text:
            found.append(skill)

    return list(set(found))

# -----------------------------
# JOB FETCHERS
# -----------------------------

@st.cache_data(ttl=3600)
def fetch_remotive_jobs():

    jobs = []

    try:
        url = "https://remotive.com/api/remote-jobs"

        response = requests.get(url, timeout=20)

        data = response.json()

        for job in data["jobs"]:

            jobs.append({
                "title": job.get("title"),
                "company": job.get("company_name"),
                "description": job.get("description", ""),
                "apply_url": job.get("url"),
                "source": "Remotive"
            })

    except Exception:
        pass

    return jobs


@st.cache_data(ttl=3600)
def fetch_remoteok_jobs():

    jobs = []

    try:
        response = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        data = response.json()

        for job in data[1:]:

            jobs.append({
                "title": job.get("position"),
                "company": job.get("company"),
                "description": str(job),
                "apply_url": job.get("url"),
                "source": "RemoteOK"
            })

    except Exception:
        pass

    return jobs

# -----------------------------
# MATCHING
# -----------------------------

def get_role_match(title):

    title = str(title).lower()

    for role in TARGET_ROLES:

        if role in title:
            return 100

    return 30

def calculate_score(job, resume_skills):

    content = (
        str(job["title"]) +
        " " +
        str(job["description"])
    ).lower()

    matched_skills = []

    for skill in resume_skills:

        if skill.lower() in content:
            matched_skills.append(skill)

    skill_score = (
        len(matched_skills)
        / max(len(resume_skills), 1)
    ) * 40

    role_score = get_role_match(job["title"]) * 0.3

    score = min(
        round(skill_score + role_score),
        100
    )

    return score, matched_skills

# -----------------------------
# APPLICATION TRACKER
# -----------------------------

def load_tracker():

    if os.path.exists(TRACKER_FILE):
        return pd.read_csv(TRACKER_FILE)

    return pd.DataFrame(
        columns=[
            "Job Title",
            "Company",
            "Apply URL",
            "Applied Date",
            "Status"
        ]
    )

def save_tracker(df):
    df.to_csv(TRACKER_FILE, index=False)

# -----------------------------
# UI
# -----------------------------

uploaded_files = st.file_uploader(
    "Upload Your Resumes",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    master_text = ""

    for file in uploaded_files:
        master_text += extract_pdf_text(file)

    resume_skills = extract_skills(master_text)

    st.success("Resume Parsed Successfully")

    st.subheader("Detected Skills")

    st.write(resume_skills)

    jobs = []

    jobs.extend(fetch_remotive_jobs())
    jobs.extend(fetch_remoteok_jobs())

    results = []

    for job in jobs:

        score, matched = calculate_score(
            job,
            resume_skills
        )

        title = str(job["title"]).lower()

        if score < 50:
            continue

        if not any(
            role in title
            for role in TARGET_ROLES
        ):
            continue

        salary = "₹10-18 LPA"

        for role, sal in SALARY_MAP.items():

            if role in title:
                salary = sal

        results.append({
            "Match %": score,
            "Job Title": job["title"],
            "Company": job["company"],
            "Salary": salary,
            "Source": job["source"],
            "Apply URL": job["apply_url"],
            "Matched Skills": ", ".join(matched)
        })

    results_df = pd.DataFrame(results)

    if len(results_df):

        results_df = results_df.sort_values(
            by="Match %",
            ascending=False
        )

        st.subheader("🎯 Recommended Jobs")

        tracker = load_tracker()

        for idx, row in results_df.iterrows():

            with st.expander(
                f"{row['Job Title']} | {row['Match %']}%"
            ):

                st.write(
                    f"**Company:** {row['Company']}"
                )

                st.write(
                    f"**Salary Estimate:** {row['Salary']}"
                )

                st.write(
                    f"**Matched Skills:** {row['Matched Skills']}"
                )

                st.link_button(
                    "Apply Now",
                    row["Apply URL"]
                )

                missing = []

                for skill in SKILLS:

                    if skill not in row[
                        "Matched Skills"
                    ].lower():

                        missing.append(skill)

                st.write(
                    "Resume Improvement Suggestions"
                )

                st.write(
                    ", ".join(missing[:5])
                )

                if st.button(
                    f"Mark Applied {idx}"
                ):

                    tracker.loc[
                        len(tracker)
                    ] = [
                        row["Job Title"],
                        row["Company"],
                        row["Apply URL"],
                        datetime.now().strftime(
                            "%Y-%m-%d"
                        ),
                        "Applied"
                    ]

                    save_tracker(tracker)

                    st.success(
                        "Saved to tracker"
                    )

        st.subheader("📋 Application Tracker")

        st.dataframe(load_tracker())

    else:

        st.warning(
            "No matching jobs found."
        )
