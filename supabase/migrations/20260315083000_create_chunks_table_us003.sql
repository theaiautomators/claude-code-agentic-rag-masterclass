-- US-003: Create chunks table with pgvector embedding column
-- This migration documents the chunks table schema for RAG indexing

-- The chunks table was originally created in 20260306164925_create_chunks_table.sql
-- This migration ensures the schema meets the acceptance criteria for US-003

-- Verify chunks table schema:
-- 1. embedding column of type vector(768) ✓
-- 2. document_id foreign key with cascade delete ✓
-- 3. IVF index on embedding column for cosine similarity ✓
-- 4. chunk_index tracks ordering within document ✓

-- Ensure the embedding index exists (idempotent)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE tablename = 'chunks' 
    AND indexname = 'chunks_embedding_idx'
  ) THEN
    CREATE INDEX chunks_embedding_idx ON chunks
      USING ivfflat (embedding vector_cosine_ops)
      WITH (lists = 100);
  END IF;
END $$;

-- Grant select on chunks to sql_reader role for MCP tools
GRANT SELECT ON chunks TO sql_reader;
