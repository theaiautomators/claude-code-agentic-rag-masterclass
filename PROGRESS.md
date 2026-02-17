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
- [ ] Ingestion UI (file upload, drag-and-drop)
- [ ] File storage (Supabase Storage)
- [ ] Chunking + embedding pipeline
- [ ] pgvector search
- [ ] Switch from Responses API to Chat Completions API (OpenRouter/Ollama/LM Studio)
- [ ] Chat history storage (stateless API — manage memory ourselves)
- [ ] Retrieval tool for the LLM
- [ ] Realtime ingestion status (Supabase Realtime)

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

Module 1 is complete and working. The next module is **Module 2: BYO Retrieval + Memory**.

Before starting Module 2, a key architectural decision must be made (see PRD.md "Architectural Decision" section):
- **Option A:** Remove Responses API code entirely, rebuild on Chat Completions API
- **Option B:** Keep both approaches, configurable per request
- The video course chose **Option A** (clean break)

### What Module 2 involves:
1. Decide on Option A vs B (or something else)
2. Build the ingestion UI (file upload)
3. Implement chunking + embedding pipeline (store in pgvector)
4. Build retrieval tool for the LLM
5. Switch to Chat Completions API (stateless — send full chat history each request)
6. Store chat history in our own database (instead of OpenAI managing it)
7. Add Supabase Realtime for ingestion status updates

### Optional improvements to Module 1 before moving on:
- Set up LangSmith (get free API key at https://smith.langchain.com, set `LANGSMITH_TRACING=true` in backend/.env)
- Thread title auto-update (currently uses first 50 chars — could use LLM to generate a title)
- Error toasts instead of silent failures
- Mobile responsive sidebar
