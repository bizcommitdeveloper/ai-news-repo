-- ============================================================================
-- Row Level Security (RLS) Policies for AI News Aggregator
-- ============================================================================
-- These policies control who can read/write data in your Supabase tables
-- Run this AFTER schema.sql in Supabase SQL Editor
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE fetch_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ARTICLES TABLE POLICIES
-- ============================================================================

-- Public read access: Anyone can read non-deleted articles
-- This allows your frontend to fetch articles without authentication
CREATE POLICY "Public can read active articles"
    ON articles
    FOR SELECT
    USING (is_deleted = false);

-- Service role can do everything (for GitHub Actions)
-- The service_role key bypasses RLS, but this is explicit for clarity
CREATE POLICY "Service role has full access to articles"
    ON articles
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- SOURCES TABLE POLICIES
-- ============================================================================

-- Public read access: Anyone can see available sources
CREATE POLICY "Public can read active sources"
    ON sources
    FOR SELECT
    USING (is_active = true);

-- Service role can manage sources
CREATE POLICY "Service role has full access to sources"
    ON sources
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- FETCH_LOGS TABLE POLICIES
-- ============================================================================

-- Only service role can access fetch logs (internal use only)
CREATE POLICY "Service role has full access to fetch_logs"
    ON fetch_logs
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- STORAGE_METRICS TABLE POLICIES
-- ============================================================================

-- Only service role can access storage metrics
CREATE POLICY "Service role has full access to storage_metrics"
    ON storage_metrics
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- OPTIONAL: Authenticated User Policies
-- ============================================================================
-- Uncomment these if you want to add user authentication later

-- -- Authenticated users can read all articles
-- CREATE POLICY "Authenticated users can read articles"
--     ON articles
--     FOR SELECT
--     USING (auth.role() = 'authenticated');

-- -- Authenticated users can read fetch logs
-- CREATE POLICY "Authenticated users can read fetch_logs"
--     ON fetch_logs
--     FOR SELECT
--     USING (auth.role() = 'authenticated');

-- ============================================================================
-- GRANT STATEMENTS
-- ============================================================================
-- These ensure the anon key can access public data

GRANT SELECT ON articles TO anon;
GRANT SELECT ON sources TO anon;
GRANT SELECT ON active_articles TO anon;
GRANT SELECT ON fetch_statistics TO anon;

-- Service role gets full access
GRANT ALL ON articles TO service_role;
GRANT ALL ON sources TO service_role;
GRANT ALL ON fetch_logs TO service_role;
GRANT ALL ON storage_metrics TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;
