"""Configuration module for OpenVPN Traffic Monitor.

This module loads configuration from environment variables (.env file)
and provides default values for application settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Paths
STATUS_LOGS: str = os.getenv('STATUS_LOGS', '/var/log/openvpn/status.log')
OPENVPN_STATS_LOGS: str = os.getenv('OPENVPN_STATS_LOGS', 'openvpn_stats.log')
OPENVPN_STATS_DB: str = os.getenv('OPENVPN_STATS_DB', 'openvpn_stats.db')
DB_DIRECTORY: str = os.getenv('DB_DIRECTORY', './')

# Retention settings
LOG_DAYS_TO_KEEP: int = int(os.getenv('LOG_DAYS_TO_KEEP', '5'))

# Log rotation settings
LOG_ROTATION_FREQUENCY: str = os.getenv('LOG_ROTATION_FREQUENCY', 'midnight')
LOG_ROTATION_INTERVAL: int = int(os.getenv('LOG_ROTATION_INTERVAL', '1'))
LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '7'))

# Application settings
APP_NAME: str = os.getenv('APP_NAME', 'OpenVPN Traffic Monitor')
DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
