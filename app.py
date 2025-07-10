import streamlit as st
import fitz  # PyMuPDF
import docx
import os
import tempfile
import spacy
import subprocess
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---- LOAD SPACY MODEL ----
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# ---- TEXT EXTRACTION ----
def extract_text(file):
    ext = os.path.splitext(file.name)[-1].lower()
    if ext == ".pdf":
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])
    elif ext == ".docx":
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif ext == ".txt":
        return file.read().decode("utf-8")
    else:
        return ""

# ---- CUSTOMIZATION LOGIC ----
def customize_resume(resume_text, jd_text):
    resume_doc = nlp(resume_text)
    jd_doc = nlp(jd_text)

    resume_sents = [sent.text for sent in resume_doc.sents]
    jd_keywords = [token.lemma_.lower() for token in jd_doc if token.pos_ in ["NOUN", "VERB", "ADJ"] and not token.is_stop]

    selected = [sent for sent in resume_sents if any(keyword in sent.lower() for keyword in jd_keywords)]

    if not selected:
        selected = resume_sents[:10]

    return "\n".join(selected)

# ---- STREAMLIT APP ----
st.title("📄 Resume Customiser using JD")
st.markdown("Upload your **resume** and **job description (JD)**. The app will output a **customized resume** as a `.txt` file aligned to the JD.")

resume_file = st.file_uploader("Upload Resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
jd_file = st.file_uploader("Upload Job Description (JD) (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

if resume_file and jd_file:
    resume_text = extract_text(resume_file)
    jd_text = extract_text(jd_file)

    if st.button("Generate Customised Resume"):
        customised_resume = customize_resume(resume_text, jd_text)

        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmp:
            tmp.write(customised_resume)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Customised Resume",
                data=f,
                file_name="customised_resume.txt",
                mime="text/plain"
            )
