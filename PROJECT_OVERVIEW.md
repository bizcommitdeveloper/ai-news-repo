# AI News Shorts - Complete Project Overview & Architecture

## Document Purpose
This document provides a comprehensive technical overview of the AI News Shorts project. It is designed to be fed to AI assistants (LLMs) to provide full context for debugging, enhancements, or modifications.

---

## 1. PROJECT SUMMARY

### 1.1 What Is This Project?
AI News Shorts is an **Inshorts-clone** - a mobile-first news aggregation platform that:
- Automatically fetches AI/Technology news from 65+ RSS sources
- Uses AI to filter out non-English and off-topic content
- Generates 60-word summaries using Google Gemini AI
- Displays news in a swipeable card interface (like Inshorts app)

### 1.2 Key Features
- **Automated Pipeline**: Runs every 6 hours via GitHub Actions
- **AI Content Filter**: Removes non-English and irrelevant articles
- **AI Summarization**: Creates exactly 60-word summaries
- **Mobile-First UI**: Swipeable cards with bookmark/share functionality
- **100% Free**: Uses free tiers of Supabase, GitHub Actions, and Google Gemini

### 1.3 Target Use Case
A personal or public AI news reader that automatically curates and summarizes the latest AI/ML/Tech news, filtering out noise from multi-language and off-topic sources.

---

## 2. TECHNOLOGY STACK

### 2.1 Backend & Database
| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | **Supabase (PostgreSQL)** | Stores articles, sources, logs |
| API | **Supabase PostgREST** | Auto-generated REST API |
| Auth | **Supabase RLS** | Row Level Security policies |
| Realtime | **Supabase Realtime** | WebSocket for live updates (optional) |

### 2.2 Automation & Processing
| Component | Technology | Purpose |
|-----------|------------|---------|
| CI/CD | **GitHub Actions** | Scheduled workflows |
| Language | **Python 3.11** | All processing scripts |
| AI Model | **Google Gemini 1.5 Flash** | Filtering & summarization |
| RSS Parsing | **feedparser** | Parse RSS/Atom feeds |

### 2.3 Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Hosting | **GitHub Pages** | Free static hosting |
| Framework | **Vanilla JS** | No build step required |
| Styling | **CSS3** | Custom Inshorts-style design |
| PWA | **Meta tags** | Mobile app-like experience |

### 2.4 Free Tier Limits
| Service | Free Limit | Our Usage |
|---------|------------|-----------|
| Supabase Database | 500 MB | ~30-50 MB |
| Supabase Bandwidth | 2 GB/month | ~500 MB |
| GitHub Actions | Unlimited (public repo) | ~20 min/day |
| Google Gemini | 1,500 requests/day | ~150-200/run |

---

## 3. ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GITHUB ACTIONS                                  │
│                         (Runs every 6 hours)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   JOB 1     │    │   JOB 2     │    │   JOB 3     │    │   JOB 4     │  │
│  │   FETCH     │───▶│   FILTER    │───▶│  SUMMARIZE  │───▶│   CLEANUP   │  │
│  │             │    │             │    │             │    │             │  │
│  │ fetch_news  │    │ filter_     │    │ summarize_  │    │ purge_data  │  │
│  │ .py         │    │ content.py  │    │ articles.py │    │ .py         │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │                  │
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUPABASE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PostgreSQL Database                             │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│  │  │   sources    │  │   articles   │  │      fetch_logs          │   │   │
│  │  │              │  │              │  │                          │   │   │
│  │  │ • id         │  │ • id         │  │ • id                     │   │   │
│  │  │ • name       │  │ • title      │  │ • source_id              │   │   │
│  │  │ • url        │  │ • description│  │ • status                 │   │   │
│  │  │ • is_active  │  │ • content    │  │ • articles_added         │   │   │
│  │  │              │  │ • url        │  │ • error_message          │   │   │
│  │  │              │  │ • image_url  │  │                          │   │   │
│  │  │              │  │ • category   │  └──────────────────────────┘   │   │
│  │  │              │  │ • is_filtered│                                 │   │
│  │  │              │  │ • is_approved│  ┌──────────────────────────┐   │   │
│  │  │              │  │ • is_summar- │  │    storage_metrics       │   │   │
│  │  │              │  │   ized       │  │                          │   │   │
│  │  │              │  │ • summary_60 │  │ • total_size_bytes       │   │   │
│  │  │              │  │ • relevance_ │  │ • articles_count         │   │   │
│  │  │              │  │   score      │  │                          │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │
│  │                                                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                    VIEW: news_shorts                          │   │   │
│  │  │  (Only approved + summarized articles for frontend)           │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PostgREST API                                   │   │
│  │  • GET /rest/v1/articles                                            │   │
│  │  • GET /rest/v1/news_shorts                                         │   │
│  │  • GET /rest/v1/sources                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                         (GitHub Pages)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      index.html                                      │   │
│  │                                                                      │   │
│  │  • Fetches from Supabase API                                        │   │
│  │  • Displays swipeable news cards                                    │   │
│  │  • Category filtering                                               │   │
│  │  • Bookmark/Share functionality                                     │   │
│  │  • Mobile-first responsive design                                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              END USER                                        │
│                    (Mobile/Desktop Browser)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. DATABASE SCHEMA

### 4.1 Table: `sources`
Stores RSS feed sources for news fetching.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,           -- "TechCrunch - AI"
    url TEXT NOT NULL UNIQUE,             -- RSS feed URL
    source_type VARCHAR(50) DEFAULT 'rss', -- 'rss', 'api'
    is_active BOOLEAN DEFAULT true,
    fetch_interval_minutes INTEGER DEFAULT 360,
    last_fetched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Table: `articles`
Main table storing all news articles with processing status.

```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id),
    
    -- Core content
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 for deduplication
    
    -- Metadata
    author VARCHAR(255),
    category VARCHAR(100),                  -- 'machine-learning', 'generative-ai', etc.
    tags TEXT[],
    image_url TEXT,
    
    -- Timestamps
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT false,
    
    -- FILTER STATUS (Added by AI filter)
    is_filtered BOOLEAN DEFAULT false,      -- Has been processed by filter
    is_approved BOOLEAN DEFAULT false,      -- Passed filter (English + relevant)
    filter_reason TEXT,                     -- "Non-English (hi)" or "Off-topic"
    detected_language VARCHAR(10),          -- 'en', 'hi', 'zh', etc.
    relevance_score INTEGER,                -- 1-10 relevance to AI/Tech
    
    -- SUMMARY STATUS (Added by AI summarizer)
    is_summarized BOOLEAN DEFAULT false,    -- Has been summarized
    summary_60 TEXT,                        -- The 60-word summary
    summary_generated_at TIMESTAMPTZ
);
```

### 4.3 Table: `fetch_logs`
Tracks each fetch operation for monitoring.

```sql
CREATE TABLE fetch_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'running',   -- 'running', 'success', 'failed'
    articles_found INTEGER DEFAULT 0,
    articles_added INTEGER DEFAULT 0,
    articles_skipped INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.4 View: `news_shorts`
Simplified view for frontend - only shows ready-to-display articles.

```sql
CREATE VIEW news_shorts AS
SELECT 
    id, title, summary_60, url, image_url,
    author, category, published_at, fetched_at, relevance_score
FROM articles
WHERE is_approved = true 
  AND is_summarized = true
  AND is_deleted = false
  AND summary_60 IS NOT NULL
ORDER BY published_at DESC NULLS LAST;
```

### 4.5 Article Lifecycle States

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARTICLE STATE MACHINE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FETCHED ──────────▶ FILTERED ──────────▶ SUMMARIZED ──────────▶ DISPLAY
│  (raw)               │                    (if approved)            │
│                      │                                             │
│  is_filtered=false   ├─▶ APPROVED ───────▶ is_summarized=true     │
│  is_approved=false   │   is_approved=true   summary_60="..."       │
│  is_summarized=false │                                             │
│                      └─▶ REJECTED ───────▶ AUTO-DELETED            │
│                          is_approved=false  (after 24 hours)       │
│                          filter_reason="..."                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. PIPELINE WORKFLOW

### 5.1 Complete Pipeline (Runs Every 6 Hours)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TRIGGER: Schedule (0 */6 * * *) OR Manual Dispatch                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ JOB 1: FETCH (fetch_news.py)                    ~5-10 min   │   │
│  │ ─────────────────────────────────────────────────────────── │   │
│  │ 1. Load active sources from database                        │   │
│  │ 2. For each source:                                         │   │
│  │    a. Fetch RSS feed using feedparser                       │   │
│  │    b. Parse entries (title, description, content, etc.)     │   │
│  │    c. Generate URL hash for deduplication                   │   │
│  │    d. Auto-categorize based on keywords                     │   │
│  │    e. Insert into database (skip duplicates)                │   │
│  │ 3. Log fetch statistics                                     │   │
│  │                                                             │   │
│  │ OUTPUT: ~50-200 new raw articles                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ JOB 2: FILTER (filter_content.py)               ~5-10 min   │   │
│  │ ─────────────────────────────────────────────────────────── │   │
│  │ 1. Fetch unfiltered articles (is_filtered=false)            │   │
│  │ 2. For each article:                                        │   │
│  │    a. Send to Gemini AI with filter prompt                  │   │
│  │    b. AI returns JSON: {language, relevance_score, etc.}    │   │
│  │    c. APPROVE if: English AND relevance_score >= 6          │   │
│  │    d. REJECT if: Non-English OR off-topic                   │   │
│  │    e. Update article with filter results                    │   │
│  │ 3. Delete old rejected articles (>24 hours)                 │   │
│  │                                                             │   │
│  │ OUTPUT: ~60-80% approved, ~20-40% rejected                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ JOB 3: SUMMARIZE (summarize_articles.py)        ~10-15 min  │   │
│  │ ─────────────────────────────────────────────────────────── │   │
│  │ 1. Fetch approved but unsummarized articles                 │   │
│  │ 2. For each article:                                        │   │
│  │    a. Send to Gemini AI with summary prompt                 │   │
│  │    b. AI returns 60-word summary                            │   │
│  │    c. Validate word count (55-65 acceptable)                │   │
│  │    d. Update article with summary                           │   │
│  │ 3. Mark failed articles as skipped                          │   │
│  │                                                             │   │
│  │ OUTPUT: 60-word summaries for all approved articles         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ JOB 4: CLEANUP (purge_data.py)                  ~2-3 min    │   │
│  │ ─────────────────────────────────────────────────────────── │   │
│  │ 1. Delete articles older than MAX_ARTICLE_AGE_DAYS (30)     │   │
│  │ 2. If count > MAX_ARTICLES_COUNT (1000), delete oldest      │   │
│  │ 3. Delete old fetch logs (>7 days)                          │   │
│  │ 4. Record storage metrics                                   │   │
│  │                                                             │   │
│  │ PURPOSE: Stay within Supabase 500MB free tier               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 AI Prompts Used

#### Filter Prompt (filter_content.py)
```
You are a content filter for an AI/Technology news app.

Analyze this article and respond with a JSON object ONLY:

{
  "language": "en",
  "is_english": true,
  "relevance_score": 8,
  "is_relevant": true,
  "category": "machine-learning",
  "reason": "Brief explanation"
}

RULES:
- relevance_score: 1-10 (10 = core AI news, 1 = completely off-topic)
- REJECT if: non-English, sports, entertainment, politics, crypto (unless AI-related)
- APPROVE if: English AND relevance_score >= 6
```

#### Summary Prompt (summarize_articles.py)
```
You are a professional news content writer for a mobile news app like Inshorts.

Summarize the following news article into EXACTLY 60 words.

Rules:
1. MUST be exactly 55-65 words
2. Journalistic, informative tone
3. Include WHO, WHAT, WHEN, WHERE, WHY
4. Start with key news point
5. Single flowing paragraph
6. No "In summary" or "This article discusses"
```

---

## 6. FILE STRUCTURE

```
ai-news-repo/
│
├── .github/
│   └── workflows/
│       └── ai-news-pipeline.yml    # Main workflow (fetch → filter → summarize → cleanup)
│
├── database/
│   ├── schema.sql                  # Original table definitions
│   ├── policies.sql                # Row Level Security
│   └── COMPLETE_MIGRATION.sql      # All columns for v2 (run once)
│
├── scripts/
│   ├── config.py                   # Configuration constants
│   ├── fetch_news.py               # JOB 1: RSS fetching
│   ├── filter_content.py           # JOB 2: AI language/relevance filter
│   ├── summarize_articles.py       # JOB 3: AI 60-word summaries
│   ├── purge_data.py               # JOB 4: Data cleanup
│   ├── monitor_storage.py          # Optional: Storage monitoring
│   └── requirements.txt            # Python dependencies
│
├── docs/
│   └── index.html                  # Inshorts-style frontend (GitHub Pages)
│
├── README.md                       # User documentation
└── PROJECT_OVERVIEW.md             # This file (AI context)
```

---

## 7. SCRIPT DETAILS

### 7.1 config.py
Central configuration for all scripts.

```python
# Key settings
MAX_ARTICLE_AGE_DAYS = 30          # Delete articles older than this
MAX_ARTICLES_COUNT = 1000          # Hard cap on total articles
LOG_RETENTION_DAYS = 7             # Keep fetch logs for 7 days
STORAGE_WARNING_PERCENT = 80       # Alert at 80% of 500MB
MAX_ARTICLES_PER_SOURCE = 50       # Limit per RSS feed per fetch
MIN_RELEVANCE_SCORE = 6            # Minimum to approve (1-10)

# Category keywords for auto-categorization
CATEGORY_KEYWORDS = {
    'machine-learning': ['machine learning', 'neural network', 'deep learning', ...],
    'generative-ai': ['chatgpt', 'gpt-4', 'midjourney', 'dall-e', ...],
    'robotics': ['robot', 'automation', 'autonomous', ...],
    ...
}
```

### 7.2 fetch_news.py
Fetches articles from RSS feeds.

**Input**: Active sources from database
**Output**: Raw articles inserted into `articles` table
**Key Functions**:
- `fetch_rss_feed(url)` - Parse RSS using feedparser
- `create_url_hash(url)` - SHA256 for deduplication
- `categorize_article(title, desc)` - Auto-categorize based on keywords
- `insert_articles(articles)` - Upsert to database

### 7.3 filter_content.py
AI-powered content filtering.

**Input**: Articles where `is_filtered = false`
**Output**: Updated articles with `is_approved`, `detected_language`, `relevance_score`
**Key Functions**:
- `filter_article(title, content)` - Send to Gemini, parse JSON response
- `update_article_filter(id, result)` - Save filter results
- `delete_rejected_articles()` - Cleanup rejected articles >24h old

**Filter Logic**:
```python
is_approved = is_english AND (relevance_score >= MIN_RELEVANCE_SCORE)
```

### 7.4 summarize_articles.py
AI-powered summarization.

**Input**: Articles where `is_approved = true AND is_summarized = false`
**Output**: Updated articles with `summary_60`
**Key Functions**:
- `generate_summary(title, content)` - Send to Gemini, get 60-word summary
- `count_words(text)` - Validate word count (accept 50-75)
- `update_article_summary(id, summary)` - Save summary

### 7.5 purge_data.py
Maintains storage limits.

**Purge Strategy**:
1. Delete articles older than `MAX_ARTICLE_AGE_DAYS`
2. If still over `MAX_ARTICLES_COUNT`, delete oldest
3. Delete fetch logs older than `LOG_RETENTION_DAYS`

---

## 8. FRONTEND DETAILS

### 8.1 UI Components

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    HEADER                                │   │
│  │  🤖 AI News Shorts                                       │   │
│  │  [My Feed] [Generative AI] [ML] [Research] [Industry]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    NEWS CARD                             │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │                                                 │    │   │
│  │  │              [IMAGE]                            │    │   │
│  │  │                                                 │    │   │
│  │  ├─────────────────────────────────────────────────┤    │   │
│  │  │  📱 Machine Learning                            │    │   │
│  │  │                                                 │    │   │
│  │  │  Article Title Goes Here                        │    │   │
│  │  │                                                 │    │   │
│  │  │  60-word summary text goes here. This is       │    │   │
│  │  │  the AI-generated summary that captures the    │    │   │
│  │  │  key points of the article in exactly 60       │    │   │
│  │  │  words for quick reading...                    │    │   │
│  │  │                                                 │    │   │
│  │  │  ─────────────────────────────────────────     │    │   │
│  │  │  2h ago              [☆] [↗] [→]              │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        👆 Swipe up for next story                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 API Calls (Frontend → Supabase)

```javascript
// Fetch summarized articles
const url = `${SUPABASE_URL}/rest/v1/articles?` +
    `is_summarized=eq.true&` +
    `is_approved=eq.true&` +
    `is_deleted=eq.false&` +
    `order=published_at.desc&` +
    `limit=100`;

// With category filter
const url = `${SUPABASE_URL}/rest/v1/articles?` +
    `category=eq.generative-ai&` +
    `is_summarized=eq.true&...`;

// Headers required
headers: {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
}
```

### 8.3 Swipe Gestures

```javascript
// Touch handling
touchstart  → Record startY position
touchmove   → Calculate deltaY, move card
touchend    → If deltaY < -80px: next card
             → If deltaY > 80px: previous card
             → Else: reset position

// Keyboard (desktop)
ArrowUp     → Next article
ArrowDown   → Previous article
```

---

## 9. GITHUB SECRETS REQUIRED

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `SUPABASE_URL` | Project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Service role key (full access) | Supabase Dashboard → Settings → API |
| `GEMINI_API_KEY` | Google AI API key | aistudio.google.com/app/apikey |
| `NEWS_API_KEY` | (Optional) NewsAPI.org key | newsapi.org |

---

## 10. RSS SOURCES (65+)

### Categories of Sources:
1. **Major Tech News**: TechCrunch, Wired, Verge, Ars Technica
2. **AI-Specific**: VentureBeat AI, MarkTechPost, The Decoder
3. **Company Blogs**: OpenAI, Google AI, DeepMind, Anthropic
4. **Research**: MIT News, Stanford HAI, Papers With Code
5. **Data Science**: Towards Data Science, KDnuggets
6. **Reddit**: r/MachineLearning, r/LocalLLaMA, r/ChatGPT

### Adding New Sources:
```sql
INSERT INTO sources (name, url, source_type, is_active) VALUES
('Source Name', 'https://example.com/rss.xml', 'rss', true);
```

---

## 11. ERROR HANDLING

### Common Issues & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "column does not exist" | Migration not run | Run COMPLETE_MIGRATION.sql |
| "Rate limit exceeded" | Too many Gemini calls | Reduce BATCH_SIZE |
| "No articles fetched" | RSS feeds changed | Check source URLs |
| "All articles rejected" | MIN_RELEVANCE_SCORE too high | Lower to 5 |
| "Storage limit" | Too many articles | Reduce MAX_ARTICLE_AGE_DAYS |

### Logging
All scripts log to stdout, visible in GitHub Actions logs:
```
2024-01-15 10:00:00 - INFO - Starting AI Content Filter
2024-01-15 10:00:01 - INFO - [1/50] Filtering: OpenAI announces...
2024-01-15 10:00:02 - INFO -   ✓ APPROVED (en, score: 10/10)
```

---

## 12. FUTURE ENHANCEMENTS

### Potential Improvements:
1. **User Authentication**: Supabase Auth for personalized feeds
2. **Bookmarks Sync**: Store bookmarks in database (currently localStorage)
3. **Push Notifications**: Alert users of breaking AI news
4. **Trending Algorithm**: Rank by engagement/recency
5. **Multi-language Support**: Translate approved articles
6. **Custom AI Model**: Fine-tune for better summaries
7. **Analytics Dashboard**: Track most popular categories
8. **Social Sharing**: Generate preview cards for Twitter/LinkedIn

---

## 13. CONTACT & SUPPORT

- **GitHub Issues**: For bugs and feature requests
- **Supabase Docs**: supabase.com/docs
- **Gemini Docs**: ai.google.dev/docs
- **GitHub Actions Docs**: docs.github.com/actions

---

## DOCUMENT METADATA

- **Version**: 2.0
- **Last Updated**: 2024
- **Purpose**: AI assistant context document
- **Maintainer**: Project Owner
