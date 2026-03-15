# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

---

## Modules

### Module 1: MCP Server Scaffold + Supabase Verification
- [x] Supabase local setup (CLI, init, start, .env, pgvector)
- [x] Python MCP server skeleton (stdio transport)
- [x] `hello` tool — basic tool to verify MCP is working
- [x] `supabase_health` tool — verifies DB connectivity
- [x] Register MCP server in Claude Code project settings (`.mcp.json`)
- [x] Smoke test: Claude Code calls `hello` tool and gets a response

### Module 2: Document Ingestion via MCP
- [x] Pydantic schemas for `Document` and `Chunk`
- [x] Supabase Storage for raw files
- [x] Chunking strategy (recursive character splitting)
- [x] Embed chunks via Gemini API (free tier)
- [x] Store embeddings in pgvector
- [x] `ingest_file` MCP tool
- [x] `list_documents` MCP tool
- [x] `delete_document` MCP tool
- [x] Smoke test: ingest a file via Claude Code, verify chunks stored in DB

### Module 3: Retrieval Tool
- [x] `search_documents` MCP tool (vector similarity search)
- [x] Relevance threshold filtering
- [x] Ranked results with source attribution
- [x] Smoke test: ask Claude Code a question, verify it calls `search_documents` and returns grounded answer

### Module 4: Record Manager
- [x] SHA-256 content hashing on ingest
- [x] Deduplication: skip if hash already exists and unchanged
- [x] Delete old chunks + re-embed on file modification (prevent orphan chunks)
- [x] Smoke test: ingest same file twice, verify no duplicate chunks

### Module 5: Metadata Extraction
- [x] `DocumentMetadata` Pydantic schema (title, summary, topics, document_type, language)
- [x] LLM structured extraction via Gemini API from first 8,000 characters
- [x] Store metadata in DB alongside chunks
- [x] Metadata-filtered retrieval (filter search space before semantic match)
- [x] Smoke test: ingest a document, verify metadata extracted and filterable

### Module 6: Multi-Format Support
- [x] Docling integration for document parsing
- [x] Support: PDF, DOCX, HTML, Markdown
- [x] Standard pipeline (fast, CPU-friendly)
- [x] Cascade deletes (delete document → delete all chunks)
- [x] Smoke test: ingest one file of each format successfully

### Module 7: Hybrid Search + Reranking
- [x] BM25 keyword search implementation
- [x] Hybrid search: combine semantic (vector) + keyword (BM25) results
- [x] RRF (Reciprocal Rank Fusion) to normalize and merge scores
- [x] Reranker integration (local bge-reranker or Cohere)
- [x] Smoke test: query with a specific product code, verify keyword result surfaces

### Module 8: Additional Tools
- [x] `get_schema` MCP tool (database schema mapping)
- [x] `query_sql` MCP tool (text-to-SQL)
- [x] Read-only Postgres user (`sql_reader`) with restricted permissions
- [x] Isolated connection string (`SQL_READER_URL`) on transaction pooler port 54322
- [x] Smoke test: Execute CTE select statements, and verify rejection of DELETE statements

### Enhancements (post-module 8)
- [x] Late chunking via `jina-embeddings-v2-base-en` (`server/late_chunking.py`) — toggled by `EMBEDDING_PROVIDER=jina_late`
- [x] Project categorization — `projects` table, `list_projects` / `create_project` tools, project filter on `search_documents` / `list_documents`
- [x] LLM auto-extraction of `project` field from document content (extended `DocumentMetadata`)
- [x] `project_confirmation_needed` flow in `ingest_file` when new project detected but `create_project=False`

### Module 9: Web Chat UI
- [ ] React + Vite + Tailwind + shadcn/ui frontend scaffold
- [ ] FastAPI backend wrapping core RAG functions (same functions MCP tools use)
- [ ] Supabase Auth (login/signup)
- [ ] RLS policies on all tables
- [ ] Chat UI with threads, SSE streaming
- [ ] Ingestion UI with drag-drop upload
- [ ] Supabase Realtime for ingestion status
- [ ] Smoke test: sign up, upload a file, ask a question, get a grounded streaming response

---

## Git Tags (Milestone Reference)

| Tag | Milestone |
|:----|:----------|
| `v0.1` | Module 1 — MCP Scaffold |
| `v0.2` | Module 2 — Ingestion |
| `v0.3` | Module 3 — Retrieval |
| `v0.4` | Module 4 — Record Manager |
| `v0.5` | Module 5 — Metadata |
| `v0.6` | Module 6 — Multi-Format |
| `v0.7` | Module 7 — Hybrid Search |
| `v0.8` | Module 8 — Additional Tools |
| `v0.9` | Module 9 — Web Chat UI |
