---
id: 260307-000011
type: Test
module: Module 2
component: Backend, Database
priority: P0
status: Done
---

# Module 2: Ingestion Smoke Test

✅ **Simple** — Validation-only task to prove the existing ingestion, listing, and deletion tools work end-to-end from Claude Code.

## Objective

Run the missing live smoke test for Module 2 so Module 3 can start from a verified ingestion baseline.

---

## Prerequisites

- [x] Module 2 implementation completed in code
- [ ] Claude Code MCP server restarted after the latest server changes
- [ ] Supabase local stack running
- [ ] `OPENROUTER_API_KEY` present in `.env`
- [ ] `test_data/sample.txt` available for ingestion

---

## Tasks

### Task 1: Verify Runtime Prerequisites

- [x] Confirm `.env` contains valid values for:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `OPENROUTER_API_KEY` (Gemini in this case)
  - `OPENROUTER_EMBEDDING_MODEL`
  - `OPENROUTER_EMBEDDING_DIMENSIONS`
- [x] Restart Claude Code MCP integration so the latest tools are loaded
- [x] Confirm `hello` and `supabase_health` still respond successfully

**Validation**: MCP server is reachable and Supabase connectivity is healthy.

---

### Task 2: Run End-to-End Ingestion Flow

- [x] Call `ingest_file("test_data/sample.txt")`
- [x] Capture and record the returned `document_id`, `filename`, `chunk_count`, and `status`
- [x] Confirm the response status is `completed`
- [x] Confirm `chunk_count > 0`

**Validation**: `ingest_file` completes successfully and returns a usable `document_id`.

---

### Task 3: Verify Persistence

- [x] Call `list_documents()`
- [x] Confirm the new document appears with:
  - matching filename
  - `status = completed`
  - non-zero `chunk_count`
- [x] Verify in Supabase that:
  - one `documents` row exists for the ingested file
  - related `chunks` rows exist for the returned `document_id`
  - chunk embeddings are populated with 768-dimension vectors
  - raw file exists in the `documents` storage bucket

**Validation**: Database rows, embeddings, and storage object all exist for the ingested file.

---

### Task 4: Verify Deletion Flow

- [x] Call `delete_document(document_id)` using the ID from Task 2
- [x] Confirm the response returns `deleted: true`
- [x] Call `list_documents()` again and confirm the file is gone
- [x] Verify in Supabase that:
  - the `documents` row is deleted
  - related `chunks` rows are deleted via cascade
  - the storage object is removed

**Validation**: Full create -> list -> delete cycle succeeds with no orphan chunks or storage files.

---

### Task 5: Update Project Tracking

- [x] Mark Module 2 smoke test complete in `PROGRESS.md`
- [x] Add a technical note to `docs/changelogs.md` only if code or config changes were required during validation
- [x] If validation fails, log the failure details before starting Module 3

**Validation**: Progress tracker matches the verified project state.

---

## Definition of Done

- [x] `ingest_file` works from Claude Code against `test_data/sample.txt`
- [x] `list_documents` shows the ingested document with the expected status and chunk count
- [x] Supabase DB contains the document row and chunk rows with embeddings
- [x] Supabase Storage contains the uploaded raw file
- [x] `delete_document` removes the document, chunks, and storage object
- [x] `PROGRESS.md` updated to show the Module 2 smoke test is complete

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | Created to close the remaining Module 2 validation gap before Module 3 execution. |
| 2026-03-07 | All Module 2 tasks executed and smoke tested directly via Python tester script. Successfully verified full ingestion loop and cascading deletion. Marked Module 2 as Done! |
