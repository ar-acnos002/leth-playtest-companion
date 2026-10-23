"""JSON session persistence with atomic replacement."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import UUID, uuid4

from leth.encounter_engine import ALTERNATIVES

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def new_session(name=""):
    now = timestamp()
    return {"id": str(uuid4()), "name": name.strip() or "Untitled session",
            "created_at": now, "updated_at": now, "ended_at": None, "entries": []}


def session_path(session_id, directory=SESSIONS_DIR):
    return Path(directory) / f"{UUID(session_id)}.json"


def save_session(session, directory=SESSIONS_DIR):
    path = session_path(session["id"], directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(export_session(session), encoding="utf-8")
    temporary.replace(path)


def load_session(session_id, directory=SESSIONS_DIR):
    return json.loads(session_path(session_id, directory).read_text(encoding="utf-8"))


def list_sessions(directory=SESSIONS_DIR):
    result = []
    for path in Path(directory).glob("*.json"):
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
            if session_path(session["id"], directory).name != path.name:
                continue
            result.append(session)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(result, key=lambda item: item["updated_at"], reverse=True)


def append_entry(session, context, encounter=None, alternative=None, narrative="", combat=False):
    if session["ended_at"]:
        raise ValueError("Resume the session before adding entries")
    if (encounter is None) == (alternative is None):
        raise ValueError("Supply exactly one encounter or narrative alternative")
    if alternative is not None and alternative not in ALTERNATIVES:
        raise ValueError("Unknown narrative alternative")
    entry = {"id": str(uuid4()), "timestamp": timestamp(),
             **{key: context[key] for key in ("quest_type", "mode", "scene_type", "environment")},
             "entry_type": "encounter" if encounter else "narrative alternative",
             "encounter": deepcopy(encounter), "alternative_type": alternative,
             "narrative": narrative, "combat": bool(combat)}
    session["entries"].append(entry)
    session["updated_at"] = entry["timestamp"]
    return entry


def end_session(session):
    session["ended_at"] = session["updated_at"] = timestamp()


def resume_session(session):
    session["ended_at"] = None
    session["updated_at"] = timestamp()


def export_session(session):
    return json.dumps(session, ensure_ascii=False, indent=2)
