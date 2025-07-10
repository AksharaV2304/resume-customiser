import streamlit as st
import os
import base64

# ---------------------- Utility Functions ----------------------

def read_file(file):
    return file.read().decode("utf-8")

def extract_candidate_name(text):
    lines = text.splitlines()
    for line in lines:
        if line.strip():
            return line.strip().split()[0]
    return "Candidate"

def fill_template(template_text, jd_text, resume_text):
    candidate_name = extract_candidate_name(resume_text)
    summary = f"Experienced professional with skills aligned to the JD.\n\nJD Snippet:\n{jd_text[:500]}"
    qualifications = "Bachelor's/Master’s Degree in relevant field."
    key_experience = resume_text[:1000]
    technical_skills = "Python, SQL, Machine Learning, etc."

    return template_text.replace("[CANDIDATE_NAME]", candidate_name)\
                        .replace("[ROLE]", "Applied Role")\
                        .replace("[SUMMARY]", summary)\
                        .replace("[QUALIFICATIONS]", qualifications)\
                        .replace("[EXPERIENCE_PLACEHOLDER]", key_experience)\
                        .replace("[TECHNICAL_SKILLS]", technical_skills)

def get_download_link(text, filename):
    b64 = base64.b64encode(text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">📥 Download Customised Resume</a>'

# ---------------------- Main App ----------------------

st.title("📄 Resume Customiser")

st.markdown("Upload a Job Description and a Raw Resume. The app will customize the resume to fit the JD based on EY’s format.")

jd_file = st.file_uploader("Upload Job Description (JD)", type=["txt", "docx"])
resume_file = st.file_uploader("Upload Raw Resume", type=["txt", "docx"])

# Update the path based on your repo
ey_template_path = os.path.join("EY_sample_resume_template.txt")

if not os.path.exists(ey_template_path):
    st.error(f"❌ Template file not found at path: {ey_template_path}")
else:
    if jd_file and resume_file:
        jd_text = read_file(jd_file)
        resume_text = read_file(resume_file)

        template_text = open(ey_template_path, "r", encoding="utf-8").read()
        customised_resume = fill_template(template_text, jd_text, resume_text)

        st.subheader("✅ Customised Resume Preview")
        st.text_area("Preview", customised_resume, height=300)

        download_link = get_download_link(customised_resume, "customised_resume.txt")
        st.markdown(download_link, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Please upload both a JD and a Resume file to begin.")
