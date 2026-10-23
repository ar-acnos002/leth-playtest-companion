#!/bin/bash
source "$(dirname "$0")/launcher-common.sh"
if ! owned_server; then
    echo "No launcher-owned Leth server is running. Nothing was stopped."
    exit 0
fi
kill -TERM "$pid"
attempt=0
while owned_server; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 15 ] || fail "Server is still shutting down; retry later. No forced termination was used."
    sleep 1
done
echo "Leth stopped. Saved sessions are unchanged."
