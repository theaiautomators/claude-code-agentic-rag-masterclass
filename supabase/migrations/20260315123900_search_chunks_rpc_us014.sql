-- US-014: Create pgvector search_chunks RPC function for vector similarity search
-- Uses cosine distance operator (<=>) with proper search_path for PostgREST compatibility
-- Accepts optional filter parameters for document_type, topics, and project_id

drop function if exists search_chunks(vector(768), int, float, text, text[], uuid);
create or replace function search_chunks(
  query_embedding    vector(768),
  match_count        int     default 5,
  match_threshold    float   default 0.7,
  filter_document_type text  default null,
  filter_topics      text[]  default null,
  filter_project_id  uuid    default null
)
returns table (
  id           uuid,
  document_id  uuid,
  content      text,
  chunk_index  int,
  similarity   float,
  filename     text,
  document_type text,
  topics       text[],
  project_id   uuid
)
language sql stable
set search_path = public, extensions
as $$
  select
    c.id,
    c.document_id,
    c.content,
    c.chunk_index,
    1 - (c.embedding <=> query_embedding) as similarity,
    d.filename,
    d.document_type,
    d.topics,
    d.project_id
  from chunks c
  join documents d on d.id = c.document_id
  where 1 - (c.embedding <=> query_embedding) > match_threshold
    and (filter_document_type is null or d.document_type = filter_document_type)
    and (filter_topics         is null or d.topics && filter_topics)
    and (filter_project_id     is null or d.project_id = filter_project_id)
  order by similarity desc
  limit match_count;
$$;

-- Grant execute permission to sql_reader role for MCP tool access
grant execute on function search_chunks to sql_reader;

-- Verify function exists by querying pg_catalog
-- This is idempotent - will not fail if function already exists
select 
  proname as function_name,
  pronargs as num_args,
  prosrc as source
from pg_catalog.pg_proc 
where proname = 'search_chunks';
