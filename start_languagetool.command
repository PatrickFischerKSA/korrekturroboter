#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/scripts/runtime_helpers.zsh"

show_error() {
  local message="$1"
  osascript -e "display alert \"LanguageTool konnte nicht gestartet werden.\" message \"${message}\" as critical"
}

if [[ ! -f "$SCRIPT_DIR/vendor/languagetool/LanguageTool/languagetool-server.jar" ]]; then
  show_error "Der lokale LanguageTool-Server wurde nicht gefunden."
  exit 1
fi

if start_languagetool_server; then
  open "http://127.0.0.1:8081/v2/check?language=de-CH&text=Das+ist+ein+Tesst"
  exit 0
fi

show_error "${LAST_RUNTIME_ERROR:-Prüfe die Datei .languagetool.log im Projektordner.}"
exit 1
