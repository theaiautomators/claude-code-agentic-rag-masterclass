# Chunking Improvements for Structured Documents

⚠️ **Medium** — Targeted changes to 2 files; requires re-ingestion of existing docs for validation.

## Why

The current `recursive_split()` function produces poor-quality chunks for structured Markdown documents:

- **Undersized chunks** (48–152 tokens) — Markdown's dense `\n\n` separators cause aggressive splitting well below the 1000-char budget
- **Broken overlap** — `prev[-200:]` is a raw character slice that cuts mid-word (e.g. `hrough \`parse_document\`...`)
- **Structure blindness** — Module entries get split across 2–3 chunks, diluting retrieval relevance; search similarity peaked at 0.645 for direct module queries

## What

Add a new `markdown_split()` function that splits on `## ` heading boundaries first, then falls back to `recursive_split()` for oversized sections, with paragraph-aware overlap. Route `.md` and `.txt` files through the new splitter in `ingest_file`.

## Files to Change

| File | Change |
|---|---|
| `server/chunking.py` | Bump default `chunk_size` 1000→1500; add `markdown_split()`, `_handle_section()`, `_apply_paragraph_aware_overlap()` |
| `server/main.py` | Update import; add extension-based routing before chunk call |

## Implementation

### `server/chunking.py`

**1. Bump default chunk_size:**
```python
def recursive_split(text: str, chunk_size: int = 1500, ...)
```

**2. Add `markdown_split(text, chunk_size=1500, chunk_overlap=200, min_chunk_size=100)`:**
- Split `text` on `\n## ` boundaries → preamble + sections list
- Process preamble via `_handle_section(heading=None, body=preamble)`
- For each section: extract heading (first line) and body (rest), call `_handle_section(heading, body)`
- Apply `_apply_paragraph_aware_overlap()` across all chunks
- Filter chunks below `min_chunk_size` chars

**3. Add `_handle_section(heading, body, chunk_size, chunk_overlap)`:**
- If `heading + "\n\n" + body` fits in `chunk_size`: return as single chunk
- Else: `recursive_split(body, chunk_size, chunk_overlap=0)`, prepend heading to each sub-chunk
- Returns `list[str]`

**4. Add `_apply_paragraph_aware_overlap(chunks, chunk_overlap)`:**
- For each consecutive pair, take `prev[-chunk_overlap:]` as tail window
- Find last `\n\n` in tail → use text after it as overlap (paragraph boundary)
- Fallback: last `" "` (word boundary)
- Fallback: raw character slice (original behaviour)

### `server/main.py`

**Update import:**
```python
from server.chunking import recursive_split, markdown_split
```

**Replace flat call with routing (~line 133):**
```python
MARKDOWN_EXTENSIONS = {".md", ".txt"}
if path.suffix.lower() in MARKDOWN_EXTENSIONS:
    chunks = markdown_split(content)
else:
    chunks = recursive_split(content)
```

Note: `.txt` is included because `markdown_split()` degrades safely when no `## ` headings exist — it falls through to `recursive_split()` automatically.

## Validation

1. Re-ingest `docs/changelogs.md` with `force=True`
   - Every chunk `content` starts with `## [2026-03-07]...` heading
   - No chunk starts with a lowercase partial word
   - `token_count` values: 30–400 words per chunk (no 48-token orphans)

2. Search quality regression:
   - `search_documents("what changed in module 6")` → similarity > 0.75 (baseline: 0.645)
   - Top result chunk contains both the heading AND full body in one chunk

3. Non-MD regression:
   - Re-ingest `test_data/sample.pdf` → chunks identical to pre-change (still uses `recursive_split`)

## Risks

| Risk | Mitigation |
|---|---|
| `## ` inside code fences | `\n## ` pattern (requires leading newline + space) reduces false splits |
| Empty sections (heading, no body) | `min_chunk_size=100` filter removes bare heading chunks |
| Existing chunks not updated automatically | Force re-ingest test docs during validation |
