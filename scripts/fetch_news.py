#!/usr/bin/env python3
"""
AI News Fetcher
===============
This script fetches AI-related news from RSS feeds and news APIs,
then stores them in Supabase. It's designed to run via GitHub Actions.

The script handles:
- Fetching from multiple RSS feeds
- Optional NewsAPI.org integration
- Deduplication via URL hashing
- Automatic categorization
- Error handling and logging
"""

import hashlib
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from html import unescape
import re

import feedparser
import requests
from supabase import create_client, Client

# Import our configuration
import config


# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_url_hash(url: str) -> str:
    """
    Creates a SHA256 hash of a URL for deduplication.
    We use hashing because URLs can be very long and indexing full URLs
    would consume significant storage space.
    """
    # Normalize URL: lowercase, remove trailing slashes, remove tracking params
    normalized = url.lower().strip().rstrip('/')
    
    # Remove common tracking parameters to catch more duplicates
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']
    for param in tracking_params:
        # Remove parameter and its value
        normalized = re.sub(rf'[?&]{param}=[^&]*', '', normalized)
    
    # Clean up any leftover ampersands or question marks
    normalized = re.sub(r'\?&', '?', normalized)
    normalized = re.sub(r'\?$', '', normalized)
    
    return hashlib.sha256(normalized.encode()).hexdigest()


def clean_html(text: str) -> str:
    """
    Removes HTML tags and cleans up text content.
    This ensures we store clean, readable text in the database.
    """
    if not text:
        return ""
    
    # Unescape HTML entities first (&amp; -> &, etc.)
    text = unescape(text)
    
    # Remove HTML tags using a simple regex
    # This is faster than BeautifulSoup for simple cleaning
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normalize whitespace: multiple spaces/newlines become single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    return text.strip()


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncates text to a maximum length, ending at a word boundary.
    This prevents storing excessively long content that wastes storage.
    """
    if not text or len(text) <= max_length:
        return text
    
    # Find the last space before the limit
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only use space if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated + "..."


def categorize_article(title: str, description: str) -> str:
    """
    Automatically assigns a category based on keywords in the title and description.
    This helps organize articles for better browsing and filtering.
    """
    # Combine title and description for keyword matching
    text = f"{title} {description}".lower()
    
    # Check each category's keywords
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category
    
    # No keywords matched, use default
    return config.DEFAULT_CATEGORY


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parses various date formats commonly found in RSS feeds.
    Returns None if parsing fails, which is fine - we'll use the fetch time instead.
    """
    if not date_str:
        return None
    
    # Common date formats in RSS feeds
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 822: "Mon, 01 Jan 2024 12:00:00 +0000"
        "%a, %d %b %Y %H:%M:%S %Z",      # With timezone name
        "%Y-%m-%dT%H:%M:%S%z",           # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",            # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",             # Simple datetime
        "%Y-%m-%d",                       # Just date
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    
    # Try feedparser's built-in date parsing as a fallback
    try:
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    
    return None


def extract_image_url(entry: Dict) -> Optional[str]:
    """
    Extracts image URL from RSS entry, checking various common locations.
    Images are optional but nice to have for better article presentation.
    """
    # Check media:content
    if 'media_content' in entry and entry['media_content']:
        for media in entry['media_content']:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image/'):
                return media.get('url')
    
    # Check enclosure
    if 'enclosures' in entry:
        for enclosure in entry['enclosures']:
            if enclosure.get('type', '').startswith('image/'):
                return enclosure.get('href') or enclosure.get('url')
    
    # Check for image in content
    if 'content' in entry:
        for content in entry.get('content', []):
            value = content.get('value', '')
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', value)
            if img_match:
                return img_match.group(1)
    
    return None


# =============================================================================
# RSS FEED FETCHING
# =============================================================================

def fetch_rss_feed(url: str, source_id: str) -> List[Dict[str, Any]]:
    """
    Fetches and parses an RSS feed, returning a list of article dictionaries.
    
    Each article dictionary contains:
    - title, description, content, url, url_hash
    - author, category, image_url
    - published_at, source_id
    """
    articles = []
    
    try:
        # Set a custom user agent to be a good citizen
        feedparser.USER_AGENT = config.USER_AGENT
        
        logger.info(f"Fetching RSS feed: {url}")
        feed = feedparser.parse(url)
        
        # Check for feed-level errors
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")
        
        # Process each entry in the feed
        for entry in feed.entries[:config.MAX_ARTICLES_PER_SOURCE]:
            try:
                # Extract required fields
                title = clean_html(entry.get('title', ''))
                if not title:
                    continue  # Skip entries without titles
                
                # Get the article URL
                article_url = entry.get('link', '')
                if not article_url:
                    continue  # Skip entries without URLs
                
                # Extract optional fields
                description = clean_html(
                    entry.get('summary', '') or entry.get('description', '')
                )
                description = truncate_text(description, config.MAX_DESCRIPTION_LENGTH)
                
                # Get full content if available
                content = ''
                if 'content' in entry:
                    for c in entry['content']:
                        content += clean_html(c.get('value', ''))
                content = truncate_text(content, config.MAX_CONTENT_LENGTH)
                
                # Parse publication date
                date_str = entry.get('published') or entry.get('updated')
                published_at = parse_date(date_str)
                
                # Build the article dictionary
                article = {
                    'source_id': source_id,
                    'title': title,
                    'description': description or None,
                    'content': content or None,
                    'url': article_url,
                    'url_hash': create_url_hash(article_url),
                    'author': entry.get('author') or entry.get('dc_creator'),
                    'category': categorize_article(title, description),
                    'image_url': extract_image_url(entry),
                    'published_at': published_at.isoformat() if published_at else None,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
        
        logger.info(f"Extracted {len(articles)} articles from {url}")
        
    except Exception as e:
        logger.error(f"Error fetching feed {url}: {e}")
    
    return articles


# =============================================================================
# NEWS API FETCHING (Optional)
# =============================================================================

def fetch_from_newsapi() -> List[Dict[str, Any]]:
    """
    Fetches AI news from NewsAPI.org (requires API key).
    This provides additional high-quality news sources beyond RSS feeds.
    
    Note: NewsAPI free tier allows 100 requests/day and only provides
    headlines, not full articles.
    """
    if not config.NEWS_API_KEY:
        logger.debug("NewsAPI key not configured, skipping")
        return []
    
    articles = []
    
    try:
        # Search for AI-related news
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'artificial intelligence OR machine learning OR ChatGPT OR AI',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': config.MAX_ARTICLES_PER_SOURCE,
            'apiKey': config.NEWS_API_KEY,
        }
        
        logger.info("Fetching from NewsAPI.org")
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            logger.error(f"NewsAPI error: {data.get('message')}")
            return []
        
        for item in data.get('articles', []):
            try:
                title = item.get('title', '')
                if not title or title == '[Removed]':
                    continue
                
                article_url = item.get('url', '')
                if not article_url:
                    continue
                
                description = item.get('description', '')
                
                # Parse the ISO date from NewsAPI
                published_at = None
                if item.get('publishedAt'):
                    try:
                        published_at = datetime.fromisoformat(
                            item['publishedAt'].replace('Z', '+00:00')
                        )
                    except ValueError:
                        pass
                
                article = {
                    'source_id': None,  # No source_id for NewsAPI articles
                    'title': clean_html(title),
                    'description': truncate_text(clean_html(description), config.MAX_DESCRIPTION_LENGTH),
                    'content': truncate_text(clean_html(item.get('content', '')), config.MAX_CONTENT_LENGTH),
                    'url': article_url,
                    'url_hash': create_url_hash(article_url),
                    'author': item.get('author'),
                    'category': categorize_article(title, description),
                    'image_url': item.get('urlToImage'),
                    'published_at': published_at.isoformat() if published_at else None,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error processing NewsAPI article: {e}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI request failed: {e}")
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
    
    return articles


# =============================================================================
# SUPABASE OPERATIONS
# =============================================================================

def get_supabase_client() -> Client:
    """Creates and returns a Supabase client using service role credentials."""
    config.validate_config()
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def get_active_sources(client: Client) -> List[Dict]:
    """Fetches all active news sources from the database."""
    response = client.table('sources').select('*').eq('is_active', True).execute()
    return response.data


def insert_articles(client: Client, articles: List[Dict]) -> Dict[str, int]:
    """
    Inserts articles into the database, handling duplicates gracefully.
    
    Returns a dictionary with counts:
    - 'added': Number of new articles inserted
    - 'skipped': Number of duplicates skipped
    """
    stats = {'added': 0, 'skipped': 0}
    
    for article in articles:
        try:
            # Use upsert with url_hash as the conflict key
            # This automatically handles duplicates by doing nothing on conflict
            response = client.table('articles').upsert(
                article,
                on_conflict='url_hash',
                ignore_duplicates=True
            ).execute()
            
            # Check if article was actually inserted (has data) or was a duplicate
            if response.data:
                stats['added'] += 1
            else:
                stats['skipped'] += 1
                
        except Exception as e:
            # Log the error but continue with other articles
            logger.error(f"Error inserting article '{article.get('title', 'Unknown')}': {e}")
            stats['skipped'] += 1
    
    return stats


def create_fetch_log(
    client: Client,
    source_id: Optional[str],
    status: str,
    articles_found: int = 0,
    articles_added: int = 0,
    articles_skipped: int = 0,
    error_message: Optional[str] = None
) -> None:
    """Records a fetch operation in the logs for monitoring."""
    try:
        client.table('fetch_logs').insert({
            'source_id': source_id,
            'status': status,
            'articles_found': articles_found,
            'articles_added': articles_added,
            'articles_skipped': articles_skipped,
            'error_message': error_message,
            'completed_at': datetime.now(timezone.utc).isoformat() if status != 'running' else None,
        }).execute()
    except Exception as e:
        logger.error(f"Error creating fetch log: {e}")


def update_source_last_fetched(client: Client, source_id: str) -> None:
    """Updates the last_fetched_at timestamp for a source."""
    try:
        client.table('sources').update({
            'last_fetched_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', source_id).execute()
    except Exception as e:
        logger.error(f"Error updating source timestamp: {e}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main entry point for the news fetching script.
    
    This function:
    1. Connects to Supabase
    2. Fetches all active sources
    3. Fetches articles from each source
    4. Inserts new articles (skipping duplicates)
    5. Logs the results
    """
    logger.info("=" * 60)
    logger.info("Starting AI News Fetcher")
    logger.info("=" * 60)
    
    # Initialize Supabase client
    try:
        client = get_supabase_client()
        logger.info("Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Track overall statistics
    total_stats = {
        'sources_processed': 0,
        'articles_found': 0,
        'articles_added': 0,
        'articles_skipped': 0,
        'errors': 0,
    }
    
    # Fetch from RSS sources
    sources = get_active_sources(client)
    logger.info(f"Found {len(sources)} active sources")
    
    for source in sources:
        source_id = source['id']
        source_url = source['url']
        source_name = source['name']
        
        logger.info(f"\nProcessing source: {source_name}")
        
        try:
            # Fetch articles from this source
            articles = fetch_rss_feed(source_url, source_id)
            
            if articles:
                # Insert into database
                stats = insert_articles(client, articles)
                
                # Update tracking
                total_stats['articles_found'] += len(articles)
                total_stats['articles_added'] += stats['added']
                total_stats['articles_skipped'] += stats['skipped']
                
                # Log success
                create_fetch_log(
                    client,
                    source_id,
                    'success',
                    articles_found=len(articles),
                    articles_added=stats['added'],
                    articles_skipped=stats['skipped']
                )
                
                logger.info(f"  Added: {stats['added']}, Skipped: {stats['skipped']}")
            else:
                create_fetch_log(client, source_id, 'success', articles_found=0)
                logger.info("  No new articles found")
            
            # Update source timestamp
            update_source_last_fetched(client, source_id)
            total_stats['sources_processed'] += 1
            
        except Exception as e:
            logger.error(f"  Error processing source: {e}")
            create_fetch_log(client, source_id, 'failed', error_message=str(e))
            total_stats['errors'] += 1
        
        # Be nice to servers: add a small delay between sources
        time.sleep(config.FETCH_DELAY_SECONDS)
    
    # Fetch from NewsAPI (if configured)
    if config.NEWS_API_KEY:
        logger.info("\nFetching from NewsAPI.org")
        try:
            newsapi_articles = fetch_from_newsapi()
            if newsapi_articles:
                stats = insert_articles(client, newsapi_articles)
                total_stats['articles_found'] += len(newsapi_articles)
                total_stats['articles_added'] += stats['added']
                total_stats['articles_skipped'] += stats['skipped']
                logger.info(f"  Added: {stats['added']}, Skipped: {stats['skipped']}")
        except Exception as e:
            logger.error(f"  NewsAPI error: {e}")
            total_stats['errors'] += 1
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("FETCH COMPLETE - Summary:")
    logger.info("=" * 60)
    logger.info(f"  Sources processed: {total_stats['sources_processed']}")
    logger.info(f"  Articles found:    {total_stats['articles_found']}")
    logger.info(f"  Articles added:    {total_stats['articles_added']}")
    logger.info(f"  Duplicates:        {total_stats['articles_skipped']}")
    logger.info(f"  Errors:            {total_stats['errors']}")
    logger.info("=" * 60)
    
    # Exit with error code if there were failures
    if total_stats['errors'] > 0 and total_stats['sources_processed'] == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
