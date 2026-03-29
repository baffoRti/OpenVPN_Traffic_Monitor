"""OpenVPN log parser for OpenVPN Traffic Monitor.

This module provides functions for parsing OpenVPN status logs
and extracting client traffic data.
"""

import re
import logging
import csv
import io
from typing import Optional

logger = logging.getLogger(__name__)


def parse_openvpn_log(log_file_path: str) -> tuple[list[dict[str, str]], Optional[str]]:
    """Parse OpenVPN status log and extract client data and timestamp.
    
    Args:
        log_file_path: Path to OpenVPN status log file.
        
    Returns:
        Tuple of (list of client data dictionaries, updated timestamp string or None).
    """
    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()
    except FileNotFoundError:
        logger.error(f"OpenVPN status log file not found: {log_file_path}")
        return [], None

    client_list_data = []
    updated_timestamp_str = None

    # Parse updated timestamp
    updated_line_match = re.search(r"^Updated,(.*)$", log_content, re.MULTILINE)
    if updated_line_match:
        updated_timestamp_str = updated_line_match.group(1).strip()
        logger.debug(f"Raw Updated Timestamp: {updated_timestamp_str}")
    else:
        logger.warning("Could not find 'Updated' timestamp in the log file.")

    # Parse client list
    client_list_start = log_content.find('OpenVPN CLIENT LIST')
    routing_table_start = log_content.find('ROUTING TABLE')

    if client_list_start == -1 or routing_table_start == -1:
        logger.error("Could not find 'OpenVPN CLIENT LIST' or 'ROUTING TABLE' sections.")
        return [], updated_timestamp_str

    client_list_section = log_content[client_list_start:routing_table_start].strip()
    client_list_lines = client_list_section.splitlines()

    header_line_index = -1
    for i, line in enumerate(client_list_lines):
        if 'Common Name' in line and 'Real Address' in line:
            header_line_index = i
            break

    if header_line_index == -1:
        logger.error("Could not find the client list header line.")
        return [], updated_timestamp_str

    header = client_list_lines[header_line_index]
    column_names = [col.strip() for col in header.split(',')]

    data_rows = client_list_lines[header_line_index + 1:]

    # Use csv.reader for robust parsing
    try:
        # Create a file-like object from the list of rows
        data_as_text = '\n'.join(data_rows)
        reader = csv.reader(io.StringIO(data_as_text))
        for row in reader:
            if not row:
                continue
            # Strip whitespace from each value
            values = [v.strip() for v in row]
            if len(values) == len(column_names):
                client_list_data.append(dict(zip(column_names, values)))
            else:
                logger.warning(f"Skipping malformed row: {row}")
    except Exception as e:
        logger.error(f"Error parsing CSV data: {e}. Falling back to manual parsing.")
        # Fallback to original manual parsing
        for row_str in data_rows:
            if not row_str.strip():
                continue
            values = [v.strip() for v in row_str.split(',')]
            if len(values) == len(column_names):
                client_list_data.append(dict(zip(column_names, values)))
            else:
                logger.warning(f"Skipping malformed row: {row_str}")

    return client_list_data, updated_timestamp_str