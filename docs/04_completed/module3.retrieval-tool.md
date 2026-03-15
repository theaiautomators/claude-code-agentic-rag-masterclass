---
id: 260307-000004
type: Feature
module: Module 3
component: Backend
priority: P0
status: Done
---

# Module 3: Retrieval Tool

✅ **Simple** — Single MCP tool with vector similarity search against existing pgvector setup.

## Objective

Build a `search_documents` MCP tool that performs vector similarity search against ingested chunks, with relevance threshold filtering and source attribution.

---

## Prerequisites

- [x] Module 2 complete (documents + chunks tables, embeddings pipeline)
- [x] At least one document ingested for testing

---

## Tasks

### Task 1: Create `search_documents` MCP Tool

- [x] Add `search_documents` tool to `server/main.py`:
  ```python
  @mcp.tool()
  def search_documents(query: str, top_k: int = 5, threshold: float = 0.7) -> list[dict]:
      """Search ingested documents using vector similarity.

      Args:
          query: The search query text.
          top_k: Number of results to return (default 5).
          threshold: Minimum similarity score 0-1 (default 0.7).
      """
  ```
- [x] Implementation flow:
  1. Embed the query using `embed_text()` from `server/embeddings.py`
  2. Call a Supabase RPC function for vector similarity search
  3. Filter by `threshold`
  4. Return top_k results with: chunk content, similarity score, document filename, chunk_index

**Validation**: Import test passes, tool is registered.

---

### Task 2: Create pgvector Search Function (Migration)

- [x] Create migration: `supabase migration new search_chunks`
- [x] SQL function for cosine similarity search:
  ```sql
  create or replace function search_chunks(
    query_embedding vector(768),
    match_count int default 5,
    match_threshold float default 0.7
  )
  returns table (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    similarity float,
    filename text
  )
  language sql stable
  as $$
    select
      c.id,
      c.document_id,
      c.content,
      c.chunk_index,
      1 - (c.embedding <=> query_embedding) as similarity,
      d.filename
    from chunks c
    join documents d on d.id = c.document_id
    where 1 - (c.embedding <=> query_embedding) > match_threshold
    order by c.embedding <=> query_embedding
    limit match_count;
  $$;
  ```
- [x] Apply migration: `supabase db reset`

**Validation**: Function exists in DB, callable via Supabase RPC.

---

### Task 3: Wire Tool to RPC Function

- [x] `search_documents` calls `client.rpc("search_chunks", {...})` with the embedded query
- [x] Return format:
  ```json
  [
    {
      "content": "chunk text...",
      "similarity": 0.85,
      "filename": "sample.txt",
      "document_id": "uuid",
      "chunk_index": 2
    }
  ]
  ```
- [x] Handle empty results gracefully (return empty list with message)

**Validation**: Call `search_documents("what is RAG?")` with a relevant document ingested — returns ranked chunks.

---

### Task 4: End-to-End Smoke Test

- [x] Ensure `test_data/sample.txt` is ingested
- [x] From Claude Code:
  1. Call `search_documents("what is chunking?")` → returns relevant chunks about chunking
  2. Call `search_documents("quantum physics")` → returns empty or low-score results (not in corpus)
  3. Verify results include filename and similarity score
- [x] Confirm Claude Code uses the search results to ground its response

**Validation**: Relevant queries return relevant chunks; irrelevant queries return nothing.

---

## Definition of Done

- [x] `search_documents` MCP tool registered and callable
- [x] pgvector similarity search function in DB via migration
- [x] Results include content, similarity score, filename, chunk_index
- [x] Relevance threshold filtering works
- [x] Smoke test passes from Claude Code

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | pgvector vector similarity search migration created and database reset. |
| 2026-03-07 | `search_documents` tool implemented in python and successfully verified with local regression test script. Marking Module 3 as Done! |
