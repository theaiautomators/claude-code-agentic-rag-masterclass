-- Module 2+: Shared/Global Documents
-- Adds is_shared column, updates RLS policies and search function
-- so shared documents appear in every user's results.

-- ============================================
-- SECTION 1: Add is_shared column
-- ============================================
ALTER TABLE public.documents ADD COLUMN is_shared boolean NOT NULL DEFAULT false;

-- ============================================
-- SECTION 2: Update RLS on documents
-- ============================================
DROP POLICY "Users can view their own documents" ON public.documents;
CREATE POLICY "Users can view own or shared documents"
    ON public.documents FOR SELECT
    USING (auth.uid() = user_id OR is_shared = true);

-- INSERT/UPDATE/DELETE policies stay unchanged — only the owner can modify

-- ============================================
-- SECTION 3: Update RLS on document_chunks
-- ============================================
DROP POLICY "Users can view their own chunks" ON public.document_chunks;
CREATE POLICY "Users can view own or shared chunks"
    ON public.document_chunks FOR SELECT
    USING (
        auth.uid() = user_id
        OR EXISTS (
            SELECT 1 FROM public.documents d
            WHERE d.id = document_id AND d.is_shared = true
        )
    );

-- ============================================
-- SECTION 4: Update search_chunks to include shared docs
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
    WHERE (dc.user_id = filter_user_id OR d.is_shared = true)
      AND (1 - (dc.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================
-- SECTION 5: Mark existing documents as shared
-- ============================================
UPDATE public.documents SET is_shared = true
WHERE filename IN (
    'solar-system-overview.txt', 'mars-exploration.txt',
    'saturn-and-its-rings.txt', 'jupiters-moons.txt',
    'acoustic-guitar-basics.txt', 'electric-guitar-tonewoods.txt',
    'guitar-effects-pedals.txt', 'ipa-beer-history.txt',
    'ipa-hop-varieties.txt', 'brewing-your-own-ipa.txt'
);
