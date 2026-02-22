# 🤖 AI News Aggregator

A fully automated AI news aggregation system built with **Supabase** and **GitHub Actions**. This system fetches AI-related news from multiple sources, stores them in a PostgreSQL database, and automatically purges old data to stay within free tier limits.

## 📋 Features

- **Automated News Fetching**: Collects AI news from RSS feeds and news APIs every 6 hours
- **Supabase Backend**: PostgreSQL database with Row Level Security and real-time subscriptions
- **Smart Data Purging**: Automatically removes articles older than 30 days to stay within free tier limits
- **Storage Monitoring**: Alerts when approaching storage limits (80% threshold)
- **RESTful API**: Auto-generated API endpoints via Supabase PostgREST
- **Real-time Updates**: WebSocket support for live news feeds

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Fetch News   │  │ Purge Old    │  │ Monitor Storage      │   │
│  │ (every 6h)   │  │ (daily)      │  │ (weekly)             │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Supabase                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   PostgreSQL Database                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │  articles   │  │  sources    │  │  fetch_logs     │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │  PostgREST API │  │  Realtime WS   │                         │
│  └────────────────┘  └────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Web Frontend (Optional)                       │
│              GitHub Pages / Vercel / Netlify                     │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Fork this Repository

Click the "Fork" button to create your own copy.

### 2. Set Up Supabase

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run the schema from `database/schema.sql`
4. Copy your project URL and API keys from **Settings > API**

### 3. Configure GitHub Secrets

Go to your repository **Settings > Secrets and variables > Actions** and add:

| Secret Name | Description |
|-------------|-------------|
| `SUPABASE_URL` | Your Supabase project URL (e.g., `https://xxxxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Service role key (has full access, keep secure!) |
| `NEWS_API_KEY` | (Optional) API key from newsapi.org for additional sources |

### 4. Enable GitHub Actions

Actions should run automatically. You can also trigger them manually from the **Actions** tab.

## 📊 Free Tier Limits & Management

### Storage Budget

| Resource | Free Limit | Our Target | Safety Margin |
|----------|------------|------------|---------------|
| Database | 500 MB | < 400 MB | 20% buffer |
| File Storage | 1 GB | 0 MB | Not used |
| Bandwidth | 2 GB/month | < 1.5 GB | 25% buffer |

### Data Retention Policy

- **Articles**: Kept for 30 days, then auto-purged
- **Fetch Logs**: Kept for 7 days
- **Maximum Articles**: ~1,000 at any time (configurable)

### Estimated Storage Usage

- Average article size: ~2-5 KB
- 1,000 articles ≈ 5 MB
- With indexes and overhead: ~20-50 MB total
- **Plenty of headroom within 500 MB limit**

## 📁 Repository Structure

```
ai-news-repo/
├── .github/
│   └── workflows/
│       ├── fetch-news.yml      # Fetches news every 6 hours
│       ├── purge-old-data.yml  # Daily cleanup job
│       └── monitor-storage.yml # Weekly storage check
├── database/
│   ├── schema.sql              # Database schema
│   ├── functions.sql           # PostgreSQL functions
│   └── policies.sql            # Row Level Security policies
├── scripts/
│   ├── fetch_news.py           # News fetching script
│   ├── purge_data.py           # Data cleanup script
│   ├── monitor_storage.py      # Storage monitoring
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Optional web frontend
│   └── index.html
└── README.md
```

## 🔧 Configuration

Edit `scripts/config.py` to customize:

```python
# Data retention settings
MAX_ARTICLE_AGE_DAYS = 30
MAX_ARTICLES_COUNT = 1000
LOG_RETENTION_DAYS = 7

# Storage thresholds
STORAGE_WARNING_PERCENT = 80
STORAGE_CRITICAL_PERCENT = 90
```

## 📡 API Endpoints

Once deployed, your news is accessible via Supabase's auto-generated REST API:

```bash
# Get latest articles
GET https://YOUR_PROJECT.supabase.co/rest/v1/articles?order=published_at.desc&limit=50

# Get articles by category
GET https://YOUR_PROJECT.supabase.co/rest/v1/articles?category=eq.machine-learning

# Search articles
GET https://YOUR_PROJECT.supabase.co/rest/v1/articles?title=ilike.*chatgpt*
```

## 🔄 Workflow Schedule

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `fetch-news.yml` | Every 6 hours | Collect new articles |
| `purge-old-data.yml` | Daily at 00:00 UTC | Remove old articles |
| `monitor-storage.yml` | Weekly on Sundays | Check storage usage |

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please open an issue first to discuss changes.
