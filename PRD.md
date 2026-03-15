# Agentic RAG Masterclass - PRD

## What We're Building

An MCP-first RAG server with tools for document ingestion, retrieval, search, and analysis — consumed by Claude Code (or any MCP-compatible client). A web chat UI is added in Module 9 as an additional interface.

This is **not** an automated pipeline with connectors. Files are ingested manually via MCP tool calls or drag-and-drop (Module 9). Configuration is via environment variables, no admin UI.

## Target Users

Technically-minded people who want to build production RAG systems using AI coding tools (Claude Code, Cursor, etc.). They don't need to know Python or React - that's the AI's job.

**They need to understand:**
- RAG concepts deeply (chunking, embeddings, retrieval, reranking)
- Codebase structure (what sits where, how pieces connect)
- How to direct AI to build what they need
- How to direct AI to fix things when they break
- How MCP tools extend AI assistants with custom capabilities

## Scope

### In Scope
- ✅ MCP server with RAG tools (stdio transport)
- ✅ Document ingestion and processing
- ✅ Vector search with pgvector
- ✅ Hybrid search (keyword + vector)
- ✅ Reranking
- ✅ Metadata extraction
- ✅ Record management (deduplication)
- ✅ Multi-format support (PDF, DOCX, HTML, Markdown)
- ✅ Text-to-SQL tool
- ✅ Web search fallback
- ✅ Web chat UI with threads and memory (Module 9)
- ✅ Auth with RLS (Module 9)
- ✅ Streaming responses via SSE (Module 9)

### Out of Scope
- ❌ Knowledge graphs / GraphRAG
- ❌ Code execution / sandboxing
- ❌ Image/audio/video processing
- ❌ Fine-tuning
- ❌ Multi-tenant admin features
- ❌ Billing/payments
- ❌ Data connectors (Google Drive, SFTP, APIs, webhooks)
- ❌ Scheduled/automated ingestion
- ❌ Admin UI (config via env vars)

## Stack

| Layer | Choice |
|-------|--------|
| MCP Server | Python (stdio transport) |
| Database | Supabase (Postgres + pgvector + Auth + Storage + Realtime) |
| Embeddings | Gemini API (free tier) |
| Reasoning LLM | Claude via Claude Code (no API key needed) |
| Observability | LangSmith |
| Frontend (Module 9) | React + TypeScript + Vite + Tailwind + shadcn/ui |
| Web Backend (Module 9) | Python + FastAPI |

## Constraints

- No LLM frameworks — raw SDK calls only (Gemini for embeddings), Pydantic for structured outputs
- MCP server uses stdio transport
- Claude Code provides the reasoning LLM — no separate chat/completion API key needed
- Row-Level Security on all tables — users only see their own data (enforced in Module 9)
- Streaming chat via SSE (Module 9)
- Ingestion status via Supabase Realtime (Module 9)

---

## Module 1: MCP Server Scaffold + Supabase Verification

**Build:** Verify local Supabase is healthy, Python MCP server skeleton with a `hello` tool, register in Claude Code project settings

**Learn:** What MCP is, how tools work, stdio transport, server registration, the bridge between AI assistants and custom backends

---

## Module 2: Document Ingestion via MCP

**Build:** `ingest_file` MCP tool (read file → chunk → embed via Gemini API → store in pgvector), `list_documents` and `delete_document` tools, Pydantic schemas for Document and Chunk, Supabase Storage for raw files

**Learn:** Chunking strategies, embeddings, vector storage, MCP tool design, how to structure tool inputs/outputs

---

## Module 3: Retrieval Tool

**Build:** `search_documents` MCP tool with vector similarity search, relevance threshold filtering, ranked results with source attribution

**Learn:** Vector search, cosine similarity, relevance scoring, how retrieval grounds LLM responses

---

## Module 4: Record Manager

**Build:** SHA-256 content hashing on ingest, deduplication (skip if hash unchanged), delete old chunks + re-embed on file modification

**Learn:** Why naive ingestion duplicates, incremental updates, content-addressed storage

---

## Module 5: Metadata Extraction

**Build:** LLM structured extraction via Gemini API, `DocumentMetadata` Pydantic schema (title, summary, topics, document_type, language), metadata-filtered retrieval in `search_documents`

**Learn:** Structured extraction, schema design, metadata-enhanced retrieval, filtering search space before semantic match

---

## Module 6: Multi-Format Support

**Build:** Docling integration for PDF, DOCX, HTML, Markdown parsing, cascade deletes (delete document → delete all chunks)

**Learn:** Document parsing challenges, format considerations, standard vs advanced pipelines

---

## Module 7: Hybrid Search + Reranking

**Build:** BM25 keyword search, hybrid search combining vector + keyword results, RRF (Reciprocal Rank Fusion) score normalization, reranker integration (local bge-reranker or Cohere)

**Learn:** Why vector alone isn't enough, hybrid strategies, reranking, score fusion

---

## Module 8: Additional Tools

**Build:** `query_sql` MCP tool (text-to-SQL with read-only Postgres user), `web_search` MCP tool (fallback when docs don't have the answer). Claude Code handles tool routing natively — no custom agent router needed.

**Learn:** Multi-tool agents, routing between structured/unstructured data, graceful fallbacks, security (read-only SQL user)

---

## Module 9: Web Chat UI

**Build:** React + Vite + Tailwind + shadcn/ui frontend, FastAPI backend wrapping the same core functions MCP tools use, Supabase Auth (login/signup), RLS policies, chat UI with threads, SSE streaming, ingestion UI with drag-drop upload, Supabase Realtime for ingestion status

**Learn:** Building a web interface on top of an existing RAG backend, auth, streaming, how the same core logic serves both MCP and web clients

---

## Success Criteria

By the end, students should have:
- ✅ A working MCP-based RAG server usable from Claude Code
- ✅ A web chat UI (Module 9) powered by the same backend
- ✅ Deep understanding of RAG concepts (chunking, embedding, retrieval, reranking)
- ✅ Understanding of MCP — how to extend AI assistants with custom tools
- ✅ Understanding of codebase structure — what lives where, how pieces connect
- ✅ Ability to direct AI coding tools to build new features
- ✅ Ability to direct AI coding tools to debug and fix issues
- ✅ Experience with multi-tool patterns (retrieval, SQL, web search)
