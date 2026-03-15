---
id: 260307-000007
type: Feature
module: Module 6
component: Backend
priority: P1
status: Backlog
---

# Module 6: Multi-Format Support

⚠️ **Medium** — Docling integration adds a dependency, and each format has parsing nuances. Core pipeline stays the same.

## Objective

Support PDF, DOCX, HTML, and Markdown file ingestion using Docling for document parsing. Ensure cascade deletes work correctly.

---

## Prerequisites

- [x] Module 2 complete (ingestion pipeline for plain text)
- [x] Module 4 complete (record manager for dedup)

---

## Tasks

### Task 1: Install Docling

- [ ] Install in venv: `pip install docling`
- [ ] Update `server/requirements.txt`
- [ ] Verify import: `from docling.document_converter import DocumentConverter`

**Validation**: Import succeeds without error.

---

### Task 2: Create Document Parser Module

- [ ] Create `server/parser.py`
- [ ] Use Docling's standard pipeline (fast, CPU-friendly):
  ```python
  from docling.document_converter import DocumentConverter

  def parse_document(file_path: str) -> str:
      """Parse a document file and return plain text content."""
      converter = DocumentConverter()
      result = converter.convert(file_path)
      return result.document.export_to_markdown()
  ```
- [ ] Handle supported formats: `.pdf`, `.docx`, `.html`, `.md`, `.txt`
- [ ] For `.txt` files, read directly (no Docling needed)
- [ ] Raise clear error for unsupported formats

**Validation**: Parse a test PDF → returns markdown text.

---

### Task 3: Update `ingest_file` to Use Parser

- [ ] Replace direct `path.read_text()` with `parse_document(str(path))`
- [ ] Detect file extension to choose parsing strategy:
  - `.txt` → direct read
  - `.pdf`, `.docx`, `.html`, `.md` → Docling parser
- [ ] Update storage upload content-type based on file extension

**Validation**: Ingest a PDF file → chunks created from parsed content.

---

### Task 4: Create Test Files for Each Format

- [ ] Add to `test_data/`:
  - `sample.pdf` — a simple PDF with text content
  - `sample.docx` — a simple Word document
  - `sample.html` — a simple HTML page
  - `sample.md` — a markdown document
- [ ] Each file should have distinct content for search testing

**Validation**: All 4 test files exist and contain readable content.

---

### Task 5: Verify Cascade Deletes

- [ ] Ingest a multi-format file
- [ ] Delete it via `delete_document`
- [ ] Verify: document record gone, all chunks gone, storage file gone
- [ ] Confirm FK cascade (`on delete cascade`) works for chunks

**Validation**: No orphan chunks after document deletion.

---

### Task 6: End-to-End Smoke Test

- [ ] Ingest one file of each format (txt, pdf, docx, html, md)
- [ ] Call `list_documents()` → all 5 documents listed
- [ ] Call `search_documents("some query")` → returns chunks from multiple formats
- [ ] Delete one document → chunks cascade-deleted

**Validation**: All formats ingest successfully, search returns cross-format results.

---

## Definition of Done

- [x] Docling installed and importable
- [x] `server/parser.py` handles PDF, DOCX, HTML, Markdown, TXT
- [x] `ingest_file` uses parser for multi-format support
- [x] Cascade deletes verified
- [x] Test files for each format
- [x] Smoke test passes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | Implemented parsing via Docling. Updated `ingest_file` and verified file ingestion, metadata extraction, vector search, and cascading deletes across all formats. Moved to completion. |
