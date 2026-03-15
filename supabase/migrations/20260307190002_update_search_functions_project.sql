drop function if exists search_chunks(vector(768), int, float, text, text[]);
create or replace function search_chunks(
  query_embedding    vector(768),
  match_count        int     default 5,
  match_threshold    float   default 0.7,
  filter_document_type text  default null,
  filter_topics      text[]  default null,
  filter_project_id  uuid    default null
)
returns table (
  id uuid, document_id uuid, content text, chunk_index int,
  similarity float, filename text, document_type text, topics text[], project_id uuid
)
language sql stable as $$
  select c.id, c.document_id, c.content, c.chunk_index,
    1 - (c.embedding <=> query_embedding) as similarity,
    d.filename, d.document_type, d.topics, d.project_id
  from chunks c join documents d on d.id = c.document_id
  where 1 - (c.embedding <=> query_embedding) > match_threshold
    and (filter_document_type is null or d.document_type = filter_document_type)
    and (filter_topics         is null or d.topics && filter_topics)
    and (filter_project_id     is null or d.project_id = filter_project_id)
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

drop function if exists keyword_search_chunks(text, int);
create or replace function keyword_search_chunks(
  search_query      text,
  match_count       int  default 5,
  filter_project_id uuid default null
)
returns table (
  id uuid, document_id uuid, content text, chunk_index int,
  rank float, filename text, document_type text, topics text[], project_id uuid
)
language sql stable as $$
  select c.id, c.document_id, c.content, c.chunk_index,
    ts_rank(c.fts, websearch_to_tsquery('english', search_query)) as rank,
    d.filename, d.document_type, d.topics, d.project_id
  from chunks c join documents d on d.id = c.document_id
  where c.fts @@ websearch_to_tsquery('english', search_query)
    and (filter_project_id is null or d.project_id = filter_project_id)
  order by rank desc
  limit match_count;
$$;
