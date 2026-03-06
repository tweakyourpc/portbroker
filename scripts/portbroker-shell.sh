#!/usr/bin/env bash

# Source this file from bash or zsh to use the `dev` helper.
# Example:
#   source ~/.config/portbroker/portbroker-shell.sh
#   dev my-app
_portbroker_bin() {
  if [ -n "${PORTBROKER_BIN:-}" ]; then
    printf '%s\n' "$PORTBROKER_BIN"
    return 0
  fi

  if command -v portbroker >/dev/null 2>&1; then
    printf '%s\n' "portbroker"
    return 0
  fi

  echo "portbroker not found in PATH." >&2
  return 127
}

dev() {
  if [ "$#" -ne 1 ]; then
    echo "usage: dev <app-name>" >&2
    return 2
  fi

  local app port broker
  app="$1"
  if ! broker="$(_portbroker_bin)"; then
    return $?
  fi

  # Keep disposable reservations tidy without blocking startup.
  ("$broker" cleanup >/dev/null 2>&1 &) >/dev/null 2>&1

  if ! port="$("$broker" alloc --name "$app" --persistent)"; then
    return $?
  fi

  export PORT="$port"
  npm start
}
