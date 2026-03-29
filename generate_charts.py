#!/usr/bin/env python3
"""Generate traffic charts from OpenVPN Traffic Monitor database."""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from openvpn_monitor.visualization.generate_charts import main

if __name__ == '__main__':
    sys.exit(main())