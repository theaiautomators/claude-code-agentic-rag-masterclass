create table documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid default auth.uid(),
  filename text not null,
  file_path text,
  content_hash text,
  chunk_count int default 0,
  status text default 'pending' check (status in ('pending', 'processing', 'completed', 'failed')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table documents enable row level security;
create policy "users see own documents" on documents
  for all using (auth.uid() = user_id);
