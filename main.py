#!/usr/bin/env python3
"""Main entry point for OpenVPN Traffic Monitor."""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from openvpn_monitor.core.main_app import main

if __name__ == '__main__':
    sys.exit(main())