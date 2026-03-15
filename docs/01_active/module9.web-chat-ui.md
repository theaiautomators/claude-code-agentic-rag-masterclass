---
id: 260307-000010
type: Feature
module: Module 9
component: Frontend, Backend, Auth
priority: P2
status: Backlog
---

# Module 9: Web Chat UI

🔴 **Complex** — Full-stack feature: React frontend, FastAPI backend wrapping existing core functions, Supabase Auth, RLS, SSE streaming, ingestion UI with Realtime. Consider breaking into sub-plans.

## Objective

Build a web chat UI on top of the existing RAG backend. FastAPI wraps the same core functions that MCP tools use. Supabase Auth for user management, RLS for data isolation.

---

## Prerequisites

- [x] Modules 1-8 complete (full RAG pipeline via MCP)
- [ ] All MCP tools working and tested

---

## Sub-Plans (Suggested Breakdown)

Due to complexity, consider splitting into:
- **9a**: Frontend scaffold + Auth (login/signup/protected routes)
- **9b**: FastAPI backend wrapping core functions + SSE streaming
- **9c**: Chat UI (threads, messages, streaming responses)
- **9d**: Ingestion UI (drag-drop upload, Realtime status)

---

## Tasks

### Task 1: Frontend Scaffold

- [ ] Create `frontend/` directory
- [ ] Init with Vite + React + TypeScript: `npm create vite@latest frontend -- --template react-ts`
- [ ] Install Tailwind CSS and shadcn/ui
- [ ] Install `@supabase/supabase-js`
- [ ] Create `.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- [ ] Verify: `npm run dev` starts on `:5173`

**Validation**: Frontend starts, blank page renders.

---

### Task 2: Supabase Auth (Frontend)

- [ ] Build login/signup page (email + password) with shadcn/ui components
- [ ] Persist session — redirect to chat on login, to login on logout
- [ ] Protected route — unauthenticated users cannot access chat
- [ ] Auth context provider for session management

**Validation**: Sign up → lands on chat. Refresh → stays logged in. Logout → redirected.

---

### Task 3: Database Schema Updates for Chat

- [ ] Create migration for threads table:
  ```sql
  create table threads (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users not null,
    title text,
    created_at timestamptz default now()
  );
  alter table threads enable row level security;
  create policy "users see own threads" on threads
    for all using (auth.uid() = user_id);
  ```
- [ ] Create migration for messages table:
  ```sql
  create table messages (
    id uuid primary key default gen_random_uuid(),
    thread_id uuid references threads(id) on delete cascade not null,
    user_id uuid references auth.users not null,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    created_at timestamptz default now()
  );
  alter table messages enable row level security;
  create policy "users see own messages" on messages
    for all using (auth.uid() = user_id);
  ```

**Validation**: Tables exist with RLS enabled.

---

### Task 4: FastAPI Backend

- [ ] Create `frontend/api/` or add to existing `server/` as `server/api.py`
- [ ] FastAPI app wrapping core functions:
  - `POST /chat` — accepts `{ thread_id, message }`, streams response via SSE
  - `GET /threads` — list user's threads
  - `POST /threads` — create new thread
  - `GET /threads/{id}/messages` — get thread messages
  - `POST /ingest` — file upload endpoint
  - `GET /documents` — list documents
  - `DELETE /documents/{id}` — delete document
- [ ] Auth middleware: validate Supabase JWT from Authorization header
- [ ] Call the same core functions that MCP tools use (chunking, embedding, search)
- [ ] SSE streaming for chat responses using local Ollama model (`qwen2.5:3b`)

**Validation**: `curl POST /chat` returns SSE stream.

---

### Task 5: Chat UI

- [ ] Sidebar: thread list (title + date), "New Thread" button
- [ ] Main panel: message list (user/assistant bubbles), input box + send button
- [ ] SSE streaming: tokens appear progressively in assistant bubble
- [ ] Messages persisted to `messages` table
- [ ] Thread title auto-generated from first message

**Validation**: Create thread, send message, see streaming response.

---

### Task 6: Ingestion UI

- [ ] Drag-and-drop file upload zone
- [ ] Upload progress indicator
- [ ] Document list with status (pending, processing, completed, failed)
- [ ] Delete button per document
- [ ] Supabase Realtime subscription for live status updates during processing

**Validation**: Upload a file → see status change from pending → processing → completed in real time.

---

### Task 7: End-to-End Smoke Test

1. Start backend: `uvicorn server.api:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Sign up with a new account
4. Upload a document via ingestion UI → status updates in real time
5. Create a new thread
6. Send a message → streaming response appears
7. Verify in Supabase: message stored under correct `user_id`
8. Log in as different user → cannot see first user's threads/documents

**Validation**: Full end-to-end flow works with auth isolation.

---

## Definition of Done

- [ ] Frontend scaffold (React + Vite + Tailwind + shadcn/ui)
- [ ] Auth working (signup, login, logout, protected routes)
- [ ] FastAPI backend wrapping core RAG functions
- [ ] Chat UI with threads, messages, SSE streaming
- [ ] Ingestion UI with drag-drop and Realtime status
- [ ] RLS enforced — users only see own data
- [ ] Smoke test passes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
