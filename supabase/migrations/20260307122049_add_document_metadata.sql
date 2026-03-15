alter table documents add column if not exists title text;
alter table documents add column if not exists summary text;
alter table documents add column if not exists topics text[];
alter table documents add column if not exists document_type text;
alter table documents add column if not exists language text default 'en';
