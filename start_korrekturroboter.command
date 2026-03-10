#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! python3 -c "import requests" >/dev/null 2>&1; then
  python3 -m pip install -r requirements.txt
fi

python3 server.py &
SERVER_PID=$!

sleep 2
open "http://127.0.0.1:8090"

wait $SERVER_PID
