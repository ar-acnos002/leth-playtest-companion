"""Exercise actual Streamlit callbacks and reruns using isolated persistence."""
from functools import partial
from pathlib import Path
from streamlit.testing.v1 import AppTest
import leth.session_manager as manager


def button(app, label):
    return next(item for item in app.button if item.label == label)


def select(app, label, value):
    next(item for item in app.selectbox if item.label == label).select(value).run()


def test_roll_submit_and_empty_intersection(tmp_path, monkeypatch):
    monkeypatch.delenv("LETH_STORAGE_MODE", raising=False)
    for name in ("save_session", "load_session", "list_sessions"):
        monkeypatch.setattr(manager, name, partial(getattr(manager, name), directory=tmp_path))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    button(app, "Create session").click().run()
    button(app, "Roll Encounter").click().run()
    assert not app.exception
    assert button(app, "Roll Encounter").disabled
    original = app.session_state.pending.copy()
    select(app, "Environment", "ROAD")
    assert app.session_state.pending == original
    app.run()
    assert app.session_state.pending == original
    button(app, "Combat").click().run()
    assert not app.exception
    entries = app.session_state.session["entries"]
    assert len(entries) == 1 and entries[0]["combat"]
    assert entries[0]["environment"] == "TYRANNY"
    assert entries[0]["narrative"] == ""
    app.run()
    assert len(app.session_state.session["entries"]) == 1
    button(app, "Roll Encounter").click().run()
    app.toggle[0].set_value(False).run()
    assert app.session_state.pending is None
    assert len(app.session_state.session["entries"]) == 1
    select(app, "Scene Type", "CULMINATION")
    select(app, "Environment", "VILLAGE")
    button(app, "Roll Encounter").click().run()
    assert app.session_state.pending["encounter"] is None
    app.radio[0].set_value("Redirect").run()
    button(app, "Submit").click().run()
    assert not app.exception
    entries = app.session_state.session["entries"]
    assert len(entries) == 2
    assert entries[-1]["alternative_type"] == "Redirect"
    assert not entries[-1]["combat"]
    assert app.session_state.narrative == ""
    button(app, "End / close session").click().run()
    assert app.session_state.session is None
    button(app, "Resume session").click().run()
    assert len(app.session_state.session["entries"]) == 2
    assert not app.exception
