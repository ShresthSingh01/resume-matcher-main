import io
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
from app.utils import clean_text

# Optional OCR
try:
    import easyocr
    OCR_AVAILABLE = True
    ocr_reader = None
except ImportError:
    OCR_AVAILABLE = False
    ocr_reader = None

def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None and OCR_AVAILABLE:
        print("⏳ Loading OCR Model...")
        ocr_reader = easyocr.Reader(['en'])
        print("✅ OCR Model Loaded")
    return ocr_reader

def parse_resume(file_bytes: bytes, filename: str) -> str:
    """
    Parse resume text from bytes.
    1. If .txt, decode utf-8.
    2. Try PyPDF2
    3. If empty/scanned, try PyMuPDF + EasyOCR
    """
    if filename.lower().endswith(".txt"):
        try:
            return clean_text(file_bytes.decode("utf-8", errors="ignore"))
        except:
            pass

    text = ""
    
    # 2. Try PyPDF2
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {e}")
    
    clean = clean_text(text)
    
    # If text is sufficient, return it
    if len(clean) > 50:
        return clean

    # 2. OCR Fallback
    if OCR_AVAILABLE:
        print("⚠️ Text too short/empty. Attempting OCR...")
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            ocr_text = ""
            reader = get_ocr_reader()
            
            for page in doc:
                # Render page to image
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                
                # Run OCR
                results = reader.readtext(img_bytes, detail=0)
                ocr_text += " ".join(results) + "\n"
                
            clean_ocr = clean_text(ocr_text)
            if clean_ocr:
                return clean_ocr
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            
    return clean # Return whatever we have (maybe empty)
