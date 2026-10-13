"""Integration tests that drive the real Streamlit app headlessly.

These run the actual script through ``AppTest``, covering the wiring that unit
tests cannot: session state, form submission, and the rendered markup. No
network access occurs -- the medicine tab is not exercised here.

One regression is pinned deliberately: a reminder row whose stored timestamp
cannot be parsed must not take down the interface. It previously raised while
rendering, which killed *every* tab including the symptom checker, and left no
way to delete the offending row.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Point the app at an empty temporary database."""
    path = tmp_path / "app.db"
    monkeypatch.setenv("CARECHECK_DB", str(path))
    return path


def launch():
    return AppTest.from_file(APP, default_timeout=180).run()


def markup(app) -> str:
    return " ".join(block.value for block in app.markdown)


def analyse(app, text):
    app.text_area(key="symptom_text").set_value(text).run()
    next(b for b in app.button if "Analyse" in str(b.label)).click().run()
    return app


def insert_raw(path: Path, name: str, instructions: str, stamp: str) -> None:
    """Write a row straight to SQLite, bypassing validation.

    This is how a row written by an older build would look.
    """
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS reminders ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_name TEXT NOT NULL,"
            "instructions TEXT NOT NULL, reminder_time TEXT NOT NULL,"
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT INTO reminders (medicine_name, instructions, reminder_time) "
                     "VALUES (?, ?, ?)", (name, instructions, stamp))


# --- Smoke ------------------------------------------------------------------

def test_app_renders_without_exceptions(db):
    app = launch()
    assert not app.exception
    assert len(app.tabs) == 4


def test_the_safety_notice_is_always_present(db):
    assert "not a medical device" in markup(launch())


# --- Triage paths -----------------------------------------------------------

def test_an_emergency_is_announced_as_an_alert(db):
    app = analyse(launch(), "sudden chest pain and trouble breathing")
    rendered = markup(app)

    assert not app.exception
    assert app.session_state["last"]["result"]["doctor_status"] == "urgent"
    assert 'class="cc-banner is-urgent"' in rendered
    assert 'role="alert">' in rendered


def test_a_mild_result_is_a_status_not_an_alert(db):
    app = analyse(launch(), "runny nose and sneezing")
    rendered = markup(app)

    assert app.session_state["last"]["result"]["doctor_status"] == "monitor"
    assert 'class="cc-banner"' in rendered
    assert 'role="status">' in rendered
    assert 'role="alert">' not in rendered


def test_the_reading_quality_card_is_not_called_confidence(db):
    """It measures text parsing, and must never read as diagnostic certainty."""
    rendered = markup(analyse(launch(), "sore throat and fever for 2 days"))
    assert "How well your text was read" in rendered
    assert "Not diagnostic certainty" in rendered
    assert "Assessment confidence" not in rendered


def test_an_empty_description_is_refused(db):
    app = launch()
    next(b for b in app.button if "Analyse" in str(b.label)).click().run()
    assert "last" not in app.session_state
    assert any("at least one symptom" in str(e.value) for e in app.error)


# --- Reminders --------------------------------------------------------------

def test_a_reminder_can_be_saved(db):
    app = launch()
    next(t for t in app.text_input if t.label == "Medicine name").set_value("Ibuprofen").run()
    next(t for t in app.text_input
         if t.label == "Instructions as prescribed").set_value("Take as directed").run()
    app.checkbox[0].set_value(True).run()
    next(b for b in app.button if "Save reminder" in str(b.label)).click().run()

    assert not app.exception
    import database
    assert [r["medicine_name"] for r in database.get_reminders()] == ["Ibuprofen"]


def test_an_unreadable_timestamp_does_not_crash_the_app(db):
    """Regression: this used to raise while rendering and kill every tab."""
    insert_raw(db, "Legacy Med", "Take one", "not-a-timestamp")
    app = launch()

    assert not app.exception, [str(e.value) for e in app.exception]
    rendered = markup(app)
    assert "Legacy Med" in rendered
    assert "Unreadable date" in rendered
    assert "Needs attention" in rendered


def test_an_unreadable_timestamp_is_excluded_from_the_upcoming_count(db):
    insert_raw(db, "Legacy Med", "Take one", "not-a-timestamp")
    insert_raw(db, "Good Med", "Take two", "2099-01-01T09:00:00")
    app = launch()

    assert not app.exception
    # One upcoming reminder, not two, and not a crash.
    assert '<div class="cc-v">1</div>' in markup(app)


def test_a_mix_of_readable_and_unreadable_rows_all_render(db):
    insert_raw(db, "Past Med", "x", "2000-01-01T09:00:00")
    insert_raw(db, "Future Med", "y", "2099-01-01T09:00:00")
    insert_raw(db, "Broken Med", "z", "???")
    rendered = markup(launch())

    for name in ("Past Med", "Future Med", "Broken Med"):
        assert name in rendered
    assert ">Past<" in rendered
    assert ">Upcoming<" in rendered
    assert ">Needs attention<" in rendered
