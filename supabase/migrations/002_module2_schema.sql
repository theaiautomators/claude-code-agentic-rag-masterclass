-- Module 2: BYO Retrieval + Memory
-- Cleanup OpenAI columns, enable pgvector, create documents + chunks tables,
-- vector search function, storage bucket, realtime

-- ============================================
-- SECTION 1: Cleanup OpenAI-specific columns
-- ============================================
ALTER TABLE public.threads DROP COLUMN IF EXISTS openai_response_id;
ALTER TABLE public.messages DROP COLUMN IF EXISTS openai_response_id;

-- ============================================
-- SECTION 2: Enable pgvector extension
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- SECTION 3: Documents table
-- ============================================
CREATE TABLE public.documents (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename text NOT NULL,
    file_type text NOT NULL,
    file_size bigint NOT NULL,
    storage_path text NOT NULL,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message text,
    chunk_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_documents_status ON public.documents(status);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own documents"
    ON public.documents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own documents"
    ON public.documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents"
    ON public.documents FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own documents"
    ON public.documents FOR DELETE
    USING (auth.uid() = user_id);

-- Reuse the update_updated_at_column() trigger function from Module 1
CREATE TRIGGER set_documents_updated_at
    BEFORE UPDATE ON public.documents
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================
-- SECTION 4: Document chunks table
-- ============================================
CREATE TABLE public.document_chunks (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id uuid NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content text NOT NULL,
    chunk_index integer NOT NULL,
    embedding vector(1536),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document_id ON public.document_chunks(document_id);
CREATE INDEX idx_chunks_user_id ON public.document_chunks(user_id);
CREATE INDEX idx_chunks_embedding ON public.document_chunks
    USING hnsw (embedding vector_cosine_ops);

ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own chunks"
    ON public.document_chunks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own chunks"
    ON public.document_chunks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chunks"
    ON public.document_chunks FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- SECTION 5: Vector search function
-- ============================================
CREATE OR REPLACE FUNCTION public.search_chunks(
    query_embedding vector(1536),
    match_count integer DEFAULT 5,
    filter_user_id uuid DEFAULT NULL,
    similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    chunk_index integer,
    metadata jsonb,
    filename text,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        dc.chunk_index,
        dc.metadata,
        d.filename,
        (1 - (dc.embedding <=> query_embedding))::float AS similarity
    FROM public.document_chunks dc
    JOIN public.documents d ON d.id = dc.document_id
    WHERE dc.user_id = filter_user_id
      AND (1 - (dc.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================
-- SECTION 6: Storage bucket for documents
-- ============================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies: users can manage files in their own folder
CREATE POLICY "Users can upload to their own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'documents'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can read their own files"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'documents'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can delete their own files"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'documents'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- ============================================
-- SECTION 7: Enable Realtime for documents
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE public.documents;
