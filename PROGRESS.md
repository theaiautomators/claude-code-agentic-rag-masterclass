# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### Module 1: App Shell + Observability

- [x] Backend scaffold (FastAPI, venv, config, health endpoint)
- [x] Database schema (threads + messages tables, RLS policies, migration SQL)
- [x] Auth middleware (JWT verification via Supabase JWKS/ES256)
- [x] Thread CRUD API (list, create, get, delete)
- [x] Chat API with SSE streaming (OpenAI Responses API)
- [x] LangSmith integration (wrapped OpenAI client — disabled until API key obtained)
- [x] Frontend scaffold (Vite + React + TypeScript + Tailwind v4 + shadcn/ui)
- [x] Auth UI (login/signup with Supabase Auth)
- [x] Chat UI (thread sidebar, message list, chat input, SSE streaming)
- [x] End-to-end validation — sign up, create thread, send message, streamed response works

### Module 2: BYO Retrieval + Memory
- [x] Switch from Responses API to Chat Completions API (OpenRouter)
- [x] Chat history storage (stateless API — send full history each request)
- [x] Database migration (pgvector, documents + chunks tables, search function, storage bucket, realtime)
- [x] File storage (Supabase Storage)
- [x] Chunking + embedding pipeline
- [x] Ingestion UI (file upload, drag-and-drop)
- [x] Realtime ingestion status (Supabase Realtime)
- [x] pgvector search
- [x] Retrieval tool for the LLM (tool calling with search_documents)

### Module 2.5: Shared/Global Documents
- [x] Database migration (is_shared column, updated RLS policies, updated search_chunks function)
- [x] Backend — list_documents returns owned + shared docs, DocumentResponse includes is_shared/user_id
- [x] Frontend — "Shared" badge on shared docs, delete button hidden for non-owners

### Module 3: Record Manager
- [ ] Not started

### Module 4: Metadata Extraction
- [ ] Not started

### Module 5: Multi-Format Support
- [ ] Not started

### Module 6: Hybrid Search & Reranking
- [ ] Not started

### Module 7: Additional Tools
- [ ] Not started

### Module 8: Sub-Agents
- [ ] Not started

## Next Steps

Module 2.5 (Shared Documents) is complete. The next module is **Module 3: Record Manager**.

### What was done in Module 2:
1. **Phase 1:** Switched from OpenAI Responses API to Chat Completions API via OpenRouter
2. **Phase 2:** Created database migration — pgvector extension, documents/chunks tables, vector search function, storage bucket, realtime
3. **Phase 3:** Built full ingestion pipeline — storage, document service, chunking, embedding, background processing
4. **Phase 4:** Built documents UI — drag-and-drop upload, document list with live Realtime status updates
5. **Phase 5:** Implemented RAG retrieval via tool calling — LLM calls search_documents tool, gets relevant chunks, answers with citations

### What was done in Module 2.5 (Shared Documents):
1. **DB migration** (`003_shared_documents.sql`) — added `is_shared` column, updated RLS on documents/chunks to allow SELECT of shared docs, updated `search_chunks()` to include shared docs in RAG results, marked 10 existing docs as shared
2. **Backend** — `list_documents()` returns owned + shared docs via PostgREST `or` filter; `DocumentResponse` now includes `is_shared` and `user_id`
3. **Frontend** — Purple "Shared" badge on shared documents; delete button only shown to the document owner
