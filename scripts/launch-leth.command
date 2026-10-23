#!/bin/bash
source "$(dirname "$0")/launcher-common.sh"
[ -x "$PYTHON" ] || fail "Missing .venv/bin/python. Follow the README installation steps first."
cd "$PROJECT_DIR"
if ! owned_server; then
    [ -z "$(port_pids)" ] || fail "Port 8501 is occupied by an unrecognized service. Nothing was opened or stopped. Close that service and retry."
    token="$("$PYTHON" -c 'import secrets; print(secrets.token_hex(16))')"
    printf '%s\n' "$token" > "$STATE_DIR/server.token"
    STREAMLIT_SERVER_COOKIE_SECRET="$token" nohup "$PYTHON" -m streamlit run "$PROJECT_DIR/app.py" \
        --server.address=127.0.0.1 --server.port=8501 --server.headless=true \
        -- "--leth-launch-token=$token" >> "$STATE_DIR/server.log" 2>&1 < /dev/null &
    printf '%s\n' "$!" > "$STATE_DIR/server.pid"
fi
attempt=0
until ready; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 30 ] || fail "Server did not become ready. See .launcher/server.log. Use the stop script before retrying."
    owned_server || fail "Server exited or process identity changed. See .launcher/server.log."
    listeners="$(port_pids)"
    [ -z "$listeners" ] || [ "$listeners" = "$pid" ] || fail "Another service took port 8501. Browser was not opened."
    sleep 1
done
# Recheck ownership immediately before handing the URL to macOS.
ready || fail "Server ownership/readiness changed. Browser was not opened."
/usr/bin/open "$URL"
echo "Leth is running at $URL"
