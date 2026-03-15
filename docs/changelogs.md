# Changelogs

## [Unreleased]

## [2026-03-07] - Fix 401 Credentials Exposure in Chat UI

### Fixed
- `server/api.py`: Split `except Exception as e` into `except HTTPException: raise` + `except Exception` to prevent GoTrue auth payload (email, password) from leaking into 401 error response body.
- `frontend/src/pages/Chat.tsx`: Added `res.ok` guard before SSE body processing — non-2xx responses now throw a clean JS error routed to the existing catch block instead of rendering raw JSON in the chat.

## [2026-03-07] - Late Chunking + Project Categorization

### Added
- `server/late_chunking.py` — Late chunking via `jinaai/jina-embeddings-v2-base-en` (768 dims, 8192-token context). Single forward pass over full document; mean-pools per-chunk token spans. Gracefully falls back to CLS-pooling per chunk if document exceeds 8192 tokens.
- `embed_chunks_with_context()` dispatcher in `server/embeddings.py` — routes to Jina late chunking when `EMBEDDING_PROVIDER=jina_late`, otherwise falls back to `embed_texts()` (Gemini/Ollama unchanged).
- `list_projects` MCP tool — lists all projects with document counts.
- `create_project` MCP tool — creates a new project (returns error if name already exists).
- `Project` Pydantic model in `server/schemas.py`.
- `project: str | None = None` field on `DocumentMetadata` for LLM-extracted project attribution.
- `supabase/migrations/20260307190000_create_projects_table.sql` — `projects` table with RLS, name unique index, `sql_reader` grant.
- `supabase/migrations/20260307190001_add_project_to_documents.sql` — `project_id uuid` FK on `documents` (on delete set null).
- `supabase/migrations/20260307190002_update_search_functions_project.sql` — `search_chunks` and `keyword_search_chunks` updated with `filter_project_id uuid` parameter and `project_id` in result set.
- `einops==0.8.2` dependency in `server/requirements.txt`.

### Changed
- `ingest_file` — added `project: str | None` and `create_project: bool` params. Resolves project by name, links document, or returns `status: project_confirmation_needed` when project is unknown and `create_project=False`.
- `list_documents` — added `project: str | None` filter param; select now includes `projects(id, name)` join.
- `search_documents` — added `project: str | None` filter param; passes `filter_project_id` to both RPC functions.
- `server/metadata.py` — system prompt updated to extract project name; all `DocumentMetadata` fallback instantiations include `project=None`.
- `ingest_file` embedding call replaced with `embed_chunks_with_context(content, chunks)`.

## [2026-03-07] - Chunking Improvements

### Added
- `markdown_split()` in `server/chunking.py` — splits on `## ` heading boundaries before falling back to `recursive_split()`, keeping each section in one chunk
- `_handle_section()` helper — returns section as single chunk if it fits, otherwise splits body and re-prepends heading to each sub-chunk
- `_apply_paragraph_aware_overlap()` helper — overlap respects `\n\n` paragraph boundaries then word boundaries instead of raw character slicing

### Changed
- `recursive_split()` default `chunk_size` bumped 1000 → 1500 to reduce undersized orphan chunks
- `ingest_file` in `server/main.py` routes `.md` and `.txt` files through `markdown_split()` and all other formats through `recursive_split()`

## [2026-03-07] - 260307-000009 - SQL Database Tools (Module 8)

### Added
- Created postgres read-only role `sql_reader` via Supabase migrations, strictly constrained to `SELECT` ops
- Implemented `get_schema` MCP Tool using psycopg2 to expose public table/column constraints dynamically to the AI agent
- Implemented `query_sql` MCP Tool. Hard-coded application guardrails to verify SQL intent starts with SELECT or WITH.
- End-to-end Python smoke test evaluating CTE and error handling workflows (`test_mcp_sql.py`)

### Changed
- Removed Web Search fallback objectives since modern AI tools (like Claude Code) feature browser tools natively.


## [2026-03-07] - 260307-000008 - Hybrid Search and Reranking (Module 7)

### Added
- Created postgres function `keyword_search_chunks` alongside `fts` TSVECTOR columns backed by a GIN index in `chunks` table for high speed BM25 keyword matches
- Merged Vector and Keyword algorithms in Python using standard Reciprocal Rank Fusion (RRF) algorithm implementation in `server/search.py`
- Implemented state-of-the-art re-scoring via cross-encoding (`ms-marco-MiniLM-L-6-v2`) inside a new `server/reranker.py` file, utilizing `sentence-transformers`
- End-to-end Python smoke test evaluating multi-vector logic (`test_mcp_hybrid_search.py`)

### Changed
- Refactored `search_documents` MCP tool to optionally accept `mode` variables (`hybrid`, `vector`, `keyword`) and the `rerank` flag to toggle components natively

## [2026-03-07] - 260307-000007 - Multi-Format Support (Module 6)

### Added
- `docling` library to `requirements.txt`
- `server/parser.py` — unified document parsing API for PDF, DOCX, MD, and HTML files leveraging the IBM Docling models
- Automated smoke test (`test_mcp_multiformat.py`) confirming cascading delete works and confirming cross-format ingestion & search

### Changed
- `server/main.py` — `ingest_file` now routes contents through `parse_document` and sets proper `content-type` MIME headers in Supabase Storage based on original file extensions

## [2026-03-07] - 260307-000006 - Metadata Extraction (Module 5)

### Added
- `supabase/migrations/20260307122049_add_document_metadata.sql` — Columns for title, summary, topics, document_type, language
- `supabase/migrations/20260307122204_search_chunks_with_metadata.sql` — Replaced search function to support metadata filtering
- `server/metadata.py` — Added Gemini API structured extraction using `DocumentMetadata`
- `test_mcp_metadata.py` — Smoke test for extraction and filtered search

### Changed
- `server/schemas.py` — Added `DocumentMetadata`
- `server/main.py` — Updated `search_documents` with optional type/topic filters, and `ingest_file` to populate metadata

## [2026-03-07] - 260307-000005 - Record Manager (Module 4)

### Added
- `supabase/migrations/20260307041258_add_content_hash_index.sql` — index on `documents(content_hash)` for fast dedup lookups
- `test_module4.py` — end-to-end smoke test for deduplication and re-ingestion

### Changed
- `server/main.py` `ingest_file` — added `force: bool = False` parameter; skips ingestion if same filename + same hash; deletes old doc and re-ingests if same filename + different hash
- `README.md` — updated tech stack (Gemini API), module list (9 modules, MCP-first), and added Testing section

## [2026-03-07] - 260307-000004 - Retrieval Tool (Module 3)

### Added
- `supabase/migrations/20260307071551_search_chunks.sql` — pgvector semantic search function with similarity thresholds
- `search_documents` MCP tool in `server/main.py` utilizing the new RPC function and the `embed_text` handler

## [2026-03-07] - 260307-000011 - Ingestion Smoke Test (Module 2)

### Changed
- `server/main.py` — restored Module 2 `ingest_file`, `list_documents`, `delete_document` functions
- `server/embeddings.py` — updated to use `gemini-embedding-001` via `GEMINI_API_KEY` rather than OpenRouter
- `.env` & `.env.example` — added `GEMINI_API_KEY` placeholder
- Module 2 completely validated against local Supabase instance

## [2026-03-07] - Switch from OpenRouter to Gemini API

### Changed
- `server/embeddings.py` — rewritten to use `google-genai` SDK with `gemini-embedding-001` (was OpenRouter `qwen3-embedding-0.6b`)
- `.env.example` — replaced `OPENROUTER_*` keys with `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_EMBEDDING_DIMENSIONS`
- PRD.md, CLAUDE.md, PROGRESS.md — all references updated from OpenRouter to Gemini API (free tier)
- Backlog plans (module5, module9) — updated to reference Gemini API
- Embeddings now use task types: `RETRIEVAL_DOCUMENT` for ingestion, `RETRIEVAL_QUERY` for search

### Added
- `google-genai` SDK dependency in `server/requirements.txt`

## [2026-03-07] - 260307-000003 - Document Ingestion via MCP (Module 2)

### Added
- `server/schemas.py` — Pydantic models for Document and Chunk
- `server/chunking.py` — recursive character text splitter (pure Python, no LangChain)
- `server/embeddings.py` — OpenRouter embedding API client (qwen3-embedding-0.6b, 768 dims, batch support)
- `ingest_file` MCP tool — read → chunk → embed → store in pgvector
- `list_documents` MCP tool — list all ingested documents
- `delete_document` MCP tool — cascade delete document + chunks + storage file
- `supabase/migrations/*_create_documents_table.sql` — documents table with RLS
- `supabase/migrations/*_create_chunks_table.sql` — chunks table with vector(768), ivfflat index, RLS
- `supabase/migrations/*_create_documents_storage_bucket.sql` — private documents storage bucket
- `test_data/sample.txt` — test file for smoke testing ingestion
- `.env.example` — added OPENROUTER_API_KEY, OPENROUTER_EMBEDDING_MODEL, OPENROUTER_EMBEDDING_DIMENSIONS

## [2026-03-07] - 260307-000002 - MCP Server Scaffold (Module 1)

### Added
- `server/main.py` — FastMCP server with stdio transport, `hello` and `supabase_health` tools
- `server/requirements.txt` — pinned dependencies (mcp, supabase, python-dotenv)
- `.mcp.json` — project-scoped MCP server registration for Claude Code
- `server/venv/` gitignored along with `__pycache__/` and `*.pyc`

### Changed
- `.gitignore` — added `server/venv/`, `__pycache__/`, `*.pyc`
- PRD.md, CLAUDE.md, PROGRESS.md, workflow.md — restructured for MCP-first architecture (9 modules)

## [2026-03-07] - 260307-000001 - PRD MCP Restructure

### Changed
- PRD.md — rewritten with 9-module MCP-first architecture
- CLAUDE.md — updated stack, rules, and project description for MCP-first
- PROGRESS.md — restructured to 9 modules with updated checklists
- docs/workflow.md — module reference and rules updated for MCP-first

### Removed
- Old web-first Module 1 (app-shell) plan archived to `docs/03_archive/`

## [2026-03-06] - 260306-000002 - Supabase Local Setup

### Added
- Supabase CLI installed, `supabase/` initialized, local stack running
- `.env` populated with local Supabase credentials
- `.env.example` with SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL
- pgvector extension enabled via migration (`20260306155855_enable_pgvector.sql`)
