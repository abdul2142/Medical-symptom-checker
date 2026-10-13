"""Tests for local reminder storage, against a throwaway database."""

from __future__ import annotations

import sqlite3

import pytest

import database


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Point the storage layer at an empty temporary database."""
    monkeypatch.setenv("CARECHECK_DB", str(tmp_path / "test.db"))
    database.init_db()
    return tmp_path / "test.db"


FUTURE = "2099-01-01T09:00:00"


# --- Schema -----------------------------------------------------------------

def test_init_db_is_idempotent(db):
    database.init_db()
    database.init_db()
    assert database.get_reminders() == []


def test_db_path_follows_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CARECHECK_DB", str(tmp_path / "elsewhere.db"))
    assert database.db_path() == tmp_path / "elsewhere.db"
    monkeypatch.delenv("CARECHECK_DB")
    assert database.db_path() == database.DEFAULT_DB_PATH


# --- Round trip -------------------------------------------------------------

def test_add_and_read_back(db):
    new_id = database.add_reminder("Ibuprofen", "Take as directed", FUTURE)
    [row] = database.get_reminders()

    assert row["id"] == new_id
    assert row["medicine_name"] == "Ibuprofen"
    assert row["instructions"] == "Take as directed"
    assert row["reminder_time"] == FUTURE
    assert row["created_at"]


def test_fields_are_trimmed(db):
    database.add_reminder("  Ibuprofen  ", "  Take as directed  ", FUTURE)
    [row] = database.get_reminders()
    assert row["medicine_name"] == "Ibuprofen"
    assert row["instructions"] == "Take as directed"


def test_reminders_are_ordered_by_time(db):
    database.add_reminder("Later", "x", "2099-06-01T18:00:00")
    database.add_reminder("Sooner", "x", "2099-01-01T08:00:00")
    assert [r["medicine_name"] for r in database.get_reminders()] == ["Sooner", "Later"]


def test_delete_removes_only_that_row(db):
    keep = database.add_reminder("Keep", "x", FUTURE)
    drop = database.add_reminder("Drop", "x", FUTURE)

    assert database.delete_reminder(drop) is True
    assert [r["id"] for r in database.get_reminders()] == [keep]


def test_delete_reports_a_missing_row(db):
    assert database.delete_reminder(4242) is False


def test_clear_reminders_returns_the_count(db):
    database.add_reminder("A", "x", FUTURE)
    database.add_reminder("B", "x", FUTURE)
    assert database.clear_reminders() == 2
    assert database.get_reminders() == []


# --- Validation -------------------------------------------------------------

@pytest.mark.parametrize("name,instructions", [
    ("", "Take as directed"),
    ("   ", "Take as directed"),
    ("Ibuprofen", ""),
    ("Ibuprofen", "   "),
])
def test_blank_fields_are_rejected(db, name, instructions):
    with pytest.raises(ValueError):
        database.add_reminder(name, instructions, FUTURE)
    assert database.get_reminders() == []


@pytest.mark.parametrize("stamp", [
    "not-a-timestamp",
    "2099-13-45T99:99:99",
    "tomorrow",
    "",
    "   ",
])
def test_an_unreadable_timestamp_is_rejected(db, stamp):
    """Regression: a malformed timestamp used to be stored happily, then crash
    every screen that formatted it -- with no way to delete the row from the
    interface."""
    with pytest.raises(ValueError):
        database.add_reminder("Ibuprofen", "Take as directed", stamp)
    assert database.get_reminders() == []


@pytest.mark.parametrize("stamp", [
    "2099-01-01T09:00:00",
    "2099-01-01 09:00:00",
    "2099-01-01T09:00",
    "2099-01-01",
])
def test_valid_iso_timestamps_are_accepted(db, stamp):
    assert database.add_reminder("Ibuprofen", "Take as directed", stamp)


def test_over_long_fields_are_rejected(db):
    with pytest.raises(ValueError, match="characters or fewer"):
        database.add_reminder("x" * 121, "Take as directed", FUTURE)
    with pytest.raises(ValueError, match="characters or fewer"):
        database.add_reminder("Ibuprofen", "y" * 501, FUTURE)
    assert database.get_reminders() == []


def test_a_quote_in_the_name_is_stored_not_executed(db):
    """Parameterised SQL, so punctuation is data rather than syntax."""
    database.add_reminder("Robitussin'); DROP TABLE reminders;--", "x", FUTURE)
    [row] = database.get_reminders()
    assert row["medicine_name"] == "Robitussin'); DROP TABLE reminders;--"


# --- Connection lifetime ----------------------------------------------------

def test_every_connection_is_closed(db, monkeypatch):
    """Regression: ``sqlite3.Connection`` used as a context manager commits the
    transaction but does *not* close the connection, which left cleanup to the
    garbage collector."""
    opened = []
    real_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)

    new_id = database.add_reminder("Ibuprofen", "Take as directed", FUTURE)
    database.get_reminders()
    database.delete_reminder(new_id)

    assert len(opened) == 3
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")


def test_validation_runs_before_any_connection_is_opened(db, monkeypatch):
    """A rejected reminder should not touch the database at all."""
    opened = []
    monkeypatch.setattr(sqlite3, "connect",
                        lambda *args, **kwargs: opened.append(1))

    with pytest.raises(ValueError):
        database.add_reminder("", "Take as directed", FUTURE)

    assert opened == []
