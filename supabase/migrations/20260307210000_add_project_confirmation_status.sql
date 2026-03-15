alter table documents
  drop constraint if exists documents_status_check;

alter table documents
  add constraint documents_status_check
  check (status in ('pending', 'processing', 'completed', 'failed', 'project_confirmation_needed'));
