#!/bin/bash
# Shared by the launch/stop entrypoints. macOS ships Bash 3.2.
set -eu
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
STATE_DIR="$PROJECT_DIR/.launcher"
PYTHON="$PROJECT_DIR/.venv/bin/python"
URL="http://127.0.0.1:8501"
mkdir -p "$STATE_DIR"
fail() { echo "Leth: $*" >&2; exit 1; }
# Serialize starts and stops, including simultaneous Finder launches.
lock_attempt=0
until mkdir "$STATE_DIR/lock" 2>/dev/null; do
    lock_attempt=$((lock_attempt + 1))
    [ "$lock_attempt" -lt 45 ] || fail "Launcher busy. If no launcher is active, remove .launcher/lock and retry."
    sleep 1
done
trap 'rmdir "$STATE_DIR/lock"' EXIT

owned_server() {
    [ -f "$STATE_DIR/server.pid" ] && [ -f "$STATE_DIR/server.token" ] || return 1
    pid="$(cat "$STATE_DIR/server.pid")"
    token="$(cat "$STATE_DIR/server.token")"
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    [ "${#token}" -eq 32 ] || return 1
    command_line="$(ps -ww -p "$pid" -o command= 2>/dev/null)" || return 1
    # Streamlit passes arguments after -- to the app without interpreting them.
    # A reused PID cannot qualify without this launch's random token and app path.
    case "$command_line" in
        *"-m streamlit run $PROJECT_DIR/app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true -- --leth-launch-token=$token") return 0 ;;
        *) return 1 ;;
    esac
}

port_pids() {
    /usr/sbin/lsof -nP -iTCP:8501 -sTCP:LISTEN -t 2>/dev/null | sort -u || true
}

ready() {
    owned_server || return 1
    [ "$(port_pids)" = "$pid" ] || return 1
    "$PYTHON" -c '
import urllib.request
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
    "http://127.0.0.1:8501/_stcore/health", timeout=1
) as response:
    assert response.status == 200 and response.read().strip() == b"ok"
' >/dev/null 2>&1
}
