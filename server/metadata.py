import os
import json
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from server.schemas import DocumentMetadata

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def extract_metadata(content: str) -> DocumentMetadata:
    """
    Extract structured metadata from document content using Gemini API.
    Truncates content to the first 8000 characters to save tokens.
    
    Returns:
        DocumentMetadata with title, summary, topics, document_type, language
        
    Raises:
        Exception: If API call fails or parsing fails
    """
    if not content or not content.strip():
        return DocumentMetadata(
            title="Unknown Title",
            summary="No content provided.",
            topics=[],
            document_type="unknown",
            language="en",
            project=None,
        )

    truncated_content = content[:8000]
    schema = DocumentMetadata.model_json_schema()

    prompt = (
        "You are an expert document analyzer. Extract structured metadata from the document below.\n"
        "Return a JSON object matching this schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Rules:\n"
        "- title: document title, or first sentence if unclear\n"
        "- summary: brief 1-2 sentence summary\n"
        "- topics: list of key topics (3-5 items)\n"
        "- document_type: one of 'article', 'report', 'notes', 'technical documentation'\n"
        "- language: 2-letter ISO code (e.g. 'en')\n"
        "- project: project or product name this document belongs to, or null if unclear\n\n"
        f"Document:\n{truncated_content}"
    )

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )
        
        raw_json = response.text or ""
        if not raw_json:
            raise ValueError("Empty response from API")
        return DocumentMetadata.model_validate_json(raw_json)
        
    except Exception as e:
        # Fallback with sensible defaults
        return DocumentMetadata(
            title="Unknown Title",
            summary=f"Content preview: {truncated_content[:200]}...",
            topics=[],
            document_type="unknown",
            language="en",
            project=None,
        )
