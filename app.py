# Simple Job Application Tracker using Streamlit + DuckDB

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

# ---------- WELCOME PAGE ----------
def welcome_page():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.title("📌 Job Application Tracker")
    
    st.markdown("""
    <div class="welcome-card">
        <h2 style="color: #4a5568; margin-bottom: 1rem;">Welcome to your personal job application management system!</h2>
        <p style="color: #718096; font-size: 1.1rem; line-height: 1.6;">
            Streamline your job search process with our elegant tracking system. 
            Upload applications, manage resumes, and stay organized on your career journey.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
            <h3 style="color: #2d3748; margin-bottom: 1rem;">Submit Application</h3>
            <p style="color: #718096; margin-bottom: 2rem;">Upload new job applications with company details, job descriptions, and your tailored resume.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Submit Application", use_container_width=True, key="submit_btn"):
            st.session_state.page = "submit"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h3 style="color: #2d3748; margin-bottom: 1rem;">Search & Download</h3>
            <p style="color: #718096; margin-bottom: 2rem;">Browse through your applications, filter by company or role, and download your resumes.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Search & Download", use_container_width=True, key="search_btn"):
            st.session_state.page = "search"
            st.rerun()
    
    # Show stats
    total_apps = con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    if total_apps > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin: 0; font-size: 2.5rem;">{total_apps}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Total Applications</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            companies = con.execute("SELECT COUNT(DISTINCT company) FROM applications").fetchone()[0]
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin: 0; font-size: 2.5rem;">{companies}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Companies</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            recent_count = con.execute("SELECT COUNT(*) FROM applications WHERE  upload_date >= CURRENT_DATE - INTERVAL 7 DAY;").fetchone()[0]
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin: 0; font-size: 2.5rem;">{recent_count}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">This Week</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent applications
        recent = con.execute("""
            SELECT company, job_title, upload_date 
            FROM applications 
            ORDER BY upload_date DESC 
            LIMIT 5
        """).fetchall()
        
        if recent:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                <h3 style="color: #2d3748; margin-bottom: 1.5rem; text-align: center;">📋 Recent Applications</h3>
            """, unsafe_allow_html=True)
            
            for i, app in enumerate(recent):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; 
                           background: rgba(102, 126, 234, 0.05); border-radius: 10px; margin: 0.5rem 0;
                           border-left: 4px solid #667eea;">
                    <div>
                        <strong style="color: #2d3748; font-size: 1.1rem;">{app[1]}</strong>
                        <div style="color: #718096; margin-top: 0.2rem;">{app[0]}</div>
                    </div>
                    <div style="color: #667eea; font-weight: 500;">{app[2].strftime('%m/%d')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- MAIN APP ----------
def main():
    st.set_page_config(page_title="Job Tracker", layout="wide", page_icon="📌")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            font-family: 'Inter', sans-serif;
        }
        
        .stApp {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        }
        
        /* Custom container */
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem auto;
            max-width: 1200px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Button styles */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.8rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Form inputs */
        .stTextInput>div>div>input, .stTextArea>div>textarea {
            border: 2px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 1rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.9);
        }
        
        .stTextInput>div>div>input:focus, .stTextArea>div>textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* File uploader */
        .stFileUploader>div {
            border: 2px dashed rgba(102, 126, 234, 0.3);
            border-radius: 12px;
            padding: 2rem;
            background: rgba(102, 126, 234, 0.05);
            transition: all 0.3s ease;
        }
        
        .stFileUploader>div:hover {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
        
        /* Headers */
        h1 {
            color: #2d3748;
            font-weight: 700;
            text-align: center;
            margin-bottom: 2rem;
            font-size: 3rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        h2, h3 {
            color: #4a5568;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }
        
        /* Cards */
        .application-card {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
        }
        
        .application-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        }
        
        /* Stats */
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        /* Success/Error messages */
        .stSuccess {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            border-radius: 12px;
            border: none;
        }
        
        .stError {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            border-radius: 12px;
            border: none;
        }
        
        /* Remove default margins */
        .block-container {
            padding-top: 1rem;
        }
        
        /* Welcome page styling */
        .welcome-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin: 2rem 0;
        }
        
        .feature-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }
        </style>
    """, unsafe_allow_html=True)

    # Navigation
    if st.session_state.page != "welcome":
        st.markdown("""
        <div style="position: fixed; top: 20px; left: 20px; z-index: 999;">
        """, unsafe_allow_html=True)
        if st.button("🏠 Back to Home", key="home_btn"):
            st.session_state.page = "welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Page routing
    if st.session_state.page == "welcome":
        welcome_page()
        return
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    page = st.session_state.page

    if page == "submit":
        st.title("📌 Job Application Tracker")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #4a5568; font-weight: 600;">🚀 Submit New Application</h2>
            <p style="color: #718096; font-size: 1.1rem;">Add a new job application to your tracker</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("job_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                company = st.text_input("🏢 Company Name", placeholder="Enter company name...")
                job_title = st.text_input("💼 Job Title", placeholder="Enter job title...")
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                cv = st.file_uploader("📄 Upload your CV", type=['pdf'], help="Upload your tailored resume for this application")
            
            jd = st.text_area("📝 Job Description", placeholder="Paste the job description here...", height=200)
            
            submitted = st.form_submit_button("✨ Submit Application", use_container_width=True)

            if submitted:
                if all([company, job_title, jd, cv]):
                    with st.spinner("Saving your application..."):
                        resume_hash, resume_path = save_resume(cv)
                        add_application(company, job_title, jd, resume_hash, resume_path)
                    st.success("✅ Application saved successfully! 🎉")
                    st.balloons()
                else:
                    st.error("⚠️ Please fill in all fields and upload your CV")

    elif page == "search":
        st.title("📌 Job Application Tracker")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #4a5568; font-weight: 600;">🔍 Search Applications</h2>
            <p style="color: #718096; font-size: 1.1rem;">Find and download your job applications</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            company_filter = st.text_input("🏢 Filter by Company", placeholder="Search companies...")
        with col2:
            role_filter = st.text_input("💼 Filter by Job Title", placeholder="Search job titles...")

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

        if results:
            st.markdown(f"""
            <div class="stat-card" style="margin: 2rem 0; display: inline-block; padding: 1rem 2rem;">
                <span style="font-size: 1.2rem; font-weight: 600;">📊 Found {len(results)} application(s)</span>
            </div>
            """, unsafe_allow_html=True)
            
            for row in results:
                st.markdown(f"""
                <div class="application-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div>
                            <h3 style="color: #2d3748; margin: 0; font-size: 1.4rem;">{row[2]} at {row[1]}</h3>
                            <p style="color: #667eea; margin: 0.5rem 0; font-weight: 500;">📅 {row[4].strftime('%B %d, %Y at %I:%M %p')}</p>
                        </div>
                    </div>
                    <div style="background: rgba(102, 126, 234, 0.05); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <strong style="color: #4a5568;">📝 Job Description:</strong>
                        <p style="color: #718096; margin-top: 0.5rem; line-height: 1.6;">{row[3][:200]}{'...' if len(row[3]) > 200 else ''}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if os.path.exists(row[6]):
                    with open(row[6], "rb") as f:
                        st.download_button(
                            "⬇️ Download Resume", 
                            f.read(), 
                            file_name=f"{row[2]}_{row[1]}.zip",
                            key=f"download_{row[0]}",
                            use_container_width=True
                        )
                else:
                    st.error("📁 Resume file not found")
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; background: white; border-radius: 16px; 
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
                <h3 style="color: #4a5568;">No applications found</h3>
                <p style="color: #718096;">Try adjusting your search criteria or submit your first application!</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
