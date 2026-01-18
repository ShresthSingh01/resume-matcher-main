from app.resume_parser import extract_email, parse_resume
from unittest.mock import patch, MagicMock
import io

def test_extract_email():
    text = "Contact me at test.user@example.com for more info."
    assert extract_email(text) == "test.user@example.com"
    
    text_no_email = "This text has no email address."
    assert extract_email(text_no_email) == ""

@patch("app.resume_parser.PdfReader")
def test_parse_resume_pypdf2(mock_pdf_reader):
    # Mocking PdfReader to return a page with text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is a resume sample content."
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Create dummy bytes
    dummy_pdf = _create_dummy_pdf_bytes()
    
    result = parse_resume(dummy_pdf, "resume.pdf")
    
    assert "This is a resume sample content." in result

def test_parse_resume_txt():
    content = "Simple text resume content".encode("utf-8")
    result = parse_resume(content, "resume.txt")
    assert "Simple text resume content" in result

def _create_dummy_pdf_bytes():
    return b"%PDF-1.4..."
