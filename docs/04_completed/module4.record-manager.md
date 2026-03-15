---
id: 260307-000005
type: Feature
module: Module 4
component: Backend, Database
priority: P1
status: Backlog
---

# Module 4: Record Manager

✅ **Simple** — Modify existing `ingest_file` to check content hashes before processing. Clear logic, minimal new code.

## Objective

Add deduplication to the ingestion pipeline. Skip re-processing if file content hasn't changed. If content changed, delete old chunks and re-embed.

---

## Prerequisites

- [x] Module 2 complete (ingest_file tool with content_hash)
- [x] `documents.content_hash` column exists

---

## Tasks

### Task 1: Add Deduplication Check to `ingest_file`

- [ ] Before creating a new document record, check if a document with the same `content_hash` already exists:
  ```python
  existing = client.table("documents").select("id, filename").eq(
      "content_hash", content_hash
  ).execute()
  ```
- [ ] If hash matches an existing document → skip ingestion, return:
  ```json
  { "status": "skipped", "reason": "duplicate", "existing_document_id": "..." }
  ```

**Validation**: Ingest the same file twice → second call returns `skipped`.

---

### Task 2: Handle File Modifications (Re-ingestion)

- [ ] Add a `force` parameter to `ingest_file`:
  ```python
  def ingest_file(file_path: str, force: bool = False) -> dict:
  ```
- [ ] When `force=True` or same filename but different hash:
  1. Delete old document (cascade deletes old chunks)
  2. Delete old file from storage
  3. Re-ingest with new content
- [ ] Add logic to detect same filename with different hash:
  ```python
  same_name = client.table("documents").select("id, content_hash").eq(
      "filename", filename
  ).execute()
  ```
  - If same name + same hash → skip (duplicate)
  - If same name + different hash → re-ingest (content changed)
  - If no match → new document

**Validation**: Modify `test_data/sample.txt`, re-ingest → old chunks deleted, new chunks created.

---

### Task 3: Add Unique Constraint on content_hash

- [ ] Create migration: `supabase migration new add_content_hash_index`
  ```sql
  create index documents_content_hash_idx on documents(content_hash);
  ```
- [ ] Apply migration

**Validation**: Index exists in DB.

---

### Task 4: End-to-End Smoke Test

- [ ] Ingest `test_data/sample.txt` → succeeds
- [ ] Ingest same file again → returns `skipped` (duplicate)
- [ ] Modify `test_data/sample.txt` content, ingest again → old chunks replaced with new ones
- [ ] Verify chunk count in DB matches expectations (no orphans)

**Validation**: No duplicate chunks exist after repeated ingestion of the same file.

---

## Definition of Done

- [ ] Duplicate detection via SHA-256 content hash
- [ ] Skip ingestion for unchanged files
- [ ] Re-ingest on content change (delete old, create new)
- [ ] `force` parameter to override dedup check
- [ ] Content hash index in DB
- [ ] Smoke test passes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
