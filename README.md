# Cloud Code Agentic RAG Masterclass

Build an agentic RAG application from scratch by collaborating with Claude Code. Follow along with our video series using the docs in this repo.

[![Claude Code RAG Masterclass](./video-thumbnail.png)](https://www.youtube.com/watch?v=xgPWCuqLoek)

[Watch the full video on YouTube](https://www.youtube.com/watch?v=xgPWCuqLoek)

## What This Is

A hands-on course where you collaborate with Claude Code to build a full-featured RAG system. You're not the one writing code—Claude is. Your job is to guide it, understand what you're building, and course-correct when needed.

**You don't need to know how to code.** You do need to be technically minded and willing to learn about APIs, databases, and system architecture.

## What You'll Build

- **Chat interface** with threaded conversations, streaming, tool calls, and subagent reasoning
- **Document ingestion** with drag-and-drop upload and processing status
- **Full RAG pipeline**: chunking, embedding, hybrid search, reranking
- **Agentic patterns**: text-to-SQL, web search, subagents with isolated context

## Tech Stack

| Layer | Tech |
|-------|------|
| MCP Server | Python (stdio transport, FastMCP) |
| Database | Supabase (Postgres + pgvector + Auth + Storage) |
| Embeddings | Gemini API (free tier, `gemini-embedding-001`) |
| Reasoning LLM | Claude via Claude Code (no API key needed) |
| Doc Processing | Docling (Module 6+) |
| Frontend | React, TypeScript, Tailwind, shadcn/ui, Vite (Module 9) |
| Web Backend | Python, FastAPI (Module 9) |
| Observability | LangSmith |

## The 9 Modules

1. **MCP Server Scaffold** — stdio transport, `hello` + `supabase_health` tools
2. **Document Ingestion** — chunking, Gemini embeddings, pgvector storage
3. **Retrieval Tool** — vector similarity search with relevance threshold
4. **Record Manager** — SHA-256 deduplication, re-ingestion on content change
5. **Metadata Extraction** — LLM-extracted title/summary/topics, filtered retrieval
6. **Multi-Format Support** — PDF, DOCX, HTML, Markdown via Docling
7. **Hybrid Search & Reranking** — BM25 + vector (RRF), reranker
8. **Additional Tools** — text-to-SQL, web search fallback
9. **Web Chat UI** — React frontend, FastAPI backend, Supabase Auth, SSE streaming

## Getting Started

1. Clone this repo
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
3. Open in your IDE (Cursor, VS Code, etc.)
4. Run `claude` in the terminal
5. Use the `/onboard` command to get started

### Prerequisites

- [Supabase CLI](https://supabase.com/docs/guides/cli) installed and `supabase start` running
- Python 3.11+ with `venv` (auto-created inside `server/`)
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free tier) in `.env`

## Testing

### Option 1: Via Claude Code (recommended)

Restart the MCP server, then prompt Claude Code naturally:

```
/mcp restart
```

| What to test | Prompt |
|---|---|
| MCP server alive | `call the hello tool` |
| DB connectivity | `call supabase_health` |
| Ingest a file | `ingest the file at test_data/sample.txt` |
| List documents | `list all ingested documents` |
| Search | `search documents for "what is chunking?"` |
| Delete a doc | `delete document <id>` |

### Option 2: Python script (headless)

```bash
source server/venv/bin/activate

python -c "
from server.main import ingest_file, list_documents, search_documents

print(ingest_file('test_data/sample.txt'))
print(list_documents())
print(search_documents('what is chunking?'))
"
```

### Option 3: Supabase Studio (visual DB inspection)

Open **http://localhost:54323** and check:

- `Table Editor → documents` — ingested files and content hashes
- `Table Editor → chunks` — chunk content and embeddings
- `Storage → documents` — raw uploaded files

## Docs

- [PRD.md](./PRD.md) — What to build (9 modules in detail)
- [CLAUDE.md](./CLAUDE.md) — Context and rules for Claude Code
- [PROGRESS.md](./PROGRESS.md) — Track your build progress
- [docs/changelogs.md](./docs/changelogs.md) — Change history

## Join the Community

If you want to connect with hundreds of builders creating production-grade AI and RAG systems, join us in [The AI Automators community](https://www.theaiautomators.com/). Share your progress, get help when you're stuck, and see what others are building.
