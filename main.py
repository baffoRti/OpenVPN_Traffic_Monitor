import config
import utils
import database
import parser
import sys
from datetime import datetime  # Import datetime here to avoid circular dependency issues if not already imported above


def main():
    # Setup logging
    logger = utils.setup_logging(config.OPENVPN_STATS_LOGS)
    logger.info("Application started.")

    # Clean old logs
    utils.clean_old_logs(config.OPENVPN_STATS_LOGS, config.LOG_DAYS_TO_KEEP, logger)

    # Initialize DB connection and tables
    conn, cursor = database.init_db(config.OPENVPN_STATS_DB)

    # Get last processed timestamp from DB
    last_processed_timestamp_db = database.get_last_processed_timestamp(cursor, logger)

    # Parse current OpenVPN log for client data and updated timestamp
    client_list_data, updated_timestamp_str = parser.parse_openvpn_log(config.STATUS_LOGS)

    if not client_list_data:
        logger.error("No client data found in the OpenVPN log file. Exiting.")
        conn.close()
        sys.exit(1)

    # Compare timestamps and conditionally execute
    if updated_timestamp_str and last_processed_timestamp_db and updated_timestamp_str == last_processed_timestamp_db:
        logger.info(
            f"OpenVPN status log has not been updated since last processing ({updated_timestamp_str}). Skipping data processing.")
        conn.close()
        sys.exit(0)
    else:
        logger.info("OpenVPN status log has been updated or not processed before. Proceeding with data processing.")

        # Get previous client state from DB
        previous_client_state = database.get_previous_client_state(cursor, logger)

        # Track active clients in the current log
        active_clients_in_current_log = set()

        # Process each client in the current OpenVPN log data
        for client in client_list_data:
            common_name = client['Common Name']
            active_clients_in_current_log.add(common_name)

            try:
                connected_since_str_full = client['Connected Since']
                connected_since_str = connected_since_str_full.split(' ')[0]  # 'YYYY-MM-DD'
                bytes_received_current = int(client['Bytes Received'])
                bytes_sent_current = int(client['Bytes Sent'])
                year_month = datetime.strptime(connected_since_str, "%Y-%m-%d").strftime("%Y-%m")
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing client data for {common_name}: {e}. Skipping client.")
                continue

            if common_name in previous_client_state:
                prev_state = previous_client_state[common_name]
                prev_connected_since = prev_state['connected_since']

                if connected_since_str_full != prev_connected_since:
                    # New session detected
                    logger.info(
                        f"Client {common_name}: New session detected. Previous session data will be added to monthly traffic.")
                    # Update current state buffer with current session details
                    database.update_current_state(cursor, common_name, connected_since_str_full, bytes_received_current,
                                                  bytes_sent_current, logger)
                    # Add full current session traffic to monthly (as if previous session ended and new started)
                    database.update_monthly_traffic(cursor, common_name, year_month, bytes_received_current,
                                                    bytes_sent_current, logger)
                else:
                    # Continuing session
                    prev_bytes_received = prev_state['bytes_received']
                    prev_bytes_sent = prev_state['bytes_sent']

                    # Calculate incremental traffic
                    delta_received = bytes_received_current - prev_bytes_received
                    delta_sent = bytes_sent_current - prev_bytes_sent

                    # Ensure deltas are not negative (can happen on server restarts or log resets)
                    if delta_received < 0 or delta_sent < 0:
                        logger.warning(
                            f"Client {common_name}: Negative traffic delta detected (R:{delta_received}, S:{delta_sent}). This might indicate a log reset or server restart. Resetting deltas to current values.")
                        delta_received = bytes_received_current
                        delta_sent = bytes_sent_current

                    logger.info(
                        f"Client {common_name}: Continuing session. Incremental traffic R:{delta_received}, S:{delta_sent}")
                    # Add incremental traffic to monthly
                    database.update_monthly_traffic(cursor, common_name, year_month, delta_received, delta_sent, logger)
                    # Update current state buffer with new cumulative values
                    database.update_current_state(cursor, common_name, connected_since_str_full, bytes_received_current,
                                                  bytes_sent_current, logger)
            else:
                # New client detected
                logger.info(
                    f"Client {common_name}: New client detected. Initial traffic R:{bytes_received_current}, S:{bytes_sent_current}")
                # Insert into current state buffer
                database.update_current_state(cursor, common_name, connected_since_str_full, bytes_received_current,
                                              bytes_sent_current, logger)
                # Add initial traffic to monthly
                database.update_monthly_traffic(cursor, common_name, year_month, bytes_received_current,
                                                bytes_sent_current, logger)

        # Handle disconnected clients
        clients_to_remove = [cn for cn in previous_client_state.keys() if cn not in active_clients_in_current_log]
        for common_name in clients_to_remove:
            if common_name in previous_client_state:
                prev_state = previous_client_state[common_name]
                connected_since_full = prev_state['connected_since']
                bytes_received_total = prev_state['bytes_received']
                bytes_sent_total = prev_state['bytes_sent']

                try:
                    # Use connected_since_full from prev_state as it's the timestamp for the session being closed
                    year_month_disc = datetime.strptime(connected_since_full, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")
                    database.update_monthly_traffic(cursor, common_name, year_month_disc, bytes_received_total,
                                                    bytes_sent_total, logger)
                    logger.info(
                        f"Moved total traffic for disconnected client {common_name} (R:{bytes_received_total}, S:{bytes_sent_total}) to monthly stats.")
                except ValueError as e:
                    logger.error(
                        f"Error parsing connected_since for disconnected client {common_name}: {e}. Skipping monthly traffic update.")

        database.remove_disconnected_clients(cursor, clients_to_remove, logger)
        conn.commit()
        logger.info("Client traffic updates and current state processing complete.")

        # Update log metadata
        database.update_log_metadata(cursor, updated_timestamp_str, logger)
        conn.commit()
        logger.info("Log metadata update complete.")

    conn.close()
    logger.info("Application finished.")


if __name__ == '__main__':
    main()
