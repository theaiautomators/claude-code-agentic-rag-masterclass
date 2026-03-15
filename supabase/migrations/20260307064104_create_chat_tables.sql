create table threads (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users not null,
    title text,
    created_at timestamptz default now()
);

alter table threads enable row level security;
create policy "users see own threads" on threads
    for all using (auth.uid() = user_id);

create table messages (
    id uuid primary key default gen_random_uuid(),
    thread_id uuid references threads(id) on delete cascade not null,
    user_id uuid references auth.users not null,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    created_at timestamptz default now()
);

alter table messages enable row level security;
create policy "users see own messages" on messages
    for all using (auth.uid() = user_id);
