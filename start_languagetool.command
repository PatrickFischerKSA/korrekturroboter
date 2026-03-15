#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LT_HOME="$SCRIPT_DIR/vendor/languagetool/LanguageTool"
LT_JAVA="$SCRIPT_DIR/.lt-java/lib/jvm/bin/java"
LT_PID_FILE="$SCRIPT_DIR/.languagetool.pid"
LT_LOG_FILE="$SCRIPT_DIR/.languagetool.log"

show_error() {
  local message="$1"
  osascript -e "display alert \"LanguageTool konnte nicht gestartet werden.\" message \"${message}\" as critical"
}

if [[ ! -x "$LT_JAVA" ]]; then
  show_error "Die lokale Java-Laufzeit fehlt. Bitte das Projekt erneut einrichten."
  exit 1
fi

if [[ ! -f "$LT_HOME/languagetool-server.jar" ]]; then
  show_error "Der lokale LanguageTool-Server wurde nicht gefunden."
  exit 1
fi

if [[ -f "$LT_PID_FILE" ]]; then
  old_pid="$(cat "$LT_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" >/dev/null 2>&1; then
    open "http://127.0.0.1:8081/v2/check?language=de-CH&text=Das+ist+ein+Tesst"
    exit 0
  fi
fi

cd "$LT_HOME"
nohup "$LT_JAVA" -jar "$LT_HOME/languagetool-server.jar" --port 8081 >"$LT_LOG_FILE" 2>&1 &
echo $! >"$LT_PID_FILE"

for _ in {1..30}; do
  if curl -sf "http://127.0.0.1:8081/v2/languages" >/dev/null 2>&1; then
    open "http://127.0.0.1:8081/v2/check?language=de-CH&text=Das+ist+ein+Tesst"
    exit 0
  fi
  sleep 1
done

DETAILS="Prüfe die Datei .languagetool.log im Projektordner."
if [[ -f "$LT_LOG_FILE" ]]; then
  TAIL_OUTPUT="$(tail -n 8 "$LT_LOG_FILE" | tr '\n' ' ' | sed "s/\"/'/g")"
  if [[ -n "$TAIL_OUTPUT" ]]; then
    DETAILS="$TAIL_OUTPUT"
  fi
fi

show_error "$DETAILS"
exit 1
