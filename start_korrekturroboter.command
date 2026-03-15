#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/scripts/runtime_helpers.zsh"
PORT_FILE="$SCRIPT_DIR/.korrekturroboter.port"
PID_FILE="$SCRIPT_DIR/.korrekturroboter.pid"
LOG_FILE="$SCRIPT_DIR/.korrekturroboter.log"

start_languagetool_if_available() {
  if [[ ! -f "$SCRIPT_DIR/vendor/languagetool/LanguageTool/languagetool-server.jar" ]]; then
    return 0
  fi

  start_languagetool_server || {
    printf '%s\n' "${LAST_RUNTIME_ERROR:-LanguageTool konnte nicht automatisch gestartet werden.}" >>"$LOG_FILE"
    return 0
  }
}

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

stop_existing_server() {
  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]]; then
      kill "$old_pid" >/dev/null 2>&1 || true
      sleep 0.5
    fi
  fi

  if [[ -f "$PORT_FILE" ]]; then
    local old_port
    old_port="$(cat "$PORT_FILE" 2>/dev/null || true)"
    if [[ -n "$old_port" ]]; then
      local listener_pid
      listener_pid="$(lsof -ti "tcp:${old_port}" 2>/dev/null | head -n 1 || true)"
      if [[ -n "$listener_pid" ]]; then
        kill "$listener_pid" >/dev/null 2>&1 || true
        sleep 0.5
      fi
    fi
  fi
}

show_error() {
  local message="$1"
  osascript -e "display alert \"Korrekturroboter konnte nicht gestartet werden.\" message \"${message}\" as critical"
}

PORT=""
if [[ -f "$PORT_FILE" ]]; then
  PORT="$(cat "$PORT_FILE" 2>/dev/null || true)"
fi

stop_existing_server
start_languagetool_if_available

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
  TAIL_OUTPUT="$(tail -n 8 "$LOG_FILE" | tr '\n' ' ' | sed "s/\"/'/g")"
  if [[ -n "$TAIL_OUTPUT" ]]; then
    DETAILS="$TAIL_OUTPUT"
  fi
fi

show_error "$DETAILS"
exit 1
