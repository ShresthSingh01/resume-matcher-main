import fitz  # PyMuPDF
import sys

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

if __name__ == "__main__":
    pdf_path = r"d:\ai-resume\resume-matcher-main\Virex Resume Parser and Role matcher.pdf"
    content = extract_text_from_pdf(pdf_path)
    with open("pdf_content.txt", "w", encoding="utf-8") as f:
        f.write(content)
