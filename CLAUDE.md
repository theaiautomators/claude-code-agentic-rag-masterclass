# CLAUDE.md

MCP-first RAG server exposing ingestion, retrieval, search, and analysis tools via stdio transport. Consumed by Claude Code (or any MCP-compatible client). Optional web chat UI in Module 9.

## Stack
- MCP Server: Python (stdio transport)
- Database: Supabase (Postgres, pgvector, Auth, Storage, Realtime)
- Embeddings: Gemini API (free tier)
- Reasoning LLM: Claude via Claude Code (no API key needed)
- Observability: LangSmith
- Frontend (Module 9): React + Vite + Tailwind + shadcn/ui
- Web Backend (Module 9): Python + FastAPI

## Rules
- Python backend must use a `venv` virtual environment
- No LangChain, no LangGraph - raw SDK calls only
- Use Pydantic for structured LLM outputs
- MCP server uses stdio transport
- Claude Code provides the reasoning LLM - no separate chat/completion API key needed
- All tables need Row-Level Security - users only see their own data (enforced in Module 9)
- Stream chat responses via SSE (Module 9)
- Use Supabase Realtime for ingestion status updates (Module 9)
- Ingestion is manual only - via MCP tool calls or drag-and-drop (Module 9). No connectors or automated pipelines

## Planning
- Save all plans to `docs/02_backlog/` folder
- Naming convention: `{sequence}.{plan-name}.md` (e.g., `1.auth-setup.md`, `2.document-ingestion.md`)
- Move to `docs/01_active/` when work begins; move to `docs/04_completed/` when done
- Plans should be detailed enough to execute without ambiguity
- Each task in the plan must include at least one validation test to verify it works
- Assess complexity and single-pass feasibility - can an agent realistically complete this in one go?
- Include a complexity indicator at the top of each plan:
  - ✅ **Simple** - Single-pass executable, low risk
  - ⚠️ **Medium** - May need iteration, some complexity
  - 🔴 **Complex** - Break into sub-plans before executing

## Development Flow
1. **Plan** - Create a detailed plan and save it to `docs/02_backlog/`
2. **Build** - Execute the plan to implement the feature
3. **Validate** - Test and verify the implementation works correctly. Use browser testing where applicable via an appropriate MCP
4. **Iterate** - Fix any issues found during validation

## Progress
Check PROGRESS.md for current module status. Update it as you complete tasks.
