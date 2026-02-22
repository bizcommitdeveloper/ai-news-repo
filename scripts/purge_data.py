#!/usr/bin/env python3
"""
Data Purge Script
=================
This script removes old articles and logs to keep the database within 
Supabase's free tier storage limits (500 MB).

It implements a two-phase purging strategy:
1. Time-based: Remove articles older than MAX_ARTICLE_AGE_DAYS
2. Count-based: If still over MAX_ARTICLES_COUNT, remove oldest articles

This script should run daily via GitHub Actions to ensure storage
never exceeds the free tier limit.
"""

import logging
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

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
# SUPABASE CONNECTION
# =============================================================================

def get_supabase_client() -> Client:
    """Creates and returns a Supabase client using service role credentials."""
    config.validate_config()
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


# =============================================================================
# PURGE FUNCTIONS
# =============================================================================

def purge_old_articles(client: Client) -> Dict[str, int]:
    """
    Removes articles that exceed our retention policy.
    
    This function performs two passes:
    1. Delete all articles older than MAX_ARTICLE_AGE_DAYS
    2. If count still exceeds MAX_ARTICLES_COUNT, delete oldest articles
    
    Returns a dictionary with:
    - 'deleted_by_age': Articles deleted due to age
    - 'deleted_by_count': Articles deleted due to count overflow
    - 'remaining': Total articles remaining
    """
    stats = {
        'deleted_by_age': 0,
        'deleted_by_count': 0,
        'remaining': 0,
    }
    
    # Calculate the cutoff date for old articles
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=config.MAX_ARTICLE_AGE_DAYS)
    cutoff_iso = cutoff_date.isoformat()
    
    logger.info(f"Purging articles older than {cutoff_date.date()} ({config.MAX_ARTICLE_AGE_DAYS} days)")
    
    # =========================================================================
    # PHASE 1: Delete articles older than MAX_ARTICLE_AGE_DAYS
    # =========================================================================
    
    try:
        # First, count how many will be deleted (for logging)
        count_response = client.table('articles') \
            .select('id', count='exact') \
            .or_(f'published_at.lt.{cutoff_iso},and(published_at.is.null,created_at.lt.{cutoff_iso})') \
            .execute()
        
        old_article_count = count_response.count or 0
        
        if old_article_count > 0:
            # Delete in batches to avoid timeout issues with large deletions
            # Supabase/PostgREST has a default limit, so we delete in chunks
            batch_size = 100
            total_deleted = 0
            
            while True:
                # Get IDs of old articles
                batch_response = client.table('articles') \
                    .select('id') \
                    .or_(f'published_at.lt.{cutoff_iso},and(published_at.is.null,created_at.lt.{cutoff_iso})') \
                    .limit(batch_size) \
                    .execute()
                
                if not batch_response.data:
                    break
                
                ids_to_delete = [article['id'] for article in batch_response.data]
                
                # Delete this batch
                client.table('articles') \
                    .delete() \
                    .in_('id', ids_to_delete) \
                    .execute()
                
                total_deleted += len(ids_to_delete)
                logger.debug(f"  Deleted batch of {len(ids_to_delete)} articles")
                
                # Safety check to prevent infinite loops
                if total_deleted >= old_article_count + 100:
                    logger.warning("Safety limit reached, stopping age-based deletion")
                    break
            
            stats['deleted_by_age'] = total_deleted
            logger.info(f"  Deleted {total_deleted} articles by age")
        else:
            logger.info("  No articles exceed age limit")
    
    except Exception as e:
        logger.error(f"Error during age-based purge: {e}")
        raise
    
    # =========================================================================
    # PHASE 2: Enforce MAX_ARTICLES_COUNT limit
    # =========================================================================
    
    try:
        # Count current articles
        count_response = client.table('articles') \
            .select('id', count='exact') \
            .eq('is_deleted', False) \
            .execute()
        
        current_count = count_response.count or 0
        logger.info(f"Current article count: {current_count}")
        
        if current_count > config.MAX_ARTICLES_COUNT:
            excess_count = current_count - config.MAX_ARTICLES_COUNT
            logger.info(f"  Exceeds limit by {excess_count}, purging oldest articles")
            
            # Get the oldest articles that exceed our limit
            oldest_response = client.table('articles') \
                .select('id') \
                .eq('is_deleted', False) \
                .order('published_at', desc=False) \
                .order('created_at', desc=False) \
                .limit(excess_count) \
                .execute()
            
            if oldest_response.data:
                ids_to_delete = [article['id'] for article in oldest_response.data]
                
                # Delete these articles
                client.table('articles') \
                    .delete() \
                    .in_('id', ids_to_delete) \
                    .execute()
                
                stats['deleted_by_count'] = len(ids_to_delete)
                logger.info(f"  Deleted {len(ids_to_delete)} articles to enforce count limit")
        else:
            logger.info(f"  Within limit ({config.MAX_ARTICLES_COUNT})")
    
    except Exception as e:
        logger.error(f"Error during count-based purge: {e}")
        raise
    
    # =========================================================================
    # Final count
    # =========================================================================
    
    try:
        final_count = client.table('articles') \
            .select('id', count='exact') \
            .eq('is_deleted', False) \
            .execute()
        
        stats['remaining'] = final_count.count or 0
        
    except Exception as e:
        logger.error(f"Error getting final count: {e}")
    
    return stats


def purge_old_fetch_logs(client: Client) -> int:
    """
    Removes fetch logs older than LOG_RETENTION_DAYS.
    
    Keeping logs indefinitely would waste storage on data that's only
    useful for recent debugging. We keep 7 days by default.
    
    Returns the number of logs deleted.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=config.LOG_RETENTION_DAYS)
    cutoff_iso = cutoff_date.isoformat()
    
    logger.info(f"Purging fetch logs older than {cutoff_date.date()}")
    
    try:
        # Count logs to be deleted
        count_response = client.table('fetch_logs') \
            .select('id', count='exact') \
            .lt('created_at', cutoff_iso) \
            .execute()
        
        log_count = count_response.count or 0
        
        if log_count > 0:
            # Delete old logs
            client.table('fetch_logs') \
                .delete() \
                .lt('created_at', cutoff_iso) \
                .execute()
            
            logger.info(f"  Deleted {log_count} old fetch logs")
            return log_count
        else:
            logger.info("  No old logs to delete")
            return 0
    
    except Exception as e:
        logger.error(f"Error purging fetch logs: {e}")
        return 0


def purge_old_storage_metrics(client: Client) -> int:
    """
    Removes storage metrics older than METRICS_RETENTION_DAYS.
    
    We only need recent metrics for monitoring trends.
    
    Returns the number of metrics deleted.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=config.METRICS_RETENTION_DAYS)
    cutoff_iso = cutoff_date.isoformat()
    
    logger.info(f"Purging storage metrics older than {cutoff_date.date()}")
    
    try:
        # Delete old metrics
        response = client.table('storage_metrics') \
            .delete() \
            .lt('measured_at', cutoff_iso) \
            .execute()
        
        # Count deleted (response.data contains deleted rows)
        deleted_count = len(response.data) if response.data else 0
        
        if deleted_count > 0:
            logger.info(f"  Deleted {deleted_count} old metrics")
        else:
            logger.info("  No old metrics to delete")
        
        return deleted_count
    
    except Exception as e:
        logger.error(f"Error purging storage metrics: {e}")
        return 0


def vacuum_database(client: Client) -> None:
    """
    Optionally reclaim storage space after deletions.
    
    Note: In Supabase, VACUUM is run automatically, but we can
    call it explicitly if we want to reclaim space immediately.
    This uses the PostgreSQL function we created in the schema.
    
    For most cases, this is not necessary as Postgres handles it.
    """
    logger.info("Recording storage metrics...")
    
    try:
        # Call our storage metrics function
        client.rpc('record_storage_metrics').execute()
        logger.info("  Storage metrics recorded")
    except Exception as e:
        # This is optional, don't fail the script if it doesn't work
        logger.warning(f"  Could not record storage metrics: {e}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main entry point for the data purge script.
    
    This function:
    1. Connects to Supabase
    2. Purges old articles (by age, then by count)
    3. Purges old fetch logs
    4. Purges old storage metrics
    5. Records current storage usage
    """
    logger.info("=" * 60)
    logger.info("Starting Data Purge")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  Max article age: {config.MAX_ARTICLE_AGE_DAYS} days")
    logger.info(f"  Max article count: {config.MAX_ARTICLES_COUNT}")
    logger.info(f"  Log retention: {config.LOG_RETENTION_DAYS} days")
    logger.info("=" * 60)
    
    # Initialize Supabase client
    try:
        client = get_supabase_client()
        logger.info("Connected to Supabase\n")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Track results for summary
    results = {
        'articles_deleted_by_age': 0,
        'articles_deleted_by_count': 0,
        'articles_remaining': 0,
        'logs_deleted': 0,
        'metrics_deleted': 0,
    }
    
    # Purge old articles
    logger.info("STEP 1: Purging old articles")
    logger.info("-" * 40)
    try:
        article_stats = purge_old_articles(client)
        results['articles_deleted_by_age'] = article_stats['deleted_by_age']
        results['articles_deleted_by_count'] = article_stats['deleted_by_count']
        results['articles_remaining'] = article_stats['remaining']
    except Exception as e:
        logger.error(f"Article purge failed: {e}")
    
    # Purge old fetch logs
    logger.info("\nSTEP 2: Purging old fetch logs")
    logger.info("-" * 40)
    results['logs_deleted'] = purge_old_fetch_logs(client)
    
    # Purge old storage metrics
    logger.info("\nSTEP 3: Purging old storage metrics")
    logger.info("-" * 40)
    results['metrics_deleted'] = purge_old_storage_metrics(client)
    
    # Record current storage usage
    logger.info("\nSTEP 4: Recording storage metrics")
    logger.info("-" * 40)
    vacuum_database(client)
    
    # Print summary
    total_deleted = (
        results['articles_deleted_by_age'] + 
        results['articles_deleted_by_count'] + 
        results['logs_deleted'] + 
        results['metrics_deleted']
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("PURGE COMPLETE - Summary:")
    logger.info("=" * 60)
    logger.info(f"  Articles deleted (age):   {results['articles_deleted_by_age']}")
    logger.info(f"  Articles deleted (count): {results['articles_deleted_by_count']}")
    logger.info(f"  Articles remaining:       {results['articles_remaining']}")
    logger.info(f"  Fetch logs deleted:       {results['logs_deleted']}")
    logger.info(f"  Storage metrics deleted:  {results['metrics_deleted']}")
    logger.info("-" * 60)
    logger.info(f"  TOTAL ROWS DELETED:       {total_deleted}")
    logger.info("=" * 60)
    
    # Return success
    logger.info("\nPurge completed successfully!")


if __name__ == "__main__":
    main()
