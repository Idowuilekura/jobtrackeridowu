import streamlit as st
import duckdb
import hashlib
import os
from datetime import datetime
from uuid import uuid4
import zipfile

# ---------- CONFIG ----------
DB_FILE = "applications.duckdb"
RESUME_DIR = "resumes/"
if not os.path.exists(RESUME_DIR):
    os.makedirs(RESUME_DIR)

# ---------- DB INIT ----------
con = duckdb.connect(DB_FILE)
con.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY,
    company TEXT,
    job_title TEXT,
    job_description TEXT,
    upload_date TIMESTAMP,
    resume_hash TEXT,
    resume_path TEXT
)
""")

# ---------- HELPERS ----------
def hash_file(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def save_resume(file):
    file_bytes = file.read()
    h = hash_file(file_bytes)
    resume_file = os.path.join(RESUME_DIR, f"{h}.zip")
    if not os.path.exists(resume_file):
        with zipfile.ZipFile(resume_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(file.name, file_bytes)
    return h, resume_file

def add_application(company, job_title, jd, resume_hash, resume_path):
    con.execute("""
    INSERT INTO applications (id, company, job_title, job_description, upload_date, resume_hash, resume_path)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid4()), company, job_title, jd, datetime.now(), resume_hash, resume_path))

# ---------- SESSION STATE ----------
if 'page' not in st.session_state:
    st.session_state.page = "welcome"

# ---------- MAIN ----------
def main():
    st.set_page_config(page_title="Job Tracker", layout="wide", page_icon="📌")
    
    st.markdown("""
        <style>
        html, body, .stApp {
            background-color: #0f172a;
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }

        .block-container {
            padding: 2rem 3rem;
        }

        .card {
            background-color: #ffffff;
            color: #1e293b;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.15);
            margin-bottom: 2rem;
        }

        .button-style button {
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .button-style button:hover {
            background: linear-gradient(135deg, #2563eb, #1e3a8a);
            transform: translateY(-2px);
        }

        .stTextInput>div>div>input, .stTextArea>div>textarea {
            border-radius: 10px;
            border: 2px solid #cbd5e1;
            padding: 0.75rem;
        }

        .stDownloadButton>button {
            background: #334155;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 10px;
        }

        .stDownloadButton>button:hover {
            background: #475569;
        }

        h1, h2, h3 {
            color: #ffffff;
        }

        .header {
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.page == "welcome":
        st.markdown("<div class='header'><h1>📌 Job Application Tracker</h1></div>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Welcome!")
        st.write("Choose what you'd like to do:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Submit Application", key="submit", use_container_width=True):
                st.session_state.page = "submit"
                st.rerun()
        with col2:
            if st.button("🔍 Search Applications", key="search", use_container_width=True):
                st.session_state.page = "search"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "submit":
        if st.button("🏠 Back to Home", key="back1"):
            st.session_state.page = "welcome"
            st.rerun()
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🚀 Submit New Job Application")
        with st.form("job_form", clear_on_submit=True):
            company = st.text_input("Company Name")
            job_title = st.text_input("Job Title")
            jd = st.text_area("Job Description", height=200)
            cv = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
            submitted = st.form_submit_button("Submit Application", help="Save your job application")

            if submitted:
                if all([company, job_title, jd, cv]):
                    resume_hash, resume_path = save_resume(cv)
                    add_application(company, job_title, jd, resume_hash, resume_path)
                    st.success("✅ Application submitted successfully!")
                else:
                    st.error("⚠️ Please complete all fields and upload a resume.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.page == "search":
        if st.button("🏠 Back to Home", key="back2"):
            st.session_state.page = "welcome"
            st.rerun()

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔍 Search & Manage Applications")

        col1, col2 = st.columns(2)
        with col1:
            company_filter = st.text_input("Filter by Company Name")
        with col2:
            role_filter = st.text_input("Filter by Job Title")

        query = "SELECT * FROM applications WHERE 1=1"
        params = []

        if company_filter:
            query += " AND company ILIKE ?"
            params.append(f"%{company_filter}%")
        if role_filter:
            query += " AND job_title ILIKE ?"
            params.append(f"%{role_filter}%")

        query += " ORDER BY upload_date DESC"
        results = con.execute(query, params).fetchall()

        st.markdown("</div>", unsafe_allow_html=True)

        if results:
            for row in results:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"#### {row[2]} at {row[1]}")
                st.caption(f"📅 Submitted on {row[4].strftime('%B %d, %Y at %H:%M')}")
                with st.expander("📝 View Job Description"):
                    st.markdown(row[3])

                if os.path.exists(row[6]):
                    with open(row[6], "rb") as f:
                        st.download_button(
                            label="⬇️ Download Resume",
                            data=f.read(),
                            file_name=f"{row[2]}_{row[1]}.zip",
                            key=f"download_{row[0]}"
                        )
                else:
                    st.error("📁 Resume file not found.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No applications found with the provided filters.")

if __name__ == "__main__":
    main()

