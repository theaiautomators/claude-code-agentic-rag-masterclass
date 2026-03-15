import os
from pathlib import Path

def parse_document(file_path: str) -> str:
    """
    Parse a document file and return its content as plain text markdown.
    Routes processing based on file extension:
    - .txt: reads directly.
    - .pdf, .docx, .html, .md: parsed using IBM Docling.
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    # Text bypasses heavyweight parsing
    if extension == ".txt":
        return path.read_text(encoding="utf-8")
        
    supported_docling_extensions = {".pdf", ".docx", ".html", ".md"}
    if extension in supported_docling_extensions:
        # Import DocumentConverter lazily so the app doesn't take 1.5s to boot if it's never used
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            raise ImportError("Docling is not installed. Please pip install docling.")
            
        try:
            converter = DocumentConverter()
            result = converter.convert(file_path)
            return result.document.export_to_markdown()
        except Exception as e:
            raise RuntimeError(f"Docling failed to parse {file_path}: {str(e)}")
            
    raise ValueError(f"Unsupported file format: {extension}")
