# CLAUDE.md

RAG app with chat (default) and document ingestion interfaces. Config via env vars, no admin UI.

## Stack
- Frontend: React + Vite + Tailwind v4 + shadcn/ui
- Backend: Python 3.9 + FastAPI
- Database: Supabase (Postgres, pgvector, Auth, Storage, Realtime)
- LLM: OpenAI (Module 1), OpenRouter (Module 2+)
- Observability: LangSmith

## Rules
- Python backend must use a `venv` virtual environment
- No LangChain, no LangGraph - raw SDK calls only
- Use Pydantic for structured LLM outputs
- All tables need Row-Level Security - users only see their own data
- Stream chat responses via SSE
- Use Supabase Realtime for ingestion status updates
- Module 2+ uses stateless completions - store and send chat history yourself
- Ingestion is manual file upload only - no connectors or automated pipelines

## Environment Notes
- **Python 3.9** — avoid `dict | None` union syntax, use `Optional[dict]` from typing
- **Supabase runs via CLI** (`npx supabase start`) not raw Docker Compose
- **Supabase uses ES256 JWTs** — verify via JWKS endpoint, not HS256 with JWT secret
- **Supabase key format** is `sb_publishable_*` / `sb_secret_*` (new format) — the `supabase-py` client doesn't support this, so use `httpx` for direct PostgREST API calls instead
- **Supabase ports**: API on 54321, Studio on 54323, DB on 54322
- **Backend runs on port 8001** (54321 is taken by Supabase)
- **Frontend runs on port 5173** (Vite default)
- LangSmith tracing is disabled (`LANGSMITH_TRACING=false`) until API key is obtained

## Planning
- Save all plans to `.agent/plans/` folder
- Naming convention: `{sequence}.{plan-name}.md` (e.g., `1.auth-setup.md`, `2.document-ingestion.md`)
- Plans should be detailed enough to execute without ambiguity
- Each task in the plan must include at least one validation test to verify it works
- Assess complexity and single-pass feasibility - can an agent realistically complete this in one go?
- Include a complexity indicator at the top of each plan:
  - ✅ **Simple** - Single-pass executable, low risk
  - ⚠️ **Medium** - May need iteration, some complexity
  - 🔴 **Complex** - Break into sub-plans before executing

## Development Flow
1. **Plan** - Create a detailed plan and save it to `.agent/plans/`
2. **Build** - Execute the plan to implement the feature
3. **Validate** - Test and verify the implementation works correctly. Use browser testing where applicable via an appropriate MCP
4. **Iterate** - Fix any issues found during validation

## How to Run
```bash
# Backend (terminal 1)
cd backend && source venv/bin/activate && uvicorn main:app --reload --port=8001

# Frontend (terminal 2)
cd frontend && npm run dev
```

## Working with This User
- Beginner-friendly explanations preferred — walk through steps clearly
- Provide full paths in terminal commands (don't assume they're in the right directory)
- Use `--port=8001` syntax (not `--port 8001`) to avoid terminal line-splitting issues
- When debugging, check both browser console AND uvicorn terminal for errors
- User pastes console errors in full — look for the key error line, not the full stack

## Progress
Check PROGRESS.md for current module status. Update it as you complete tasks.
