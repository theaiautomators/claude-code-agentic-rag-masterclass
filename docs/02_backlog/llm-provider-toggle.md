# LLM Provider Toggle: Gemini ↔ Ollama (Local)

⚠️ **Medium** — New migration, new module, changes to 3 existing files, 1 new `ollama` pip dependency.

## Why

Gemini requires an API key and internet access. Replacing it with local Ollama models (via `nomic-embed-text` for embeddings, `qwen2.5:3b` for metadata extraction) makes the stack fully offline-capable and free. A runtime config table in Supabase lets you flip the provider without redeploying or touching `.env`.

## What

1. Create a `config` table in Supabase (key-value store for runtime settings)
2. New `server/config.py` — thin read/write wrapper around the config table
3. Refactor `server/embeddings.py` — provider abstraction: `gemini` | `ollama`
4. Refactor `server/metadata.py` — provider abstraction: `gemini` | `ollama`
5. Add two MCP tools to `server/main.py`: `get_config` and `set_config`
6. Install `ollama` Python package into the venv

## Design Decisions

- **`nomic-embed-text` outputs 768 dims** — identical to the current `gemini-embedding-001` setting. Zero Supabase schema changes needed.
- Config is read **per-call** (not cached at startup) so toggling takes effect on the next ingest or search immediately.
- Switching `embedding_provider` mid-flight makes existing chunk vectors incompatible with the new model's query vectors. `set_config` must print a prominent warning when changing this key.
- Config table has **no RLS** for now — it is a global server setting, not per-user. This is acceptable until Module 9 introduces multi-tenancy.
- Gemini credentials remain in `.env`; Ollama credentials are just a base URL (default `http://localhost:11434`). Neither is stored in the config table.

## Config Keys

| Key | Values | Default | Notes |
|---|---|---|---|
| `embedding_provider` | `gemini` \| `ollama` | `gemini` | Changing requires full re-ingest |
| `metadata_provider` | `gemini` \| `ollama` | `gemini` | Safe to switch anytime |
| `ollama_base_url` | any URL | `http://localhost:11434` | Shared by both Ollama uses |
| `ollama_embed_model` | any model tag | `nomic-embed-text` | Must output 768 dims |
| `ollama_metadata_model` | any model tag | `qwen2.5:3b` | Must support JSON output |

---

## Files to Change

| File | Change |
|---|---|
| New migration `20260307180000_create_config_table.sql` | `config` table + seed defaults |
| `server/config.py` (**new**) | `get_config(key)`, `set_config(key, value)`, `get_all_config()` |
| `server/embeddings.py` | Provider branching via `get_config("embedding_provider")` |
| `server/metadata.py` | Provider branching via `get_config("metadata_provider")` |
| `server/main.py` | Import config module; add `get_config` and `set_config` MCP tools |
| `server/requirements.txt` | Add `ollama` |

---

## Implementation

### 1. Migration: `supabase/migrations/20260307180000_create_config_table.sql`

```sql
create table config (
  key   text primary key,
  value text not null,
  updated_at timestamptz default now()
);

-- Seed defaults
insert into config (key, value) values
  ('embedding_provider',   'gemini'),
  ('metadata_provider',    'gemini'),
  ('ollama_base_url',      'http://localhost:11434'),
  ('ollama_embed_model',   'nomic-embed-text'),
  ('ollama_metadata_model','qwen2.5:3b');
```

Apply with: `supabase db push` (local stack).

---

### 2. `server/config.py` (new file)

```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

_DEFAULTS = {
    "embedding_provider":    "gemini",
    "metadata_provider":     "gemini",
    "ollama_base_url":       "http://localhost:11434",
    "ollama_embed_model":    "nomic-embed-text",
    "ollama_metadata_model": "qwen2.5:3b",
}

def _client():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    )

def get_config(key: str) -> str:
    """Fetch a single config value; falls back to hardcoded default."""
    try:
        result = _client().table("config").select("value").eq("key", key).single().execute()
        return result.data["value"]
    except Exception:
        return _DEFAULTS.get(key, "")

def set_config(key: str, value: str) -> None:
    """Upsert a config key. Creates row if missing."""
    _client().table("config").upsert(
        {"key": key, "value": value, "updated_at": "now()"},
        on_conflict="key",
    ).execute()

def get_all_config() -> dict[str, str]:
    """Return all config rows as a dict."""
    try:
        rows = _client().table("config").select("key, value").execute()
        return {r["key"]: r["value"] for r in rows.data}
    except Exception:
        return dict(_DEFAULTS)
```

---

### 3. `server/embeddings.py` — provider abstraction

Replace current file with:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ───────────────────────────────────────────────────────────────────
def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    from google import genai
    from google.genai.types import EmbedContentConfig

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    model    = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    dims     = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))

    client = genai.Client(api_key=api_key)
    response = client.models.embed_content(
        model=model,
        contents=texts,
        config=EmbedContentConfig(task_type=task_type, output_dimensionality=dims),
    )
    return [e.values for e in response.embeddings]

# ── Ollama ────────────────────────────────────────────────────────────────────
def _embed_ollama(texts: list[str]) -> list[list[float]]:
    import ollama as _ollama
    from server.config import get_config

    base_url = get_config("ollama_base_url")
    model    = get_config("ollama_embed_model")

    client = _ollama.Client(host=base_url)
    return [client.embeddings(model=model, prompt=t)["embedding"] for t in texts]

# ── Public API ────────────────────────────────────────────────────────────────
def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    from server.config import get_config
    provider = get_config("embedding_provider")

    if provider == "ollama":
        return _embed_ollama(texts)
    return _embed_gemini(texts, task_type)

def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    return embed_texts([text], task_type=task_type)[0]
```

---

### 4. `server/metadata.py` — provider abstraction

```python
import os
import json
from dotenv import load_dotenv
from server.schemas import DocumentMetadata

load_dotenv()

_SYSTEM_PROMPT = (
    "You are an expert document analyzer. Extract the title, a brief summary, "
    "a list of key topics, the document type (e.g., 'article', 'report', 'notes', "
    "'technical documentation'), and the 2-letter ISO language code for the following text. "
    "Do not invent information. If you cannot determine the title, use the first sentence."
)

def _fallback(reason: str) -> DocumentMetadata:
    return DocumentMetadata(
        title="Unknown Title",
        summary=reason,
        topics=[],
        document_type="unknown",
        language="en",
    )

# ── Gemini ────────────────────────────────────────────────────────────────────
def _extract_gemini(content: str) -> DocumentMetadata:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=f"{_SYSTEM_PROMPT}\n\nDocument Text:\n{content}",
        config=dict(
            response_mime_type="application/json",
            response_schema=DocumentMetadata,
            temperature=0.0,
        ),
    )
    return DocumentMetadata.model_validate_json(response.text)

# ── Ollama ────────────────────────────────────────────────────────────────────
def _extract_ollama(content: str) -> DocumentMetadata:
    import ollama as _ollama
    from server.config import get_config

    base_url = get_config("ollama_base_url")
    model    = get_config("ollama_metadata_model")

    schema = DocumentMetadata.model_json_schema()
    prompt = f"{_SYSTEM_PROMPT}\n\nDocument Text:\n{content}"

    client = _ollama.Client(host=base_url)
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=schema,
        options={"temperature": 0},
    )
    raw = response["message"]["content"]
    return DocumentMetadata.model_validate_json(raw)

# ── Public API ────────────────────────────────────────────────────────────────
def extract_metadata(content: str) -> DocumentMetadata:
    from server.config import get_config

    if not content or not content.strip():
        return _fallback("No content provided.")

    truncated = content[:8000]
    provider  = get_config("metadata_provider")

    try:
        if provider == "ollama":
            return _extract_ollama(truncated)
        return _extract_gemini(truncated)
    except Exception as e:
        return _fallback(f"Extraction failed ({provider}): {e}")
```

---

### 5. `server/main.py` — two new MCP tools

Add after the existing imports:
```python
from server.config import get_all_config, set_config as _set_config
```

Add two new tools before `if __name__ == "__main__":`:

```python
@mcp.tool()
def get_config() -> dict:
    """Return all runtime configuration values (embedding provider, metadata provider, Ollama settings)."""
    return get_all_config()


@mcp.tool()
def set_config(key: str, value: str) -> dict:
    """Update a runtime configuration value.

    Common keys:
      embedding_provider   — 'gemini' or 'ollama'  ⚠️ changing this requires full re-ingest
      metadata_provider    — 'gemini' or 'ollama'  (safe to change anytime)
      ollama_base_url      — e.g. 'http://localhost:11434'
      ollama_embed_model   — e.g. 'nomic-embed-text'
      ollama_metadata_model— e.g. 'qwen2.5:3b'

    Args:
        key:   Config key to update.
        value: New value.
    """
    EMBEDDING_WARNING = (
        "⚠️  embedding_provider changed. Existing chunks were embedded with the previous model. "
        "You MUST re-ingest all documents (use force=True) or search results will be meaningless."
    )
    _set_config(key, value)
    result = {"updated": True, "key": key, "value": value}
    if key == "embedding_provider":
        result["warning"] = EMBEDDING_WARNING
    return result
```

---

### 6. `server/requirements.txt` — add ollama

```
ollama
```

Install with: `pip install ollama` inside the venv.

---

## Validation

### Step 1 — Migration applied
```sql
-- Run in Supabase Studio / psql
select * from config;
-- Expect 5 rows with default values
```

### Step 2 — Gemini mode still works (regression)
- Call `get_config` MCP tool → all keys visible, `embedding_provider=gemini`
- Ingest any file → succeeds, uses Gemini
- `search_documents("...")` → returns results as before

### Step 3 — Switch metadata to Ollama
```
set_config("metadata_provider", "ollama")
```
- Ingest a new file → metadata row populated (title/summary/topics correct)
- No Gemini API call made (verify by temporarily revoking API key or checking Ollama logs: `ollama logs`)

### Step 4 — Switch embeddings to Ollama
```
set_config("embedding_provider", "ollama")
```
- Re-ingest all docs with `force=True`
- `search_documents("...")` → returns relevant results (similarity > 0.7)
- Confirm 768-dim vectors in DB: `select array_length(embedding, 1) from chunks limit 1;`

### Step 5 — Switch back to Gemini (round-trip)
```
set_config("embedding_provider", "gemini")
set_config("metadata_provider", "gemini")
```
- Re-ingest all docs with `force=True`
- Search works with Gemini again

---

## Risks

| Risk | Mitigation |
|---|---|
| Mismatched vector spaces after provider switch | `set_config` returns a visible warning; re-ingest is required |
| Ollama not running | `_embed_ollama` / `_extract_ollama` raise a clear `ConnectionError`; `ingest_file` returns `status: error` |
| `qwen2.5:3b` JSON hallucinations | `model_validate_json` raises, `_fallback` is returned; ingestion still completes |
| `ollama` package import error when using Gemini | Both providers are imported lazily (inside the branch), so missing `ollama` package only fails when Ollama mode is active |
| `config` table missing (pre-migration) | `get_config` catches exceptions and returns hardcoded `_DEFAULTS`; server stays functional |

## Ollama Setup (prerequisite)

```bash
# Pull required models before switching providers
ollama pull nomic-embed-text   # embeddings (768 dims)
ollama pull qwen2.5:3b         # metadata extraction
```
