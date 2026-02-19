from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks

from dependencies import get_current_user
from models.schemas import DocumentResponse, DocumentListResponse
from services.document_service import DocumentService
from services.storage_service import StorageService
from services.ingestion_service import IngestionService

router = APIRouter()

ALLOWED_TYPES = {"text/plain", "text/markdown", "text/csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/", response_model=DocumentListResponse)
async def list_documents(user: dict = Depends(get_current_user)):
    service = DocumentService(user["user_id"])
    docs = service.list_documents()
    return {"documents": docs}


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    # Validate file type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    user_id = user["user_id"]

    # Upload to storage
    storage = StorageService(user_id)
    storage_path = storage.upload_file(
        filename=file.filename,
        content=content,
        content_type=content_type,
    )

    # Create document record
    doc_service = DocumentService(user_id)
    doc = doc_service.create_document(
        filename=file.filename,
        file_type=content_type,
        file_size=len(content),
        storage_path=storage_path,
    )

    # Start ingestion in background
    ingestion = IngestionService(user_id)
    background_tasks.add_task(ingestion.process_document, doc["id"])

    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user: dict = Depends(get_current_user)):
    service = DocumentService(user["user_id"])
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str, user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    doc_service = DocumentService(user_id)
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete storage file (ignore errors — file may already be gone)
    try:
        storage = StorageService(user_id)
        storage.delete_file(doc["storage_path"])
    except Exception:
        pass

    # Delete document record (cascades to chunks)
    doc_service.delete_document(document_id)
    return {"status": "deleted"}
