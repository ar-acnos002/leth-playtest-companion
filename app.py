"""Run with: streamlit run app.py."""
from copy import deepcopy
import streamlit as st

from leth.storage import storage_mode
from leth.session_import import import_session
from leth.display import format_journal_timestamp
from leth.encounter_engine import ALTERNATIVES, EncounterEngine
from leth.session_manager import (
    append_entry, end_session, export_session, list_sessions, load_session,
    new_session, resume_session, save_session,
)

st.set_page_config(page_title="Leth Playtest Companion", page_icon="📖")

# Streamlit themes use primaryColor for focus as well as toggle accents.
# Override only valid text fields; retain native red validation/error styling.
st.markdown(
    """
    <style>
    :is([data-testid="stTextInput"], [data-testid="stTextArea"])
    :is([data-baseweb="input"], [data-baseweb="textarea"]):focus-within:not(:has([aria-invalid="true"])) {
        border-color: #C7CBC9;
        box-shadow: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    configured_mode = st.secrets.get("LETH_STORAGE_MODE")
except FileNotFoundError:
    configured_mode = None
try:
    CLOUD_MODE = storage_mode(configured_mode) == "cloud"
except ValueError as exc:
    st.error(str(exc))
    st.stop()


def persist(session):
    if not CLOUD_MODE:
        save_session(session)


def replacement_allowed():
    if CLOUD_MODE and st.session_state.session and not st.session_state.get("discard_confirmed", False):
        st.warning("Export your journal, then confirm replacement or closing in the sidebar.")
        return False
    return True


def clear_draft():
    st.session_state.pending = None
    st.session_state.locked = False
    st.session_state.narrative = ""
    st.session_state.alternative = ALTERNATIVES[0]


def activate(session):
    st.session_state.session = session
    clear_draft()
    st.session_state.pop("discard_confirmed", None)


def unlock():
    if not st.session_state.locked:
        st.session_state.pending = None


def submit(combat=False):
    pending = st.session_state.pending
    if not pending:
        return
    # Persist a copy first; a failed write leaves the draft available to retry.
    session = deepcopy(st.session_state.session)
    append_entry(session, pending["context"], encounter=pending["encounter"],
                 alternative=st.session_state.alternative if pending["encounter"] is None else None,
                 narrative=st.session_state.narrative, combat=combat)
    try:
        persist(session)
    except OSError as exc:
        st.session_state.error = f"Could not save journal: {exc}"
        return
    st.session_state.session = session
    clear_draft()


if "session" not in st.session_state:
    st.session_state.session = None
    clear_draft()

st.title("Leth Playtest Companion")
try:
    engine = EncounterEngine()
except (OSError, ValueError, KeyError) as exc:
    st.error(f"Could not load rules: {exc}")
    st.stop()

if CLOUD_MODE:
    st.warning("Cloud sessions are temporary. Export JSON regularly to preserve progress. "
               "Refresh, disconnection, or a cloud restart can lose this session and its draft.")

with st.sidebar:
    st.header("Session")
    if st.session_state.session:
        current = st.session_state.session
        st.download_button("Export current session JSON", export_session(current),
                           file_name=f'leth-{current["id"]}.json', mime="application/json")
        st.caption("Exports include submitted entries only. Submit your draft before exporting.")
        if CLOUD_MODE:
            st.checkbox("I exported my progress or accept losing it when replacing/closing this session",
                        key="discard_confirmed")
    name = st.text_input("New session name (optional)")
    if st.button("Create session") and replacement_allowed():
        session = new_session(name)
        try:
            persist(session)
            activate(session)
            st.rerun()
        except OSError as exc:
            st.error(f"Could not create session: {exc}")
    uploaded = st.file_uploader("Import Leth session JSON (up to 5 MB)", type=["json"])
    if st.button("Import session", disabled=uploaded is None) and replacement_allowed():
        try:
            imported = import_session(uploaded.getvalue())
            if imported["ended_at"]:
                resume_session(imported)
            activate(imported)
            st.rerun()
        except ValueError as exc:
            st.error(f"Could not import session: {exc}")
    if not CLOUD_MODE:
        saved = list_sessions()
        if saved:
            by_id = {item["id"]: item for item in saved}
            selected = st.selectbox("Saved sessions", list(by_id), format_func=lambda sid:
                                    f'{by_id[sid]["name"]} · {by_id[sid]["created_at"]}')
            if st.button("Resume session"):
                try:
                    session = load_session(selected)
                    resume_session(session)
                    persist(session)
                    activate(session)
                    st.rerun()
                except (OSError, ValueError) as exc:
                    st.error(f"Could not resume session: {exc}")
    if st.session_state.session and st.button("End / close session") and replacement_allowed():
        session = deepcopy(st.session_state.session)
        end_session(session)
        try:
            persist(session)
            activate(None)
            st.rerun()
        except OSError as exc:
            st.error(f"Could not close session: {exc}")
    st.caption("Creating, importing, resuming, or closing a session discards its unsubmitted draft.")
    if not CLOUD_MODE:
        st.caption("Imports stay in memory until the next journal update or close, which saves "
                   "using the imported ID and may replace the corresponding local session.")
    st.header("Context")
    quest = st.selectbox("Quest Type", list(engine.scene_pools))
    mode = st.selectbox("Mode", list(engine.scene_pools[quest]))
    scene = st.selectbox("Scene Type", list(engine.scene_pools[quest][mode]))
    environment = st.selectbox("Environment", list(engine.environment_pools))

session = st.session_state.session
if not session:
    st.info("Create or import a session to begin." if CLOUD_MODE else "Create, resume, or import a session to begin.")
    st.stop()
st.subheader(session["name"])
if "error" in st.session_state:
    st.error(st.session_state.pop("error"))
context = dict(quest_type=quest, mode=mode, scene_type=scene, environment=environment)
def roll_encounter():
    encounter = engine.roll(**context)
    st.session_state.pending = {"context": context.copy(), "encounter": encounter}
    st.session_state.locked = True


roll_column, lock_column = st.columns(2)
with roll_column:
    st.button("Roll Encounter", disabled=st.session_state.locked, on_click=roll_encounter)
with lock_column:
    st.toggle("Encounter locked", key="locked", on_change=unlock,
              disabled=st.session_state.pending is None)

pending = st.session_state.pending
if pending:
    st.caption("Rolled context: " + " / ".join(pending["context"].values()))
    if pending["context"] != context:
        st.info("Context changed. Submission will use the rolled context shown above.")
    if pending["encounter"]:
        st.subheader(pending["encounter"]["name"])
        st.write(pending["encounter"]["description"])
    else:
        st.info("No eligible encounter. Choose a narrative alternative.")
        st.radio("Alternative", ALTERNATIVES, key="alternative", horizontal=True)
st.text_area("Narrative (optional)", key="narrative")
left, right = st.columns(2)
left.button("Submit", disabled=pending is None, on_click=submit)
right.button("Combat", disabled=pending is None, on_click=submit, args=(True,))
st.caption("Unlocking discards the unsubmitted result. Combat is resolved externally.")

st.subheader("Chronological journal")
for entry in session["entries"]:
    title = entry["encounter"]["name"] if entry["encounter"] else entry["alternative_type"]
    with st.expander(f'{format_journal_timestamp(entry["timestamp"])} · {title}' + (" · Combat" if entry["combat"] else "")):
        st.caption(" / ".join(entry[key] for key in ("quest_type", "mode", "scene_type", "environment")))
        if entry["encounter"]:
            st.write(entry["encounter"]["description"])
        if entry["narrative"]:
            st.write(entry["narrative"])
if not session["entries"]:
    st.caption("No entries yet.")
st.download_button("Export session JSON", export_session(session),
                   file_name=f'leth-{session["id"]}.json', mime="application/json")
