from copy import deepcopy
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import leth.session_manager as manager
from leth.encounter_engine import EncounterEngine
from leth.session_import import import_session
from leth.storage import storage_mode

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


@pytest.fixture
def example():
    session = manager.new_session("Existing journal")
    context = dict(quest_type="FIND", mode="TRAVEL", scene_type="SETUP", environment="ROAD")
    encounter = EncounterEngine().encounters[2]
    manager.append_entry(session, context, encounter=encounter, narrative="A wounded animal", combat=True)
    manager.append_entry(session, context, alternative="Redirect", narrative="")
    return session


def test_storage_default(monkeypatch):
    monkeypatch.delenv("LETH_STORAGE_MODE", raising=False)
    assert storage_mode() == "local"
    assert storage_mode("cloud") == "cloud"
    monkeypatch.setenv("LETH_STORAGE_MODE", "cloud")
    assert storage_mode() == "cloud"
    monkeypatch.setenv("LETH_STORAGE_MODE", "typo")
    with pytest.raises(ValueError):
        storage_mode()


def test_export_import_round_trip(example):
    original = deepcopy(example)
    imported = import_session(manager.export_session(example).encode())
    assert imported == original
    assert json.loads(manager.export_session(imported)) == original
    assert example == original
    assert imported["entries"][0]["combat"] is True
    assert imported["entries"][0]["narrative"] == "A wounded animal"
    assert imported["entries"][1]["alternative_type"] == "Redirect"
    assert imported["entries"][1]["narrative"] == ""


@pytest.mark.parametrize("data", [b'bad', b'\xff', b'[]', b'{}', b'{"entries": []}'])
def test_malformed_import(data):
    with pytest.raises(ValueError):
        import_session(data)


@pytest.mark.parametrize("field,value", [
    ("combat", "true"), ("timestamp", "yesterday"), ("entry_type", "unknown"),
    ("narrative", None), ("encounter", {}), ("environment", "UNKNOWN"),
    ("id", "../outside"),
])
def test_incompatible_entries(example, field, value):
    example["entries"][0][field] = value
    with pytest.raises(ValueError):
        import_session(manager.export_session(example))


def test_import_limit_and_duplicate_ids(example):
    with pytest.raises(ValueError, match="5 MB"):
        import_session(b' ' * (5 * 1024 * 1024 + 1))
    example["entries"][1]["id"] = example["entries"][0]["id"]
    with pytest.raises(ValueError, match="duplicate"):
        import_session(manager.export_session(example))


def test_cloud_isolation_no_disk(monkeypatch):
    monkeypatch.setenv("LETH_STORAGE_MODE", "cloud")

    def forbidden(*args, **kwargs):
        pytest.fail("Cloud mode accessed shared session storage")

    for name in ("save_session", "load_session", "list_sessions", "session_path"):
        monkeypatch.setattr(manager, name, forbidden)
    first, second = AppTest.from_file(APP).run(), AppTest.from_file(APP).run()
    click(first, "Create session")
    click(second, "Create session")
    assert first.session_state.session["id"] != second.session_state.session["id"]
    click(first, "Roll Encounter")
    click(first, "Combat")
    assert len(first.session_state.session["entries"]) == 1
    assert second.session_state.session["entries"] == []
    assert not any(item.label == "Saved sessions" for item in first.selectbox)
    before = deepcopy(first.session_state.session)
    first.run()
    assert first.session_state.session == before
    click(first, "End / close session")  # blocked until acknowledgement
    assert first.session_state.session == before
    first.checkbox[0].check().run()
    click(first, "End / close session")
    assert first.session_state.session is None
    assert second.session_state.session is not None


def test_cloud_import_ui(monkeypatch, example):
    monkeypatch.setenv("LETH_STORAGE_MODE", "cloud")
    def forbidden(*args, **kwargs):
        pytest.fail("Import accessed shared session storage")
    for name in ("save_session", "load_session", "list_sessions"):
        monkeypatch.setattr(manager, name, forbidden)

    # AppTest 1.49 does not expose file-uploader interactions; emulate its return.
    class Upload:
        def getvalue(self):
            return manager.export_session(example).encode()

    import streamlit as st
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: Upload())
    app = AppTest.from_file(APP).run()
    click(app, "Import session")
    assert app.session_state.session == example
    click(app, "Roll Encounter")
    click(app, "Submit")
    assert len(app.session_state.session["entries"]) == 3
    assert app.session_state.session["entries"][:2] == example["entries"]


def test_bad_import_preserves_active_session(monkeypatch):
    monkeypatch.setenv("LETH_STORAGE_MODE", "cloud")
    import streamlit as st
    class Upload:
        def getvalue(self):
            return b'{"not": "a session"}'
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: Upload())
    app = AppTest.from_file(APP).run()
    click(app, "Create session")
    before = deepcopy(app.session_state.session)
    app.checkbox[0].check().run()
    click(app, "Import session")
    assert app.session_state.session == before
    assert any("Could not import" in error.value for error in app.error)


def test_closed_session_can_be_imported(example):
    manager.end_session(example)
    imported = import_session(manager.export_session(example))
    assert imported == example
    manager.resume_session(imported)
    assert imported["ended_at"] is None
    assert imported["entries"] == example["entries"]
