-- Create read-only role
create role sql_reader with login password 'sql_reader_password';

-- Grant read access to public schema
grant usage on schema public to sql_reader;
grant select on all tables in schema public to sql_reader;
alter default privileges in schema public grant select on tables to sql_reader;
