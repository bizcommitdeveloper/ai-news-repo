"""
Configuration settings for AI News Aggregator
==============================================
This file contains all configurable parameters for the news aggregation system.
Modify these values to adjust behavior according to your needs.
"""

import os
from typing import List

# =============================================================================
# SUPABASE CONNECTION
# =============================================================================
# These are loaded from environment variables (GitHub Secrets)
# Never hardcode credentials in this file!

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Optional: NewsAPI.org key for additional news sources
NEWS_API_KEY: str = os.environ.get("NEWS_API_KEY", "")

# =============================================================================
# DATA RETENTION SETTINGS
# =============================================================================
# These settings determine how much data we keep to stay within free tier limits

# Maximum age of articles in days before they're purged
# With 6-hour fetch intervals, 30 days ≈ 120 fetch cycles
MAX_ARTICLE_AGE_DAYS: int = 30

# Maximum number of articles to keep regardless of age
# This is a hard cap to prevent storage overflow
# At ~5KB per article, 1000 articles ≈ 5MB (well under 500MB limit)
MAX_ARTICLES_COUNT: int = 1000

# How long to keep fetch logs (for debugging)
LOG_RETENTION_DAYS: int = 7

# How long to keep storage metrics history
METRICS_RETENTION_DAYS: int = 30

# =============================================================================
# STORAGE THRESHOLDS
# =============================================================================
# These percentages trigger warnings when storage approaches limits

# Storage warning threshold (80% of 500MB = 400MB)
STORAGE_WARNING_PERCENT: int = 80

# Storage critical threshold (90% of 500MB = 450MB)
STORAGE_CRITICAL_PERCENT: int = 90

# Supabase free tier storage limit in bytes (500 MB)
STORAGE_LIMIT_BYTES: int = 500 * 1024 * 1024

# =============================================================================
# FETCH SETTINGS
# =============================================================================

# Maximum number of articles to fetch per source per run
# Prevents overwhelming the database during initial setup
MAX_ARTICLES_PER_SOURCE: int = 50

# Timeout for HTTP requests in seconds
REQUEST_TIMEOUT: int = 30

# User agent string for HTTP requests
USER_AGENT: str = "AI-News-Aggregator/1.0 (GitHub Actions; +https://github.com)"

# Maximum content length to store (in characters)
# Truncate very long articles to save space
MAX_CONTENT_LENGTH: int = 10000

# Maximum description length (in characters)
MAX_DESCRIPTION_LENGTH: int = 1000

# =============================================================================
# CATEGORY MAPPINGS
# =============================================================================
# Keywords used to automatically categorize articles

CATEGORY_KEYWORDS: dict = {
    "machine-learning": [
        "machine learning", "ml ", "neural network", "deep learning",
        "transformer", "llm", "large language model", "training model"
    ],
    "generative-ai": [
        "generative ai", "gen ai", "chatgpt", "gpt-4", "gpt-5", "claude",
        "midjourney", "dall-e", "stable diffusion", "text-to-image",
        "image generation", "content generation"
    ],
    "robotics": [
        "robot", "robotics", "automation", "autonomous", "humanoid",
        "boston dynamics", "industrial robot"
    ],
    "computer-vision": [
        "computer vision", "image recognition", "object detection",
        "facial recognition", "visual ai", "image processing"
    ],
    "nlp": [
        "natural language", "nlp", "text analysis", "sentiment analysis",
        "speech recognition", "voice ai", "conversational ai"
    ],
    "ethics": [
        "ai ethics", "bias", "fairness", "responsible ai", "ai safety",
        "alignment", "regulation", "governance", "privacy"
    ],
    "research": [
        "research", "paper", "study", "breakthrough", "discovery",
        "arxiv", "peer-reviewed", "publication"
    ],
    "industry": [
        "startup", "funding", "investment", "acquisition", "partnership",
        "enterprise", "business", "market", "valuation"
    ],
    "hardware": [
        "gpu", "tpu", "chip", "nvidia", "semiconductor", "hardware",
        "processor", "computing power", "inference"
    ]
}

# Default category if no keywords match
DEFAULT_CATEGORY: str = "general"

# =============================================================================
# RSS FEED PROCESSING
# =============================================================================

# Fields to extract from RSS entries (in order of preference)
RSS_TITLE_FIELDS: List[str] = ["title"]
RSS_DESCRIPTION_FIELDS: List[str] = ["summary", "description", "content"]
RSS_CONTENT_FIELDS: List[str] = ["content", "content:encoded", "summary"]
RSS_DATE_FIELDS: List[str] = ["published", "pubDate", "updated", "created"]
RSS_AUTHOR_FIELDS: List[str] = ["author", "dc:creator", "creator"]
RSS_IMAGE_FIELDS: List[str] = ["media_content", "enclosure", "image"]

# =============================================================================
# LOGGING
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

# Whether to print detailed fetch information
VERBOSE_LOGGING: bool = os.environ.get("VERBOSE_LOGGING", "false").lower() == "true"

# =============================================================================
# RATE LIMITING
# =============================================================================

# Delay between fetching from different sources (seconds)
# Helps prevent rate limiting from sources
FETCH_DELAY_SECONDS: float = 2.0

# Maximum concurrent requests (not currently used, for future async implementation)
MAX_CONCURRENT_REQUESTS: int = 5


def validate_config() -> bool:
    """
    Validates that required configuration is present.
    Returns True if valid, raises ValueError if not.
    """
    errors = []
    
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL environment variable is not set")
    
    if not SUPABASE_SERVICE_KEY:
        errors.append("SUPABASE_SERVICE_KEY environment variable is not set")
    
    if SUPABASE_URL and not SUPABASE_URL.startswith("https://"):
        errors.append("SUPABASE_URL must start with https://")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


def get_storage_warning_bytes() -> int:
    """Returns the byte threshold for storage warnings."""
    return int(STORAGE_LIMIT_BYTES * STORAGE_WARNING_PERCENT / 100)


def get_storage_critical_bytes() -> int:
    """Returns the byte threshold for critical storage alerts."""
    return int(STORAGE_LIMIT_BYTES * STORAGE_CRITICAL_PERCENT / 100)
