create or replace function keyword_search_chunks(
  search_query text,
  match_count int default 5
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  chunk_index int,
  rank float,
  filename text
)
language sql stable
as $$
  select
    c.id,
    c.document_id,
    c.content,
    c.chunk_index,
    ts_rank(c.fts, websearch_to_tsquery('english', search_query)) as rank,
    d.filename
  from chunks c
  join documents d on d.id = c.document_id
  where c.fts @@ websearch_to_tsquery('english', search_query)
  order by rank desc
  limit match_count;
$$;
