"""Database operations for OpenVPN Traffic Monitor.

This module provides functions for SQLite database operations
including initialization, queries, and updates.
"""

import sqlite3
import logging


def init_db(db_path: str) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Initialize database and create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_traffic_monthly (
        common_name TEXT NOT NULL,
        year_month TEXT NOT NULL,
        bytes_received INTEGER,
        bytes_sent INTEGER,
        PRIMARY KEY (common_name, year_month)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS log_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_updated_time TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS current_client_state (
        common_name TEXT NOT NULL PRIMARY KEY,
        connected_since TEXT NOT NULL,
        bytes_received INTEGER,
        bytes_sent INTEGER
    )
    ''')
    conn.commit()
    return conn, cursor


def init_tables(conn: sqlite3.Connection) -> sqlite3.Cursor:
    """Initialize database tables using an existing connection."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_traffic_monthly (
        common_name TEXT NOT NULL,
        year_month TEXT NOT NULL,
        bytes_received INTEGER,
        bytes_sent INTEGER,
        PRIMARY KEY (common_name, year_month)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS log_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_updated_time TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS current_client_state (
        common_name TEXT NOT NULL PRIMARY KEY,
        connected_since TEXT NOT NULL,
        bytes_received INTEGER,
        bytes_sent INTEGER
    )
    ''')
    conn.commit()
    return cursor


def get_last_processed_timestamp(cursor: sqlite3.Cursor, logger: logging.Logger) -> str | None:
    """Get the last processed timestamp from log_metadata table."""
    last_processed_timestamp_db = None
    try:
        cursor.execute("SELECT last_updated_time FROM log_metadata ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            last_processed_timestamp_db = result[0]
        logger.info(f"Last processed timestamp from DB: {last_processed_timestamp_db}")
    except sqlite3.OperationalError as e:
        logger.warning(
            f"Table log_metadata does not exist or could not be queried: {e}. last_processed_timestamp_db remains None.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching last processed timestamp: {e}")
    return last_processed_timestamp_db


def get_previous_client_state(cursor: sqlite3.Cursor, logger: logging.Logger) -> dict[str, dict]:
    """Get previous client state from current_client_state table."""
    previous_client_state = {}
    try:
        cursor.execute("SELECT common_name, connected_since, bytes_received, bytes_sent FROM current_client_state")
        rows = cursor.fetchall()

        for row in rows:
            common_name, connected_since, bytes_received, bytes_sent = row
            previous_client_state[common_name] = {
                'connected_since': connected_since,
                'bytes_received': bytes_received,
                'bytes_sent': bytes_sent
            }
        logger.info(
            f"Populated previous_client_state with {len(previous_client_state)} records from current_client_state.")
    except sqlite3.OperationalError as e:
        logger.warning(
            f"Table current_client_state does not exist or could not be queried: {e}. previous_client_state remains empty.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching previous client state: {e}")
    return previous_client_state


def update_monthly_traffic(
    cursor: sqlite3.Cursor,
    common_name: str,
    year_month: str,
    received_bytes: int,
    sent_bytes: int,
    logger: logging.Logger
) -> None:
    """Update monthly traffic statistics for a client."""
    try:
        cursor.execute(
            "SELECT bytes_received, bytes_sent FROM user_traffic_monthly WHERE common_name = ? AND year_month = ?",
            (common_name, year_month)
        )
        existing_entry = cursor.fetchone()

        if existing_entry:
            total_received = existing_entry[0] + received_bytes
            total_sent = existing_entry[1] + sent_bytes
            cursor.execute(
                "UPDATE user_traffic_monthly SET bytes_received = ?, bytes_sent = ? WHERE common_name = ? AND year_month = ?",
                (total_received, total_sent, common_name, year_month)
            )
            logger.debug(f"Updated monthly traffic for {common_name} ({year_month}): +{received_bytes}R, +{sent_bytes}S")
        else:
            cursor.execute(
                "INSERT INTO user_traffic_monthly (common_name, year_month, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
                (common_name, year_month, received_bytes, sent_bytes)
            )
            logger.debug(f"Inserted new monthly traffic for {common_name} ({year_month}): {received_bytes}R, {sent_bytes}S")
    except sqlite3.Error as e:
        logger.error(f"Database error in update_monthly_traffic for {common_name}: {e}")
        raise


def update_current_state(
    cursor: sqlite3.Cursor,
    common_name: str,
    connected_since: str,
    bytes_received: int,
    bytes_sent: int,
    logger: logging.Logger
) -> None:
    """Update current client state."""
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO current_client_state (common_name, connected_since, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
            (common_name, connected_since, bytes_received, bytes_sent)
        )
        logger.debug(
            f"Updated current state for {common_name}. Connected: {connected_since}, R: {bytes_received}, S: {bytes_sent}")
    except sqlite3.Error as e:
        logger.error(f"Database error in update_current_state for {common_name}: {e}")
        raise


def remove_disconnected_clients(
    cursor: sqlite3.Cursor,
    clients_to_remove: list[str],
    logger: logging.Logger
) -> None:
    """Remove disconnected clients from current_client_state table."""
    if clients_to_remove:
        try:
            placeholders = ','.join(['?' for _ in clients_to_remove])
            cursor.execute(f"DELETE FROM current_client_state WHERE common_name IN ({placeholders})", clients_to_remove)
            logger.info(f"Removed disconnected clients from current_client_state: {clients_to_remove}")
        except sqlite3.Error as e:
            logger.error(f"Database error in remove_disconnected_clients: {e}")
            raise


def update_log_metadata(
    cursor: sqlite3.Cursor,
    updated_timestamp_str: str | None,
    logger: logging.Logger
) -> None:
    """Update log metadata with the latest timestamp."""
    try:
        cursor.execute("DELETE FROM log_metadata")
        if updated_timestamp_str:
            cursor.execute("INSERT INTO log_metadata (last_updated_time) VALUES (?) ", (updated_timestamp_str,))
            logger.info(f"Log metadata (last_updated_time: {updated_timestamp_str}) stored.")
        else:
            logger.info("No updated timestamp found to store in log_metadata.")
    except sqlite3.Error as e:
        logger.error(f"Database error in update_log_metadata: {e}")
        raise
