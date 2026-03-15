-- US-004: Create projects table for document categorization
-- Documents the projects table schema (already exists from 20260307190000_create_projects_table.sql)
-- Ensures unique constraint on name column
-- Grants SELECT on projects to sql_reader role for MCP tools
-- Inserts seed project for testing

-- Verify projects table structure (idempotent documentation)
-- Table should have: id (uuid primary key), name (text unique not null), description (text), created_at (timestamptz)

-- Ensure unique constraint on name exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'projects_name_key'
  ) THEN
    ALTER TABLE projects ADD CONSTRAINT projects_name_key UNIQUE (name);
  END IF;
END $$;

-- Grant SELECT on projects to sql_reader role for MCP tools
GRANT SELECT ON projects TO sql_reader;

-- Insert seed project if not exists
INSERT INTO projects (name, description)
VALUES ('claude-code-agentic-rag-masterclass', 'Main project for RAG indexing and semantic search')
ON CONFLICT (name) DO NOTHING;
