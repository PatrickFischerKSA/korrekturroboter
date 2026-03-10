#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PORT_FILE="$SCRIPT_DIR/.korrekturroboter.port"
PID_FILE="$SCRIPT_DIR/.korrekturroboter.pid"
LOG_FILE="$SCRIPT_DIR/.korrekturroboter.log"

find_free_port() {
  python3 - <<'PY'
import socket
for port in (8090, 8091, 8092, 8093, 8094, 8095, 8765, 8877):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
PY
}

is_running() {
  local port="$1"
  curl -sf "http://127.0.0.1:${port}" >/dev/null 2>&1
}

show_error() {
  local message="$1"
  osascript -e "display alert \"Korrekturroboter konnte nicht gestartet werden.\" message \"${message}\" as critical"
}

PORT=""
if [[ -f "$PORT_FILE" ]]; then
  PORT="$(cat "$PORT_FILE" 2>/dev/null || true)"
fi

if [[ -n "$PORT" ]] && is_running "$PORT"; then
  open "http://127.0.0.1:${PORT}"
  exit 0
fi

PORT="$(find_free_port)"
if [[ -z "$PORT" ]]; then
  show_error "Es ist kein freier lokaler Port verfügbar."
  exit 1
fi

echo "$PORT" >"$PORT_FILE"
KORREKTURROBOTER_PORT="$PORT" nohup python3 server.py >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"

for _ in {1..40}; do
  if is_running "$PORT"; then
    open "http://127.0.0.1:${PORT}"
    exit 0
  fi
  sleep 0.5
done

DETAILS="Prüfe die Datei .korrekturroboter.log im Projektordner."
if [[ -f "$LOG_FILE" ]]; then
  TAIL_OUTPUT="$(tail -n 8 "$LOG_FILE" | tr '\n' ' ' | sed 's/\"/'\"'\"'/g')"
  if [[ -n "$TAIL_OUTPUT" ]]; then
    DETAILS="$TAIL_OUTPUT"
  fi
fi

show_error "$DETAILS"
exit 1
