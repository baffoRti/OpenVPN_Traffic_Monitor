#!/usr/bin/env python3
"""Generate traffic charts from OpenVPN Traffic Monitor database."""

import argparse
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .charts import generate_all_charts, plot_monthly_traffic, plot_client_traffic, plot_top_clients, plot_current_clients
from ..utils.config import OPENVPN_STATS_DB


def main():
    parser = argparse.ArgumentParser(description='Generate traffic charts from OpenVPN Traffic Monitor database.')
    parser.add_argument('--db', default=OPENVPN_STATS_DB,
                        help=f'Path to SQLite database file (default: {OPENVPN_STATS_DB})')
    parser.add_argument('--output-dir', default='charts',
                        help='Directory to save charts (default: charts)')
    parser.add_argument('--chart', choices=['all', 'monthly', 'client', 'top', 'current'],
                        default='all', help='Type of chart to generate (default: all)')
    parser.add_argument('--client', type=str,
                        help='Client name for client-specific chart (required for --chart=client)')
    parser.add_argument('--top-n', type=int, default=10,
                        help='Number of top clients to show (default: 10)')
    parser.add_argument('--show', action='store_true',
                        help='Show charts instead of saving to files')
    
    args = parser.parse_args()
    
    # Validate client argument
    if args.chart == 'client' and not args.client:
        parser.error("--client is required when --chart=client")
    
    # Create output directory if saving
    if not args.show:
        os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        if args.chart == 'all':
            print(f"Generating all charts in '{args.output_dir}'...")
            generate_all_charts(args.db, args.output_dir)
            print(f"All charts saved to '{args.output_dir}/'")
        elif args.chart == 'monthly':
            output_file = None if args.show else os.path.join(args.output_dir, 'monthly_traffic.png')
            plot_monthly_traffic(args.db, output_file)
            if not args.show:
                print(f"Monthly traffic chart saved to '{output_file}'")
        elif args.chart == 'client':
            output_file = None if args.show else os.path.join(args.output_dir, f'client_{args.client}.png')
            plot_client_traffic(args.db, args.client, output_file)
            if not args.show:
                print(f"Client traffic chart saved to '{output_file}'")
        elif args.chart == 'top':
            output_file = None if args.show else os.path.join(args.output_dir, f'top_{args.top_n}_clients.png')
            plot_top_clients(args.db, args.top_n, output_file)
            if not args.show:
                print(f"Top clients chart saved to '{output_file}'")
        elif args.chart == 'current':
            output_file = None if args.show else os.path.join(args.output_dir, 'current_clients.png')
            plot_current_clients(args.db, output_file)
            if not args.show:
                print(f"Current clients chart saved to '{output_file}'")
        
        if args.show:
            print("Displaying charts...")
            import matplotlib.pyplot as plt
            plt.show()
            
    except Exception as e:
        print(f"Error generating charts: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()