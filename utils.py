import logging
import os
import tempfile
from datetime import datetime, timedelta


# This import will be resolved in main.py or other modules that use utils
# For standalone testing, you might need to mock or define CONFIG here

def setup_logging(log_file_path, level=logging.INFO):
    logging.basicConfig(
        filename=log_file_path,
        filemode='a',
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    # Return a named logger for this module for consistency
    return logging.getLogger(__name__)


def clean_old_logs(log_file_path, days_to_keep, logger):
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
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                for line in kept_lines:
                    tmp_file.write(line)

            os.replace(tmp_file.name, log_file_path)
            logger.info(
                f"Log cleanup complete for '{log_file_path}'. Total lines: {total_lines}, Kept: {len(kept_lines)}, Removed: {removed_count}.")
        else:
            logger.info(f"No old log entries found to remove in '{log_file_path}'. Total lines: {total_lines}.")

    except Exception as e:
        logger.error(f"An error occurred during log cleanup for '{log_file_path}': {e}")


def convert_bytes_to_human_readable(bytes_value):
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
