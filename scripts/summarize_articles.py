#!/usr/bin/env python3
"""
AI Article Summarizer - Inshorts Style (v2)
============================================
This script uses Google Gemini AI to summarize APPROVED articles
into exactly 60 words, creating Inshorts-style news shorts.

IMPORTANT: Only processes articles that passed the content filter!

Workflow:
1. Fetch APPROVED + UNSUMMARIZED articles from Supabase
2. Use Gemini to create 60-word summaries
3. Update articles with summaries in database
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import google.generativeai as genai
from supabase import create_client, Client

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Processing settings
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 1.1
MAX_RETRIES = 3

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SUMMARIZATION PROMPT
# =============================================================================

SUMMARY_PROMPT = """You are a professional news content writer for a mobile news app like Inshorts.

Your task: Summarize the following news article into EXACTLY 60 words.

Rules:
1. MUST be exactly 55-65 words (aim for 60)
2. Write in a journalistic, informative tone
3. Include the most important facts: WHO, WHAT, WHEN, WHERE, WHY
4. Start with the key news point, not "The article discusses..."
5. Use simple, clear English language
6. Write as a single flowing paragraph
7. Do NOT include phrases like "In summary" or "This article"
8. Make it engaging and complete - reader should understand the full story

Article Title: {title}

Article Content:
{content}

Write the 60-word summary now (no preamble, just the summary):"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_config() -> bool:
    errors = []
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is not set")
    if not SUPABASE_SERVICE_KEY:
        errors.append("SUPABASE_SERVICE_KEY is not set")
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return False
    return True


def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def setup_gemini() -> genai.GenerativeModel:
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        # Use a stable, generally available text model.
        # 1.5 Flash is returning 404 for v1beta; 1.0 Pro remains supported.
        model_name="gemini-1.0-pro",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 200,
        }
    )


def count_words(text: str) -> int:
    return len(text.split())


def generate_summary(model: genai.GenerativeModel, title: str, content: str) -> Optional[str]:
    if not content or len(content.strip()) < 50:
        return None
    
    if len(content) > 5000:
        content = content[:5000] + "..."
    
    prompt = SUMMARY_PROMPT.format(title=title, content=content)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            
            if response.text:
                summary = response.text.strip()
                if summary.startswith('"') and summary.endswith('"'):
                    summary = summary[1:-1]
                
                word_count = count_words(summary)
                if 50 <= word_count <= 75:
                    return summary
                else:
                    logger.warning(f"Summary has {word_count} words, retrying...")
                    continue
            
        except Exception as e:
            logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            continue
    
    return None


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def fetch_approved_unsummarized_articles(client: Client, limit: int = BATCH_SIZE) -> List[Dict]:
    """Fetches articles that are APPROVED but not yet summarized."""
    try:
        response = client.table('articles') \
            .select('id, title, description, content, url') \
            .eq('is_approved', True) \
            .eq('is_summarized', False) \
            .eq('is_deleted', False) \
            .order('fetched_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return response.data or []
    
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return []


def update_article_summary(client: Client, article_id: str, summary: str) -> bool:
    try:
        client.table('articles').update({
            'summary_60': summary,
            'is_summarized': True,
            'summary_generated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', article_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}")
        return False


def mark_article_skipped(client: Client, article_id: str) -> None:
    try:
        client.table('articles').update({
            'is_summarized': True,
            'summary_generated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', article_id).execute()
    except Exception as e:
        logger.error(f"Error marking article {article_id} as skipped: {e}")


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_articles():
    logger.info("=" * 60)
    logger.info("Starting AI Article Summarizer (Approved Articles Only)")
    logger.info("=" * 60)
    
    if not validate_config():
        logger.error("Configuration validation failed!")
        sys.exit(1)
    
    logger.info("Initializing Supabase and Gemini...")
    supabase = get_supabase_client()
    gemini_model = setup_gemini()
    
    # Only fetch APPROVED articles
    logger.info(f"Fetching up to {BATCH_SIZE} approved, unsummarized articles...")
    articles = fetch_approved_unsummarized_articles(supabase, BATCH_SIZE)
    
    if not articles:
        logger.info("No approved articles need summarization. Done!")
        return
    
    logger.info(f"Found {len(articles)} approved articles to summarize")
    
    stats = {
        'processed': 0,
        'summarized': 0,
        'skipped': 0,
        'failed': 0
    }
    
    for i, article in enumerate(articles, 1):
        article_id = article['id']
        title = article.get('title', 'Untitled')
        content = article.get('content') or article.get('description') or ''
        
        short_title = title[:50] + "..." if len(title) > 50 else title
        logger.info(f"\n[{i}/{len(articles)}] Summarizing: {short_title}")
        
        if not content or len(content.strip()) < 100:
            logger.warning(f"  Skipping - insufficient content")
            mark_article_skipped(supabase, article_id)
            stats['skipped'] += 1
            continue
        
        summary = generate_summary(gemini_model, title, content)
        
        if summary:
            if update_article_summary(supabase, article_id, summary):
                word_count = count_words(summary)
                logger.info(f"  ✓ Summarized ({word_count} words)")
                stats['summarized'] += 1
            else:
                logger.error(f"  ✗ Failed to save summary")
                stats['failed'] += 1
        else:
            logger.warning(f"  ✗ Could not generate summary")
            mark_article_skipped(supabase, article_id)
            stats['skipped'] += 1
        
        stats['processed'] += 1
        time.sleep(RATE_LIMIT_DELAY)
    
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARIZATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Processed:  {stats['processed']}")
    logger.info(f"  Summarized: {stats['summarized']}")
    logger.info(f"  Skipped:    {stats['skipped']}")
    logger.info(f"  Failed:     {stats['failed']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    process_articles()
