# 📱 AI News Shorts v2 - With Content Filtering

Complete Inshorts-style AI news app with **intelligent content filtering** that removes non-English and off-topic articles automatically.

## 🔄 Pipeline Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AI NEWS PIPELINE                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   📥 FETCH          🔍 FILTER           ✍️ SUMMARIZE      📱 DISPLAY │
│   ─────────────    ─────────────       ─────────────    ──────────── │
│   RSS Sources  →   AI checks:      →   AI creates   →   Inshorts    │
│   65+ feeds        • English only      60-word          Mobile UI   │
│                    • AI/Tech only      summaries                    │
│                    • Quality check                                  │
│                                                                      │
│   Result:          Approved ✓          Ready for        Swipeable   │
│   Raw articles     Rejected ✗          display          cards       │
│                    (auto-deleted)                                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 🎯 What Gets Filtered Out

| Rejected | Reason |
|----------|--------|
| 🌍 Non-English | Hindi, Chinese, Spanish, etc. |
| ⚽ Sports news | Cricket, football, etc. |
| 🎬 Entertainment | Movies, celebrities |
| 💰 Crypto/NFT | Unless AI-related |
| 🗳️ Politics | Unless AI policy |
| 📢 Spam/Ads | Promotional content |

| Approved | Examples |
|----------|----------|
| 🤖 AI/ML | OpenAI, Google AI, new models |
| 🔬 Research | Papers, breakthroughs |
| 🏢 Tech Industry | Startups, funding |
| 🤖 Robotics | Automation, robots |
| ⚖️ AI Ethics | Regulation, safety |

---

## 🆓 Cost: Completely FREE

| Service | Free Limit | Pipeline Usage |
|---------|------------|----------------|
| **Google Gemini** | 1,500/day | ~150-200 (filter + summarize) |
| **Supabase** | 500 MB | ~20-50 MB |
| **GitHub Actions** | Unlimited | ~20 min/day |

---

## 🚀 Setup Instructions

### Step 1: Get Gemini API Key (FREE)

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with Google
3. Click **Create API Key**
4. Copy the key

### Step 2: Run Database Migrations

In **Supabase SQL Editor**, run these in order:

**First** - Run the original schema (if not already done):
```sql
-- From database/schema.sql in original repo
```

**Second** - Run the filter migration:
```sql
-- Paste contents of database/migration_add_filter.sql
```

This adds columns:
- `is_filtered` - Has been checked
- `is_approved` - Passed filter
- `filter_reason` - Why rejected
- `detected_language` - Language code
- `relevance_score` - 1-10 score
- `summary_60` - 60-word summary
- `is_summarized` - Has summary

### Step 3: Add GitHub Secret

Repository → Settings → Secrets → Actions → New secret:

| Name | Value |
|------|-------|
| `GEMINI_API_KEY` | Your API key from Step 1 |

(Keep existing `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`)

### Step 4: Replace Workflow File

Delete or rename your existing workflow, then add:
`.github/workflows/ai-news-pipeline.yml`

### Step 5: Update Scripts

Add these to your `scripts/` folder:
- `filter_content.py` - NEW
- `summarize_articles.py` - UPDATED
- `requirements.txt` - UPDATED

### Step 6: Deploy Frontend

Update `docs/index.html` with your Supabase credentials:
```javascript
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';
```

---

## 📁 Complete File Structure

```
your-repo/
├── .github/workflows/
│   └── ai-news-pipeline.yml     # Complete pipeline
├── database/
│   ├── schema.sql               # Original schema
│   └── migration_add_filter.sql # NEW: Filter columns
├── scripts/
│   ├── config.py                # Configuration
│   ├── fetch_news.py            # Fetch RSS
│   ├── filter_content.py        # NEW: AI filter
│   ├── summarize_articles.py    # UPDATED: Only approved
│   ├── purge_data.py            # Cleanup
│   └── requirements.txt         # Updated deps
└── docs/
    └── index.html               # Inshorts UI
```

---

## 🔍 Filter Configuration

Edit `scripts/filter_content.py` to adjust:

```python
# Minimum relevance score (1-10) to approve
MIN_RELEVANCE_SCORE = 6  # Default: 6

# Batch size per run
BATCH_SIZE = 100  # Filter is fast, can process more
```

### Relevance Score Guide

| Score | Meaning | Example |
|-------|---------|---------|
| 10 | Core AI news | "OpenAI releases GPT-5" |
| 8-9 | AI applications | "Hospital uses AI for diagnosis" |
| 6-7 | Tech with AI angle | "New smartphone with AI features" |
| 4-5 | General tech | "Apple releases new iPhone" |
| 1-3 | Off-topic | "Cricket World Cup results" |

---

## 📊 Monitoring

Check **Actions** tab for:
- Articles fetched
- Filter approval rate
- Summaries generated
- Rejection reasons

### Sample Filter Output:

```
[1/50] Filtering: OpenAI announces GPT-5 with multimodal...
  ✓ APPROVED (en, score: 10/10)

[2/50] Filtering: विराट कोहली ने क्रिकेट से संन्यास...
  ✗ REJECTED: Non-English (hi)

[3/50] Filtering: Taylor Swift concert tour dates...
  ✗ REJECTED: Off-topic entertainment content
```

---

## 🔧 Troubleshooting

**"All articles getting rejected"**
- Lower `MIN_RELEVANCE_SCORE` to 5
- Check if sources are actually AI-related

**"Non-English still appearing"**
- Run filter again (some may have been skipped)
- Check article has enough content to detect language

**"Gemini rate limit"**
- Free tier: 60/min, 1500/day
- Pipeline has built-in delays
- Reduce batch size if needed

---

## 🎉 Result

After setup, every 6 hours:

1. ✅ New articles fetched from 65+ sources
2. ✅ AI filters out non-English & off-topic
3. ✅ AI summarizes approved articles to 60 words
4. ✅ Old rejected articles auto-deleted
5. ✅ Clean, relevant AI news in your app!

Your Inshorts-style AI news app will only show **English, AI/Tech focused, 60-word summaries**. No more irrelevant content! 🎯
