#!/bin/sh
# portbroker installer
#
# This script verifies a supported platform and Python version, downloads the
# stdlib-only portbroker CLI plus its dashboard and agent skill templates into
# the current user's local install directories, and configures detected coding
# agents through `portbroker install-skill`. It makes no network requests other
# than downloading these files from the repository URL below.
#
# Inspect before executing with:
#   curl -fsSLO https://raw.githubusercontent.com/tweakyourpc/portbroker/main/install.sh
#   sh install.sh --dry-run
set -eu

DRY_RUN=false
case "${1:-}" in
  "") ;;
  --dry-run) DRY_RUN=true ;;
  *) printf '%s\n' "usage: sh install.sh [--dry-run]" >&2; exit 2 ;;
esac

case "$(uname -s)" in
  Linux|Darwin) ;;
  *) printf '%s\n' "portbroker supports Linux and macOS only." >&2; exit 1 ;;
esac

command -v python3 >/dev/null 2>&1 || {
  printf '%s\n' "Python 3.11 or later is required." >&2
  exit 1
}
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
  printf '%s\n' "Python 3.11 or later is required." >&2
  exit 1
}
command -v curl >/dev/null 2>&1 || {
  printf '%s\n' "curl is required." >&2
  exit 1
}

REPOSITORY="${PORTBROKER_REPOSITORY:-https://raw.githubusercontent.com/tweakyourpc/portbroker/main}"
BIN_DIR="${HOME}/.local/bin"
DATA_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/portbroker"
BIN_PATH="${BIN_DIR}/portbroker"

if [ "$DRY_RUN" = true ]; then
  printf '%s\n' "Would install: ${BIN_PATH}"
  printf '%s\n' "Would install: ${DATA_DIR}/dashboard.html"
  printf '%s\n' "Would install: ${DATA_DIR}/skills/{claude-code,codex,opencode}.md"
  printf '%s\n' "Would run: ${BIN_PATH} install-skill"
  exit 0
fi

mkdir -p "$BIN_DIR" "$DATA_DIR/skills"
curl -fsSL "$REPOSITORY/portbroker" -o "$BIN_PATH"
curl -fsSL "$REPOSITORY/dashboard.html" -o "$DATA_DIR/dashboard.html"
for skill in claude-code codex opencode; do
  curl -fsSL "$REPOSITORY/skills/$skill.md" -o "$DATA_DIR/skills/$skill.md"
done
chmod +x "$BIN_PATH"

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) printf '%s\n' "Warning: ${BIN_DIR} is not in PATH. Add it before invoking portbroker directly." >&2 ;;
esac

"$BIN_PATH" install-skill

printf '%s\n' "Installed portbroker at ${BIN_PATH}"
printf '%s\n' "Start the dashboard with:"
printf '%s\n' 'PORT="$(portbroker get --name portbroker-dashboard 2>/dev/null || portbroker alloc --name portbroker-dashboard --persistent)" portbroker web --port "$PORT" --persistent'
