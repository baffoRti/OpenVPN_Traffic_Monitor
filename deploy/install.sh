#!/bin/bash
# OpenVPN Traffic Monitor Installation Script
# Run this script on the target server

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[~]${NC} $1"
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================================="
echo "   OpenVPN Traffic Monitor - Installation Script"
echo "==================================================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "python3 could not be found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_status "Found Python $PYTHON_VERSION"

# Check if OpenVPN status log exists
print_status "Checking OpenVPN status log..."
STATUS_LOG="/var/log/openvpn/status.log"
if [ ! -f "$STATUS_LOG" ]; then
    print_warning "OpenVPN status log not found at $STATUS_LOG"
    echo "         Please ensure OpenVPN is configured to export status logs."
    echo "         You can set custom path in .env file later."
fi

# Create virtual environment
print_status "Setting up virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_status "Virtual environment created."
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
print_status "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Configure environment
print_status "Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_status "Created .env file from template."
    print_status "Please edit .env to configure your setup."
else
    print_status ".env file already exists. Skipping."
fi

# Make scripts executable
print_status "Setting up scripts..."
chmod +x scripts/*.sh
chmod +x OpenVPN_Traffic_Monitor.sh 2>/dev/null || true
print_status "Scripts made executable."

# Create charts directory
print_status "Creating charts directory..."
mkdir -p charts
print_status "Charts directory created."

echo ""
echo "==================================================="
echo "   Installation completed successfully!"
echo "==================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Test the application: python main.py"
echo "3. View statistics: python display_stats.py"
echo "4. Set up cron for automatic updates (see README.md)"
echo ""
echo "For detailed instructions, see INSTALL.md or README.md"
echo ""
echo "==================================================="
