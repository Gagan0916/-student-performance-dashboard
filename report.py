"""Builds downloadable report exports (CSV and PDF) from the current session's analysis."""

import io

import pandas as pd
from fpdf import FPDF

from grading import score_to_grade

# The PDF core fonts only support latin-1; AI-generated text often contains
# typographic Unicode punctuation that would otherwise crash the PDF build.
_PDF_CHAR_REPLACEMENTS = {
    "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "•": "-",
}


def _pdf_safe(text):
    for char, replacement in _PDF_CHAR_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def build_csv_report(student_name, subject_rows, cgpa, summary):
    df = pd.DataFrame(subject_rows)
    df["grade"] = df["marks"].apply(lambda m: score_to_grade(m)[0])
    buffer = io.StringIO()
    buffer.write(f"Student,{student_name}\n")
    buffer.write(f"CGPA,{cgpa}\n\n")
    df.to_csv(buffer, index=False)
    buffer.write(f"\nSummary,{summary}\n")
    return buffer.getvalue().encode("utf-8")


def build_pdf_report(student_name, subject_rows, cgpa, summary, tip):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Student Performance Report", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _pdf_safe(f"Student: {student_name}"), ln=True)
    pdf.cell(0, 8, f"CGPA: {cgpa}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Subjects", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 8, "Subject", border=1)
    pdf.cell(35, 8, "Marks", border=1)
    pdf.cell(35, 8, "Attendance %", border=1)
    pdf.cell(30, 8, "Grade", border=1, ln=True)

    pdf.set_font("Helvetica", "", 10)
    for row in subject_rows:
        grade, _ = score_to_grade(row["marks"])
        pdf.cell(50, 8, _pdf_safe(str(row["subject"])), border=1)
        pdf.cell(35, 8, str(row["marks"]), border=1)
        pdf.cell(35, 8, str(row["attendance_pct"]), border=1)
        pdf.cell(30, 8, grade, border=1, ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "AI Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _pdf_safe(summary))

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Focus Tip", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _pdf_safe(tip))

    return bytes(pdf.output(dest="S"))
