-- ============================================================================
-- AI News Aggregator Database Schema
-- ============================================================================
-- This schema is optimized for Supabase's free tier (500 MB limit)
-- Run this in Supabase SQL Editor to set up your database
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search optimization

-- ============================================================================
-- TABLES
-- ============================================================================

-- Sources table: Stores information about news sources (RSS feeds, APIs)
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL DEFAULT 'rss',  -- 'rss', 'api', 'scraper'
    is_active BOOLEAN DEFAULT true,
    fetch_interval_minutes INTEGER DEFAULT 360,  -- 6 hours default
    last_fetched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Articles table: Main table storing all news articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    
    -- Core article data
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash for deduplication
    
    -- Metadata
    author VARCHAR(255),
    category VARCHAR(100),
    tags TEXT[],  -- Array of tags for categorization
    image_url TEXT,
    
    -- Timestamps
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- For soft deletes (optional, helps with debugging)
    is_deleted BOOLEAN DEFAULT false
);

-- Fetch logs: Track each fetch operation for monitoring
CREATE TABLE IF NOT EXISTS fetch_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    status VARCHAR(50) DEFAULT 'running',  -- 'running', 'success', 'failed'
    articles_found INTEGER DEFAULT 0,
    articles_added INTEGER DEFAULT 0,
    articles_skipped INTEGER DEFAULT 0,  -- Duplicates
    
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Storage metrics: Track database size over time
CREATE TABLE IF NOT EXISTS storage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    
    total_size_bytes BIGINT,
    articles_count INTEGER,
    articles_size_bytes BIGINT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Strategic indexes for common queries while minimizing storage overhead

-- Articles indexes
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_is_deleted ON articles(is_deleted) WHERE is_deleted = false;

-- Full-text search index on title (uses pg_trgm for fuzzy matching)
CREATE INDEX IF NOT EXISTS idx_articles_title_trgm ON articles USING gin(title gin_trgm_ops);

-- Fetch logs indexes
CREATE INDEX IF NOT EXISTS idx_fetch_logs_created_at ON fetch_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fetch_logs_source_id ON fetch_logs(source_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for sources table
DROP TRIGGER IF EXISTS update_sources_updated_at ON sources;
CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to purge old articles (keeps last N days or max count)
CREATE OR REPLACE FUNCTION purge_old_articles(
    max_age_days INTEGER DEFAULT 30,
    max_count INTEGER DEFAULT 1000
)
RETURNS TABLE(deleted_count INTEGER, remaining_count INTEGER) AS $$
DECLARE
    deleted INTEGER := 0;
    remaining INTEGER := 0;
    cutoff_date TIMESTAMPTZ;
    excess_count INTEGER;
BEGIN
    -- Calculate cutoff date
    cutoff_date := NOW() - (max_age_days || ' days')::INTERVAL;
    
    -- Delete articles older than max_age_days
    WITH deleted_rows AS (
        DELETE FROM articles
        WHERE published_at < cutoff_date
           OR (published_at IS NULL AND created_at < cutoff_date)
        RETURNING 1
    )
    SELECT COUNT(*) INTO deleted FROM deleted_rows;
    
    -- Check if we still exceed max_count
    SELECT COUNT(*) INTO remaining FROM articles WHERE is_deleted = false;
    
    IF remaining > max_count THEN
        excess_count := remaining - max_count;
        
        -- Delete oldest articles exceeding the limit
        WITH to_delete AS (
            SELECT id FROM articles
            WHERE is_deleted = false
            ORDER BY COALESCE(published_at, created_at) ASC
            LIMIT excess_count
        ),
        deleted_excess AS (
            DELETE FROM articles
            WHERE id IN (SELECT id FROM to_delete)
            RETURNING 1
        )
        SELECT deleted + COUNT(*) INTO deleted FROM deleted_excess;
        
        remaining := max_count;
    END IF;
    
    RETURN QUERY SELECT deleted, remaining;
END;
$$ LANGUAGE plpgsql;

-- Function to purge old fetch logs
CREATE OR REPLACE FUNCTION purge_old_fetch_logs(retention_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted_rows AS (
        DELETE FROM fetch_logs
        WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL
        RETURNING 1
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted_rows;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get database storage statistics
CREATE OR REPLACE FUNCTION get_storage_stats()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT,
    total_size TEXT,
    total_size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.tablename::TEXT,
        (SELECT COUNT(*) FROM articles WHERE t.tablename = 'articles'
         UNION ALL SELECT COUNT(*) FROM sources WHERE t.tablename = 'sources'
         UNION ALL SELECT COUNT(*) FROM fetch_logs WHERE t.tablename = 'fetch_logs'
         UNION ALL SELECT COUNT(*) FROM storage_metrics WHERE t.tablename = 'storage_metrics'
         LIMIT 1) as row_count,
        pg_size_pretty(pg_total_relation_size(t.tablename::regclass)) as total_size,
        pg_total_relation_size(t.tablename::regclass) as total_size_bytes
    FROM pg_tables t
    WHERE t.schemaname = 'public'
      AND t.tablename IN ('articles', 'sources', 'fetch_logs', 'storage_metrics');
END;
$$ LANGUAGE plpgsql;

-- Function to record storage metrics
CREATE OR REPLACE FUNCTION record_storage_metrics()
RETURNS void AS $$
DECLARE
    total BIGINT;
    article_count INTEGER;
    article_size BIGINT;
BEGIN
    -- Get total database size
    SELECT pg_database_size(current_database()) INTO total;
    
    -- Get articles count and size
    SELECT COUNT(*) INTO article_count FROM articles WHERE is_deleted = false;
    SELECT pg_total_relation_size('articles'::regclass) INTO article_size;
    
    -- Insert metrics
    INSERT INTO storage_metrics (total_size_bytes, articles_count, articles_size_bytes)
    VALUES (total, article_count, article_size);
    
    -- Keep only last 30 days of metrics
    DELETE FROM storage_metrics
    WHERE measured_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for active articles (excludes soft-deleted)
CREATE OR REPLACE VIEW active_articles AS
SELECT 
    a.id,
    a.title,
    a.description,
    a.url,
    a.author,
    a.category,
    a.tags,
    a.image_url,
    a.published_at,
    a.fetched_at,
    s.name as source_name
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE a.is_deleted = false
ORDER BY a.published_at DESC NULLS LAST;

-- View for recent fetch statistics
CREATE OR REPLACE VIEW fetch_statistics AS
SELECT 
    s.name as source_name,
    COUNT(fl.id) as total_fetches,
    SUM(fl.articles_added) as total_articles_added,
    MAX(fl.completed_at) as last_successful_fetch,
    COUNT(CASE WHEN fl.status = 'failed' THEN 1 END) as failed_fetches
FROM sources s
LEFT JOIN fetch_logs fl ON s.id = fl.source_id
GROUP BY s.id, s.name;

-- ============================================================================
-- SEED DATA: Default AI News Sources
-- ============================================================================

INSERT INTO sources (name, url, source_type, fetch_interval_minutes) VALUES
    ('MIT Technology Review - AI', 'https://www.technologyreview.com/feed/', 'rss', 360),
    ('VentureBeat AI', 'https://venturebeat.com/category/ai/feed/', 'rss', 360),
    ('AI News', 'https://www.artificialintelligence-news.com/feed/', 'rss', 360),
    ('The Verge - AI', 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'rss', 360),
    ('Ars Technica - AI', 'https://feeds.arstechnica.com/arstechnica/technology-lab', 'rss', 360),
    ('Towards Data Science', 'https://towardsdatascience.com/feed', 'rss', 360),
    ('Google AI Blog', 'https://blog.google/technology/ai/rss/', 'rss', 720),
    ('OpenAI Blog', 'https://openai.com/blog/rss/', 'rss', 720)
ON CONFLICT (url) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE articles IS 'Stores all fetched AI news articles. Auto-purged after 30 days.';
COMMENT ON TABLE sources IS 'News sources (RSS feeds, APIs) that are fetched regularly.';
COMMENT ON TABLE fetch_logs IS 'Logs of each fetch operation for monitoring and debugging.';
COMMENT ON TABLE storage_metrics IS 'Historical storage usage for tracking and alerting.';
COMMENT ON FUNCTION purge_old_articles IS 'Removes old articles to stay within storage limits. Called daily by GitHub Actions.';
