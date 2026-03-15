# Plan: Late Chunking + Project Categorization

🔴 **Complex** — New DB schema, new inference module, embedding layer refactor, ingest flow changes. Execute sequentially by phase.

**Status: COMPLETED 2026-03-07**

## What was implemented
- Phase 1: 3 DB migrations (projects table, project_id on documents, updated search functions)
- Phase 2: schemas.py (Project model, project field on DocumentMetadata), metadata.py (prompt + fallbacks updated)
- Phase 3: server/late_chunking.py (Jina v2 late chunking module)
- Phase 4: embed_chunks_with_context() dispatcher in embeddings.py (EMBEDDING_PROVIDER=jina_late)
- Phase 5: main.py (ingest_file, list_documents, search_documents updated; list_projects and create_project added)
- Phase 6: einops installed and added to requirements.txt
