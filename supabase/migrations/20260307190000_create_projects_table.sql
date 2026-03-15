create table projects (
  id          uuid primary key default gen_random_uuid(),
  name        text unique not null,
  description text,
  created_at  timestamptz default now()
);
alter table projects enable row level security;
create policy "service role full access" on projects for all using (true) with check (true);
create index projects_name_idx on projects (name);
grant select on projects to sql_reader;
