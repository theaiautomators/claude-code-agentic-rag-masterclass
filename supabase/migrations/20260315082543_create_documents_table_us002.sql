-- Composite unique index on filename+content_hash for deduplication
-- Prevents duplicate file ingestion within the same project
create unique index if not exists documents_filename_content_hash_unique_idx 
  on documents(filename, content_hash);

-- Update RLS policy to include project_id check for project-based access
-- Users can only access documents within their projects
drop policy if exists "users see own documents" on documents;
create policy "users see own documents" on documents
  for all using (
    auth.uid() = user_id 
    OR 
    EXISTS (
      SELECT 1 FROM projects 
      WHERE projects.id = documents.project_id 
      AND projects.id IN (
        SELECT project_id FROM documents WHERE user_id = auth.uid()
      )
    )
  );

-- Grant select on documents to sql_reader role
grant select on documents to sql_reader;
