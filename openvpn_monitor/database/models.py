"""Data models for OpenVPN Traffic Monitor.

This module contains dataclasses representing various data structures
used throughout the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ClientData:
    """Represents a client's data parsed from OpenVPN status log."""
    common_name: str
    real_address: str
    bytes_received: int
    bytes_sent: int
    connected_since: str  # Format: 'YYYY-MM-DD HH:MM:SS'
    
    @property
    def year_month(self) -> str:
        """Extract year-month from connected_since for monthly traffic grouping."""
        try:
            dt = datetime.strptime(self.connected_since, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m")
        except ValueError:
            # Fallback for date-only format
            return self.connected_since[:7]


@dataclass
class MonthlyTraffic:
    """Represents monthly traffic statistics for a client."""
    common_name: str
    year_month: str  # Format: 'YYYY-MM'
    bytes_received: int
    bytes_sent: int


@dataclass
class LogMetadata:
    """Represents metadata about the last processed log."""
    last_updated_time: str  # Format: 'YYYY-MM-DD HH:MM:SS'


@dataclass
class ClientState:
    """Represents the current state of a connected client."""
    common_name: str
    connected_since: str  # Format: 'YYYY-MM-DD HH:MM:SS'
    bytes_received: int
    bytes_sent: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database operations."""
        return {
            'common_name': self.common_name,
            'connected_since': self.connected_since,
            'bytes_received': self.bytes_received,
            'bytes_sent': self.bytes_sent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClientState':
        """Create ClientState from dictionary."""
        return cls(
            common_name=data['common_name'],
            connected_since=data['connected_since'],
            bytes_received=data['bytes_received'],
            bytes_sent=data['bytes_sent']
        )


@dataclass
class AppConfig:
    """Application configuration settings."""
    status_logs: str
    openvpn_stats_logs: str
    openvpn_stats_db: str
    log_days_to_keep: int
    log_rotation_frequency: str = 'midnight'
    log_rotation_interval: int = 1
    log_backup_count: int = 7
    db_directory: str = './'
    app_name: str = 'OpenVPN Traffic Monitor'
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create AppConfig from environment variables."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        return cls(
            status_logs=os.getenv('STATUS_LOGS', '/var/log/openvpn/status.log'),
            openvpn_stats_logs=os.getenv('OPENVPN_STATS_LOGS', 'openvpn_stats.log'),
            openvpn_stats_db=os.getenv('OPENVPN_STATS_DB', 'openvpn_stats.db'),
            log_days_to_keep=int(os.getenv('LOG_DAYS_TO_KEEP', '5')),
            log_rotation_frequency=os.getenv('LOG_ROTATION_FREQUENCY', 'midnight'),
            log_rotation_interval=int(os.getenv('LOG_ROTATION_INTERVAL', '1')),
            log_backup_count=int(os.getenv('LOG_BACKUP_COUNT', '7')),
            db_directory=os.getenv('DB_DIRECTORY', './'),
            app_name=os.getenv('APP_NAME', 'OpenVPN Traffic Monitor'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )