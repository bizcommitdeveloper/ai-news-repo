-- ============================================================================
-- COMBINED MIGRATION: All columns for AI News Pipeline v2
-- ============================================================================
-- Run this ONCE in Supabase SQL Editor
-- This adds ALL required columns for filtering and summarization
-- ============================================================================

-- ============================================================================
-- STEP 1: Add Summary Columns (for 60-word summaries)
-- ============================================================================
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS summary_60 TEXT,
ADD COLUMN IF NOT EXISTS summary_generated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_summarized BOOLEAN DEFAULT false;

-- ============================================================================
-- STEP 2: Add Filter Columns (for language/relevance filtering)
-- ============================================================================
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS is_filtered BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS filter_reason TEXT,
ADD COLUMN IF NOT EXISTS detected_language VARCHAR(10),
ADD COLUMN IF NOT EXISTS relevance_score INTEGER;

-- ============================================================================
-- STEP 3: Create Indexes for Performance
-- ============================================================================

-- Index for fetching unfiltered articles
CREATE INDEX IF NOT EXISTS idx_articles_unfiltered
ON articles(fetched_at DESC)
WHERE is_filtered = false AND is_deleted = false;

-- Index for fetching approved but unsummarized articles
CREATE INDEX IF NOT EXISTS idx_articles_approved_unsummarized
ON articles(fetched_at DESC)
WHERE is_approved = true AND is_summarized = false AND is_deleted = false;

-- Index for displaying approved & summarized articles
CREATE INDEX IF NOT EXISTS idx_articles_ready
ON articles(published_at DESC)
WHERE is_approved = true AND is_summarized = true AND is_deleted = false;

-- ============================================================================
-- STEP 4: Create View for Frontend (Only approved & summarized)
-- ============================================================================
DROP VIEW IF EXISTS news_shorts;

CREATE VIEW news_shorts AS
SELECT 
    id,
    title,
    summary_60,
    url,
    image_url,
    author,
    category,
    published_at,
    fetched_at,
    relevance_score
FROM articles
WHERE is_approved = true 
  AND is_summarized = true
  AND is_deleted = false
  AND summary_60 IS NOT NULL
ORDER BY published_at DESC NULLS LAST;

-- Grant access to the view
GRANT SELECT ON news_shorts TO anon;
GRANT SELECT ON news_shorts TO authenticated;

-- ============================================================================
-- STEP 5: Helper Functions
-- ============================================================================

-- Function to get pipeline statistics
CREATE OR REPLACE FUNCTION get_pipeline_stats()
RETURNS TABLE(
    total_articles BIGINT,
    pending_filter BIGINT,
    approved BIGINT,
    rejected BIGINT,
    pending_summary BIGINT,
    ready_to_display BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_articles,
        COUNT(*) FILTER (WHERE is_filtered = false)::BIGINT as pending_filter,
        COUNT(*) FILTER (WHERE is_approved = true)::BIGINT as approved,
        COUNT(*) FILTER (WHERE is_filtered = true AND is_approved = false)::BIGINT as rejected,
        COUNT(*) FILTER (WHERE is_approved = true AND is_summarized = false)::BIGINT as pending_summary,
        COUNT(*) FILTER (WHERE is_approved = true AND is_summarized = true AND summary_60 IS NOT NULL)::BIGINT as ready_to_display
    FROM articles
    WHERE is_deleted = false;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup rejected articles (older than 1 day)
CREATE OR REPLACE FUNCTION cleanup_rejected_articles()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM articles
        WHERE is_filtered = true 
          AND is_approved = false
          AND fetched_at < NOW() - INTERVAL '1 day'
        RETURNING 1
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 6: Set defaults for existing articles
-- ============================================================================
-- Mark all existing articles as needing filtering
UPDATE articles 
SET is_filtered = false, 
    is_approved = false,
    is_summarized = false
WHERE is_filtered IS NULL;

-- ============================================================================
-- VERIFICATION: Check all columns exist
-- ============================================================================
SELECT 
    column_name, 
    data_type,
    column_default
FROM information_schema.columns 
WHERE table_name = 'articles' 
  AND column_name IN (
    'summary_60', 
    'is_summarized', 
    'summary_generated_at',
    'is_filtered', 
    'is_approved', 
    'filter_reason', 
    'detected_language', 
    'relevance_score'
  )
ORDER BY column_name;

-- ============================================================================
-- VERIFICATION: Test the view
-- ============================================================================
SELECT COUNT(*) as ready_articles FROM news_shorts;

-- ============================================================================
-- VERIFICATION: Test the stats function
-- ============================================================================
SELECT * FROM get_pipeline_stats();