import streamlit as st
from groq import Groq
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import re

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)


st.set_page_config(page_title="AI DDR Generator", page_icon="", layout="wide")
st.title(" AI DDR Report Generator")
st.markdown("Upload Inspection + Thermal Reports → Generate Professional DDR")

# ==============================
# PDF TEXT EXTRACTOR
# ==============================
def extract_text(file):
    text = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        path = tmp.name

    reader = PdfReader(path)
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"

    return text.strip()


# ==============================
# RULE-BASED SEVERITY SCORING
# ==============================
def calculate_severity(text):
    text = text.lower()

    high_keywords = ["severe", "critical", "water leakage", "structural damage", "high moisture"]
    medium_keywords = ["moderate", "damp", "crack", "heat loss"]
    
    if any(k in text for k in high_keywords):
        return "HIGH 🔴"
    elif any(k in text for k in medium_keywords):
        return "MEDIUM 🟠"
    else:
        return "LOW 🟢"


# ==============================
# MISSING INFO DETECTOR
# ==============================
def detect_missing(text):
    if len(text.strip()) < 50:
        return "Not Available"
    return "Information Present"


# ==============================
# GROQ DDR GENERATOR
# ==============================
def generate_ddr(inspection, thermal):

    prompt = f"""
Generate a professional Detailed Diagnostic Report (DDR).

STRICT:
- No hallucination
- Missing → write Not Available
- Conflict → mention clearly
- Remove duplicates
- Simple client language

FORMAT:

1. Property Issue Summary
2. Area-wise Observations
3. Probable Root Cause
4. Severity Assessment (with reasoning)
5. Recommended Actions
6. Additional Notes
7. Missing or Unclear Information

Inspection Report:
{inspection}

Thermal Report:
{thermal}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# ==============================
# CREATE PDF REPORT
# ==============================
def create_pdf(report_text):
    pdf_path = "DDR_Report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    y = height - 40
    for line in report_text.split("\n"):
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, line[:90])
        y -= 15

    c.save()
    return pdf_path


# ==============================
# UI FILE UPLOAD
# ==============================
col1, col2 = st.columns(2)

with col1:
    inspection_file = st.file_uploader("Upload Inspection Report", type=["pdf"])

with col2:
    thermal_file = st.file_uploader("Upload Thermal Report", type=["pdf"])


# ==============================
# GENERATE BUTTON
# ==============================
if st.button("🚀 Generate Advanced DDR"):

    if not inspection_file or not thermal_file:
        st.error("Upload BOTH reports")
    else:
        with st.spinner("Reading files..."):
            inspection_text = extract_text(inspection_file)
            thermal_text = extract_text(thermal_file)

        severity_level = calculate_severity(inspection_text + thermal_text)
        missing_info = detect_missing(inspection_text + thermal_text)

        with st.spinner("Generating DDR..."):
            ddr = generate_ddr(inspection_text, thermal_text)

        st.success("DDR Generated Successfully")

        st.subheader("📊 Severity Score")
        st.write(severity_level)

        st.subheader("❗ Missing Info Check")
        st.write(missing_info)

        st.subheader("📑 DDR Report")
        st.text_area("DDR", ddr, height=500)

        # Save TXT
        with open("DDR_Report.txt", "w", encoding="utf-8") as f:
            f.write(ddr)

        # Create PDF
        pdf_path = create_pdf(ddr)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button("Download TXT", ddr, file_name="DDR_Report.txt")

        with col2:
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="DDR_Report.pdf")
