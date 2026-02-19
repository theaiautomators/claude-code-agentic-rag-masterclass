from langsmith import traceable

from services.storage_service import StorageService
from services.document_service import DocumentService
from services.chunking_service import chunk_text
from services.embedding_service import generate_embeddings


class IngestionService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.storage = StorageService(user_id)
        self.documents = DocumentService(user_id)

    @traceable(name="process_document", run_type="chain")
    def process_document(self, document_id: str) -> None:
        """
        Full ingestion pipeline:
        1. Set status to processing
        2. Download file from storage
        3. Decode text
        4. Chunk text
        5. Generate embeddings
        6. Save chunks to DB
        7. Set status to completed
        """
        try:
            # 1. Set status to processing
            doc = self.documents.get_document(document_id)
            if not doc:
                return

            self.documents.update_document(document_id, {"status": "processing"})

            # 2. Download file from storage
            file_bytes = self.storage.download_file(doc["storage_path"])

            # 3. Decode text
            text = file_bytes.decode("utf-8")

            # 4. Chunk text
            chunks = chunk_text(text)
            if not chunks:
                self.documents.update_document(document_id, {
                    "status": "completed",
                    "chunk_count": 0,
                })
                return

            # 5. Generate embeddings
            embeddings = generate_embeddings(chunks)

            # 6. Save chunks to DB
            chunk_records = []
            for i, (content, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_records.append({
                    "content": content,
                    "chunk_index": i,
                    "embedding": embedding,
                    "metadata": {
                        "filename": doc["filename"],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                })
            self.documents.save_chunks(document_id, chunk_records)

            # 7. Set status to completed
            self.documents.update_document(document_id, {
                "status": "completed",
                "chunk_count": len(chunks),
            })

        except Exception as e:
            # Set status to failed with error message
            self.documents.update_document(document_id, {
                "status": "failed",
                "error_message": str(e),
            })
