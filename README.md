# Leth Playtest Companion v0.1

A local Streamlit encounter roller with optional journaling for solo Leth playtests.
Requires Python 3.10 or newer.

## Install and run

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`. Open the local URL printed by
Streamlit. No external APIs, database, or account is used.

Create a session or resume a saved one in the sidebar. Select Quest Type, Mode,
Scene Type, and Environment manually, then click **Roll Encounter**. Available
quests and distributions come directly from the supplied rules. Results retain the original scene distribution's relative
frequencies after filtering by environment eligibility.

A roll locks automatically. Unlocking discards that unsubmitted result and permits
a new roll. Changing selectors never rolls or advances play; submission always
uses the context captured with the result. For an empty intersection, choose
Quiet Beat, Redirect, or Misdirect. Submit with an optional narrative, or use Combat
to mark the entry for externally resolved combat. Both actions accept empty text.

In default local mode, sessions save on creation, journal submission, resume, and close in `sessions/`
relative to the project root, even when launched from another working directory.
Closing retains history; resuming reopens the session. Switching or closing sessions
discards unsubmitted drafts. Draft rolls and narrative survive Streamlit reruns but
are temporary and are not restored after a server restart. Saved journals persist.
Export downloads the complete session, including metadata and entries. Timestamps
are UTC, and the journal follows submission order. Back up local session files if
needed; concurrent editing of one session in multiple browser tabs is unsupported.

The three JSON files in `rules/` are authoritative and unchanged. `VALIDATION.md`
documents the supplied rules and expected empty intersections. No combat mechanics,
scene progression, character sheets, or narrative generation are included.

## Tests

```sh
python -m pytest -q
```

## macOS Finder / Dock launcher

After installing into `.venv` above, double-click `scripts/launch-leth.command` in
Finder. It starts the existing Python environment in the background, waits for
Streamlit, then opens `http://127.0.0.1:8501` in your default browser. Terminal may
appear for the `.command` file; use the Automator app below to avoid that window.
The server listens only on the local loopback address. Closing the browser does
not stop it. Double-click `scripts/stop-leth.command` to stop it.

Launching again opens the same launcher-owned server. An unrelated service (or
Leth started manually in Terminal) on port 8501 is refused: close it yourself
before launching. The stop script checks both the recorded PID and a random
per-launch command-line token before sending TERM; it never kills by port or name.
A manually started server is deliberately not adopted or stopped.

Logs append to `.launcher/server.log`; `.launcher/server.pid` and `server.token`
identify the background process. These local files are ignored by Git. A lock
serializes launch/stop operations. If a launcher is forcibly interrupted and leaves
`.launcher/lock`, remove that empty directory only after confirming no launch or
stop operation is active. Existing sessions are never modified by the scripts.
The server runs until stopped or the Mac restarts; launch it again after reboot.

### Create Leth Companion.app

1. Open **Automator**, select **New Document → Application**.
2. Add the **Run Shell Script** action and select `/bin/bash` as the shell.
3. Enter the following, replacing the example with your project's absolute path
   (keep the quotes for paths with spaces):

   ```sh
   /bin/bash "/absolute/path/to/leth-playtest-companion/scripts/launch-leth.command"
   ```

4. Save as **Leth Companion.app** in Applications or another convenient folder.
5. Double-click the app in Finder, or drag it into the Dock and click it there.

Optionally create a second Automator Application named **Stop Leth.app**, using
`stop-leth.command` in the same command. Update these absolute paths if you move
the project. The scripts themselves resolve the project relative to their own
location, regardless of Automator's working directory. No Python packaging or
additional dependencies are required.

### Verify the launcher

- Launch the app: the browser should open only after Leth is ready. Check that
  the journal and saved-session list are available.
- Launch again: `.launcher/server.pid` should stay the same and the existing app
  should open.
- Run the stop app: localhost should stop responding; launch again to restart.
  Saved sessions should still be available.
- Optional port-conflict check: stop Leth, then run
  `.venv/bin/python -m http.server 8501 --bind 127.0.0.1` in Terminal. Launch Leth:
  it should report the occupied port and leave the browser unopened. Stop Leth
  should leave that test service running. Press Control-C in Terminal to end it.
- If startup fails, inspect `.launcher/server.log` and Automator's error message.

## Temporary cloud mode and JSON transfer

Local mode remains the default when `LETH_STORAGE_MODE` is absent. The Mac
Automator launchers need no changes and continue using `sessions/`. Keep cloud
settings out of your local shell and local secrets file unless deliberately testing
cloud mode. Explicit environment values override the app's secrets setting;
values other than `local` or `cloud` stop the app with a configuration error.

To try temporary cloud behavior locally:

```sh
LETH_STORAGE_MODE=cloud .venv/bin/python -m streamlit run app.py
```

Cloud mode keeps only the active session in Streamlit's per-browser-connection
session state. It never lists, loads, or saves `sessions/` files. There is no cloud
sync, database, account, or shared journal library. Browser refresh, disconnection,
closing the tab, or cloud restarts can lose the session and any draft. Two browser
connections have independent copies, even if they import the same session ID.

Use **Export current session JSON** in the sidebar regularly and before leaving.
Only submitted entries are exported: submit a pending roll/narrative first.
Exporting does not end, clear, or change the session. Cloud create/import/close
operations require acknowledgement before replacing an active session; that
acknowledgement cannot protect against browser or server interruptions.

Use **Import Leth session JSON** and **Import session** to continue from an export.
Imports up to 5 MB are checked for metadata, UUIDs, timezone-aware timestamps,
supported context, eligible encounter IDs, narrative alternatives, and field types.
Existing exports need no migration. Journal order, encounter snapshots, narrative,
combat flags, and ISO timestamps are preserved. Importing a closed session reopens
it (clears `ended_at` and updates `updated_at`); entry timestamps stay unchanged.
An invalid import leaves the active session intact. Importing does not write the
uploaded JSON to disk. In local mode, later normal updates/close save the imported
session under its existing ID, potentially replacing that ID's local file; back up
local journals before transferring a different copy of the same session.

## Streamlit Community Cloud deployment (manual)

The application uses `streamlit==1.49.1`, verified by the automated suite, rather
than allowing automatic Streamlit upgrades. Python 3.11 is the tested runtime;
select Python 3.11 in deployment Advanced settings. Dependencies still include
pytest for running the suite; no new runtime dependency was introduced.

When ready to publish separately:

1. Review the Git staging list before publishing. Include `app.py`, `leth/`,
   `requirements.txt`, `.streamlit/config.toml`, and the three authoritative
   `rules/encounters.json`, `rules/scene_pools.json`, and
   `rules/environment_pools.json` files. Keep local journals, exports, `.venv`,
   `.launcher`, logs, and secrets out of Git. Ignore rules cannot remove data
   already committed, and exports placed in arbitrary directories still require
   review. Use the ignored `exports/` folder for personal downloads/backups.
2. On Community Cloud, select the repository/branch and `app.py` entrypoint.
3. In **Advanced settings → Secrets** before the first deployment, enter this
   root-level TOML setting (quotes required):

   ```toml
   LETH_STORAGE_MODE = "cloud"
   ```

   For an existing deployment, use **App settings → Secrets** and save/restart.
   This is the equivalent of setting `LETH_STORAGE_MODE=cloud`. The app reads
   Streamlit secrets and environment configuration; do not put the setting in
   the committed theme config or add the Mac's loopback flags to cloud settings.
4. Confirm the temporary-session warning is shown and no saved-session picker
   appears. Missing the cloud setting intentionally defaults to local mode, so
   verify it before inviting other users.
5. Smoke-test two browser connections, JSON upload/download, session replacement
   confirmation, and import after restarting the app. Separately verify the Mac
   launcher still creates, resumes, exports, and closes local sessions.

Official references:
[deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[app secrets settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings).
