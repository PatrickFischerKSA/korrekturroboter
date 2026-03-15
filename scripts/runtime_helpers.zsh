#!/bin/zsh

RUNTIME_ROOT="${HOME}/.korrekturroboter-runtime"
JAVA_PREFIX="$RUNTIME_ROOT/openjdk-21"
JAVA_BIN="$JAVA_PREFIX/lib/jvm/bin/java"
RUNTIME_LOG_FILE="$SCRIPT_DIR/.runtime-bootstrap.log"

find_conda_bin() {
  local candidate
  for candidate in \
    "${CONDA_EXE:-}" \
    "$(command -v conda 2>/dev/null)" \
    "/opt/anaconda3/bin/conda" \
    "/opt/homebrew/Caskroom/miniforge/base/bin/conda" \
    "/usr/local/Caskroom/miniforge/base/bin/conda" \
    "$HOME/miniforge3/bin/conda" \
    "$HOME/mambaforge/bin/conda" \
    "$HOME/anaconda3/bin/conda"
  do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

runtime_note() {
  local message="$1"
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" >>"$RUNTIME_LOG_FILE"
}

ensure_local_java() {
  mkdir -p "$RUNTIME_ROOT"

  if [[ -x "$JAVA_BIN" ]]; then
    return 0
  fi

  local conda_bin
  conda_bin="$(find_conda_bin)" || {
    LAST_RUNTIME_ERROR="Es wurde keine lokale conda-Installation gefunden. Bitte Anaconda oder Miniforge installieren."
    runtime_note "$LAST_RUNTIME_ERROR"
    return 1
  }

  runtime_note "Lokale Java-Laufzeit wird ueber $conda_bin eingerichtet."
  if ! "$conda_bin" create -y -p "$JAVA_PREFIX" -c conda-forge openjdk=21 >>"$RUNTIME_LOG_FILE" 2>&1; then
    LAST_RUNTIME_ERROR="Die lokale Java-Laufzeit konnte nicht eingerichtet werden. Details stehen in .runtime-bootstrap.log."
    runtime_note "$LAST_RUNTIME_ERROR"
    return 1
  fi

  if [[ ! -x "$JAVA_BIN" ]]; then
    LAST_RUNTIME_ERROR="Java wurde installiert, aber der erwartete Startpfad fehlt."
    runtime_note "$LAST_RUNTIME_ERROR"
    return 1
  fi

  runtime_note "Lokale Java-Laufzeit ist bereit."
  return 0
}

pid_is_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

wait_for_languagetool() {
  local tries="${1:-30}"
  local delay="${2:-1}"
  local i
  for i in $(seq 1 "$tries"); do
    if curl -sf "http://127.0.0.1:8081/v2/languages" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

start_languagetool_server() {
  LT_HOME="$SCRIPT_DIR/vendor/languagetool/LanguageTool"
  LT_PID_FILE="$SCRIPT_DIR/.languagetool.pid"
  LT_LOG_FILE="$SCRIPT_DIR/.languagetool.log"

  if [[ ! -f "$LT_HOME/languagetool-server.jar" ]]; then
    LAST_RUNTIME_ERROR="Der lokale LanguageTool-Server wurde im Projekt nicht gefunden."
    runtime_note "$LAST_RUNTIME_ERROR"
    return 1
  fi

  ensure_local_java || return 1

  if pid_is_running "$LT_PID_FILE"; then
    return 0
  fi

  runtime_note "LanguageTool wird lokal auf Port 8081 gestartet."
  (
    cd "$LT_HOME" || exit 1
    nohup "$JAVA_BIN" -jar "$LT_HOME/languagetool-server.jar" --port 8081 >"$LT_LOG_FILE" 2>&1 &
    echo $! >"$LT_PID_FILE"
  )

  if wait_for_languagetool 30 1; then
    runtime_note "LanguageTool ist erreichbar."
    return 0
  fi

  LAST_RUNTIME_ERROR="LanguageTool konnte lokal nicht gestartet werden. Details stehen in .languagetool.log."
  runtime_note "$LAST_RUNTIME_ERROR"
  return 1
}
