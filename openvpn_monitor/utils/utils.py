"""Utility functions for OpenVPN Traffic Monitor.

This module provides helper functions for logging, log cleanup,
and data formatting.
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Optional


def setup_logging(
    log_file_path: str,
    level: int = logging.INFO,
    rotation_frequency: str = 'midnight',
    rotation_interval: int = 1,
    backup_count: int = 7
) -> logging.Logger:
    """Set up logging configuration with time-based rotation.
    
    Args:
        log_file_path: Path to the log file.
        level: Logging level (default: logging.INFO).
        rotation_frequency: Rotation frequency (midnight, H, D, W0-W6).
        rotation_interval: Rotation interval (default: 1).
        backup_count: Number of backup files to keep (default: 7).
        
    Returns:
        Logger instance configured for the application.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create timed rotating file handler
    from logging.handlers import TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
        log_file_path,
        when=rotation_frequency,
        interval=rotation_interval,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Also log to console if in debug mode
    if level == logging.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def clean_old_logs(log_file_path: str, days_to_keep: int, logger: logging.Logger) -> None:
    """Clean old log entries based on retention period.
    
    Args:
        log_file_path: Path to the log file to clean.
        days_to_keep: Number of days to retain log entries.
        logger: Logger instance for recording operations.
        
    Returns:
        None
    """
    if not os.path.exists(log_file_path):
        logger.warning(f"Log file '{log_file_path}' not found. Skipping cleanup.")
        return

    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    kept_lines = []
    removed_count = 0
    total_lines = 0

    try:
        with open(log_file_path, 'r') as f:
            for line in f:
                total_lines += 1
                try:
                    timestamp_str = line.split(' - ')[0]
                    log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    if log_time >= cutoff_date:
                        kept_lines.append(line)
                    else:
                        removed_count += 1
                except (ValueError, IndexError):
                    logger.debug(f"Could not parse timestamp from line: {line.strip()}. Keeping line.")
                    kept_lines.append(line)

        if removed_count > 0:
            tmp_file = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                    for line in kept_lines:
                        tmp_file.write(line)
                os.replace(tmp_file.name, log_file_path)
                logger.info(
                    f"Log cleanup complete for '{log_file_path}'. Total lines: {total_lines}, Kept: {len(kept_lines)}, Removed: {removed_count}.")
            except Exception as e:
                logger.error(f"Error during log file replacement: {e}")
                # Try to clean up temporary file if it exists
                if tmp_file and os.path.exists(tmp_file.name):
                    try:
                        os.unlink(tmp_file.name)
                        logger.debug(f"Removed temporary file: {tmp_file.name}")
                    except OSError as unlink_err:
                        logger.error(f"Failed to remove temporary file {tmp_file.name}: {unlink_err}")
                raise
        else:
            logger.info(f"No old log entries found to remove in '{log_file_path}'. Total lines: {total_lines}.")

    except Exception as e:
        logger.error(f"An error occurred during log cleanup for '{log_file_path}': {e}")


def convert_bytes_to_human_readable(bytes_value: Optional[int]) -> str:
    """Convert bytes to human-readable format.
    
    Args:
        bytes_value: Number of bytes to convert.
        
    Returns:
        String representation in human-readable format (e.g., "1.5 MB").
    """
    if bytes_value is None:
        return "N/A"
    bytes_value = int(bytes_value)
    if bytes_value == 0:
        return "0 B"
    sizes = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while bytes_value >= 1024 and i < len(sizes) - 1:
        bytes_value /= 1024.0
        i += 1
    return f"{bytes_value:.2f} {sizes[i]}"
