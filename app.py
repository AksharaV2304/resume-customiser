import streamlit as st
import docx
import fitz  # PyMuPDF
import tempfile
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_text(file):
    if file.name.endswith('.pdf'):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return text
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith('.txt'):
        return file.read().decode("utf-8")
    else:
        return ""

def customize_resume(resume_text, jd_text):
    resume_doc = nlp(resume_text)
    jd_doc = nlp(jd_text)
    jd_keywords = set(token.lemma_.lower() for token in jd_doc if not token.is_stop and token.is_alpha)
    
    matched_sentences = [
        sent.text for sent in resume_doc.sents
        if any(token.lemma_.lower() in jd_keywords for token in sent if token.is_alpha)
    ]
    
    return "\n".join(matched_sentences)

# Streamlit UI
st.set_page_config(page_title="Resume Customiser", layout="centered")
st.title("📄 Resume Customiser using JD")
st.markdown("Upload your **resume** and **job description (JD)**. The app will output a **customized resume** as a `.txt` file aligned to the JD.")

resume_file = st.file_uploader("Upload Resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
jd_file = st.file_uploader("Upload Job Description (JD) (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

if resume_file and jd_file:
    resume_text = extract_text(resume_file)
    jd_text = extract_text(jd_file)

    if st.button("Generate Customised Resume"):
        customised_resume = customize_resume(resume_text, jd_text)

        # Save to temporary text file
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.txt') as tmp:
            tmp.write(customised_resume)
            tmp_path = tmp.name

        # Let user download
        with open(tmp_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Customised Resume",
                data=f,
                file_name="customised_resume.txt",
                mime="text/plain"
            )
