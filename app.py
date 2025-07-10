import streamlit as st
import os
import fitz  # PyMuPDF
import docx
import spacy
from spacy.cli import download
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile

# ---------- Load spaCy model (handle download) ----------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ---------- Utility Functions ----------
def read_pdf_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def read_docx_text(docx_file):
    doc = docx.Document(docx_file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def read_txt_text(txt_file):
    return txt_file.read().decode("utf-8")

def extract_text(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        return read_pdf_text(uploaded_file)
    elif filename.endswith(".docx"):
        return read_docx_text(uploaded_file)
    elif filename.endswith(".txt"):
        return read_txt_text(uploaded_file)
    else:
        return ""

def customize_resume(resume_text, jd_text):
    # Extract keywords from JD using spaCy
    jd_doc = nlp(jd_text)
    jd_keywords = [token.lemma_ for token in jd_doc if token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB']]
    jd_keywords = list(set(jd_keywords))

    # Keep only sentences from resume that have keywords from JD
    sentences = resume_text.split("\n")
    filtered_sentences = [sent for sent in sentences if any(kw.lower() in sent.lower() for kw in jd_keywords)]
    
    # If nothing matched, fallback to full resume
    if not filtered_sentences:
        filtered_sentences = sentences
    
    return "\n".join(filtered_sentences)

# ---------- Streamlit UI ----------
st.title("📄 Resume Customiser using JD")

st.markdown("Upload your **resume** and **job description (JD)**. The app will output a **customized resume** as a `.txt` file aligned to the JD.")

resume_file = st.file_uploader("Upload Resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
jd_file = st.file_uploader("Upload Job Description (JD) (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

if resume_file and jd_file:
    resume_text = extract_text(resume_file)
    jd_text = extract_text(jd_file)

    if st.button("Generate Customised Resume"):
        customised_resume = customize_resume(resume_text, jd_text)
        
        # Save to a temporary text file
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmp:
            tmp.write(customised_resume)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            st.download_button(
                label="📥 Download Customised Resume",
                data=f,
                file_name="customised_resume.txt",
                mime="text/plain"
            )
