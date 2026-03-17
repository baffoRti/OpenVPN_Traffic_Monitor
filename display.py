import sqlite3
import config  # For openvpn_stats_db
import utils  # For convert_bytes_to_human_readable


def display_db_contents(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- Contents of user_traffic_monthly table ---")
    cursor.execute("SELECT * FROM user_traffic_monthly")
    user_traffic_records = cursor.fetchall()
    if user_traffic_records:
        print("Common Name     | Year-Month | Bytes Received | Bytes Sent")
        print("--------------------------------------------------")
        for row in user_traffic_records:
            common_name, year_month, bytes_received, bytes_sent = row
            human_received = utils.convert_bytes_to_human_readable(bytes_received)
            human_sent = utils.convert_bytes_to_human_readable(bytes_sent)
            print(f"{common_name:<15} | {year_month:<10} | {human_received:<14} | {human_sent:<10}")
    else:
        print("No records found in user_traffic_monthly.")

    print("\n--- Contents of log_metadata table ---")
    cursor.execute("SELECT * FROM log_metadata")
    log_metadata_records = cursor.fetchall()
    if log_metadata_records:
        print("ID | Last Updated Time")
        print("-----------------------")
        for row in log_metadata_records:
            print(f"{row[0]:<2} | {row[1]}")
    else:
        print("No records found in log_metadata.")

    print("\n--- Contents of current_client_state table ---")
    cursor.execute("SELECT * FROM current_client_state")
    current_client_state_records = cursor.fetchall()
    if current_client_state_records:
        print("Common Name     | Connected Since     | Bytes Received | Bytes Sent")
        print("------------------------------------------------------------------")
        for row in current_client_state_records:
            common_name, connected_since, bytes_received, bytes_sent = row
            human_received = utils.convert_bytes_to_human_readable(bytes_received)
            human_sent = utils.convert_bytes_to_human_readable(bytes_sent)
            print(f"{common_name:<15} | {connected_since:<19} | {human_received:<14} | {human_sent:<10}")
    else:
        print("No records found in current_client_state.")

    conn.close()


if __name__ == '__main__':
    # This allows direct execution of display.py for debugging or standalone use.
    # It will connect to the default database defined in config.py.
    print("\n--- Displaying database contents (standalone) ---")
    display_db_contents(config.OPENVPN_STATS_DB)
    print("--- Display complete ---")
