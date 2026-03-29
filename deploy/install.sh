#!/bin/bash
# OpenVPN Traffic Monitor Installation Script
# Run this script on the target server

set -e  # Exit on any error

echo "OpenVPN Traffic Monitor Installation"
echo "===================================="

# Check Python version
echo "1. Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Found Python $PYTHON_VERSION"

# Check if OpenVPN status log exists
echo "2. Checking OpenVPN status log..."
STATUS_LOG="/var/log/openvpn/status.log"
if [ ! -f "$STATUS_LOG" ]; then
    echo "Warning: OpenVPN status log not found at $STATUS_LOG"
    echo "         Please ensure OpenVPN is configured to export status logs."
    echo "         You can set custom path in .env file later."
fi

# Create virtual environment
echo "3. Setting up virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "   Virtual environment created."
fi

# Activate virtual environment
echo "4. Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "5. Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "6. Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Configure environment
echo "7. Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Created .env file from template."
    echo "   Please edit .env to configure your setup."
else
    echo "   .env file already exists. Skipping."
fi

# Make scripts executable
echo "8. Setting up scripts..."
chmod +x scripts/*.sh
chmod +x OpenVPN_Traffic_Monitor.sh 2>/dev/null || true

# Create charts directory
mkdir -p charts

echo ""
echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Test the application: python main.py"
echo "3. View statistics: python display_stats.py"
echo "4. Generate charts: python generate_charts.py --show"
echo "5. Set up cron for automatic updates (see README.md)"
echo ""
echo "For detailed instructions, see INSTALL.md or README.md"