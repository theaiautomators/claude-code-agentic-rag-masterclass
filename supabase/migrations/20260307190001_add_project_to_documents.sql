alter table documents
  add column if not exists project_id uuid references projects(id) on delete set null;
create index if not exists documents_project_id_idx on documents (project_id);
