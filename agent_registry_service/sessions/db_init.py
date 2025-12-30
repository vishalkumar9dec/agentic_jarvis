"""
Database initialization for Session Management.

This module provides functions to initialize and manage the SQLite database
for session tracking, conversation history, and agent invocations.

Features:
- Create database from schema.sql
- Validate schema version
- Provide database connection with proper settings
- Support for migrations (future)
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseInitError(Exception):
    """Exception raised for database initialization errors."""
    pass


def get_schema_path() -> Path:
    """
    Get the path to the schema.sql file.

    Returns:
        Path to schema.sql
    """
    current_dir = Path(__file__).parent
    schema_path = current_dir / "schema.sql"

    if not schema_path.exists():
        raise DatabaseInitError(f"Schema file not found: {schema_path}")

    return schema_path


def initialize_database(db_path: str, force_recreate: bool = False) -> None:
    """
    Initialize the database from schema.sql.

    Args:
        db_path: Path to the SQLite database file
        force_recreate: If True, drop existing tables and recreate

    Raises:
        DatabaseInitError: If initialization fails
    """
    try:
        # Create directory if it doesn't exist
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        conn = get_connection(db_path)

        if force_recreate:
            logger.warning(f"Force recreating database at {db_path}")
            _drop_all_tables(conn)

        # Read and execute schema
        schema_path = get_schema_path()
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema (SQLite supports multiple statements with executescript)
        conn.executescript(schema_sql)
        conn.commit()

        # Verify schema version
        version = get_schema_version(conn)
        logger.info(f"Database initialized successfully (schema version: {version})")

        conn.close()

    except sqlite3.Error as e:
        logger.error(f"SQLite error during initialization: {e}", exc_info=True)
        raise DatabaseInitError(f"Failed to initialize database: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
        raise DatabaseInitError(f"Failed to initialize database: {e}")


def get_connection(db_path: str, timeout: float = 30.0) -> sqlite3.Connection:
    """
    Get a database connection with proper settings.

    Args:
        db_path: Path to the SQLite database file
        timeout: Database timeout in seconds

    Returns:
        SQLite connection with proper configuration

    Note:
        - Foreign keys are enabled
        - Row factory is set to sqlite3.Row for dict-like access
        - WAL mode enabled for better concurrency
    """
    try:
        conn = sqlite3.connect(db_path, timeout=timeout, check_same_thread=False)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Enable Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")

        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn

    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise DatabaseInitError(f"Database connection failed: {e}")


def get_schema_version(conn: sqlite3.Connection) -> Optional[str]:
    """
    Get the current schema version from the database.

    Args:
        conn: Database connection

    Returns:
        Schema version string or None if not found
    """
    try:
        cursor = conn.execute(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row['version'] if row else None

    except sqlite3.Error as e:
        logger.warning(f"Could not retrieve schema version: {e}")
        return None


def verify_schema(conn: sqlite3.Connection) -> bool:
    """
    Verify that all required tables exist.

    Args:
        conn: Database connection

    Returns:
        True if schema is valid, False otherwise
    """
    required_tables = [
        'sessions',
        'conversation_history',
        'agent_invocations',
        'session_context',
        'schema_version'
    ]

    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = {row['name'] for row in cursor.fetchall()}

        missing_tables = set(required_tables) - existing_tables

        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return False

        logger.info("Schema verification successful")
        return True

    except sqlite3.Error as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def _drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables from the database.

    Args:
        conn: Database connection

    Warning:
        This is destructive! Use with caution.
    """
    # Get all table names
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = [row['name'] for row in cursor.fetchall()]

    # Drop all tables
    for table in tables:
        if table != 'sqlite_sequence':  # Don't drop SQLite internal table
            conn.execute(f"DROP TABLE IF EXISTS {table}")

    # Drop all views
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view'"
    )
    views = [row['name'] for row in cursor.fetchall()]

    for view in views:
        conn.execute(f"DROP VIEW IF EXISTS {view}")

    conn.commit()
    logger.info(f"Dropped {len(tables)} tables and {len(views)} views")


def get_database_stats(conn: sqlite3.Connection) -> dict:
    """
    Get statistics about the database.

    Args:
        conn: Database connection

    Returns:
        Dictionary with database statistics
    """
    stats = {}

    try:
        # Count sessions
        cursor = conn.execute("SELECT COUNT(*) as count FROM sessions")
        stats['total_sessions'] = cursor.fetchone()['count']

        # Count messages
        cursor = conn.execute("SELECT COUNT(*) as count FROM conversation_history")
        stats['total_messages'] = cursor.fetchone()['count']

        # Count invocations
        cursor = conn.execute("SELECT COUNT(*) as count FROM agent_invocations")
        stats['total_invocations'] = cursor.fetchone()['count']

        # Count active sessions
        cursor = conn.execute("SELECT COUNT(*) as count FROM sessions WHERE status = 'active'")
        stats['active_sessions'] = cursor.fetchone()['count']

        # Database size
        cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats['database_size_bytes'] = cursor.fetchone()['size']

        return stats

    except sqlite3.Error as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if len(sys.argv) < 2:
        print("Usage: python db_init.py <db_path> [--force-recreate]")
        print("Example: python db_init.py data/sessions.db")
        sys.exit(1)

    db_path = sys.argv[1]
    force_recreate = '--force-recreate' in sys.argv

    try:
        # Initialize database
        print(f"Initializing database at: {db_path}")
        initialize_database(db_path, force_recreate=force_recreate)

        # Verify schema
        conn = get_connection(db_path)
        if verify_schema(conn):
            print("✓ Schema verification passed")

            # Show stats
            stats = get_database_stats(conn)
            print(f"\nDatabase Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        conn.close()
        print(f"\n✓ Database successfully initialized!")

    except DatabaseInitError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
