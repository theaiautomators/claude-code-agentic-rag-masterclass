---
id: 260307-000006
type: Feature
module: Module 5
component: Backend, Database
priority: P1
status: Backlog
---

# Module 5: Metadata Extraction

⚠️ **Medium** — Involves LLM structured extraction via Gemini API, DB schema changes, and modifying the search tool for filtered retrieval.

## Objective

Extract structured metadata from documents during ingestion using an LLM. Use metadata to filter the search space before semantic matching.

---

## Prerequisites

- [x] Module 2 complete (ingestion pipeline)
- [x] Module 3 complete (search_documents tool)
- [ ] Gemini API key in `.env` (`GEMINI_API_KEY`)

---

## Tasks

### Task 1: Add Metadata Columns to Documents Table

- [ ] Create migration: `supabase migration new add_document_metadata`
  ```sql
  alter table documents add column if not exists title text;
  alter table documents add column if not exists summary text;
  alter table documents add column if not exists topics text[];
  alter table documents add column if not exists document_type text;
  alter table documents add column if not exists language text default 'en';
  ```
- [ ] Apply migration

**Validation**: Columns exist in Supabase Studio.

---

### Task 2: Create `DocumentMetadata` Pydantic Schema

- [ ] Add to `server/schemas.py`:
  ```python
  class DocumentMetadata(BaseModel):
      title: str
      summary: str
      topics: list[str]
      document_type: str  # e.g., "article", "report", "manual", "notes"
      language: str = "en"
  ```

**Validation**: Schema importable without error.

---

### Task 3: Create Metadata Extraction Function

- [ ] Create `server/metadata.py`
- [ ] Use Gemini API (`google-genai` SDK) to extract metadata:
  - Send first 8,000 characters of document content
  - System prompt instructs LLM to return structured JSON matching `DocumentMetadata` schema
  - Parse response with Pydantic for validation
- [ ] Use `GEMINI_API_KEY` (already in `.env`) and `GEMINI_CHAT_MODEL` (e.g., `gemini-2.0-flash`)
- [ ] Update `.env.example`

**Validation**: Pass a test document → returns valid `DocumentMetadata` object.

---

### Task 4: Integrate Metadata into Ingestion Pipeline

- [ ] After chunking in `ingest_file`, call metadata extraction
- [ ] Store extracted metadata in the `documents` table
- [ ] Handle extraction failures gracefully (log warning, continue without metadata)

**Validation**: Ingest a file → document record has title, summary, topics populated.

---

### Task 5: Add Metadata Filters to `search_documents`

- [ ] Extend `search_documents` with optional filter parameters:
  ```python
  def search_documents(
      query: str,
      top_k: int = 5,
      threshold: float = 0.7,
      document_type: str | None = None,
      topics: list[str] | None = None,
  ) -> list[dict]:
  ```
- [ ] Update the `search_chunks` RPC function (or create a new one) to accept metadata filters
- [ ] Filter on `documents.document_type` and `documents.topics` before vector search

**Validation**: Filter by `document_type="article"` → only returns chunks from articles.

---

### Task 6: End-to-End Smoke Test

- [ ] Ingest `test_data/sample.txt` → metadata extracted (title, summary, topics)
- [ ] Call `search_documents("chunking", document_type="article")` → filtered results
- [ ] Call `list_documents()` → shows metadata fields
- [ ] Verify metadata in Supabase Studio

**Validation**: Metadata extraction and filtered search both work end-to-end.

---

## Environment Variables

Add to `.env` and `.env.example`:
```
GEMINI_CHAT_MODEL=gemini-2.0-flash
```

---

## Definition of Done

- [x] Metadata columns on documents table
- [x] `DocumentMetadata` Pydantic schema
- [x] LLM extraction function via Gemini API
- [x] Metadata populated during ingestion
- [x] `search_documents` supports metadata filters
- [x] `.env.example` updated with `GEMINI_CHAT_MODEL`
- [x] Smoke test passes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | Implemented Supabase migration, Pydantic schema, and Gemini structured extraction. Modified `ingest_file` and `search_documents`. Smoke test verified successfully. Moved to completion. |
