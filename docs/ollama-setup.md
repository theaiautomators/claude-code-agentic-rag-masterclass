# Ollama Local LLM Setup Guide

This guide covers installing and configuring Ollama on macOS so the RAG server can use local models as a drop-in replacement for the Gemini API.

---

## Prerequisites

- macOS (Apple Silicon or Intel)
- [Homebrew](https://brew.sh) installed
- Supabase local stack already running (`supabase start`)

---

## 1. Install Ollama

```bash
brew install ollama
```

Or download the desktop app directly from [https://ollama.com/download](https://ollama.com/download) if you prefer a menubar icon.

Verify the install:

```bash
ollama --version
```

---

## 2. Start the Ollama Server

Ollama exposes a local HTTP API on port `11434`. Start it with:

```bash
ollama serve
```

It will run in the foreground. To keep it running in the background across reboots, the desktop app handles this automatically. For CLI-only installs, add it as a launchd service or just run it in a separate terminal.

Confirm it is running:

```bash
curl http://localhost:11434
# Expected: "Ollama is running"
```

---

## 3. Pull Required Models

### Embedding model — `nomic-embed-text`

Used to replace Gemini's `gemini-embedding-001`. Outputs **768-dimensional vectors**, which matches the existing pgvector column in Supabase — no schema changes needed.

```bash
ollama pull nomic-embed-text
```

Size: ~274 MB.

### Metadata extraction model — `qwen2.5:3b`

Used to replace `gemini-2.5-flash` for structured document metadata extraction (title, summary, topics, etc.). Trained specifically for JSON-constrained output.

```bash
ollama pull qwen2.5:3b
```

Size: ~2 GB.

Verify both models are available:

```bash
ollama list
```

Expected output:

```
NAME                    ID              SIZE    MODIFIED
nomic-embed-text:latest 0a109f422b47    274 MB  ...
qwen2.5:3b              357c56f9a432    2.0 GB  ...
```

---

## 4. Smoke-Test the Models

### Test embedding

```bash
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Hello world"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
emb = data['embedding']
print(f'Dims: {len(emb)}')   # Should print: Dims: 768
print(f'First 5: {emb[:5]}')
"
```

### Test metadata extraction (JSON output)

```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Return a JSON object with keys: title, summary, topics (array), document_type, language. Document: The Ollama setup guide explains how to install and run local LLMs on macOS."}],
    "format": "json",
    "stream": false,
    "options": {"temperature": 0}
  }' | python3 -m json.tool
```

Expected: valid JSON with all five keys populated.

---

## 5. Configure the RAG Server to Use Ollama

Once Ollama is running and models are pulled, use the MCP tools inside Claude Code to switch providers:

### Switch metadata extraction only (safe, no re-ingest needed)

```
set_config("metadata_provider", "ollama")
```

### Switch embeddings (requires full re-ingest)

```
set_config("embedding_provider", "ollama")
```

> **Warning:** Embeddings from different models live in incompatible vector spaces. After switching `embedding_provider`, re-ingest every document using `force=True`:
> ```
> ingest_file("/path/to/doc.md", force=True)
> ```
> Searching against old Gemini-embedded chunks with an Ollama query vector will return meaningless results.

### Verify current config

```
get_config()
```

Expected when fully switched to Ollama:

```json
{
  "embedding_provider":    "ollama",
  "metadata_provider":     "ollama",
  "ollama_base_url":       "http://localhost:11434",
  "ollama_embed_model":    "nomic-embed-text",
  "ollama_metadata_model": "qwen2.5:3b"
}
```

### Switch back to Gemini at any time

```
set_config("embedding_provider", "gemini")
set_config("metadata_provider",  "gemini")
```

Re-ingest all documents with `force=True` after switching `embedding_provider`.

---

## 6. Optional: Use a Different Model

You can override the defaults by updating the config keys:

```
# Use a larger model for better metadata quality
set_config("ollama_metadata_model", "qwen2.5:7b")

# Use a different embedding model (must also output 768 dims or you need a schema change)
set_config("ollama_embed_model", "mxbai-embed-large")  # outputs 1024 dims — needs migration
```

> If you switch to an embedding model with different dimensions (e.g. `mxbai-embed-large` at 1024 dims), the Supabase `chunks` table `embedding vector(768)` column must be migrated to match, and all documents must be re-ingested.

---

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `curl http://localhost:11434` → connection refused | Run `ollama serve` in a terminal, or open the Ollama desktop app |
| `ollama pull` hangs | Check internet connection; models are downloaded from Ollama's registry |
| Embedding returns wrong number of dims | Verify `ollama_embed_model` is `nomic-embed-text` via `get_config()` |
| Metadata JSON parse fails | The model may have returned markdown-wrapped JSON. Try `qwen2.5:7b` for higher reliability |
| `ModuleNotFoundError: No module named 'ollama'` | Run `pip install ollama` inside the venv: `source server/venv/bin/activate && pip install ollama` |
| Slow inference | `qwen2.5:3b` runs in ~2–5 s on Apple Silicon M1/M2. For faster results use `qwen2.5:1.5b` |

---

## Architecture Note

Ollama runs **natively on your Mac**, not inside Docker. The Supabase local stack manages its own Docker containers separately. The MCP server (plain Python process) communicates with both:

```
Your Mac
├── MCP server (Python, stdio)  ──→  http://localhost:11434  →  Ollama (native)
│                               ──→  http://localhost:54321  →  Supabase (Docker)
└── Claude Code (consumes MCP server via stdio)
```

No Docker networking changes are needed.
