# 🚀 Setup Guide: AI News Aggregator

This guide walks you through setting up your AI News Aggregator from scratch. By the end, you'll have a fully automated system that fetches AI news every 6 hours and publishes it to the web.

**Time required:** About 15-20 minutes

---

## Prerequisites

Before starting, make sure you have:
- A GitHub account (free)
- A Supabase account (free tier is sufficient)
- Basic familiarity with GitHub (forking repos, adding secrets)

---

## Step 1: Fork the Repository

First, create your own copy of this repository:

1. Click the **Fork** button in the top-right corner of this repository
2. Select your GitHub account as the destination
3. Wait for the fork to complete

You now have your own copy that you can configure.

---

## Step 2: Set Up Supabase

### 2.1 Create a Supabase Account

If you don't have one already:
1. Go to [supabase.com](https://supabase.com)
2. Click **Start your project** and sign up with GitHub
3. Accept the terms and authorize the app

### 2.2 Create a New Project

1. Click **New Project**
2. Fill in the details:
   - **Name:** `ai-news-aggregator` (or your preferred name)
   - **Database Password:** Generate a strong password and **save it somewhere safe**
   - **Region:** Choose the region closest to you
3. Click **Create new project**
4. Wait 2-3 minutes for the project to be provisioned

### 2.3 Set Up the Database Schema

Now we'll create the tables and functions:

1. In your Supabase project, click **SQL Editor** in the left sidebar
2. Click **New query**
3. Copy the entire contents of `database/schema.sql` from this repository
4. Paste it into the SQL editor
5. Click **Run** (or press Ctrl/Cmd + Enter)
6. You should see "Success. No rows returned" at the bottom

Next, set up the security policies:

1. Click **New query** again
2. Copy the entire contents of `database/policies.sql`
3. Paste and click **Run**

### 2.4 Get Your API Keys

You'll need two keys for GitHub Actions:

1. Go to **Settings** (gear icon in left sidebar)
2. Click **API** under Project Settings
3. You'll see:
   - **Project URL** - Copy this (looks like `https://xxxxx.supabase.co`)
   - **anon (public) key** - This is for your frontend
   - **service_role key** - Click "Reveal" to see it. **This is secret - never expose it!**

Keep this page open; you'll need these values in the next step.

---

## Step 3: Configure GitHub Secrets

GitHub Secrets securely store your Supabase credentials:

1. Go to your forked repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these secrets one by one:

| Secret Name | Value | Notes |
|-------------|-------|-------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | Your Project URL from Supabase |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJ...` | The service_role key (NOT the anon key) |
| `NEWS_API_KEY` | `your-newsapi-key` | **Optional:** Get one free at [newsapi.org](https://newsapi.org) |

**Important:** The `SUPABASE_SERVICE_KEY` is powerful - it bypasses Row Level Security. Only use it in server-side code (like GitHub Actions), never in frontend code.

---

## Step 4: Enable GitHub Actions

GitHub Actions should be enabled by default on forked repos, but let's verify:

1. Go to the **Actions** tab in your repository
2. If you see "Workflows aren't being run on this repository," click **I understand my workflows, go ahead and enable them**
3. You should now see three workflows listed:
   - Fetch AI News
   - Purge Old Data
   - Monitor Storage

---

## Step 5: Run Your First Fetch

Let's test everything by manually triggering a news fetch:

1. In the **Actions** tab, click **Fetch AI News** in the left sidebar
2. Click **Run workflow** → **Run workflow** (green button)
3. Watch the workflow run (usually takes 1-2 minutes)
4. Click into the run to see detailed logs

If successful, you should see log output like:
```
Starting AI News Fetcher
Found 8 active sources
Processing source: MIT Technology Review - AI
  Added: 15, Skipped: 0
...
```

### Verifying the Data

Let's check that articles were saved:

1. Go back to your Supabase project
2. Click **Table Editor** in the left sidebar
3. Click on the **articles** table
4. You should see rows of AI news articles!

---

## Step 6: Set Up the Frontend (Optional)

The included frontend is a simple HTML page that displays your news:

### Option A: GitHub Pages (Easiest)

1. Go to your repository **Settings** → **Pages**
2. Under "Source," select **Deploy from a branch**
3. Choose `main` branch and `/frontend` folder
4. Click **Save**
5. Wait a few minutes, then visit `https://yourusername.github.io/ai-news-repo/`

Before this will work, you need to add your Supabase credentials:

1. Edit `frontend/index.html`
2. Find these lines near the bottom:
   ```javascript
   const SUPABASE_URL = 'YOUR_SUPABASE_URL';
   const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';
   ```
3. Replace with your actual values (use the **anon** key here, not service_role!)
4. Commit and push the changes

### Option B: Other Hosting

You can also host `frontend/index.html` on:
- Netlify (drag & drop the frontend folder)
- Vercel
- Cloudflare Pages
- Any static hosting service

Just remember to update the Supabase credentials first.

---

## Step 7: Customize (Optional)

### Adjust Data Retention

Edit `scripts/config.py` to change how much data is kept:

```python
MAX_ARTICLE_AGE_DAYS = 30      # How long to keep articles
MAX_ARTICLES_COUNT = 1000      # Maximum articles to store
LOG_RETENTION_DAYS = 7         # How long to keep fetch logs
```

### Add News Sources

Add more RSS feeds by inserting into the `sources` table:

1. Go to Supabase **Table Editor** → **sources**
2. Click **Insert row**
3. Fill in:
   - `name`: The source name (e.g., "Wired AI")
   - `url`: The RSS feed URL
   - `source_type`: `rss`
   - `is_active`: `true`
   - `fetch_interval_minutes`: `360` (6 hours)

The next fetch cycle will include your new source.

### Change Fetch Schedule

Edit `.github/workflows/fetch-news.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Current: every 6 hours
  # Change to:
  - cron: '0 */3 * * *'  # Every 3 hours
  # Or:
  - cron: '0 8,20 * * *' # Twice daily at 8am and 8pm UTC
```

---

## Monitoring & Maintenance

### Weekly Storage Checks

The **Monitor Storage** workflow runs every Sunday and alerts you if storage is getting high. Check the Actions tab to see reports.

### Manual Cleanup

If you need to free up space immediately:

1. Go to **Actions** → **Purge Old Data**
2. Click **Run workflow**
3. The script will remove old articles and logs

### Troubleshooting

**Workflow failed with "SUPABASE_URL is not set"**
→ Double-check your GitHub Secrets are named exactly as shown

**No articles being fetched**
→ Some RSS feeds may be blocked or changed. Check the workflow logs for errors.

**Frontend shows "Failed to load articles"**
→ Make sure you're using the anon key (not service_role) in the frontend

---

## Cost Breakdown

This entire setup runs within free tier limits:

| Service | Free Limit | Our Usage |
|---------|------------|-----------|
| Supabase Database | 500 MB | ~20-50 MB typically |
| Supabase Bandwidth | 2 GB/month | Depends on frontend traffic |
| GitHub Actions | Unlimited (public repos) | ~10 min/day |

As long as you keep the repository public and don't store excessive data, everything stays free.

---

## Need Help?

- **GitHub Issues:** Open an issue in this repository
- **Supabase Docs:** [supabase.com/docs](https://supabase.com/docs)
- **GitHub Actions Docs:** [docs.github.com/actions](https://docs.github.com/actions)

Happy news aggregating! 🤖📰
