"""Visualization module for OpenVPN Traffic Monitor.

This module provides functions to generate various charts
for analyzing VPN traffic data stored in SQLite database.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def bytes_to_human_readable(size_in_bytes: int, unit: str = 'auto') -> Tuple[float, str]:
    """Convert bytes to human-readable format.

    Args:
        size_in_bytes: Size in bytes.
        unit: Target unit ('B', 'KB', 'MB', 'GB', 'TB') or 'auto'.

    Returns:
        Tuple of (converted_value, unit_label).
    """
    if size_in_bytes == 0:
        return 0.0, 'B'
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    if unit == 'auto':
        # Auto-select the most appropriate unit
        i = 0
        value = float(size_in_bytes)
        while value >= 1024 and i < len(units) - 1:
            value /= 1024
            i += 1
        return value, units[i]
    else:
        # Convert to specified unit
        i = units.index(unit.upper())
        value = size_in_bytes / (1024 ** i)
        return value, unit


def setup_chart_style() -> None:
    """Set up consistent chart styling."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'figure.figsize': (12, 8),
        'figure.dpi': 100,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'lines.linewidth': 2,
        'lines.markersize': 8,
    })


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        SQLite connection object.

    Raises:
        sqlite3.Error: If connection fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to connect to database: {e}")


def plot_monthly_traffic(db_path: str, output_file: Optional[str] = None) -> None:
    """Plot monthly traffic (received and sent) as line chart.

    Args:
        db_path: Path to SQLite database file.
        output_file: If provided, save chart to this file (PNG).
                    If None, display the chart.
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Query total monthly traffic
        query = """
            SELECT year_month, 
                   SUM(bytes_received) as total_received, 
                   SUM(bytes_sent) as total_sent
            FROM user_traffic_monthly
            GROUP BY year_month
            ORDER BY year_month
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No monthly traffic data found.")
            return
        
        # Prepare data
        months = [row['year_month'] for row in rows]
        received_bytes = [row['total_received'] for row in rows]
        sent_bytes = [row['total_sent'] for row in rows]
        
        # Convert to MB for display
        received_mb = [b / (1024 * 1024) for b in received_bytes]
        sent_mb = [b / (1024 * 1024) for b in sent_bytes]
        
        # Setup chart
        setup_chart_style()
        fig, ax = plt.subplots()
        
        # Plot lines
        ax.plot(months, received_mb, marker='o', label='Received', color='#2E86AB')
        ax.plot(months, sent_mb, marker='s', label='Sent', color='#A23B72')
        
        # Formatting
        ax.set_title('Monthly VPN Traffic', fontsize=18, pad=20)
        ax.set_xlabel('Month', fontsize=14)
        ax.set_ylabel('Traffic (MB)', fontsize=14)
        ax.legend(loc='upper left', frameon=True, shadow=True)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of points
        for i, (x, y_r, y_s) in enumerate(zip(months, received_mb, sent_mb)):
            ax.annotate(f'{y_r:.1f}', (x, y_r), textcoords="offset points", 
                       xytext=(0,10), ha='center', fontsize=9)
            ax.annotate(f'{y_s:.1f}', (x, y_s), textcoords="offset points", 
                       xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        
        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {output_file}")
        else:
            plt.show()
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def plot_client_traffic(db_path: str, common_name: str, output_file: Optional[str] = None) -> None:
    """Plot monthly traffic for a specific client.

    Args:
        db_path: Path to SQLite database file.
        common_name: Client identifier (common_name).
        output_file: If provided, save chart to this file (PNG).
                    If None, display the chart.
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Query client-specific monthly traffic
        query = """
            SELECT year_month, bytes_received, bytes_sent
            FROM user_traffic_monthly
            WHERE common_name = ?
            ORDER BY year_month
        """
        cursor.execute(query, (common_name,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print(f"No traffic data found for client '{common_name}'.")
            return
        
        # Prepare data
        months = [row['year_month'] for row in rows]
        received_bytes = [row['bytes_received'] for row in rows]
        sent_bytes = [row['bytes_sent'] for row in rows]
        
        # Convert to MB
        received_mb = [b / (1024 * 1024) for b in received_bytes]
        sent_mb = [b / (1024 * 1024) for b in sent_bytes]
        
        # Setup chart
        setup_chart_style()
        fig, ax = plt.subplots()
        
        # Plot stacked area chart
        ax.fill_between(months, 0, received_mb, alpha=0.3, color='#2E86AB', label='Received')
        ax.fill_between(months, 0, sent_mb, alpha=0.3, color='#A23B72', label='Sent')
        
        # Also plot lines for clarity
        ax.plot(months, received_mb, color='#2E86AB', linewidth=2)
        ax.plot(months, sent_mb, color='#A23B72', linewidth=2)
        
        # Formatting
        ax.set_title(f'Monthly Traffic for Client: {common_name}', fontsize=18, pad=20)
        ax.set_xlabel('Month', fontsize=14)
        ax.set_ylabel('Traffic (MB)', fontsize=14)
        ax.legend(loc='upper left', frameon=True, shadow=True)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {output_file}")
        else:
            plt.show()
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def plot_top_clients(db_path: str, top_n: int = 10, output_file: Optional[str] = None) -> None:
    """Plot top N clients by total traffic as horizontal bar chart.

    Args:
        db_path: Path to SQLite database file.
        top_n: Number of top clients to display.
        output_file: If provided, save chart to this file (PNG).
                    If None, display the chart.
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Query top clients by total traffic
        query = """
            SELECT common_name, 
                   SUM(bytes_received + bytes_sent) as total_traffic
            FROM user_traffic_monthly
            GROUP BY common_name
            ORDER BY total_traffic DESC
            LIMIT ?
        """
        cursor.execute(query, (top_n,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No client traffic data found.")
            return
        
        # Prepare data
        clients = [row['common_name'] for row in rows]
        total_bytes = [row['total_traffic'] for row in rows]
        
        # Convert to GB for better readability
        total_gb = [b / (1024 ** 3) for b in total_bytes]
        
        # Setup chart
        setup_chart_style()
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create horizontal bar chart
        y_pos = range(len(clients))
        bars = ax.barh(y_pos, total_gb, color='#3A86FF', alpha=0.8)
        
        # Add value labels
        for bar, gb_val in zip(bars, total_gb):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{gb_val:.2f} GB', ha='left', va='center', fontsize=10)
        
        # Formatting
        ax.set_title(f'Top {top_n} Clients by Total Traffic', fontsize=18, pad=20)
        ax.set_xlabel('Total Traffic (GB)', fontsize=14)
        ax.set_ylabel('Client', fontsize=14)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(clients, fontsize=11)
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {output_file}")
        else:
            plt.show()
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def plot_current_clients(db_path: str, output_file: Optional[str] = None) -> None:
    """Plot current active clients with their traffic.

    Args:
        db_path: Path to SQLite database file.
        output_file: If provided, save chart to this file (PNG).
                    If None, display the chart.
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Query current client state
        query = """
            SELECT common_name, connected_since, 
                   bytes_received, bytes_sent
            FROM current_client_state
            ORDER BY bytes_received + bytes_sent DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No current client data found.")
            return
        
        # Prepare data
        clients = [row['common_name'] for row in rows]
        received_bytes = [row['bytes_received'] for row in rows]
        sent_bytes = [row['bytes_sent'] for row in rows]
        
        # Convert to MB
        received_mb = [b / (1024 * 1024) for b in received_bytes]
        sent_mb = [b / (1024 * 1024) for b in sent_bytes]
        
        # Setup chart
        setup_chart_style()
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create stacked bar chart
        x = range(len(clients))
        width = 0.35
        
        bars1 = ax.bar(x, received_mb, width, label='Received', color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x, sent_mb, width, bottom=received_mb, label='Sent', color='#A23B72', alpha=0.8)
        
        # Formatting
        ax.set_title('Current Active Clients Traffic', fontsize=18, pad=20)
        ax.set_xlabel('Client', fontsize=14)
        ax.set_ylabel('Traffic (MB)', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(clients, rotation=45, ha='right', fontsize=10)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Add total traffic labels on top
        for i, (rec, sent) in enumerate(zip(received_mb, sent_mb)):
            total = rec + sent
            ax.text(i, total, f'{total:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {output_file}")
        else:
            plt.show()
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def generate_all_charts(db_path: str, output_dir: str = 'charts') -> None:
    """Generate all charts and save to specified directory.

    Args:
        db_path: Path to SQLite database file.
        output_dir: Directory to save charts (created if doesn't exist).
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("Generating charts...")
    
    # Generate monthly traffic chart
    try:
        plot_monthly_traffic(
            db_path, 
            output_file=str(output_path / f'monthly_traffic_{timestamp}.png')
        )
    except Exception as e:
        print(f"Failed to generate monthly traffic chart: {e}")
    
    # Generate top clients chart
    try:
        plot_top_clients(
            db_path, 
            top_n=10,
            output_file=str(output_path / f'top_clients_{timestamp}.png')
        )
    except Exception as e:
        print(f"Failed to generate top clients chart: {e}")
    
    # Generate current clients chart
    try:
        plot_current_clients(
            db_path,
            output_file=str(output_path / f'current_clients_{timestamp}.png')
        )
    except Exception as e:
        print(f"Failed to generate current clients chart: {e}")
    
    print(f"All charts saved to {output_dir}")


# Example usage and testing
if __name__ == "__main__":
    # Example: Generate all charts for the default database
    # You may need to adjust the database path
    import sys
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "openvpn_stats.db"
    
    print(f"Using database: {db_path}")
    generate_all_charts(db_path, output_dir='charts')