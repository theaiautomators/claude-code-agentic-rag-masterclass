create table chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade not null,
  user_id uuid default auth.uid(),
  content text not null,
  embedding vector(768),
  chunk_index int not null,
  token_count int,
  created_at timestamptz default now()
);

alter table chunks enable row level security;
create policy "users see own chunks" on chunks
  for all using (auth.uid() = user_id);

-- Vector similarity search index
create index chunks_embedding_idx on chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);
