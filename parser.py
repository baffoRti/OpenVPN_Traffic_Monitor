import re
import logging

logger = logging.getLogger(__name__)


def parse_openvpn_log(log_file_path):
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

    for row_str in data_rows:
        if not row_str.strip():
            continue

        values = [v.strip() for v in row_str.split(',')]

        if len(values) == len(column_names):
            client_list_data.append(dict(zip(column_names, values)))
        else:
            logger.warning(f"Skipping malformed row: {row_str}")

    return client_list_data, updated_timestamp_str
