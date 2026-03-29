#!/usr/bin/env python3
"""Help and usage information for OpenVPN Traffic Monitor."""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

def print_help():
    print("""
OpenVPN Traffic Monitor - Command Reference
===========================================

1. PROCESS LOGS
   python main.py
   Process OpenVPN status logs and update database.
   
   Options:
     No additional options. Configure via .env file.

2. VIEW STATISTICS
   python display_stats.py [OPTIONS]
   
   Options:
     --current-month    Show traffic for current month only
     --previous-month   Show traffic for previous month only
     --month YYYY-MM    Show traffic for specific month (e.g., 2026-03)
     --db PATH          Path to database file (default: from .env)
     --help             Show this help message
   
   Examples:
     python display_stats.py                    # All data
     python display_stats.py --current-month    # Current month only
     python display_stats.py --month 2026-02    # Specific month

3. GENERATE CHARTS
   python generate_charts.py [OPTIONS]
   
   Options:
     --chart TYPE       Chart type: all, monthly, client, top, current
     --client NAME      Client name for client-specific chart
     --top-n N          Number of top clients to show (default: 10)
     --output-dir DIR   Output directory for charts (default: charts)
     --db PATH          Path to database file (default: from .env)
     --show             Display charts instead of saving to files
     --help             Show this help message
   
   Examples:
     python generate_charts.py                    # All charts
     python generate_charts.py --chart monthly    # Monthly traffic chart
     python generate_charts.py --chart client --client User001
     python generate_charts.py --show             # Display charts

4. AUTOMATION (CRON)
   ./OpenVPN_Traffic_Monitor.sh
   Script for automatic log processing (set up in cron).

5. INSTALLATION
   ./deploy/install.sh
   Automatic installation script for new servers.

For more information, see README.md or visit:
https://github.com/baffoRti/OpenVPN_Traffic_Monitor
""")


if __name__ == '__main__':
    print_help()