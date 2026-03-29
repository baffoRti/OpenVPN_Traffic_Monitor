import sqlite3
from datetime import datetime, timedelta
from ..utils import config # For openvpn_stats_db
from ..utils import utils  # For convert_bytes_to_human_readable


def get_current_month():
    """Return current month in YYYY-MM format."""
    return datetime.now().strftime("%Y-%m")

def get_previous_month():
    """Return previous month in YYYY-MM format."""
    current = datetime.now()
    first_day_of_current_month = current.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    return last_day_of_previous_month.strftime("%Y-%m")

def display_db_contents(db_path, month_filter=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- User traffic monthly ---")
    if month_filter:
        cursor.execute("SELECT * FROM user_traffic_monthly WHERE year_month = ?", (month_filter,))
    else:
        cursor.execute("SELECT * FROM user_traffic_monthly")
    user_traffic_records = cursor.fetchall()
    if user_traffic_records:
        # Sort records alphabetically by common_name
        user_traffic_records.sort(key=lambda x: x[0].lower())
        print("Common Name     | Year-Month | Received Traffic | Sent Traffic | Total Traffic")
        print("-------------------------------------------------------------------------------")
        for row in user_traffic_records:
            common_name, year_month, bytes_received, bytes_sent = row
            total_traffic_bytes = bytes_received + bytes_sent
            human_received = utils.convert_bytes_to_human_readable(bytes_received)
            human_sent = utils.convert_bytes_to_human_readable(bytes_sent)
            human_total = utils.convert_bytes_to_human_readable(total_traffic_bytes)
            print(f"{common_name:<15} | {year_month:<10} | {human_received:<16} | {human_sent:<12} | {human_total:<12}")
    else:
        print("No records found in user_traffic_monthly.")


    print("\n--- Current client state ---")
    cursor.execute("SELECT * FROM current_client_state")
    current_client_state_records = cursor.fetchall()
    if current_client_state_records:
        # Sort records alphabetically by common_name
        current_client_state_records.sort(key=lambda x: x[0].lower())
        print("Common Name     | Connected Since     | Received Traffic | Sent Traffic | Total Traffic")
        print("----------------------------------------------------------------------------------------")
        for row in current_client_state_records:
            common_name, connected_since, bytes_received, bytes_sent = row
            total_traffic_bytes = bytes_received + bytes_sent
            human_received = utils.convert_bytes_to_human_readable(bytes_received)
            human_sent = utils.convert_bytes_to_human_readable(bytes_sent)
            human_total = utils.convert_bytes_to_human_readable(total_traffic_bytes)
            print(f"{common_name:<15} | {connected_since:<19} | {human_received:<16} | {human_sent:<12} | {human_total:<12}")
    else:
        print("No records found in current_client_state.")

    print()
    cursor.execute("SELECT * FROM log_metadata")
    log_metadata_records = cursor.fetchall()
    if log_metadata_records:
        print("Last Updated Time")
        print("--------------------")
        for row in log_metadata_records:
            print(f"{row[1]}")
    else:
        print("No records found in log_metadata.")


    # Display overall monthly traffic summary
    print("\n--- Overall Monthly Traffic Summary ---")
    cursor.execute("SELECT SUM(bytes_received), SUM(bytes_sent) FROM user_traffic_monthly")
    overall_monthly_summary = cursor.fetchone()
    if overall_monthly_summary and overall_monthly_summary[0] is not None:
        overall_received = overall_monthly_summary[0]
        overall_sent = overall_monthly_summary[1]
        overall_total = overall_received + overall_sent
        print(f"Total Received Across All Users: {utils.convert_bytes_to_human_readable(overall_received)}")
        print(f"Total Sent Across All Users:     {utils.convert_bytes_to_human_readable(overall_sent)}")
        print(f"Overall Total Traffic:           {utils.convert_bytes_to_human_readable(overall_total)}")
    else:
        print("No monthly traffic data to summarize.")

    conn.close()


if __name__ == '__main__':
    display_db_contents(config.OPENVPN_STATS_DB)
    print()
