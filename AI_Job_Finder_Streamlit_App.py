
import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="AI Job Finder", layout="wide")

st.title("AI-Powered Job Finder")
st.write("India + Remote focused job search for Business Analyst, Data Analyst, PMO, and Operations roles")

uploaded_file = st.file_uploader("Upload Resume", type=["txt"])

DEFAULT_SKILLS = [
    "sql","power bi","excel","tableau","business analyst",
    "data analyst","project coordinator","stakeholder management",
    "dashboard","kpi","reporting","process improvement"
]

def extract_keywords(text):
    text = text.lower()
    return [s for s in DEFAULT_SKILLS if s in text]

@st.cache_data(ttl=3600)
def fetch_jobs():
    jobs = []
    try:
        data = requests.get("https://remotive.com/api/remote-jobs", timeout=20).json()
        jobs.extend(data.get("jobs", []))
    except:
        pass
    return jobs

def score_job(job, skills):
    content = (
        str(job.get("title","")) + " " +
        str(job.get("description",""))
    ).lower()
    return sum(1 for s in skills if s in content)

if uploaded_file:
    resume_text = uploaded_file.read().decode("utf-8", errors="ignore")
    skills = extract_keywords(resume_text)

    st.subheader("Detected Skills")
    st.write(skills)

    jobs = fetch_jobs()

    results = []
    for job in jobs:
        score = score_job(job, skills)
        if score > 0:
            results.append({
                "Match Score": round((score/max(len(skills),1))*100,1),
                "Job Title": job.get("title"),
                "Company": job.get("company_name"),
                "Category": job.get("category"),
                "Apply Link": job.get("url")
            })

    df = pd.DataFrame(results).sort_values("Match Score", ascending=False)

    st.subheader("Recommended Jobs")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download Results CSV", csv, "job_matches.csv")
