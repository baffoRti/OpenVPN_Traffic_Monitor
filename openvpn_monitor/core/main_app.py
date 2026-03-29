"""OpenVPN Traffic Monitor - Main application module.

This module processes OpenVPN status logs, extracts client traffic data,
and stores it in an SQLite database for analysis and monitoring.
Uses the new class-based architecture.
"""

import sys
from ..utils import config, utils
from .monitor import TrafficMonitor
from ..database.models import AppConfig


def main() -> int:
    """Main application entry point.
    
    Processes OpenVPN status logs and updates traffic statistics in the database.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    # Setup logging with rotation
    logger = utils.setup_logging(
        log_file_path=config.OPENVPN_STATS_LOGS,
        rotation_frequency=config.LOG_ROTATION_FREQUENCY,
        rotation_interval=config.LOG_ROTATION_INTERVAL,
        backup_count=config.LOG_BACKUP_COUNT
    )
    logger.info("Application started.")
    
    # Clean old logs
    utils.clean_old_logs(config.OPENVPN_STATS_LOGS, config.LOG_DAYS_TO_KEEP, logger)
    
    # Create configuration object
    app_config = AppConfig(
        status_logs=config.STATUS_LOGS,
        openvpn_stats_logs=config.OPENVPN_STATS_LOGS,
        openvpn_stats_db=config.OPENVPN_STATS_DB,
        log_days_to_keep=config.LOG_DAYS_TO_KEEP,
        log_rotation_frequency=config.LOG_ROTATION_FREQUENCY,
        log_rotation_interval=config.LOG_ROTATION_INTERVAL,
        log_backup_count=config.LOG_BACKUP_COUNT,
        db_directory=config.DB_DIRECTORY,
        app_name=config.APP_NAME,
        debug=config.DEBUG
    )
    
    # Create and run traffic monitor
    monitor = TrafficMonitor(app_config, logger)
    
    try:
        success = monitor.process_log()
        if success:
            logger.info("Log processing completed successfully.")
            return 0
        else:
            logger.error("Log processing failed.")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error during log processing: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())