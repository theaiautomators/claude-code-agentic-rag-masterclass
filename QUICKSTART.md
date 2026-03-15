# Quickstart

Get the RAG server running in ~10 minutes.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [Supabase CLI](https://supabase.com/docs/guides/cli) installed
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free tier)

---

## 1. Clone and enter the project

```bash
git clone <repo-url>
cd claude-code-agentic-rag-masterclass
```

---

## 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
SUPABASE_ANON_KEY=         # from: supabase status
SUPABASE_SERVICE_ROLE_KEY= # from: supabase status
SUPABASE_DB_URL=           # from: supabase status (DB URL)
GEMINI_API_KEY=            # from: aistudio.google.com
```

> The other values (`SUPABASE_URL`, `GEMINI_EMBEDDING_MODEL`, `SQL_READER_URL`) are pre-filled and correct for local dev.

---

## 3. Start Supabase

```bash
supabase start
```

This starts Postgres, pgvector, Storage, and runs all migrations automatically.

Copy the keys printed by `supabase start` (or run `supabase status` anytime) into your `.env`.

Verify the DB is up at **http://localhost:54323** (Supabase Studio).

---

## 4. Set up the Python virtual environment

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

---

## 5. Launch Claude Code

```bash
claude
```

The MCP server starts automatically via `.mcp.json` — no separate process needed.

---

## 6. Verify everything works

In Claude Code, run these prompts in order:

| Step | Prompt |
|------|--------|
| MCP alive | `call the hello tool` |
| DB connected | `call supabase_health` |
| Ingest a file | `ingest the file at test_data/sample.md` |
| List documents | `list all ingested documents` |
| Search | `search documents for "what is chunking?"` |

All five should succeed without errors.

---

## Useful commands

| Task | Command |
|------|---------|
| Restart MCP server | `/mcp restart` (in Claude Code) |
| Supabase Studio | http://localhost:54323 |
| Stop Supabase | `supabase stop` |
| Re-activate venv | `source server/venv/bin/activate` |

---

## Troubleshooting

**MCP server not responding** — run `/mcp restart` in Claude Code, then try `call the hello tool` again.

**`supabase_health` fails** — confirm Supabase is running (`supabase status`) and your `.env` keys match.

**Embedding errors** — check your `GEMINI_API_KEY` in `.env` is valid and has quota.

**Import errors on startup** — make sure you ran `pip install -r requirements.txt` inside `server/venv`.
