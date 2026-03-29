"""Database manager class for OpenVPN Traffic Monitor."""

import sqlite3
import logging
from typing import Optional
from .models import ClientState, ClientData, MonthlyTraffic, LogMetadata


class DatabaseManager:
    """Manages database operations for OpenVPN Traffic Monitor."""
    
    def __init__(self, db_path: str, logger: logging.Logger):
        """Initialize DatabaseManager.
        
        Args:
            db_path: Path to SQLite database file.
            logger: Logger instance for recording operations.
        """
        self.db_path = db_path
        self.logger = logger
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
    
    def connect(self) -> None:
        """Establish database connection and initialize tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self._init_tables()
            self.logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _init_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_traffic_monthly (
            common_name TEXT NOT NULL,
            year_month TEXT NOT NULL,
            bytes_received INTEGER,
            bytes_sent INTEGER,
            PRIMARY KEY (common_name, year_month)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_updated_time TEXT
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_client_state (
            common_name TEXT NOT NULL PRIMARY KEY,
            connected_since TEXT NOT NULL,
            bytes_received INTEGER,
            bytes_sent INTEGER
        )
        ''')
        
        if self.conn:
            self.conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
    
    def get_last_processed_timestamp(self) -> Optional[str]:
        """Get the last processed timestamp from log_metadata table."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        try:
            self.cursor.execute("SELECT last_updated_time FROM log_metadata ORDER BY id DESC LIMIT 1")
            result = self.cursor.fetchone()
            if result:
                timestamp = result[0]
                self.logger.info(f"Last processed timestamp from DB: {timestamp}")
                return timestamp
        except sqlite3.OperationalError as e:
            self.logger.warning(f"Table log_metadata does not exist: {e}")
        except Exception as e:
            self.logger.error(f"Error fetching last processed timestamp: {e}")
        
        return None
    
    def get_previous_client_state(self) -> dict[str, ClientState]:
        """Get previous client state from current_client_state table."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        previous_state = {}
        try:
            self.cursor.execute("SELECT common_name, connected_since, bytes_received, bytes_sent FROM current_client_state")
            rows = self.cursor.fetchall()
            
            for row in rows:
                common_name, connected_since, bytes_received, bytes_sent = row
                previous_state[common_name] = ClientState(
                    common_name=common_name,
                    connected_since=connected_since,
                    bytes_received=bytes_received,
                    bytes_sent=bytes_sent
                )
            
            self.logger.info(f"Populated previous_client_state with {len(previous_state)} records")
        except sqlite3.OperationalError as e:
            self.logger.warning(f"Table current_client_state does not exist: {e}")
        except Exception as e:
            self.logger.error(f"Error fetching previous client state: {e}")
        
        return previous_state
    
    def batch_update_monthly_traffic(self, traffic_list: list[MonthlyTraffic], batch_size: int = 10) -> None:
        """Batch update monthly traffic statistics.
        
        Args:
            traffic_list: List of MonthlyTraffic objects to process.
            batch_size: Number of operations per batch (default: 10).
        """
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        if not traffic_list:
            return
        
        # Process in batches (no explicit transaction, rely on outer transaction)
        for i in range(0, len(traffic_list), batch_size):
            batch = traffic_list[i:i+batch_size]
            try:
                for traffic in batch:
                    # Use INSERT OR REPLACE for simplicity (UPSERT)
                    # This will replace the entire row, so we need to calculate totals first
                    self.cursor.execute(
                        "SELECT bytes_received, bytes_sent FROM user_traffic_monthly WHERE common_name = ? AND year_month = ?",
                        (traffic.common_name, traffic.year_month)
                    )
                    existing = self.cursor.fetchone()
                    
                    if existing:
                        total_received = existing[0] + traffic.bytes_received
                        total_sent = existing[1] + traffic.bytes_sent
                        self.cursor.execute(
                            "UPDATE user_traffic_monthly SET bytes_received = ?, bytes_sent = ? WHERE common_name = ? AND year_month = ?",
                            (total_received, total_sent, traffic.common_name, traffic.year_month)
                        )
                    else:
                        self.cursor.execute(
                            "INSERT INTO user_traffic_monthly (common_name, year_month, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
                            (traffic.common_name, traffic.year_month, traffic.bytes_received, traffic.bytes_sent)
                        )
                self.logger.debug(f"Processed batch of {len(batch)} monthly traffic updates")
            except sqlite3.Error as e:
                self.logger.error(f"Database error in batch_update_monthly_traffic batch {i//batch_size}: {e}")
                raise
    
    def update_monthly_traffic(self, traffic: MonthlyTraffic) -> None:
        """Update monthly traffic statistics."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        try:
            self.cursor.execute(
                "SELECT bytes_received, bytes_sent FROM user_traffic_monthly WHERE common_name = ? AND year_month = ?",
                (traffic.common_name, traffic.year_month)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                total_received = existing[0] + traffic.bytes_received
                total_sent = existing[1] + traffic.bytes_sent
                self.cursor.execute(
                    "UPDATE user_traffic_monthly SET bytes_received = ?, bytes_sent = ? WHERE common_name = ? AND year_month = ?",
                    (total_received, total_sent, traffic.common_name, traffic.year_month)
                )
                self.logger.debug(f"Updated monthly traffic for {traffic.common_name} ({traffic.year_month})")
            else:
                self.cursor.execute(
                    "INSERT INTO user_traffic_monthly (common_name, year_month, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
                    (traffic.common_name, traffic.year_month, traffic.bytes_received, traffic.bytes_sent)
                )
                self.logger.debug(f"Inserted new monthly traffic for {traffic.common_name} ({traffic.year_month})")
        except sqlite3.Error as e:
            self.logger.error(f"Database error in update_monthly_traffic: {e}")
            raise
    
    def batch_update_current_state(self, client_list: list[ClientData], batch_size: int = 10) -> None:
        """Batch update current client state.
        
        Args:
            client_list: List of ClientData objects to process.
            batch_size: Number of operations per batch (default: 10).
        """
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        if not client_list:
            return
        
        # Prepare data for executemany
        data = [(c.common_name, c.connected_since, c.bytes_received, c.bytes_sent) for c in client_list]
        
        # Process in batches (no explicit transaction)
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            try:
                self.cursor.executemany(
                    "INSERT OR REPLACE INTO current_client_state (common_name, connected_since, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
                    batch
                )
                self.logger.debug(f"Processed batch of {len(batch)} current state updates")
            except sqlite3.Error as e:
                self.logger.error(f"Database error in batch_update_current_state batch {i//batch_size}: {e}")
                raise
    
    def update_current_state(self, client: ClientData) -> None:
        """Update current client state."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO current_client_state (common_name, connected_since, bytes_received, bytes_sent) VALUES (?, ?, ?, ?)",
                (client.common_name, client.connected_since, client.bytes_received, client.bytes_sent)
            )
            self.logger.debug(f"Updated current state for {client.common_name}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error in update_current_state: {e}")
            raise
    
    def remove_disconnected_clients(self, clients_to_remove: list[str]) -> None:
        """Remove disconnected clients from current_client_state table."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        if not clients_to_remove:
            return
        
        try:
            placeholders = ','.join(['?' for _ in clients_to_remove])
            self.cursor.execute(f"DELETE FROM current_client_state WHERE common_name IN ({placeholders})", clients_to_remove)
            self.logger.info(f"Removed {len(clients_to_remove)} disconnected clients")
        except sqlite3.Error as e:
            self.logger.error(f"Database error in remove_disconnected_clients: {e}")
            raise
    
    def update_log_metadata(self, timestamp: Optional[str]) -> None:
        """Update log metadata with the latest timestamp."""
        if not self.cursor:
            raise RuntimeError("Database connection not established")
        
        try:
            self.cursor.execute("DELETE FROM log_metadata")
            if timestamp:
                self.cursor.execute("INSERT INTO log_metadata (last_updated_time) VALUES (?)", (timestamp,))
                self.logger.info(f"Log metadata updated with timestamp: {timestamp}")
            else:
                self.logger.info("No timestamp to store in log_metadata")
        except sqlite3.Error as e:
            self.logger.error(f"Database error in update_log_metadata: {e}")
            raise
    
    def commit(self) -> None:
        """Commit current transaction."""
        if self.conn:
            self.conn.commit()
            self.logger.debug("Transaction committed")