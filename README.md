# OpenVPN Traffic Monitor

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Monitoring and analysis of OpenVPN client traffic with SQLite storage and visualization.

## Key Features

- **Automatic data collection**: Parses OpenVPN logs, extracts client traffic information
- **Statistics storage**: SQLite database with monthly traffic per client
- **Visualization**: Traffic charts (monthly, per-client, top-N, current connections)

## Quick Start

### 1. Server Installation

```bash
# Clone repository
git clone https://github.com/baffoRti/OpenVPN_Traffic_Monitor.git
cd OpenVPN_Traffic_Monitor

# Run installation script
./deploy/install.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env according to your configuration
```

### 2. Configuration

Edit the `.env` file:
```bash
# OpenVPN status log path
STATUS_LOGS=/var/log/openvpn/status.log

# Application log file name
OPENVPN_STATS_LOGS=openvpn_stats.log

# Database file name
OPENVPN_STATS_DB=openvpn_stats.db

# Log retention days
LOG_DAYS_TO_KEEP=30

# Log rotation settings
LOG_ROTATION_FREQUENCY=midnight
LOG_ROTATION_INTERVAL=1
LOG_BACKUP_COUNT=7
```

### 3. Initial Run

```bash
# Main log processor
python main.py

# View statistics
python display_stats.py

# Generate all charts
python generate_charts.py

# View charts (opens in separate windows)
python generate_charts.py --show
```

### 4. Automation (cron)

```bash
# Add to crontab for execution every 5 minutes
crontab -e
```

Add line:
```cron
*/5 * * * * /path/to/project/OpenVPN_Traffic_Monitor.sh
```

## Project Structure

```
OpenVPN_Traffic_Monitor/
├── main.py                     # Main log processing script
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── openvpn_monitor/            # Main Python package
│   ├── __init__.py
│   ├── core/                   # Core application logic
│   │   ├── __init__.py
│   │   ├── main_app.py         # Processing logic
│   │   └── monitor.py          # Monitoring class
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── database.py         # Functional database interface
│   │   ├── database_class.py   # OOP database interface
│   │   └── models.py           # Data models (dataclasses)
│   ├── parser/                 # OpenVPN log parsing
│   │   ├── __init__.py
│   │   ├── parser.py           # Functional parser
│   │   └── parser_class.py     # OOP parser
│   ├── visualization/          # Visualization and display
│   │   ├── __init__.py
│   │   ├── charts.py           # Chart generation functions
│   │   ├── display.py          # Console statistics output
│   │   └── generate_charts.py  # CLI for chart generation
│   └── utils/                  # Utilities and configuration
│       ├── __init__.py
│       ├── utils.py            # General utilities
│       └── config.py           # Configuration (from .env)
├── scripts/                    # Deployment scripts
│   ├── OpenVPN_Traffic_Monitor.sh
│   └── setup_venv.sh
└── deploy/                     # Installation tools
    └── install.sh              # Automatic installation script
```

## Usage Examples

### View Statistics
```bash
# Show all data
$ python display_stats.py

--- User traffic monthly ---
Common Name     | Year-Month | Received Traffic | Sent Traffic | Total Traffic
-------------------------------------------------------------------------------
User001         | 2026-03    | 37.62 MB         | 103.10 MB    | 140.72 MB   
User002         | 2026-03    | 81.89 MB         | 1.75 GB      | 1.83 GB     

# Show current month only
$ python display_stats.py --current-month

# Show previous month only
$ python display_stats.py --previous-month

# Show specific month
$ python display_stats.py --month 2026-02
```

### Generate Charts
```bash
# All charts
python generate_charts.py --output-dir ./charts

# Specific charts
python generate_charts.py --chart monthly
python generate_charts.py --chart client --client User001
python generate_charts.py --chart top --top-n 10
python generate_charts.py --chart current

# View charts
python generate_charts.py --show
```

### Command Reference
For a complete command reference, run:
```bash
python help.py
```

This will display detailed help for all available commands including:
- `main.py` - log processing
- `display_stats.py` - statistics viewing with filtering options
- `generate_charts.py` - chart generation with various chart types
- `OpenVPN_Traffic_Monitor.sh` - automation script for cron

### Example Chart Output

After running `python generate_charts.py`, the following charts are generated:

```
$ python generate_charts.py --output-dir ./charts
Generating monthly traffic chart... Saved to charts/monthly_traffic.png
Generating client traffic chart... Saved to charts/client_traffic.png
Generating top clients chart... Saved to charts/top_clients.png
Generating current clients chart... Saved to charts/current_clients.png
All charts generated successfully in './charts/' directory.
```

**Example chart types:**

1. **Monthly Traffic Chart** (line chart):
   - X-axis: Months (Jan 2026, Feb 2026, Mar 2026)
   - Y-axis: Traffic (GB)
   - Two lines: Received (blue), Sent (red)
   - Shows traffic trends over time

2. **Client Comparison** (bar chart):
   - X-axis: Client names (User001, User002, ...)
   - Y-axis: Total traffic (GB)
   - Bars grouped by client with received/sent segments

3. **Top Clients** (horizontal bar chart):
   - Y-axis: Top 10 clients by total traffic
   - X-axis: Traffic volume (GB)
   - Sorted descending

4. **Current Clients** (pie chart):
   - Each slice represents a currently connected client
   - Slice size = percentage of total current traffic
   - Legend with client names and percentages

Charts are saved as PNG files in the specified output directory (default: `charts/`).

## Technical Details

### Dependencies
- Python 3.8+
- SQLite3
- matplotlib (for charts)
- python-dotenv (for configuration)

### Database Schema
- `user_traffic_monthly` - Monthly traffic per client
- `current_client_state` - Current state of connected clients
- `log_metadata` - Log processing metadata

## Troubleshooting

### Problem: "Log file not found"
Ensure the path to OpenVPN log is correctly specified in `.env`.

### Problem: "Database access error"
Check write permissions in the project directory.

### Problem: "Charts not generating"
Ensure matplotlib is installed:
```bash
pip list | grep matplotlib
```
