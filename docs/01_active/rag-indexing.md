# RAG Indexing Setup

This document describes the RAG (Retrieval-Augmented Generation) indexing architecture for the claude-code-agentic-rag-masterclass project running on arr-stack.

## Architecture Overview

The RAG system uses:
- **Supabase** with pgvector extension for vector storage and similarity search
- **Gemini API** (gemini-embedding-001) for generating 768-dimensional embeddings
- **MCP Server** (Model Context Protocol) providing tools for document ingestion and search
- **Recursive character chunking** with token-based sizing for optimal context preservation

## Prerequisites

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/theaiautomators/claude-code-agentic-rag-masterclass.git
   cd claude-code-agentic-rag-masterclass
   ```

2. **Install Python dependencies:**
   ```bash
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root with:
   ```
   SUPABASE_URL=http://192.168.0.105:8000
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   SQL_READER_URL=postgresql://sql_reader:password@192.168.0.105:5432/postgres
   ```

   **Note:** arr-stack uses local network IP (192.168.0.105), not localhost. This is required for containerized environments.

### Database Schema

The following tables are created via migrations:

- **projects**: Document categorization with unique name constraint
- **documents**: Stores file metadata, content_hash (SHA-256), status, chunk_count
- **chunks**: Stores text chunks with pgvector embedding column (vector(768))
- **Storage bucket**: 'documents' bucket for raw file storage (private, RLS-enabled)

Key schema features:
- Composite unique index on `filename + content_hash` for deduplication
- IVF index (ivfflat) on embedding column for cosine similarity search
- Foreign key cascade delete from documents to chunks
- Row-level security (RLS) for project-based access control

## MCP Tools

The MCP server provides the following tools for RAG operations:

### 1. `hello(name: str = "world")`
Verifies the MCP server is running.
```
hello("developer") → "Hello, developer! RAG Masterclass MCP server is running."
```

### 2. `supabase_health()`
Checks Supabase local stack connectivity.
```
supabase_health() → {"status": "connected", "supabase_url": "...", "auth_users_count": N}
```

### 3. `ingest_file(file_path, force=False, project=None, create_project=False)`
Ingests a document into the RAG system.

**Flow:**
1. Parse document (PDF, DOCX, MD, TXT, HTML via Docling)
2. Compute SHA-256 content hash for deduplication
3. Check for existing document with same filename
4. Skip if hash matches (duplicate), or delete old + re-ingest if different
5. Upload raw file to Supabase Storage
6. Chunk content using recursive_split (general) or markdown_split (MD/TXT)
7. Generate embeddings via Gemini API (768 dimensions)
8. Insert chunks into pgvector table
9. Extract metadata via LLM (title, summary, topics, document_type, language)
10. Link to project (auto-create if create_project=True)

**Returns:**
```json
{
  "status": "completed|skipped|error|project_confirmation_needed",
  "document_id": "uuid",
  "filename": "example.pdf",
  "chunk_count": 5,
  "content_hash": "sha256_hex_string",
  "metadata_extracted": true,
  "project_id": "uuid"
}
```

**Usage:**
```
# Ingest a file
ingest_file("/path/to/doc.pdf")

# Force re-ingestion even if content unchanged
ingest_file("/path/to/doc.pdf", force=True)

# Assign to project (auto-create if missing)
ingest_file("/path/to/doc.pdf", project="my-project", create_project=True)
```

### 4. `list_documents(project: str | None = None)`
Lists all ingested documents with metadata.

**Returns:**
```json
[
  {
    "id": "uuid",
    "filename": "example.pdf",
    "status": "completed",
    "chunk_count": 5,
    "content_hash": "sha256_hex",
    "created_at": "2026-03-15T08:00:00Z",
    "project_id": "uuid",
    "projects": {"id": "uuid", "name": "my-project"}
  }
]
```

**Usage:**
```
# List all documents
list_documents()

# Filter by project
list_documents(project="my-project")
```

### 5. `delete_document(document_id: str)`
Deletes a document and all its chunks (cascade delete).

**Returns:**
```json
{"deleted": true, "document_id": "uuid", "filename": "example.pdf"}
```

**Usage:**
```
delete_document("document-uuid-here")
```

### 6. `search_documents(query, top_k=5, threshold=0.7, mode="hybrid", rerank=False, document_type=None, topics=None, project=None)`
Searches documents using vector similarity and optional metadata filters.

**Modes:**
- `hybrid`: Combines vector + keyword search with Reciprocal Rank Fusion (RRF)
- `vector`: Pure pgvector cosine similarity search
- `keyword`: Full-text search via keyword_search_chunks RPC

**Filters:**
- `document_type`: Filter by metadata document_type (e.g., 'article', 'report')
- `topics`: Filter to documents containing at least one topic
- `project`: Filter by project name

**Returns:**
```json
[
  {
    "id": "chunk-uuid",
    "content": "chunk text...",
    "similarity": 0.92,
    "filename": "source.pdf",
    "document_type": "article",
    "topics": ["rag", "vector-search"],
    "project_name": "my-project"
  }
]
```

**Usage:**
```
# Basic search
search_documents("What is RAG indexing?", top_k=5)

# Hybrid search with reranking
search_documents("RAG architecture", mode="hybrid", rerank=True, top_k=10)

# Filtered search
search_documents("embedding models", document_type="technical", project="ml-research")
```

### 7. `list_projects()`
Lists all projects with document counts.

**Returns:**
```json
[
  {"id": "uuid", "name": "project-a", "description": "...", "document_count": 15}
]
```

### 8. `create_project(name: str, description: str = "")`
Creates a new project. Returns error if name already exists.

**Returns:**
```json
{"status": "created", "id": "uuid", "name": "new-project", "description": "..."}
```

### 9. `get_schema()`
Returns database schema for SQL query construction.

**Returns:**
```json
[{"table_name": "documents", "column_name": "id", "data_type": "uuid"}, ...]
```

### 10. `query_sql(sql: str)`
Executes read-only SQL SELECT queries against the database.

**Usage:**
```
query_sql("SELECT COUNT(*) FROM documents WHERE status = 'completed'")
```

## Batch Ingestion

Use the `index_docs` script for batch ingestion of multiple files:

```bash
python scripts/index_docs.py --project my-project --force --dirs docs/ knowledge-base/
```

**Arguments:**
- `--project`: Assign documents to this project
- `--force`: Re-ingest even if content hash matches
- `--create-project`: Auto-create project if it doesn't exist
- `--dirs`: One or more directories to scan recursively

**Supported formats:** .pdf, .docx, .md, .txt

## Testing

Run tests from the server/venv:

```bash
cd server
source venv/bin/activate
python -m pytest
```

Key test files:
- `test_supabase_health.py`: Connectivity tests
- `test_ingest_file.py`: Ingestion workflow tests
- `test_search_documents.py`: Search functionality tests
- `test_e2e_smoke.py`: End-to-end pipeline tests

## Codebase Patterns

- **Supabase client**: `create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)`
- **Embeddings**: 768 dimensions (must match pgvector `vector(768)` column)
- **Chunking**: Token-based (512 tokens target, 50 token overlap) using tiktoken
- **Deduplication**: SHA-256 hash comparison on filename match
- **Storage**: Supabase Storage bucket API uses `.from_().upload()` and `.from_().remove()`
- **RLS**: Storage policies use `storage.foldername(name)` for user folder extraction

## Troubleshooting

### Common Issues

1. **"File not found"**: Ensure absolute or correctly relative path
2. **"No chunks produced"**: File content too short (< 512 tokens) or unsupported format
3. **"Project confirmation needed"**: Project exists but wasn't auto-created; re-run with `create_project=True`
4. **Embedding dimension mismatch**: Ensure Gemini API returns exactly 768 dimensions
5. **Connection refused**: Verify arr-stack IP (192.168.0.105:8000) is reachable

### Debugging

Enable verbose output by running MCP server with logging:
```bash
python -m server.main 2>&1 | tee mcp.log
```

Check Supabase connectivity:
```bash
curl http://192.168.0.105:8000/rest/v1/
```

Verify environment variables:
```bash
cat .env | grep -E "SUPABASE|GEMINI"
```
