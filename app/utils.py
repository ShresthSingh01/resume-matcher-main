import re

def clean_text(text: str) -> str:
    """
    Normalize whitespace and clean text.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str, size: int = 300, overlap: int = 50) -> list:
    """
    Chunk text into smaller segments.
    """
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
