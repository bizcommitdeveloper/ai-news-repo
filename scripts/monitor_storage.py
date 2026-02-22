#!/usr/bin/env python3
"""
Storage Monitor Script
======================
This script monitors database storage usage and alerts when approaching
Supabase's free tier limit (500 MB).

It's designed to run weekly via GitHub Actions, providing early warning
before storage becomes critical. This gives you time to:
1. Adjust retention settings
2. Remove unnecessary data
3. Upgrade to a paid plan if needed

The script creates GitHub Actions workflow outputs that can be used
to trigger notifications (Slack, email, etc.) if desired.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

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
# STORAGE ANALYSIS FUNCTIONS
# =============================================================================

def get_table_sizes(client: Client) -> Dict[str, Dict[str, Any]]:
    """
    Gets the size of each table in the database.
    
    Returns a dictionary with table names as keys and size info as values:
    {
        'articles': {'rows': 1000, 'size_bytes': 5242880, 'size_human': '5 MB'},
        ...
    }
    """
    tables = {}
    table_names = ['articles', 'sources', 'fetch_logs', 'storage_metrics']
    
    for table_name in table_names:
        try:
            # Get row count
            count_response = client.table(table_name).select('*', count='exact').limit(0).execute()
            row_count = count_response.count or 0
            
            tables[table_name] = {
                'rows': row_count,
                'size_bytes': 0,  # We'll estimate this
                'size_human': 'N/A',
            }
            
        except Exception as e:
            logger.warning(f"Could not get size for table {table_name}: {e}")
            tables[table_name] = {'rows': 0, 'size_bytes': 0, 'size_human': 'Error'}
    
    return tables


def estimate_storage_usage(table_sizes: Dict) -> Dict[str, Any]:
    """
    Estimates total storage usage based on table row counts.
    
    Since we can't directly query pg_total_relation_size() from the client,
    we estimate based on average row sizes:
    - articles: ~5 KB per row (title, description, content, etc.)
    - sources: ~500 bytes per row
    - fetch_logs: ~200 bytes per row
    - storage_metrics: ~100 bytes per row
    
    These are conservative estimates; actual usage may be lower due to compression.
    """
    # Average row size estimates (in bytes)
    row_size_estimates = {
        'articles': 5 * 1024,        # 5 KB
        'sources': 500,              # 500 bytes
        'fetch_logs': 200,           # 200 bytes
        'storage_metrics': 100,      # 100 bytes
    }
    
    # Index overhead multiplier (indexes typically add 20-50% overhead)
    index_overhead = 1.3
    
    total_estimated_bytes = 0
    table_estimates = {}
    
    for table_name, sizes in table_sizes.items():
        row_size = row_size_estimates.get(table_name, 1000)
        estimated_bytes = int(sizes['rows'] * row_size * index_overhead)
        
        table_estimates[table_name] = {
            'rows': sizes['rows'],
            'estimated_bytes': estimated_bytes,
            'estimated_human': format_bytes(estimated_bytes),
        }
        
        total_estimated_bytes += estimated_bytes
    
    return {
        'tables': table_estimates,
        'total_bytes': total_estimated_bytes,
        'total_human': format_bytes(total_estimated_bytes),
        'limit_bytes': config.STORAGE_LIMIT_BYTES,
        'limit_human': format_bytes(config.STORAGE_LIMIT_BYTES),
        'usage_percent': round((total_estimated_bytes / config.STORAGE_LIMIT_BYTES) * 100, 2),
    }


def format_bytes(bytes_value: int) -> str:
    """Formats bytes into human-readable format (KB, MB, GB)."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"


def get_storage_status(usage_percent: float) -> str:
    """
    Determines the storage status based on usage percentage.
    
    Returns one of:
    - 'OK': Under warning threshold
    - 'WARNING': Between warning and critical thresholds
    - 'CRITICAL': Above critical threshold
    """
    if usage_percent >= config.STORAGE_CRITICAL_PERCENT:
        return 'CRITICAL'
    elif usage_percent >= config.STORAGE_WARNING_PERCENT:
        return 'WARNING'
    else:
        return 'OK'


def get_article_statistics(client: Client) -> Dict[str, Any]:
    """
    Gets detailed statistics about articles for analysis.
    
    This helps understand storage patterns and identify optimization opportunities.
    """
    stats = {
        'total_count': 0,
        'oldest_article': None,
        'newest_article': None,
        'category_distribution': {},
        'source_distribution': {},
    }
    
    try:
        # Total count
        count_response = client.table('articles').select('*', count='exact').limit(0).execute()
        stats['total_count'] = count_response.count or 0
        
        # Oldest article
        oldest = client.table('articles') \
            .select('title, published_at, created_at') \
            .order('published_at', desc=False) \
            .limit(1) \
            .execute()
        
        if oldest.data:
            stats['oldest_article'] = {
                'title': oldest.data[0].get('title', '')[:50] + '...',
                'date': oldest.data[0].get('published_at') or oldest.data[0].get('created_at'),
            }
        
        # Newest article
        newest = client.table('articles') \
            .select('title, published_at, created_at') \
            .order('published_at', desc=True) \
            .limit(1) \
            .execute()
        
        if newest.data:
            stats['newest_article'] = {
                'title': newest.data[0].get('title', '')[:50] + '...',
                'date': newest.data[0].get('published_at') or newest.data[0].get('created_at'),
            }
        
    except Exception as e:
        logger.warning(f"Could not get article statistics: {e}")
    
    return stats


def record_metrics(client: Client, storage_info: Dict) -> None:
    """Records current storage metrics for historical tracking."""
    try:
        client.table('storage_metrics').insert({
            'total_size_bytes': storage_info['total_bytes'],
            'articles_count': storage_info['tables'].get('articles', {}).get('rows', 0),
            'articles_size_bytes': storage_info['tables'].get('articles', {}).get('estimated_bytes', 0),
        }).execute()
        logger.info("Storage metrics recorded for historical tracking")
    except Exception as e:
        logger.warning(f"Could not record storage metrics: {e}")


# =============================================================================
# GITHUB ACTIONS OUTPUT
# =============================================================================

def set_github_output(name: str, value: str) -> None:
    """
    Sets a GitHub Actions output variable.
    
    This allows subsequent workflow steps to access the storage status
    and trigger notifications if needed.
    """
    github_output = os.environ.get('GITHUB_OUTPUT')
    
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
        logger.debug(f"Set GitHub output: {name}={value}")
    else:
        # Running locally, just log it
        logger.info(f"[LOCAL] Would set GitHub output: {name}={value}")


def create_summary_report(storage_info: Dict, article_stats: Dict) -> str:
    """Creates a formatted summary report for logging and GitHub."""
    status = get_storage_status(storage_info['usage_percent'])
    
    lines = [
        "=" * 60,
        "STORAGE MONITORING REPORT",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 60,
        "",
        f"STATUS: {status}",
        f"USAGE: {storage_info['usage_percent']}% of {storage_info['limit_human']}",
        f"ESTIMATED TOTAL: {storage_info['total_human']}",
        "",
        "TABLE BREAKDOWN:",
        "-" * 40,
    ]
    
    for table_name, info in storage_info['tables'].items():
        lines.append(f"  {table_name}: {info['rows']:,} rows (~{info['estimated_human']})")
    
    lines.extend([
        "",
        "ARTICLE STATISTICS:",
        "-" * 40,
        f"  Total articles: {article_stats['total_count']:,}",
    ])
    
    if article_stats.get('oldest_article'):
        lines.append(f"  Oldest: {article_stats['oldest_article']['date']}")
    
    if article_stats.get('newest_article'):
        lines.append(f"  Newest: {article_stats['newest_article']['date']}")
    
    lines.extend([
        "",
        "THRESHOLDS:",
        "-" * 40,
        f"  Warning:  {config.STORAGE_WARNING_PERCENT}% ({format_bytes(config.get_storage_warning_bytes())})",
        f"  Critical: {config.STORAGE_CRITICAL_PERCENT}% ({format_bytes(config.get_storage_critical_bytes())})",
        "",
        "=" * 60,
    ])
    
    if status == 'CRITICAL':
        lines.extend([
            "",
            "⚠️  CRITICAL: Storage is approaching limit!",
            "    Actions to consider:",
            "    1. Reduce MAX_ARTICLE_AGE_DAYS in config.py",
            "    2. Reduce MAX_ARTICLES_COUNT in config.py",
            "    3. Run purge_data.py manually",
            "    4. Consider upgrading to Supabase Pro",
            "",
        ])
    elif status == 'WARNING':
        lines.extend([
            "",
            "⚠️  WARNING: Storage is getting high",
            "    Monitor closely and consider reducing retention settings.",
            "",
        ])
    
    return "\n".join(lines)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main entry point for the storage monitoring script.
    
    This function:
    1. Connects to Supabase
    2. Analyzes storage usage
    3. Gets article statistics
    4. Records metrics for historical tracking
    5. Generates a report
    6. Sets GitHub Actions outputs for notifications
    """
    logger.info("Starting Storage Monitor")
    
    # Initialize Supabase client
    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        set_github_output('status', 'ERROR')
        set_github_output('error', str(e))
        sys.exit(1)
    
    # Get table sizes
    logger.info("Analyzing table sizes...")
    table_sizes = get_table_sizes(client)
    
    # Estimate storage usage
    logger.info("Estimating storage usage...")
    storage_info = estimate_storage_usage(table_sizes)
    
    # Get article statistics
    logger.info("Getting article statistics...")
    article_stats = get_article_statistics(client)
    
    # Record metrics for historical tracking
    record_metrics(client, storage_info)
    
    # Determine status
    status = get_storage_status(storage_info['usage_percent'])
    
    # Generate and print report
    report = create_summary_report(storage_info, article_stats)
    print(report)
    
    # Set GitHub Actions outputs
    set_github_output('status', status)
    set_github_output('usage_percent', str(storage_info['usage_percent']))
    set_github_output('total_bytes', str(storage_info['total_bytes']))
    set_github_output('article_count', str(article_stats['total_count']))
    
    # Also output as JSON for complex workflows
    set_github_output('report_json', json.dumps({
        'status': status,
        'usage_percent': storage_info['usage_percent'],
        'total_bytes': storage_info['total_bytes'],
        'total_human': storage_info['total_human'],
        'article_count': article_stats['total_count'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }))
    
    # Exit with appropriate code
    if status == 'CRITICAL':
        logger.error("Storage is CRITICAL - immediate action required!")
        sys.exit(2)  # Non-zero but different from connection error
    elif status == 'WARNING':
        logger.warning("Storage is at WARNING level - monitor closely")
        sys.exit(0)  # Still success, but logged warning
    else:
        logger.info("Storage is OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
