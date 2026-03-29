"""OpenVPN log parser class for OpenVPN Traffic Monitor."""

import re
import csv
import io
import logging
from typing import Optional
from ..database.models import ClientData


class OpenVPNParser:
    """Parser for OpenVPN status logs."""
    
    def __init__(self, log_path: str, logger: logging.Logger):
        """Initialize OpenVPNParser.
        
        Args:
            log_path: Path to OpenVPN status log file.
            logger: Logger instance for recording operations.
        """
        self.log_path = log_path
        self.logger = logger
    
    def _validate_client_data(self, row_dict: dict) -> bool:
        """Validate client data from parsed row.
        
        Args:
            row_dict: Dictionary with parsed row data.
            
        Returns:
            True if data is valid, False otherwise.
        """
        # Check required fields
        required_fields = ['Common Name', 'Bytes Received', 'Bytes Sent', 'Connected Since']
        for field in required_fields:
            if field not in row_dict or not row_dict[field]:
                self.logger.warning(f"Missing or empty required field '{field}' in row: {row_dict}")
                return False
        
        # Validate numeric fields
        try:
            bytes_received = int(row_dict['Bytes Received'])
            bytes_sent = int(row_dict['Bytes Sent'])
            
            if bytes_received < 0 or bytes_sent < 0:
                self.logger.warning(f"Negative traffic values: Received={bytes_received}, Sent={bytes_sent}")
                return False
            
            # Reasonable upper limit (1 PB = 1e15 bytes)
            if bytes_received > 1e15 or bytes_sent > 1e15:
                self.logger.warning(f"Unreasonably large traffic values: Received={bytes_received}, Sent={bytes_sent}")
                return False
                
        except ValueError:
            self.logger.warning(f"Invalid numeric values in traffic fields: {row_dict}")
            return False
        
        # Validate date format
        connected_since = row_dict['Connected Since']
        try:
            from datetime import datetime
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%m/%d/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S"
            ]
            valid = False
            for fmt in formats:
                try:
                    datetime.strptime(connected_since, fmt)
                    valid = True
                    break
                except ValueError:
                    continue
            
            if not valid:
                self.logger.warning(f"Invalid date format for 'Connected Since': {connected_since}")
                return False
                
            # Additional check: date should not be in the future
            parsed_date = datetime.strptime(connected_since, "%Y-%m-%d %H:%M:%S") if " " in connected_since else datetime.strptime(connected_since, "%Y-%m-%d")
            if parsed_date > datetime.now():
                self.logger.warning(f"Connected Since date is in the future: {connected_since}")
                # Not returning False, just warning
                
        except Exception as e:
            self.logger.warning(f"Error validating date '{connected_since}': {e}")
            return False
        
        return True
    
    def parse(self) -> tuple[list[ClientData], Optional[str]]:
        """Parse OpenVPN status log and extract client data and timestamp.
        
        Returns:
            Tuple of (list of ClientData objects, updated timestamp string or None).
        """
        try:
            with open(self.log_path, 'r') as f:
                log_content = f.read()
        except FileNotFoundError:
            self.logger.error(f"OpenVPN status log file not found: {self.log_path}")
            return [], None
        
        client_list: list[ClientData] = []
        updated_timestamp: Optional[str] = None
        
        # Parse updated timestamp
        updated_match = re.search(r"^Updated,(.*)$", log_content, re.MULTILINE)
        if updated_match:
            updated_timestamp = updated_match.group(1).strip()
            self.logger.debug(f"Raw Updated Timestamp: {updated_timestamp}")
            # Validate timestamp format
            try:
                from datetime import datetime
                # Try to parse the timestamp
                if updated_timestamp:
                    datetime.strptime(updated_timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.logger.warning(f"Invalid 'Updated' timestamp format: {updated_timestamp}")
        else:
            self.logger.warning("Could not find 'Updated' timestamp in the log file.")
        
        # Parse client list
        client_list_start = log_content.find('OpenVPN CLIENT LIST')
        routing_table_start = log_content.find('ROUTING TABLE')
        
        if client_list_start == -1 or routing_table_start == -1:
            self.logger.error("Could not find 'OpenVPN CLIENT LIST' or 'ROUTING TABLE' sections.")
            return [], updated_timestamp
        
        client_list_section = log_content[client_list_start:routing_table_start].strip()
        client_list_lines = client_list_section.splitlines()
        
        # Find header line
        header_index = -1
        for i, line in enumerate(client_list_lines):
            if 'Common Name' in line and 'Real Address' in line:
                header_index = i
                break
        
        if header_index == -1:
            self.logger.error("Could not find the client list header line.")
            return [], updated_timestamp
        
        header = client_list_lines[header_index]
        column_names = [col.strip() for col in header.split(',')]
        
        data_rows = client_list_lines[header_index + 1:]
        
        # Use csv.reader for robust parsing
        try:
            data_text = '\n'.join(data_rows)
            reader = csv.reader(io.StringIO(data_text))
            for row in reader:
                if not row:
                    continue
                values = [v.strip() for v in row]
                if len(values) == len(column_names):
                    row_dict = dict(zip(column_names, values))
                    if self._validate_client_data(row_dict):
                        try:
                            client_data = ClientData(
                                common_name=row_dict.get('Common Name', ''),
                                real_address=row_dict.get('Real Address', ''),
                                bytes_received=int(row_dict.get('Bytes Received', 0)),
                                bytes_sent=int(row_dict.get('Bytes Sent', 0)),
                                connected_since=row_dict.get('Connected Since', '')
                            )
                            client_list.append(client_data)
                        except (ValueError, KeyError) as e:
                            self.logger.warning(f"Error parsing client data: {e}. Row: {row}")
                else:
                    self.logger.warning(f"Skipping malformed row: {row}")
        except Exception as e:
            self.logger.error(f"Error parsing CSV data: {e}. Falling back to manual parsing.")
            # Fallback to manual parsing
            for row_str in data_rows:
                if not row_str.strip():
                    continue
                values = [v.strip() for v in row_str.split(',')]
                if len(values) == len(column_names):
                    row_dict = dict(zip(column_names, values))
                    if self._validate_client_data(row_dict):
                        try:
                            client_data = ClientData(
                                common_name=row_dict.get('Common Name', ''),
                                real_address=row_dict.get('Real Address', ''),
                                bytes_received=int(row_dict.get('Bytes Received', 0)),
                                bytes_sent=int(row_dict.get('Bytes Sent', 0)),
                                connected_since=row_dict.get('Connected Since', '')
                            )
                            client_list.append(client_data)
                        except (ValueError, KeyError) as e:
                            self.logger.warning(f"Error parsing client data: {e}. Row: {row_str}")
                else:
                    self.logger.warning(f"Skipping malformed row: {row_str}")
        
        self.logger.info(f"Parsed {len(client_list)} clients from log file")
        return client_list, updated_timestamp