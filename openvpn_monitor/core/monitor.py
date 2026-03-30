"""Main traffic monitor class for OpenVPN Traffic Monitor."""

import logging
from datetime import datetime
from typing import Optional

from ..database.models import AppConfig, ClientData, MonthlyTraffic
from ..parser.parser_class import OpenVPNParser
from ..database.database_class import DatabaseManager


class TrafficMonitor:
    """Main class for monitoring OpenVPN traffic."""
    
    def __init__(self, config: AppConfig, logger: logging.Logger):
        """Initialize TrafficMonitor.
        
        Args:
            config: Application configuration.
            logger: Logger instance for recording operations.
        """
        self.config = config
        self.logger = logger
        self.parser = OpenVPNParser(config.status_logs, logger)
        self.db_manager = DatabaseManager(config.openvpn_stats_db, logger)
        self.active_clients_in_current_log: set[str] = set()
        
        # Caches
        self.client_state_cache: dict[str, dict] = {}  # common_name -> client state dict
        self.last_timestamp_cache: Optional[str] = None
        
        # Batch processing buffers
        self.monthly_traffic_buffer: list[MonthlyTraffic] = []
        self.client_state_buffer: list[ClientData] = []
    
    def process_log(self) -> bool:
        """Process OpenVPN log file and update database.
        
        Returns:
            True if processing was successful, False otherwise.
        """
        try:
            self.db_manager.connect()
            
            # Get last processed timestamp (use cache if available)
            if self.last_timestamp_cache is None:
                self.last_timestamp_cache = self.db_manager.get_last_processed_timestamp()
            last_timestamp = self.last_timestamp_cache
            
            # Parse current log
            client_list, current_timestamp = self.parser.parse()
            
            if not client_list:
                self.logger.info("No client data found in the OpenVPN log file.")
                return False
            
            # Check if log has been updated
            if (current_timestamp and last_timestamp and 
                current_timestamp == last_timestamp):
                self.logger.info(
                    f"OpenVPN status log has not been updated since last processing ({current_timestamp}). "
                    "Skipping data processing."
                )
                return True
            
            self.logger.info("OpenVPN status log has been updated or not processed before. Proceeding.")
            
            # Get previous client state
            previous_state = self.db_manager.get_previous_client_state()
            
            # Track active clients
            self.active_clients_in_current_log = set()
            
            # Clear batch buffers
            self.monthly_traffic_buffer.clear()
            self.client_state_buffer.clear()
            
            # Process each client
            for client in client_list:
                self._process_client(client, previous_state)
            
            # Handle disconnected clients
            self._handle_disconnected_clients(previous_state)
            
            # Batch update monthly traffic from buffer
            if self.monthly_traffic_buffer:
                try:
                    self.db_manager.batch_update_monthly_traffic(self.monthly_traffic_buffer, batch_size=10)
                    self.logger.info(f"Batch updated monthly traffic for {len(self.monthly_traffic_buffer)} records")
                except Exception as e:
                    self.logger.error(f"Error in batch update for monthly traffic: {e}")
                    # Fallback to individual updates
                    for traffic in self.monthly_traffic_buffer:
                        try:
                            self.db_manager.update_monthly_traffic(traffic)
                        except Exception as fallback_e:
                            self.logger.error(f"Fallback update failed for {traffic.common_name}: {fallback_e}")
            
            # Update log metadata
            self.db_manager.update_log_metadata(current_timestamp)
            
            # Commit all changes
            self.db_manager.commit()
            self.logger.info("Client traffic updates and log metadata processing complete.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing log: {e}")
            return False
        finally:
            self.db_manager.close()
    
    def _process_client(self, client: ClientData, previous_state: dict) -> None:
        """Process individual client data.
        
        Args:
            client: ClientData object with current client information.
            previous_state: Dictionary of previous client states.
        """
        common_name = client.common_name
        self.active_clients_in_current_log.add(common_name)
        
        try:
            connected_since_str = client.connected_since
            # Extract date part for year-month grouping
            connected_since_date = connected_since_str.split(' ')[0]
            year_month = datetime.strptime(connected_since_date, "%Y-%m-%d").strftime("%Y-%m")
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing date for client {common_name}: {e}. Skipping client.")
            return
        
        if common_name in previous_state:
            prev_state = previous_state[common_name]
            prev_connected_since = prev_state.connected_since
            
            if connected_since_str != prev_connected_since:
                # New session detected
                self.logger.info(
                    f"Client {common_name}: New session detected. "
                    "Previous session data will be added to monthly traffic."
                )
                # Update current state with new session
                self.db_manager.update_current_state(client)
                # Add full current session traffic to monthly (buffer for batch)
                traffic = MonthlyTraffic(
                    common_name=common_name,
                    year_month=year_month,
                    bytes_received=client.bytes_received,
                    bytes_sent=client.bytes_sent
                )
                self.monthly_traffic_buffer.append(traffic)
            else:
                # Continuing session
                prev_bytes_received = prev_state.bytes_received
                prev_bytes_sent = prev_state.bytes_sent
                
                # Calculate incremental traffic
                delta_received = client.bytes_received - prev_bytes_received
                delta_sent = client.bytes_sent - prev_bytes_sent
                
                # Handle negative deltas (log reset or server restart)
                if delta_received < 0 or delta_sent < 0:
                    self.logger.warning(
                        f"Client {common_name}: Negative traffic delta detected "
                        f"(R:{delta_received}, S:{delta_sent}). Resetting to current values."
                    )
                    delta_received = client.bytes_received
                    delta_sent = client.bytes_sent
                
                self.logger.info(
                    f"Client {common_name}: Continuing session. "
                    f"Incremental traffic R:{delta_received}, S:{delta_sent}"
                )
                # Add incremental traffic to monthly (buffer for batch)
                traffic = MonthlyTraffic(
                    common_name=common_name,
                    year_month=year_month,
                    bytes_received=delta_received,
                    bytes_sent=delta_sent
                )
                self.monthly_traffic_buffer.append(traffic)
                # Update current state with cumulative values
                self.db_manager.update_current_state(client)
        else:
            # New client detected
            self.logger.info(
                f"Client {common_name}: New client detected. "
                f"Initial traffic R:{client.bytes_received}, S:{client.bytes_sent}"
            )
            # Insert into current state
            self.db_manager.update_current_state(client)
            # Add initial traffic to monthly (buffer for batch)
            traffic = MonthlyTraffic(
                common_name=common_name,
                year_month=year_month,
                bytes_received=client.bytes_received,
                bytes_sent=client.bytes_sent
            )
            self.monthly_traffic_buffer.append(traffic)
    
    def _handle_disconnected_clients(self, previous_state: dict) -> None:
        """Handle clients that are no longer connected.
        
        Args:
            previous_state: Dictionary of previous client states.
        """
        clients_to_remove = [
            cn for cn in previous_state.keys() 
            if cn not in self.active_clients_in_current_log
        ]
        
        for common_name in clients_to_remove:
            if common_name in previous_state:
                prev_state = previous_state[common_name]
                connected_since_full = prev_state.connected_since
                bytes_received_total = prev_state.bytes_received
                bytes_sent_total = prev_state.bytes_sent
                
                try:
                    # Use connected_since from prev_state for monthly grouping
                    year_month = datetime.strptime(
                        connected_since_full, "%Y-%m-%d %H:%M:%S"
                    ).strftime("%Y-%m")
                    
                    traffic = MonthlyTraffic(
                        common_name=common_name,
                        year_month=year_month,
                        bytes_received=bytes_received_total,
                        bytes_sent=bytes_sent_total
                    )
                    self.monthly_traffic_buffer.append(traffic)
                    self.logger.info(
                        f"Prepared monthly traffic for disconnected client {common_name} "
                        f"(R:{bytes_received_total}, S:{bytes_sent_total}) for batch update."
                    )
                except ValueError as e:
                    self.logger.error(
                        f"Error parsing connected_since for disconnected client {common_name}: {e}. "
                        "Skipping monthly traffic update."
                    )
        
        if clients_to_remove:
            self.db_manager.remove_disconnected_clients(clients_to_remove)
