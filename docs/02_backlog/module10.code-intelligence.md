---
id: module10
type: Feature
module: Module 10
component: MCP Tools, Database, Parsers
priority: P1
status: Backlog
---

# Module 10: Code Intelligence & Impact Analysis

🔴 **Complex** — Multiple language parsers, new DB schema, graph traversal, git hook. Break into sub-tasks and validate each layer before proceeding.

## Objective

Add a code intelligence layer to the RAG system that:
1. Indexes codebases by parsing source files into a **dependency graph** (who calls what, who imports what)
2. Embeds each symbol (function, class, method) for semantic search
3. Exposes two new MCP tools: `index_codebase` and `analyze_impact`
4. Auto re-indexes changed files on every git commit via a post-commit hook
5. Answers natural language questions like *"what breaks if I change embed_texts?"*

Supports: **Python, TypeScript/JavaScript, SQL, MongoDB (Mongoose/Pydantic schemas)**

---

## New Database Tables

### Table: `code_symbols`

Stores every named symbol (function, class, method) extracted from source files.

```sql
create table code_symbols (
    id              uuid primary key default gen_random_uuid(),
    project_id      uuid references projects(id) on delete cascade,
    file_path       text not null,
    symbol_name     text not null,
    symbol_type     text not null, -- 'function' | 'class' | 'method' | 'import' | 'schema'
    language        text not null, -- 'python' | 'typescript' | 'javascript' | 'sql' | 'mongodb'
    start_line      int not null,
    end_line        int not null,
    signature       text,          -- just the def/function/class line
    body            text,          -- full source of the symbol
    embedding       vector(768),   -- nomic-embed-text on signature + body
    created_at      timestamptz default now()
);

create index on code_symbols (project_id);
create index on code_symbols (symbol_name);
create index on code_symbols using hnsw (embedding vector_cosine_ops);
```

### Table: `code_edges`

Stores directional relationships between symbols.

```sql
create table code_edges (
    id              uuid primary key default gen_random_uuid(),
    project_id      uuid references projects(id) on delete cascade,
    from_symbol_id  uuid references code_symbols(id) on delete cascade,
    to_symbol_name  text not null,   -- name of target (may not be indexed yet)
    to_file_path    text,            -- resolved file path if known
    edge_type       text not null,   -- 'calls' | 'imports' | 'inherits' | 'uses'
    source_line     int,             -- line where the relationship occurs
    created_at      timestamptz default now()
);

create index on code_edges (project_id);
create index on code_edges (from_symbol_id);
create index on code_edges (to_symbol_name);
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MCP Tools (server/main.py)          │
│                                                      │
│   index_codebase(path, project)                      │
│   analyze_impact(symbol, project, depth)             │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
    ┌──────▼──────┐            ┌──────▼──────┐
    │   Parsers   │            │  Impact     │
    │             │            │  Traversal  │
    │  Python AST │            │             │
    │  tree-sitter│            │  Graph walk │
    │  sqlparse   │            │  via edges  │
    │  Mongoose   │            │  table      │
    └──────┬──────┘            └──────┬──────┘
           │                          │
    ┌──────▼──────────────────────────▼──────┐
    │              Supabase                   │
    │   code_symbols   code_edges            │
    │   (+ embeddings via Ollama)            │
    └─────────────────────────────────────────┘
           │
    ┌──────▼──────────────────┐
    │   Git Post-Commit Hook  │
    │   re-indexes changed    │
    │   files automatically   │
    └─────────────────────────┘
```

---

## Tasks

### Task 1: Database Migration

- [ ] Create migration: `supabase migration new code_intelligence`
- [ ] Add `code_symbols` table with HNSW index
- [ ] Add `code_edges` table with indexes
- [ ] Apply: `supabase db reset`

**Validation:** `\d code_symbols` and `\d code_edges` return correct schema in psql.

---

### Task 2: Python Parser (`server/parsers/python_parser.py`)

Use Python's built-in `ast` module.

Extracts:
- All `FunctionDef` / `AsyncFunctionDef` → symbol_type: `function`
- All `ClassDef` → symbol_type: `class`
- All `Import` / `ImportFrom` → edge_type: `imports`
- All `Call` nodes inside function bodies → edge_type: `calls`

Output per file:
```python
{
  "symbols": [
    {
      "symbol_name": "embed_texts",
      "symbol_type": "function",
      "start_line": 24,
      "end_line": 43,
      "signature": "def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:",
      "body": "def embed_texts(...):\n    ..."
    }
  ],
  "edges": [
    {
      "from_symbol": "embed_texts",
      "to_symbol_name": "ollama.embed",
      "edge_type": "calls",
      "source_line": 36
    }
  ]
}
```

- [ ] Implement `parse_python_file(file_path: str) -> dict`
- [ ] Handle nested classes (methods extracted as `method` type)
- [ ] Handle `*` imports gracefully (skip or record as wildcard)

**Validation:** Run against `server/embeddings.py` — should return `embed_texts`, `embed_text`, `embed_chunks_with_context` symbols and `ollama.Client`, `ollama.embed` call edges.

---

### Task 3: TypeScript/JavaScript Parser (`server/parsers/ts_parser.py`)

Use `tree-sitter` with `tree-sitter-typescript` grammar.

```
pip install tree-sitter tree-sitter-typescript tree-sitter-javascript
```

Extracts:
- `function_declaration`, `arrow_function` → `function`
- `class_declaration` → `class`
- `method_definition` → `method`
- `import_statement` → `imports` edge
- `call_expression` → `calls` edge

- [ ] Implement `parse_ts_file(file_path: str) -> dict`
- [ ] Implement `parse_js_file(file_path: str) -> dict` (reuse same grammar, skip type annotations)
- [ ] Handle React components (treat as `function`)

**Validation:** Run against `frontend/src/App.tsx` — returns component functions and their import edges.

---

### Task 4: SQL Parser (`server/parsers/sql_parser.py`)

Use `sqlparse` library (already available).

Extracts:
- `CREATE TABLE` → symbol_type: `schema`
- `CREATE FUNCTION` / `CREATE OR REPLACE FUNCTION` → `function`
- `CREATE INDEX` → recorded as metadata on the table symbol
- References to other tables in `REFERENCES` → `uses` edge

- [ ] Implement `parse_sql_file(file_path: str) -> dict`
- [ ] Handle multi-statement files (migrations)

**Validation:** Run against a Supabase migration file — returns table names and FK relationships as edges.

---

### Task 5: MongoDB Schema Parser (`server/parsers/mongo_parser.py`)

MongoDB has no DDL. Instead, parse the schema definitions in code:

- **Python (Pydantic models)**: reuse Python AST parser, flag `class X(BaseModel)` as `schema` type
- **TypeScript (Mongoose schemas)**: use TS parser, detect `new Schema({...})` calls

- [ ] Extend Python parser to detect `BaseModel` subclasses → `symbol_type: schema`
- [ ] Extend TS parser to detect `mongoose.Schema` / `new Schema` → `symbol_type: schema`

**Validation:** Given a Pydantic model file, returns the model class as a `schema` symbol with field names in the body.

---

### Task 6: Indexer Core (`server/code_indexer.py`)

Orchestrates parsers, embeds symbols, upserts to Supabase.

```python
def index_file(file_path: str, project_id: str) -> dict:
    # 1. Pick parser based on extension
    # 2. Parse → symbols + edges
    # 3. Embed each symbol (signature + body) via Ollama
    # 4. Upsert code_symbols (delete old rows for this file first)
    # 5. Upsert code_edges
    # 6. Return { symbols_indexed, edges_indexed }

def index_codebase(root_path: str, project_id: str, extensions: list[str] = None) -> dict:
    # Walk directory, call index_file for each matching file
    # Skip: node_modules, .git, venv, __pycache__, dist, build
    # Default extensions: .py, .ts, .tsx, .js, .jsx, .sql
```

- [ ] Implement file → parser routing by extension
- [ ] Implement directory walker with skip list
- [ ] Upsert logic: delete existing symbols for file path before re-inserting (idempotent)
- [ ] Batch embed symbols (call `embed_texts` with all bodies at once)

**Validation:** `index_codebase("server/", project_id)` completes without error and rows appear in `code_symbols`.

---

### Task 7: Impact Analysis Engine (`server/impact_analysis.py`)

Graph traversal to find all symbols affected by a change.

```python
def analyze_impact(
    symbol_name: str,
    project_id: str,
    depth: int = 3
) -> list[dict]:
    # 1. Find symbol by exact name OR semantic search (embed query → cosine)
    # 2. BFS/DFS traverse code_edges: find all from_symbol_id where to_symbol_name matches
    # 3. For each impacted symbol, fetch file_path + start_line + end_line
    # 4. Return sorted list: { symbol_name, file_path, start_line, edge_type, depth }
```

Traversal strategy:
- Start from the target symbol
- Level 1: direct callers (`calls` edges pointing to target)
- Level 2: callers of callers
- Continue up to `depth` (default 3)
- Also include `imports` edges (files that import the changed module)

- [ ] Implement BFS traversal over `code_edges`
- [ ] Semantic fallback: if exact name not found, embed query and find closest symbol
- [ ] Deduplicate results (same symbol reached via multiple paths)
- [ ] Format output as `file_path:line_number — symbol_name (via: edge_type)`

**Validation:** After indexing, `analyze_impact("embed_texts", project_id)` returns `embed_text`, `embed_chunks_with_context`, and the `ingest_file` tool as impacted symbols.

---

### Task 8: MCP Tools (`server/main.py`)

Add two new tools to the FastMCP server.

#### `index_codebase(path, project, extensions=None)`

```python
@mcp.tool()
def index_codebase(
    path: str,
    project: str,
    extensions: list[str] | None = None
) -> str:
    """
    Index a codebase directory into the code intelligence graph.
    Parses all source files and extracts symbols and their relationships.

    Args:
        path: Absolute or relative path to the codebase root
        project: Project name to associate this index with
        extensions: File extensions to index (default: .py .ts .tsx .js .jsx .sql)
    """
```

#### `analyze_impact(symbol, project, depth=3)`

```python
@mcp.tool()
def analyze_impact(
    symbol: str,
    project: str,
    depth: int = 3
) -> str:
    """
    Analyze the blast radius of changing a symbol (function, class, schema).
    Returns a list of all code locations that would be impacted by the change.

    Args:
        symbol: Function/class/method name or natural language description
        project: Project to search within
        depth: How many levels of callers to traverse (default: 3)
    """
```

- [ ] Add `index_codebase` tool
- [ ] Add `analyze_impact` tool
- [ ] Return formatted markdown with `file:line — symbol` per impacted location

**Validation:** Claude Code can call both tools via MCP. `analyze_impact("embed_texts", "RAG Masterclass")` returns readable impact list.

---

### Task 9: Git Post-Commit Hook

Auto re-indexes only files changed in the commit.

```bash
#!/bin/bash
# .git/hooks/post-commit

REPO_ROOT=$(git rev-parse --show-toplevel)
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD)

for file in $CHANGED_FILES; do
    ext="${file##*.}"
    if [[ "$ext" =~ ^(py|ts|tsx|js|jsx|sql)$ ]]; then
        echo "[code-index] Re-indexing $file"
        cd "$REPO_ROOT" && source server/venv/bin/activate && \
        python -c "
from server.code_indexer import index_file
from server.db import get_project_id_by_name
project_id = get_project_id_by_name('$PROJECT_NAME')
result = index_file('$file', project_id)
print(result)
"
    fi
done
```

- [ ] Create `scripts/install_hooks.sh` that copies the hook and makes it executable
- [ ] Support `PROJECT_NAME` env var (read from `.env`)
- [ ] Handle first commit edge case (no `HEAD~1`)
- [ ] Make hook non-blocking (run in background, don't slow down commits)

**Validation:** Modify a `.py` file, commit it, observe `code_symbols` rows updated for that file only.

---

## Definition of Done

- [ ] `code_symbols` and `code_edges` tables exist in Supabase
- [ ] Python, TypeScript, SQL, MongoDB parsers all operational
- [ ] `index_codebase("server/", "RAG Masterclass")` indexes all Python files successfully
- [ ] `analyze_impact("embed_texts", "RAG Masterclass")` returns correct impact list with file:line
- [ ] Git post-commit hook auto re-indexes on change
- [ ] Natural language query "what breaks if I change embed_texts?" routes to `analyze_impact` via Claude Code

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Plan created, status: Backlog |
