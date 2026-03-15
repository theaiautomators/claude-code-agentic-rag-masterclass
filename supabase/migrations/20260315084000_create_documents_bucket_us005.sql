-- US-005: Create Supabase Storage bucket for raw document files
-- Creates 'documents' bucket for raw file storage
-- Bucket is private (not public)
-- RLS policy allows authenticated users to upload to their folder

-- Create storage bucket if not exists (idempotent)
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT (id) DO NOTHING;

-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if exists to recreate
DROP POLICY IF EXISTS "authenticated users upload to own folder" ON storage.objects;

-- RLS policy: Authenticated users can upload objects to their own folder
-- Users can insert objects where the bucket is 'documents' and the path starts with their user_id
CREATE POLICY "authenticated users upload to own folder"
  ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

-- RLS policy: Users can read their own objects
DROP POLICY IF EXISTS "users read own objects" ON storage.objects;
CREATE POLICY "users read own objects"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'documents'
    AND (owner_id = auth.uid() OR (storage.foldername(name))[1] = auth.uid()::text)
  );

-- RLS policy: Users can update their own objects
DROP POLICY IF EXISTS "users update own objects" ON storage.objects;
CREATE POLICY "users update own objects"
  ON storage.objects
  FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'documents'
    AND (owner_id = auth.uid() OR (storage.foldername(name))[1] = auth.uid()::text)
  );

-- RLS policy: Users can delete their own objects
DROP POLICY IF EXISTS "users delete own objects" ON storage.objects;
CREATE POLICY "users delete own objects"
  ON storage.objects
  FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'documents'
    AND (owner_id = auth.uid() OR (storage.foldername(name))[1] = auth.uid()::text)
  );

-- Grant storage bucket read access to sql_reader role
GRANT SELECT ON storage.buckets TO sql_reader;
GRANT SELECT ON storage.objects TO sql_reader;
