"""Validate existing session JSON without writing files or changing its schema."""
from datetime import datetime
import json
from uuid import UUID

from leth.encounter_engine import ALTERNATIVES, EncounterEngine

MAX_IMPORT_BYTES = 5 * 1024 * 1024


def import_session(data):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def identifier(value, label):
        require(isinstance(value, str), f"{label} must be a UUID string.")
        try:
            UUID(value)
        except ValueError:
            raise ValueError(f"{label} must be a valid UUID.") from None

    def timestamp(value, label):
        require(isinstance(value, str), f"{label} must be an ISO timestamp.")
        try:
            parsed = datetime.fromisoformat(value)
            require(parsed.tzinfo is not None, f"{label} must include a timezone offset.")
        except ValueError as exc:
            raise ValueError(f"{label} must be an ISO timestamp with a timezone offset.") from exc

    require(isinstance(data, (str, bytes)), "Upload a JSON text file.")
    require(len(data.encode('utf-8') if isinstance(data, str) else data) <= MAX_IMPORT_BYTES,
            "Session file exceeds the 5 MB limit.")
    try:
        session = json.loads(data)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("File is not valid UTF-8 JSON.") from None
    require(isinstance(session, dict), "Session must be a JSON object.")
    required = {"id", "name", "created_at", "updated_at", "ended_at", "entries"}
    require(required <= session.keys(), "Missing required session metadata or entries.")
    identifier(session["id"], "Session ID")
    require(isinstance(session["name"], str), "Session name must be text.")
    for key in ("created_at", "updated_at"):
        timestamp(session[key], key)
    if session["ended_at"] is not None:
        timestamp(session["ended_at"], "ended_at")
    require(isinstance(session["entries"], list), "Entries must be a list.")
    engine = EncounterEngine()
    seen = set()
    for index, entry in enumerate(session["entries"], 1):
        label = f"Entry {index}"
        fields = {"id", "timestamp", "quest_type", "mode", "scene_type", "environment",
                  "entry_type", "encounter", "alternative_type", "narrative", "combat"}
        require(isinstance(entry, dict) and fields <= entry.keys(), f"{label}: missing required fields.")
        identifier(entry["id"], f"{label} ID")
        require(entry["id"] not in seen, f"{label}: duplicate entry ID.")
        seen.add(entry["id"])
        timestamp(entry["timestamp"], f"{label} timestamp")
        require(all(isinstance(entry[key], str) for key in
                    ("quest_type", "mode", "scene_type", "environment")), f"{label}: invalid context.")
        try:
            eligible = engine.eligible_ids(*(entry[key] for key in
                                            ("quest_type", "mode", "scene_type", "environment")))
        except KeyError:
            raise ValueError(f"{label}: unsupported rules context.") from None
        require(isinstance(entry["narrative"], str), f"{label}: narrative must be text.")
        require(type(entry["combat"]) is bool, f"{label}: combat must be true or false.")
        if entry["entry_type"] == "encounter":
            encounter = entry["encounter"]
            require(isinstance(encounter, dict), f"{label}: encounter must be an object.")
            require(type(encounter.get("id")) is int and encounter["id"] in eligible,
                    f"{label}: encounter ID is not eligible for its context.")
            require(all(isinstance(encounter.get(key), str) and encounter[key]
                        for key in ("name", "description")), f"{label}: encounter name/description missing.")
            require(entry["alternative_type"] is None, f"{label}: encounter cannot also be an alternative.")
        else:
            require(entry["entry_type"] == "narrative alternative", f"{label}: unknown entry type.")
            require(entry["encounter"] is None and entry["alternative_type"] in ALTERNATIVES,
                    f"{label}: invalid narrative alternative.")
    return session
