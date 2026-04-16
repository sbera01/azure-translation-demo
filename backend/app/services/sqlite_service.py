from pathlib import Path
from datetime import datetime, timezone
import sqlite3

_SQLITE_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app_state.db"


def _create_schema_and_seed(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_config (
            config_key TEXT PRIMARY KEY,
            config_value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS translation_cache (
            cache_key TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            target_language TEXT NOT NULL,
            source_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT NOT NULL,
            target_language TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            alt_text_reviewed INTEGER NOT NULL,
            saved_at TEXT NOT NULL
        );
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO app_config (config_key, config_value)
        VALUES (?, ?)
        """,
        ("auto_translate_enabled", "1"),
    )


def _create_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        _SQLITE_DB_PATH,
        timeout=30,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _is_malformed_database_error(error: sqlite3.DatabaseError) -> bool:
    message = str(error).lower()
    markers = (
        "malformed",
        "database disk image",
        "not a database",
        "integrity check failed",
    )
    return any(marker in message for marker in markers)


def _backup_corrupted_database() -> None:
    if not _SQLITE_DB_PATH.exists():
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = _SQLITE_DB_PATH.with_name(
        f"{_SQLITE_DB_PATH.stem}.corrupt-{timestamp}.db"
    )
    _SQLITE_DB_PATH.replace(backup_path)


def _validate_connection(connection: sqlite3.Connection) -> None:
    connection.execute("SELECT COUNT(*) FROM sqlite_master;").fetchone()
    quick_check = connection.execute("PRAGMA quick_check;").fetchone()
    if quick_check is None:
        raise sqlite3.DatabaseError("integrity check failed: no quick_check result")

    if str(quick_check[0]).lower() != "ok":
        raise sqlite3.DatabaseError(f"integrity check failed: {quick_check[0]}")


def get_sqlite_connection() -> sqlite3.Connection:
    _SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection: sqlite3.Connection | None = None
    try:
        connection = _create_connection()
        _validate_connection(connection)
        return connection
    except sqlite3.DatabaseError as error:
        if connection is not None:
            connection.close()

        if not _is_malformed_database_error(error):
            raise

        _backup_corrupted_database()
        recovered_connection = _create_connection()
        _validate_connection(recovered_connection)
        return recovered_connection


def init_sqlite_db() -> None:
    try:
        with get_sqlite_connection() as connection:
            _create_schema_and_seed(connection)
        return
    except sqlite3.DatabaseError as error:
        if not _is_malformed_database_error(error):
            raise

    _backup_corrupted_database()
    with _create_connection() as connection:
        _create_schema_and_seed(connection)
