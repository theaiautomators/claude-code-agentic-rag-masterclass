# RAG Masterclass - Documentation Workflow

## Overview

This project uses a **structured task workflow** to ensure every feature, bug fix, and module is planned, executed, validated, and tracked. All documentation lives in `docs/` and plans live in `.agent/plans/`.

---

## The 4-Phase Development Flow

### Phase 0: Requirement Gathering (Mandatory)
1. Analyze the request for complexity and ambiguity
2. Clarify until **>90% confidence** on what needs to be built
3. Present a bulleted summary of the approach and **wait for user approval**

### Phase 1: Planning
1. Assess complexity using the indicator below:
   - **Simple** - Single-pass executable, low risk
   - **Medium** - May need iteration, some complexity
   - **Complex** - Break into sub-plans before executing
2. Create a plan + task file at `docs/02_backlog/{sequence}.{plan-name}.md`
   - Example: `1.auth-setup.md`, `2.document-ingestion.md`
   - Must include `## Definition of Done` and `## Execution Log`
3. Plans must include at least one **validation test** per task
4. When work begins, move the file from `docs/02_backlog/` → `docs/01_active/`

### Phase 2: Build & Validate
1. Execute the plan step by step
2. Update `## Execution Log` in the task file with timestamped entries
3. After completing each major step, verify with the validation test defined in the plan
4. Validation methods (pick appropriate):
   - **Automated**: Playwright for UI flows and smoke tests
   - **Manual**: Browser testing for visual/interactive verification
   - **LangSmith**: Inspect tool calls, verify exact SQL generated and chunks retrieved
5. **Review Gate**: Compare implementation vs plan. Pass → proceed. Fail → retry (max 3) or halt and ask user.
6. **Context hygiene**: If session context exceeds 50%, run `/clear` before continuing — degraded context causes loops and hallucinations.

### Phase 3: Completion & Archival
- **Completed**: All `## Definition of Done` items checked → move file from `docs/01_active/` to `docs/04_completed/` → update `docs/changelogs.md`
- **Cancelled/Blocked**: Note lessons learned → move to `docs/03_archive/`
- Update `PROGRESS.md` to reflect current module status
- **Git tag** each completed module: `v0.1` through `v0.8` (see Module Reference)

---

## Task Template Selection

| Intent | Template type |
|:-------|:-------------|
| Build a module feature | `task-feature.md` |
| Fix a bug | `task-bug.md` |
| Refactor existing code | `task-refactor.md` |
| Write/update documentation | `task-documentation.md` |
| Architectural decision | `task-brainstorm.md` |
| DB schema / data migration | `task-migration.md` |
| Testing & validation | `task-testing.md` |

---

## Task Lifecycle (Folder Structure)

```
docs/
├── 01_active/       <- In Progress / Pending Verification
├── 02_backlog/      <- Planned but not started
├── 03_archive/      <- Cancelled / obsolete / blocked
├── 04_completed/    <- Successfully finished and verified
├── 05_user-story/   <- User stories and acceptance criteria
├── 06_rules/        <- Project-specific rules and standards
└── changelogs.md    <- Running log of all changes
```

**Status flow**: `02_backlog` → `01_active` → `04_completed`
**Cancelled flow**: `01_active` → `03_archive`

> Plans and task files are the same file — created in `02_backlog`, moved to `01_active` when work starts.

---

## Naming Conventions

| Type | Format | Example |
|:-----|:-------|:--------|
| Task files | `YYMMDD-HHMMSS-<slug>.md` | `260306-143000-auth-setup.md` |
| Plan files | `{seq}.{plan-name}.md` | `1.auth-setup.md` |
| User stories | `US-{ID}-{slug}.md` | `US-001-document-upload.md` |
| Rules | `{topic}-rules.md` | `backend-rules.md` |

---

## Required Task Frontmatter

```markdown
---
id: YYMMDD-HHMMSS
type: Feature | Bug | Refactor | Documentation | Migration | Test | Analysis
module: Module 1 | Module 2 | Module 3 | ...
component: Frontend | Backend | Database | Auth | Ingestion | Retrieval | Agent | Infra
priority: P0 | P1 | P2 | P3
status: Backlog | In Progress | Pending Verification | Completed | Cancelled
---
```

---

## Changelog Standard

`docs/changelogs.md` uses [Keep a Changelog](https://keepachangelog.com/) format:
- Newest entries at top, below `## [Unreleased]`
- Entry format: `## [YYYY-MM-DD] - [Task-ID] - [Task Title]`
- Sections: `Added`, `Changed`, `Removed`, `Fixed`
- Must summarize **technical** changes (not just "completed task")

---

## Project-Specific Rules (Non-Negotiable)

These rules apply to every task in this project:

| Rule | Detail |
|:-----|:-------|
| No LLM frameworks | Raw OpenAI/OpenRouter SDK only. No LangChain, no LangGraph. |
| Structured outputs | Use Pydantic models for all LLM structured responses |
| Row-Level Security | Every Supabase table must have RLS — users see only their own data |
| MCP transport | MCP server uses stdio transport |
| Reasoning LLM | Claude via Claude Code — no separate chat/completion API key needed |
| Streaming | Chat responses via SSE (Module 9 only) |
| Realtime status | Ingestion progress updates via Supabase Realtime (Module 9 only) |
| Ingestion | Manual only — via MCP tool calls or drag-and-drop (Module 9). No connectors or automated pipelines |
| Python env | Always use `venv` for the backend |
| Planning | All plans saved to `docs/02_backlog/` before any code is written |
| Text-to-SQL security | Never use service role for SQL — use a read-only `sql_reader` Postgres user with dedicated `SQL_READER_URL` on port 6543 |

---

## Module Reference

| Module | Focus |
|:-------|:------|
| Module 1 | MCP server scaffold, Supabase verification |
| Module 2 | Document ingestion via MCP (chunking, embedding, pgvector) |
| Module 3 | Retrieval tool (vector similarity search) |
| Module 4 | Record Manager (deduplication, content hashing) |
| Module 5 | Metadata extraction (LLM-structured, filterable) |
| Module 6 | Multi-format support (PDF, DOCX, HTML, Markdown via docling) |
| Module 7 | Hybrid search + reranking (keyword + vector, RRF, cross-encoder) |
| Module 8 | Additional tools (Text-to-SQL, web search fallback) |
| Module 9 | Web Chat UI (React, FastAPI, Auth, SSE streaming) |

---

## Troubleshooting Patterns

| Symptom | Likely Cause | Fix |
|:--------|:-------------|:----|
| Zero results returned | Overly strict metadata filtering | Update system prompt to prioritize hybrid search over strict filters |
| 204 / No Content error | Sub-agent failing to resolve Document ID | Verify ID-to-filename mapping in `analyze_document` tool call |
| Agent enters a loop | Conflicting tool instructions or degraded context | `/clear` session and provide a more directive prompt |
| Slow streaming | Local model VRAM bottleneck | Switch to standard Docling pipeline or cloud LLM |
| Duplicate chunks after re-upload | Missing content hash check | Verify SHA-256 dedup logic in ingestion service |

---

## Key Files

| File | Purpose |
|:-----|:--------|
| `CLAUDE.md` | Core rules and dev flow for Claude Code |
| `PRD.md` | Full product requirements and module specs |
| `PROGRESS.md` | Module completion tracker — update as you go |
| `docs/02_backlog/` | Plans created here before work starts |
| `docs/01_active/` | Plans move here when work begins |
| `docs/workflow.md` | This file — the task and documentation workflow |
| `docs/changelogs.md` | Running technical changelog |
| `docs/06_rules/` | Detailed standards and rules per domain |
