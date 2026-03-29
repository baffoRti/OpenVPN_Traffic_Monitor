#!/usr/bin/env python3
"""Display statistics from OpenVPN Traffic Monitor database."""

import sys
import os
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from openvpn_monitor.visualization.display import display_db_contents, get_current_month, get_previous_month
from openvpn_monitor.utils.config import OPENVPN_STATS_DB


def main():
    parser = argparse.ArgumentParser(
        description='Display traffic statistics from OpenVPN Traffic Monitor database.',
        epilog='Examples:\n'
               '  python display_stats.py                    # Show all data\n'
               '  python display_stats.py --current-month    # Show current month only\n'
               '  python display_stats.py --previous-month   # Show previous month only\n'
               '  python display_stats.py --month 2026-03    # Show specific month\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--current-month', action='store_true',
                       help='Show traffic data for current month only')
    group.add_argument('--previous-month', action='store_true',
                       help='Show traffic data for previous month only')
    group.add_argument('--month', type=str, metavar='YYYY-MM',
                       help='Show traffic data for specific month (e.g., 2026-03)')
    
    parser.add_argument('--db', default=OPENVPN_STATS_DB,
                        help=f'Path to SQLite database (default: {OPENVPN_STATS_DB})')
    
    args = parser.parse_args()
    
    # Determine month filter
    month_filter = None
    if args.current_month:
        month_filter = get_current_month()
        print(f"Showing data for current month: {month_filter}")
    elif args.previous_month:
        month_filter = get_previous_month()
        print(f"Showing data for previous month: {month_filter}")
    elif args.month:
        month_filter = args.month
        print(f"Showing data for month: {month_filter}")
    
    try:
        display_db_contents(args.db, month_filter)
    except Exception as e:
        print(f"Error displaying statistics: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())