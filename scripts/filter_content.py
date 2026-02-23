#!/usr/bin/env python3
"""
AI Content Filter - Language & Relevance Check
===============================================
This script filters articles using Google Gemini AI to:
1. Detect language (must be English)
2. Check relevance (must be AI/Tech related)
3. Assess quality (must have meaningful content)

Articles that fail the filter are marked for deletion.
Only approved articles proceed to summarization.

Runs AFTER fetch_news.py and BEFORE summarize_articles.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

import google.generativeai as genai
from supabase import create_client, Client

# =============================================================================
# CONFIGURATION
# =============================================================================

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Google Gemini AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Processing settings
BATCH_SIZE = 100  # Articles per run (filter is fast)
RATE_LIMIT_DELAY = 0.5  # Seconds between API calls
MIN_RELEVANCE_SCORE = 6  # Minimum score to approve (1-10)
MIN_CONTENT_LENGTH = 50  # Minimum characters to process

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# =============================================================================
# FILTER PROMPT - Checks Language, Relevance, Quality
# =============================================================================

FILTER_PROMPT = """You are a content filter for an AI/Technology news app.

Analyze this article and respond with a JSON object ONLY (no other text):

{
  "language": "en",
  "is_english": true,
  "relevance_score": 8,
  "is_relevant": true,
  "category": "machine-learning",
  "reason": "Brief explanation"
}

RULES:
1. language: ISO 639-1 code (en, es, zh, hi, fr, etc.)
2. is_english: true only if the article is primarily in English
3. relevance_score: 1-10 how relevant to AI/Technology
   - 10: Core AI news (OpenAI, Google AI, new models, breakthroughs)
   - 8-9: AI applications, ML research, tech industry AI
   - 6-7: General tech news with AI angle
   - 4-5: Tech news, tangentially related
   - 1-3: Off-topic (sports, politics, entertainment, non-tech)
4. is_relevant: true if relevance_score >= 6
5. category: One of [machine-learning, generative-ai, robotics, research, industry, ethics, hardware, general]
6. reason: Why approved/rejected (max 20 words)

REJECT if:
- Not in English
- About sports, entertainment, politics (unless AI-related)
- Cryptocurrency/blockchain (unless AI-related)
- Generic news not about technology
- Spam, ads, or promotional content
- Duplicate/repetitive content

Article Title: {title}

Article Content:
{content}

Respond with JSON only:"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_config() -> bool:
    """Validates required environment variables."""
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
    """Creates Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def setup_gemini() -> genai.GenerativeModel:
    """Configures and returns Gemini model."""
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.1,  # Low temperature for consistent filtering
            "top_p": 0.95,
            "max_output_tokens": 300,
        }
    )
    
    return model


def parse_filter_response(response_text: str) -> Optional[Dict]:
    """Parses the JSON response from Gemini."""
    try:
        # Clean up response - remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None


def filter_article(model: genai.GenerativeModel, title: str, content: str) -> Dict:
    """
    Filters an article using Gemini AI.
    
    Returns a dict with:
    - is_approved: bool
    - detected_language: str
    - relevance_score: int
    - filter_reason: str
    - category: str
    """
    default_result = {
        'is_approved': False,
        'detected_language': 'unknown',
        'relevance_score': 0,
        'filter_reason': 'Failed to analyze',
        'category': 'general'
    }
    
    # Skip if content too short
    if not content or len(content.strip()) < MIN_CONTENT_LENGTH:
        default_result['filter_reason'] = 'Content too short'
        return default_result
    
    # Truncate content for faster processing
    if len(content) > 2000:
        content = content[:2000] + "..."
    
    prompt = FILTER_PROMPT.format(title=title, content=content)
    
    try:
        response = model.generate_content(prompt)
        
        if response.text:
            result = parse_filter_response(response.text)
            
            if result:
                is_english = result.get('is_english', False)
                relevance_score = result.get('relevance_score', 0)
                is_relevant = result.get('is_relevant', False) and relevance_score >= MIN_RELEVANCE_SCORE
                
                return {
                    'is_approved': is_english and is_relevant,
                    'detected_language': result.get('language', 'unknown'),
                    'relevance_score': relevance_score,
                    'filter_reason': result.get('reason', 'No reason provided'),
                    'category': result.get('category', 'general')
                }
    
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        default_result['filter_reason'] = f'API error: {str(e)[:50]}'
    
    return default_result


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def fetch_unfiltered_articles(client: Client, limit: int = BATCH_SIZE) -> List[Dict]:
    """Fetches articles that haven't been filtered yet."""
    try:
        response = client.table('articles') \
            .select('id, title, description, content') \
            .eq('is_filtered', False) \
            .eq('is_deleted', False) \
            .order('fetched_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return response.data or []
    
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return []


def update_article_filter(client: Client, article_id: str, filter_result: Dict) -> bool:
    """Updates an article with filter results."""
    try:
        update_data = {
            'is_filtered': True,
            'is_approved': filter_result['is_approved'],
            'detected_language': filter_result['detected_language'],
            'relevance_score': filter_result['relevance_score'],
            'filter_reason': filter_result['filter_reason'],
        }
        
        # Update category if we have a better one
        if filter_result.get('category'):
            update_data['category'] = filter_result['category']
        
        client.table('articles').update(update_data).eq('id', article_id).execute()
        return True
    
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}")
        return False


def delete_rejected_articles(client: Client) -> int:
    """Deletes articles that were rejected by the filter (older than 1 day)."""
    try:
        # Use soft delete
        response = client.table('articles') \
            .update({'is_deleted': True}) \
            .eq('is_filtered', True) \
            .eq('is_approved', False) \
            .lt('fetched_at', (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).isoformat()) \
            .execute()
        
        return len(response.data) if response.data else 0
    
    except Exception as e:
        logger.error(f"Error deleting rejected articles: {e}")
        return 0


def get_filter_statistics(client: Client) -> Dict:
    """Gets filtering statistics."""
    try:
        # Total articles
        total = client.table('articles').select('id', count='exact').eq('is_deleted', False).execute()
        
        # Approved
        approved = client.table('articles').select('id', count='exact') \
            .eq('is_approved', True).eq('is_deleted', False).execute()
        
        # Rejected
        rejected = client.table('articles').select('id', count='exact') \
            .eq('is_filtered', True).eq('is_approved', False).eq('is_deleted', False).execute()
        
        # Pending
        pending = client.table('articles').select('id', count='exact') \
            .eq('is_filtered', False).eq('is_deleted', False).execute()
        
        return {
            'total': total.count or 0,
            'approved': approved.count or 0,
            'rejected': rejected.count or 0,
            'pending': pending.count or 0
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {'total': 0, 'approved': 0, 'rejected': 0, 'pending': 0}


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_articles():
    """Main function to filter articles."""
    logger.info("=" * 60)
    logger.info("Starting AI Content Filter")
    logger.info("=" * 60)
    logger.info(f"Minimum relevance score: {MIN_RELEVANCE_SCORE}/10")
    
    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed!")
        sys.exit(1)
    
    # Initialize clients
    logger.info("Initializing Supabase and Gemini...")
    supabase = get_supabase_client()
    gemini_model = setup_gemini()
    
    # Get initial statistics
    stats_before = get_filter_statistics(supabase)
    logger.info(f"Current stats - Total: {stats_before['total']}, Approved: {stats_before['approved']}, Pending: {stats_before['pending']}")
    
    # Fetch unfiltered articles
    logger.info(f"\nFetching up to {BATCH_SIZE} unfiltered articles...")
    articles = fetch_unfiltered_articles(supabase, BATCH_SIZE)
    
    if not articles:
        logger.info("No unfiltered articles found. Done!")
        return
    
    logger.info(f"Found {len(articles)} articles to filter")
    
    # Processing statistics
    results = {
        'processed': 0,
        'approved': 0,
        'rejected_language': 0,
        'rejected_relevance': 0,
        'failed': 0
    }
    
    # Process each article
    for i, article in enumerate(articles, 1):
        article_id = article['id']
        title = article.get('title', 'Untitled')
        content = article.get('content') or article.get('description') or ''
        
        # Truncate title for logging
        short_title = title[:40] + "..." if len(title) > 40 else title
        logger.info(f"\n[{i}/{len(articles)}] Filtering: {short_title}")
        
        # Filter the article
        filter_result = filter_article(gemini_model, title, content)
        
        # Update database
        if update_article_filter(supabase, article_id, filter_result):
            results['processed'] += 1
            
            if filter_result['is_approved']:
                results['approved'] += 1
                logger.info(f"  ✓ APPROVED ({filter_result['detected_language']}, score: {filter_result['relevance_score']}/10)")
            else:
                # Categorize rejection reason
                if filter_result['detected_language'] != 'en':
                    results['rejected_language'] += 1
                    logger.info(f"  ✗ REJECTED: Non-English ({filter_result['detected_language']})")
                else:
                    results['rejected_relevance'] += 1
                    logger.info(f"  ✗ REJECTED: {filter_result['filter_reason']}")
        else:
            results['failed'] += 1
            logger.error(f"  ✗ Failed to update article")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
    
    # Clean up old rejected articles
    logger.info("\n" + "-" * 40)
    logger.info("Cleaning up old rejected articles...")
    deleted = delete_rejected_articles(supabase)
    if deleted > 0:
        logger.info(f"  Deleted {deleted} old rejected articles")
    
    # Get final statistics
    stats_after = get_filter_statistics(supabase)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("CONTENT FILTER COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Processed:           {results['processed']}")
    logger.info(f"  ✓ Approved:          {results['approved']}")
    logger.info(f"  ✗ Rejected (lang):   {results['rejected_language']}")
    logger.info(f"  ✗ Rejected (topic):  {results['rejected_relevance']}")
    logger.info(f"  Failed:              {results['failed']}")
    logger.info("-" * 40)
    logger.info("Database Status:")
    logger.info(f"  Total articles:      {stats_after['total']}")
    logger.info(f"  Approved:            {stats_after['approved']}")
    logger.info(f"  Rejected:            {stats_after['rejected']}")
    logger.info(f"  Pending filter:      {stats_after['pending']}")
    logger.info("=" * 60)
    
    # Calculate approval rate
    if results['processed'] > 0:
        approval_rate = (results['approved'] / results['processed']) * 100
        logger.info(f"\n📊 Approval Rate: {approval_rate:.1f}%")


if __name__ == "__main__":
    process_articles()
