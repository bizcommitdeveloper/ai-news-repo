-- ============================================================================
-- EXPANDED AI NEWS SOURCES
-- ============================================================================
-- Run this in Supabase SQL Editor to add more news sources
-- Compatible with ai-news-repo schema (sources table)
-- These are verified RSS feeds covering AI, ML, tech, and research
-- ============================================================================
-- Columns: name, url, source_type, fetch_interval_minutes, is_active
-- Uses ON CONFLICT (url) to skip sources already in the schema seed
-- ============================================================================

INSERT INTO sources (name, url, source_type, fetch_interval_minutes, is_active) VALUES

-- ===========================================
-- MAJOR TECH NEWS OUTLETS
-- ===========================================
('TechCrunch - AI', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'rss', 360, true),
('Wired - AI', 'https://www.wired.com/feed/tag/ai/latest/rss', 'rss', 360, true),
('The Verge - Tech', 'https://www.theverge.com/rss/index.xml', 'rss', 360, true),
('Ars Technica - Index', 'https://feeds.arstechnica.com/arstechnica/index', 'rss', 360, true),
('Engadget', 'https://www.engadget.com/rss.xml', 'rss', 360, true),
('ZDNet - AI', 'https://www.zdnet.com/topic/artificial-intelligence/rss.xml', 'rss', 360, true),
('CNET - AI', 'https://www.cnet.com/rss/news/', 'rss', 360, true),
('Mashable - Tech', 'https://mashable.com/feeds/rss/tech', 'rss', 360, true),
('The Next Web', 'https://thenextweb.com/feed', 'rss', 360, true),
('Gizmodo', 'https://gizmodo.com/rss', 'rss', 360, true),

-- ===========================================
-- AI-SPECIFIC NEWS SITES
-- ===========================================
('Analytics India Magazine', 'https://analyticsindiamag.com/feed/', 'rss', 360, true),
('AI Trends', 'https://www.aitrends.com/feed/', 'rss', 360, true),
('MarkTechPost', 'https://www.marktechpost.com/feed/', 'rss', 360, true),
('Synced AI', 'https://syncedreview.com/feed/', 'rss', 360, true),
('The Decoder', 'https://the-decoder.com/feed/', 'rss', 360, true),
('AI Business', 'https://aibusiness.com/rss.xml', 'rss', 360, true),
('Unite.AI', 'https://www.unite.ai/feed/', 'rss', 360, true),
('DataDrivenInvestor - AI', 'https://medium.com/feed/datadriveninvestor/tagged/artificial-intelligence', 'rss', 360, true),

-- ===========================================
-- COMPANY BLOGS (Primary Sources)
-- ===========================================
('DeepMind Blog', 'https://deepmind.google/blog/rss.xml', 'rss', 720, true),
('Meta AI Blog', 'https://ai.meta.com/blog/rss/', 'rss', 720, true),
('Microsoft AI Blog', 'https://blogs.microsoft.com/ai/feed/', 'rss', 720, true),
('NVIDIA Blog - AI', 'https://blogs.nvidia.com/feed/', 'rss', 720, true),
('Amazon Science', 'https://www.amazon.science/index.rss', 'rss', 720, true),
('Apple Machine Learning', 'https://machinelearning.apple.com/rss.xml', 'rss', 720, true),
('Anthropic News', 'https://www.anthropic.com/rss.xml', 'rss', 720, true),
('Hugging Face Blog', 'https://huggingface.co/blog/feed.xml', 'rss', 720, true),

-- ===========================================
-- RESEARCH & ACADEMIC
-- ===========================================
('MIT News - AI', 'https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml', 'rss', 720, true),
('Stanford HAI', 'https://hai.stanford.edu/news/rss.xml', 'rss', 720, true),
('Berkeley AI Research', 'https://bair.berkeley.edu/blog/feed.xml', 'rss', 720, true),
('Google Research Blog', 'https://blog.research.google/feeds/posts/default?alt=rss', 'rss', 720, true),
('Papers With Code', 'https://paperswithcode.com/rss', 'rss', 360, true),
('Distill.pub', 'https://distill.pub/rss.xml', 'rss', 720, true),
('Two Minute Papers', 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg', 'rss', 720, true),

-- ===========================================
-- DATA SCIENCE & ML COMMUNITY
-- ===========================================
('KDnuggets', 'https://www.kdnuggets.com/feed', 'rss', 360, true),
('Machine Learning Mastery', 'https://machinelearningmastery.com/feed/', 'rss', 720, true),
('Analytics Vidhya', 'https://www.analyticsvidhya.com/feed/', 'rss', 360, true),
('Data Science Central', 'https://www.datasciencecentral.com/feed/', 'rss', 360, true),
('R-Bloggers', 'https://www.r-bloggers.com/feed/', 'rss', 720, true),
('Towards AI', 'https://pub.towardsai.net/feed', 'rss', 360, true),

-- ===========================================
-- BUSINESS & INDUSTRY
-- ===========================================
('Forbes - AI', 'https://www.forbes.com/ai/feed/', 'rss', 360, true),
('Harvard Business Review - AI', 'https://hbr.org/topic/subject/ai-and-machine-learning?ab=seriesnav-bigidea-topic-rss', 'rss', 720, true),
('MIT Sloan - AI', 'https://sloanreview.mit.edu/tag/artificial-intelligence/feed/', 'rss', 720, true),
('InfoWorld - AI', 'https://www.infoworld.com/category/artificial-intelligence/index.rss', 'rss', 360, true),
('SiliconANGLE - AI', 'https://siliconangle.com/category/ai/feed/', 'rss', 360, true),

-- ===========================================
-- ROBOTICS & HARDWARE
-- ===========================================
('IEEE Spectrum - Robotics', 'https://spectrum.ieee.org/feeds/topic/robotics.rss', 'rss', 720, true),
('IEEE Spectrum - AI', 'https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss', 'rss', 720, true),
('Robot Report', 'https://www.therobotreport.com/feed/', 'rss', 720, true),
('Tom''s Hardware - AI', 'https://www.tomshardware.com/feeds/all', 'rss', 360, true),

-- ===========================================
-- ETHICS & POLICY
-- ===========================================
('AI Ethics Brief', 'https://brief.montrealethics.ai/feed', 'rss', 720, true),
('Future of Life Institute', 'https://futureoflife.org/feed/', 'rss', 720, true),
('Algorithm Watch', 'https://algorithmwatch.org/en/feed/', 'rss', 720, true),

-- ===========================================
-- NEWSLETTERS & AGGREGATORS
-- ===========================================
('The Batch (deeplearning.ai)', 'https://www.deeplearning.ai/the-batch/feed/', 'rss', 720, true),
('Import AI Newsletter', 'https://importai.substack.com/feed', 'rss', 720, true),
('Last Week in AI', 'https://lastweekin.ai/feed', 'rss', 720, true),
('AI Weekly', 'https://aiweekly.substack.com/feed', 'rss', 720, true),

-- ===========================================
-- REDDIT (via RSS)
-- ===========================================
('Reddit - Machine Learning', 'https://www.reddit.com/r/MachineLearning/.rss', 'rss', 360, true),
('Reddit - Artificial', 'https://www.reddit.com/r/artificial/.rss', 'rss', 360, true),
('Reddit - LocalLLaMA', 'https://www.reddit.com/r/LocalLLaMA/.rss', 'rss', 360, true),
('Reddit - ChatGPT', 'https://www.reddit.com/r/ChatGPT/.rss', 'rss', 360, true),
('Reddit - Singularity', 'https://www.reddit.com/r/singularity/.rss', 'rss', 360, true)

ON CONFLICT (url) DO NOTHING;

-- ============================================================================
-- VERIFY: Show all active sources
-- ============================================================================
SELECT name, source_type,
       fetch_interval_minutes / 60 as fetch_hours,
       is_active
FROM sources
WHERE is_active = true
ORDER BY name;
