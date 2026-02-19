-- Module 1: App Shell
-- Tables: threads, messages
-- RLS: users only see their own data

create extension if not exists "uuid-ossp";

-- ============================================
-- THREADS TABLE
-- ============================================
create table public.threads (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null default 'New Chat',
    openai_response_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_threads_user_id on public.threads(user_id);

alter table public.threads enable row level security;

create policy "Users can view their own threads"
    on public.threads for select
    using (auth.uid() = user_id);

create policy "Users can create their own threads"
    on public.threads for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own threads"
    on public.threads for update
    using (auth.uid() = user_id);

create policy "Users can delete their own threads"
    on public.threads for delete
    using (auth.uid() = user_id);

-- ============================================
-- MESSAGES TABLE
-- ============================================
create table public.messages (
    id uuid primary key default uuid_generate_v4(),
    thread_id uuid not null references public.threads(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    openai_response_id text,
    token_usage jsonb,
    created_at timestamptz not null default now()
);

create index idx_messages_thread_id on public.messages(thread_id, created_at);

alter table public.messages enable row level security;

create policy "Users can view messages in their threads"
    on public.messages for select
    using (auth.uid() = user_id);

create policy "Users can create messages in their threads"
    on public.messages for insert
    with check (auth.uid() = user_id);

-- ============================================
-- Updated_at trigger
-- ============================================
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger set_threads_updated_at
    before update on public.threads
    for each row execute function public.update_updated_at_column();
