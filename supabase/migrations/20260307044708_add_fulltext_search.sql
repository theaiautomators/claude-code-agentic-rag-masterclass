alter table chunks add column if not exists fts tsvector
  generated always as (to_tsvector('english', content)) stored;

create index chunks_fts_idx on chunks using gin(fts);
