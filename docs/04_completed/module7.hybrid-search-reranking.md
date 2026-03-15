---
id: 260307-000008
type: Feature
module: Module 7
component: Backend, Database
priority: P1
status: Backlog
---

# Module 7: Hybrid Search + Reranking

⚠️ **Medium** — Adds BM25 keyword search, RRF fusion, and reranker. Multiple new components but each is well-scoped.

## Objective

Combine vector similarity search with BM25 keyword search using Reciprocal Rank Fusion (RRF). Add a reranker to improve result quality.

---

## Prerequisites

- [x] Module 3 complete (vector search via `search_documents`)
- [x] Module 5 complete (metadata filtering)

---

## Tasks

### Task 1: Add Full-Text Search to Chunks Table

- [ ] Create migration: `supabase migration new add_fulltext_search`
  ```sql
  alter table chunks add column if not exists fts tsvector
    generated always as (to_tsvector('english', content)) stored;

  create index chunks_fts_idx on chunks using gin(fts);
  ```
- [ ] Apply migration

**Validation**: `fts` column and GIN index exist in Supabase Studio.

---

### Task 2: Create BM25 Keyword Search Function

- [ ] Create migration: `supabase migration new keyword_search_function`
  ```sql
  create or replace function keyword_search_chunks(
    search_query text,
    match_count int default 5
  )
  returns table (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    rank float,
    filename text
  )
  language sql stable
  as $$
    select
      c.id,
      c.document_id,
      c.content,
      c.chunk_index,
      ts_rank(c.fts, websearch_to_tsquery('english', search_query)) as rank,
      d.filename
    from chunks c
    join documents d on d.id = c.document_id
    where c.fts @@ websearch_to_tsquery('english', search_query)
    order by rank desc
    limit match_count;
  $$;
  ```
- [ ] Apply migration

**Validation**: RPC call with a keyword query returns matching chunks.

---

### Task 3: Implement RRF Fusion in Python

- [ ] Create `server/search.py` with hybrid search logic:
  ```python
  def reciprocal_rank_fusion(
      vector_results: list[dict],
      keyword_results: list[dict],
      k: int = 60,
  ) -> list[dict]:
      """Combine vector and keyword results using RRF."""
  ```
- [ ] RRF formula: `score = sum(1 / (k + rank))` for each result across both lists
- [ ] Merge by chunk ID, combine scores, sort by fused score descending
- [ ] Return unified result list with `rrf_score`, `vector_similarity`, `keyword_rank`

**Validation**: Given two result lists, RRF produces a merged, re-ranked list.

---

### Task 4: Update `search_documents` for Hybrid Mode

- [ ] Add `mode` parameter:
  ```python
  def search_documents(
      query: str,
      top_k: int = 5,
      threshold: float = 0.7,
      mode: str = "hybrid",  # "vector", "keyword", or "hybrid"
      ...
  ) -> list[dict]:
  ```
- [ ] `"vector"` — existing vector search only
- [ ] `"keyword"` — BM25 keyword search only
- [ ] `"hybrid"` — both + RRF fusion (default)

**Validation**: Each mode returns results; hybrid merges both sources.

---

### Task 5: Add Reranker

- [ ] Create `server/reranker.py`
- [ ] Option A: Local reranker via `sentence-transformers` + `bge-reranker-base`
- [ ] Option B: Cohere rerank API (requires API key)
- [ ] Reranker takes (query, candidate chunks) → re-scored and re-sorted
- [ ] Integrate as post-processing step in `search_documents` when `rerank=True`
- [ ] Add optional `rerank: bool = False` parameter to `search_documents`

**Validation**: Results with `rerank=True` may have different ordering than without.

---

### Task 6: End-to-End Smoke Test

- [ ] Ingest a document with specific terms (e.g., product codes, proper nouns)
- [ ] Vector search: `search_documents("what is the concept?", mode="vector")`
- [ ] Keyword search: `search_documents("PROD-12345", mode="keyword")` → keyword match surfaces
- [ ] Hybrid search: `search_documents("PROD-12345 description", mode="hybrid")` → both signals combined
- [ ] With reranking: `search_documents("query", rerank=True)` → re-ranked results

**Validation**: Keyword search finds exact terms that vector search misses; hybrid combines both.

---

## Definition of Done

- [x] Full-text search column and GIN index on chunks
- [x] BM25 keyword search function in DB
- [x] RRF fusion in Python
- [x] `search_documents` supports vector/keyword/hybrid modes
- [x] Reranker integrated (local or API)
- [x] Smoke test passes for all search modes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | Implemented full text search, BM25, and RRF logic. Added lightweight MS-MARCO BGE reranker using sentence-transformers. Verified tests and moving to complete. |
