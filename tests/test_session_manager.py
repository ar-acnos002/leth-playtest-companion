import json
import pytest
from leth.encounter_engine import ALTERNATIVES
from leth.session_manager import (
    append_entry, end_session, export_session, list_sessions, load_session,
    new_session, resume_session, save_session,
)

CONTEXT = dict(quest_type="FIND", mode="TRAVEL", scene_type="SETUP", environment="ROAD")
ENCOUNTER = dict(id=2, name="Ailing", description="Full description")


def test_save_load_and_order(tmp_path):
    session = new_session("Test")
    first = append_entry(session, CONTEXT, encounter=ENCOUNTER)
    second = append_entry(session, CONTEXT, encounter=ENCOUNTER, combat=True)
    save_session(session, tmp_path)
    loaded = load_session(session["id"], tmp_path)
    assert loaded == session
    assert [entry["id"] for entry in loaded["entries"]] == [first["id"], second["id"]]
    assert first["id"] != second["id"]
    assert first["timestamp"] <= second["timestamp"]
    assert first["narrative"] == ""
    assert first["combat"] is False
    assert second["combat"] is True
    assert json.loads(export_session(session)) == session
    assert list_sessions(tmp_path) == [session]


@pytest.mark.parametrize("alternative", ALTERNATIVES)
def test_alternatives(alternative):
    session = new_session()
    entry = append_entry(session, CONTEXT, alternative=alternative)
    assert entry["entry_type"] == "narrative alternative"
    assert entry["alternative_type"] == alternative
    assert entry["narrative"] == ""
    assert entry["encounter"] is None
    assert all(entry[key] == value for key, value in CONTEXT.items())


def test_close_resume_and_snapshot(tmp_path):
    session = new_session()
    context, encounter = CONTEXT.copy(), ENCOUNTER.copy()
    append_entry(session, context, encounter=encounter, narrative="A note")
    context["mode"] = "EXPLORE"
    encounter["name"] = "Changed"
    assert session["entries"][0]["mode"] == "TRAVEL"
    assert session["entries"][0]["encounter"]["name"] == "Ailing"
    end_session(session)
    save_session(session, tmp_path)
    with pytest.raises(ValueError):
        append_entry(session, CONTEXT, encounter=ENCOUNTER)
    restored = load_session(session["id"], tmp_path)
    assert restored["ended_at"]
    resume_session(restored)
    assert restored["ended_at"] is None
    assert len(restored["entries"]) == 1


def test_invalid_entries_and_paths(tmp_path):
    session = new_session()
    with pytest.raises(ValueError):
        append_entry(session, CONTEXT)
    with pytest.raises(ValueError):
        append_entry(session, CONTEXT, alternative="Unknown")
    with pytest.raises(ValueError):
        load_session("../outside", tmp_path)
