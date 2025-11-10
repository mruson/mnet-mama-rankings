"""Scheduler for periodically fetching MAMA rankings.

This script can be run as a daemon or via cron to regularly
fetch and store rankings updates.
"""
import os
import sys
import time
import argparse
from datetime import datetime
from .fetcher import fetch_current_rankings
from .storage import init_db, save_rankings, get_recent_changes

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'rankings.db')


def fetch_and_store():
    """Fetch current rankings and store them in the database."""
    print(f"[{datetime.now().isoformat()}] Fetching MAMA rankings...")

    rankings = fetch_current_rankings()
    if not rankings:
        print("  ERROR: Failed to fetch rankings")
        return False

    print(f"  Successfully fetched rankings (updated at: {rankings.get('updatedAt')})")

    # Initialize DB if needed
    init_db(DB_PATH)

    # Save and detect changes
    snapshot_id = save_rankings(DB_PATH, rankings)
    print(f"  Saved snapshot #{snapshot_id}")

    # Report any changes
    changes = get_recent_changes(DB_PATH, limit=10)
    if changes:
        print(f"  Detected {len(changes)} ranking changes:")
        for change in changes:
            direction = "↑" if change['change'] > 0 else "↓"
            print(f"    {direction} {change['artist']} ({change['category']}): "
                  f"#{change['old_rank']} → #{change['new_rank']}")
    else:
        print("  No ranking changes detected")

    return True


def run_continuous(interval_minutes: int):
    """Run the fetcher continuously at specified interval.

    Args:
        interval_minutes: Minutes between each fetch
    """
    print(f"Starting continuous fetcher (interval: {interval_minutes} minutes)")
    print(f"Database: {os.path.abspath(DB_PATH)}")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            fetch_and_store()
            print(f"  Next fetch in {interval_minutes} minutes\n")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            break
        except Exception as e:
            print(f"  ERROR: {e}")
            print(f"  Retrying in {interval_minutes} minutes\n")
            time.sleep(interval_minutes * 60)


def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description='Fetch and track MAMA rankings over time'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Minutes between fetches (default: 60)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (useful for cron jobs)'
    )

    args = parser.parse_args()

    if args.once:
        success = fetch_and_store()
        sys.exit(0 if success else 1)
    else:
        run_continuous(args.interval)


if __name__ == "__main__":
    main()
