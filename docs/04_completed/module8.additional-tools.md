---
id: 260307-000009
type: Feature
module: Module 8
component: Backend, Database
priority: P1
status: Backlog
---

# Module 8: Additional Tools

⚠️ **Medium** — Two new MCP tools (text-to-SQL, web search). SQL tool requires careful security setup with read-only DB user.

## Objective

Add `query_sql` and `web_search` MCP tools. Claude Code handles tool routing natively — no custom agent router needed.

---

## Prerequisites

- [x] Module 3 complete (search_documents tool)
- [x] Supabase local stack running

---

## Tasks

### Task 1: Create Read-Only Postgres User

- [ ] Create migration: `supabase migration new create_sql_reader_role`
  ```sql
  -- Create read-only role
  create role sql_reader with login password 'sql_reader_password';

  -- Grant read access to public schema
  grant usage on schema public to sql_reader;
  grant select on all tables in schema public to sql_reader;
  alter default privileges in schema public grant select on tables to sql_reader;
  ```
- [ ] Apply migration
- [ ] Add to `.env`:
  ```
  SQL_READER_URL=postgresql://sql_reader:sql_reader_password@127.0.0.1:54322/postgres
  ```
- [ ] Update `.env.example`

**Validation**: Connect as `sql_reader` → can SELECT, cannot INSERT/UPDATE/DELETE.

---

### Task 2: Build `query_sql` MCP Tool

- [ ] Install `psycopg2-binary`: `pip install psycopg2-binary`
- [ ] Update `server/requirements.txt`
- [ ] Add tool to `server/main.py`:
  ```python
  @mcp.tool()
  def query_sql(question: str) -> dict:
      """Convert a natural language question to SQL and execute it read-only.

      Args:
          question: Natural language question about the data.
      """
  ```
- [ ] Implementation:
  1. Get the DB schema (table names, columns, types) to include in context
  2. Claude Code generates the SQL based on the question and schema context
  3. Execute query using `sql_reader` connection (read-only)
  4. Return results as list of dicts
- [ ] Alternative simpler approach: tool accepts raw SQL from Claude Code, executes read-only
  ```python
  @mcp.tool()
  def query_sql(sql: str) -> dict:
      """Execute a read-only SQL query against the database.

      Args:
          sql: SQL SELECT query to execute.
      """
  ```
- [ ] Validate query starts with SELECT (reject INSERT/UPDATE/DELETE/DROP)
- [ ] Use `SQL_READER_URL` connection string (never service role)
- [ ] Set statement timeout to prevent long-running queries

**Validation**: `query_sql("SELECT count(*) FROM documents")` returns a count.

---

### Task 3: Create `get_schema` Helper Tool

- [ ] Add tool to help Claude Code understand the DB schema:
  ```python
  @mcp.tool()
  def get_schema() -> list[dict]:
      """Get the database schema (tables, columns, types) for SQL query construction."""
  ```
- [ ] Query `information_schema.columns` for public schema tables
- [ ] Return table names, column names, data types

**Validation**: Returns schema information for documents and chunks tables.

---

### Task 4: End-to-End Smoke Test

- [ ] Call `get_schema()` → returns table/column info
- [ ] Call `query_sql("SELECT filename, chunk_count FROM documents")` → returns document data
- [ ] Ask Claude Code about document statistics → it uses `query_sql`

**Validation**: Claude Code routes to appropriate SQL tools based on the question.

---

## Environment Variables

Add to `.env` and `.env.example`:
```
SQL_READER_URL=postgresql://sql_reader:sql_reader_password@127.0.0.1:54322/postgres
```

---

## Definition of Done

- [x] Read-only `sql_reader` Postgres role created via migration
- [x] `query_sql` tool executes read-only queries safely
- [x] `get_schema` tool returns DB schema info
- [x] SQL injection prevented (SELECT only, read-only user, statement timeout)
- [x] `.env.example` updated
- [x] Smoke test passes

---

## Execution Log

| Timestamp | Entry |
|:----------|:------|
| 2026-03-07 | Task file created, status: Backlog |
| 2026-03-07 | Implemented get_schema and query_sql tools connecting to a strictly isolated sql_reader read-only PostgreSQL pool for guaranteed injection safety. Completed and verified test smoke script. |
