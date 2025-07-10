import os
import fitz
import docx
import re
import json
import time
import requests
import tempfile
import streamlit as st
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# LM Studio endpoint
def call_lmstudio(prompt, model="zephyr-7b-beta.Q4_K_M.gguf", retries=3):
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "stream": False
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            if attempt == retries - 1:
                st.error(f"LLM call failed: {e}")
                return ""
            time.sleep(2)

def read_resume_text(uploaded_file):
    suffix = uploaded_file.name.lower()
    if suffix.endswith(".pdf"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif suffix.endswith(".docx"):
        uploaded_file.seek(0)
        doc = docx.Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    else:
        return uploaded_file.read().decode("utf-8")

def customise_resume(prompt_text, resume_text, candidate_name, ey_template):
    jd_prompt = f"""Create a structured job description based only on the following three sections:
1. Responsibilities
2. Requirements
3. Preferred Skills

Prompt:
{prompt_text}
"""
    generated_jd = call_lmstudio(jd_prompt)
    if not generated_jd:
        return "", "", "JD generation failed."

    custom_prompt = f"""
You are a resume writer. Given the candidate's resume and the job description, rewrite the following sections to make the resume aligned with the JD. DO NOT INVENT DETAILS. Use only the content in the resume.

Resume:
{resume_text}

Job Description:
{generated_jd}

Provide the output in this format (with labels):
SUMMARY:
...

QUALIFICATIONS:
...

EXPERIENCE:
...

TECHNICAL_SKILLS:
...
"""
    result = call_lmstudio(custom_prompt)
    if not result:
        return "", "", "Customization failed."

    summary = re.search(r"SUMMARY:(.*?)QUALIFICATIONS:", result, re.DOTALL | re.IGNORECASE)
    qualifications = re.search(r"QUALIFICATIONS:(.*?)EXPERIENCE:", result, re.DOTALL | re.IGNORECASE)
    experience = re.search(r"EXPERIENCE:(.*?)TECHNICAL_SKILLS:", result, re.DOTALL | re.IGNORECASE)
    tech_skills = re.search(r"TECHNICAL_SKILLS:(.*)", result, re.DOTALL | re.IGNORECASE)

    # Fill template
    final_resume = ey_template
    final_resume = final_resume.replace("[CANDIDATE_NAME]", candidate_name)
    final_resume = final_resume.replace("[ROLE]", prompt_text)
    final_resume = final_resume.replace("[SUMMARY]", summary.group(1).strip() if summary else "")
    final_resume = final_resume.replace("[QUALIFICATIONS]", qualifications.group(1).strip() if qualifications else "")
    final_resume = final_resume.replace("[EXPERIENCE_PLACEHOLDER]", experience.group(1).strip() if experience else "")
    final_resume = final_resume.replace("[TECHNICAL_SKILLS]", tech_skills.group(1).strip() if tech_skills else "")

    return final_resume, generated_jd, "✅ Success"

# --- Streamlit UI ---
st.title("📄 EY Resume Customization App")

prompt_text = st.text_area("Enter JD Prompt (ex: JD for IRB model validation)", height=100)
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
template_file = st.file_uploader("Upload EY Template (.txt)", type=["txt"])

if st.button("Customize Resume"):
    if not prompt_text or not resume_file or not template_file:
        st.warning("Please upload resume, template, and enter a prompt.")
    else:
        candidate_name = os.path.splitext(resume_file.name)[0]
        resume_text = read_resume_text(resume_file)
        ey_template = template_file.read().decode("utf-8")

        with st.spinner("Processing..."):
            final_resume, jd_text, status = customise_resume(prompt_text, resume_text, candidate_name, ey_template)

        if status == "✅ Success":
            st.success("Resume customized successfully!")
            st.text_area("Generated JD", jd_text, height=300)
            st.text_area("Customized Resume Output", final_resume, height=400)

            tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tmp_path.write(final_resume.encode("utf-8"))
            tmp_path.close()

            with open(tmp_path.name, "rb") as f:
                st.download_button("Download Customized Resume", f, file_name=f"{candidate_name}_customised.txt", mime="text/plain")
        else:
            st.error(status)
