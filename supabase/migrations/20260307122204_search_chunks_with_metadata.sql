-- Drop the old one just in case the signature changes enough to cause issues
drop function if exists search_chunks(vector(768), int, float);

create or replace function search_chunks(
  query_embedding vector(768),
  match_count int default 5,
  match_threshold float default 0.7,
  -- text arrays drop the type length restriction, 'text[]' is valid in postgres
  filter_document_type text default null,
  filter_topics text[] default null
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  chunk_index int,
  similarity float,
  filename text,
  document_type text,
  topics text[]
)
language sql stable
as $$
  select
    c.id,
    c.document_id,
    c.content,
    c.chunk_index,
    1 - (c.embedding <=> query_embedding) as similarity,
    d.filename,
    d.document_type,
    d.topics
  from chunks c
  join documents d on d.id = c.document_id
  where 1 - (c.embedding <=> query_embedding) > match_threshold
    and (filter_document_type is null or d.document_type = filter_document_type)
    and (filter_topics is null or d.topics && filter_topics)
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
