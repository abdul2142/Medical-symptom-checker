"""Local SQLite storage for medicine reminders.

Reminders never leave this machine and CareCheck never generates or alters a
dose: the instruction text is stored exactly as the user entered it from their
own prescription.

Every connection is closed explicitly. ``sqlite3.Connection`` used as a context
manager commits or rolls back the transaction but does *not* close the
connection, so ``with get_connection() as conn`` alone would leave cleanup to
the garbage collector.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, ContextManager

#: Override with the ``CARECHECK_DB`` environment variable (used by the tests).
DEFAULT_DB_PATH = Path(__file__).with_name("health_mock.db")

MAX_NAME_LENGTH = 120
MAX_INSTRUCTIONS_LENGTH = 500

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reminders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name  TEXT NOT NULL,
    instructions   TEXT NOT NULL,
    reminder_time  TEXT NOT NULL,
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders (reminder_time);
"""


def db_path() -> Path:
    """The database file in use, resolved fresh so tests can redirect it."""
    override = os.environ.get("CARECHECK_DB")
    return Path(override) if override else DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a connection with row access by column name.

    Callers are responsible for closing it; prefer :func:`_connect`.
    """
    connection = sqlite3.connect(db_path())
    connection.row_factory = sqlite3.Row
    return connection


def _connect() -> ContextManager[sqlite3.Connection]:
    """A connection that is always closed on exit.

    Pair it with the connection's own context manager when writing
    (``with _connect() as conn, conn:``) so the transaction commits before the
    connection closes.
    """
    return closing(get_connection())


def init_db() -> None:
    """Create the schema if it does not exist. Safe to call on every run."""
    with _connect() as conn, conn:
        conn.executescript(_SCHEMA)


def _require_text(value: str, field: str, limit: int) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} is required.")
    if len(text) > limit:
        raise ValueError(f"{field} must be {limit} characters or fewer.")
    return text


def _require_iso(value: str, field: str) -> str:
    """Reject a timestamp the reader would later choke on.

    Without this an unparseable value could be stored and then crash every
    screen that formats it, with no way to delete the row from the interface.
    """
    text = _require_text(value, field, 64)
    try:
        datetime.fromisoformat(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp.") from exc
    return text


def add_reminder(medicine_name: str, instructions: str, reminder_time: str) -> int:
    """Store one reminder and return its new id.

    Raises ``ValueError`` if a field is blank, over-long, or not a valid
    timestamp, so the storage layer is correct on its own rather than relying on
    the UI to validate first.
    """
    name = _require_text(medicine_name, "Medicine name", MAX_NAME_LENGTH)
    note = _require_text(instructions, "Instructions", MAX_INSTRUCTIONS_LENGTH)
    when = _require_iso(reminder_time, "Reminder time")

    with _connect() as conn, conn:
        cursor = conn.execute(
            "INSERT INTO reminders (medicine_name, instructions, reminder_time) "
            "VALUES (?, ?, ?)",
            (name, note, when),
        )
        return int(cursor.lastrowid)


def get_reminders() -> list[dict[str, Any]]:
    """Every stored reminder, earliest scheduled time first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, medicine_name, instructions, reminder_time, created_at "
            "FROM reminders ORDER BY reminder_time ASC, id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_reminder(reminder_id: int) -> bool:
    """Delete one reminder. Returns True if a row was removed."""
    with _connect() as conn, conn:
        cursor = conn.execute("DELETE FROM reminders WHERE id = ?", (int(reminder_id),))
        return cursor.rowcount > 0


def clear_reminders() -> int:
    """Delete every reminder and return how many were removed."""
    with _connect() as conn, conn:
        cursor = conn.execute("DELETE FROM reminders")
        return cursor.rowcount
