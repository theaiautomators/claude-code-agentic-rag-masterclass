-- Index on content_hash for fast deduplication lookups
create index if not exists documents_content_hash_idx on documents(content_hash);
