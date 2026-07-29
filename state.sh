#!/usr/bin/env bash
# Configure and explicitly synchronize a private model-router state checkout.
set -euo pipefail

LOGDIR="$HOME/.claude/model-router"
POINTER="$LOGDIR/state-repo"
DEVICE_FILE="$LOGDIR/device-id"

usage() {
  echo "Usage: bash state.sh configure <state-repo> | pull | push | status" >&2
  exit 2
}

state_repo() {
  if [[ ! -f "$POINTER" ]]; then
    echo "Shared state is not configured; run: bash state.sh configure <state-repo>" >&2
    exit 1
  fi
  local repo
  repo="$(<"$POINTER")"
  if [[ ! -d "$repo/.git" || ! -f "$repo/calibration.md" ]]; then
    echo "Configured state checkout is invalid: $repo" >&2
    exit 1
  fi
  printf '%s\n' "$repo"
}

configure() {
  [[ $# -eq 1 ]] || usage
  local repo device
  repo="$(cd "$1" && pwd)"
  if [[ ! -d "$repo/.git" || ! -f "$repo/calibration.md" ]]; then
    echo "State checkout must be a Git repository containing calibration.md: $repo" >&2
    exit 1
  fi
  mkdir -p "$LOGDIR"
  printf '%s\n' "$repo" > "$POINTER"
  if [[ ! -s "$DEVICE_FILE" ]]; then
    device="$(hostname | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9._-' '-')"
    printf '%s\n' "${device%-}" > "$DEVICE_FILE"
  fi
  echo "Configured shared state: $repo"
  echo "Device id: $(<"$DEVICE_FILE")"
}

pull_state() {
  local repo
  repo="$(state_repo)"
  if [[ -n "$(git -C "$repo" status --porcelain)" ]]; then
    echo "State checkout has local changes; push them before pulling." >&2
    exit 1
  fi
  git -C "$repo" pull --rebase
}

push_state() {
  local repo device timestamp
  repo="$(state_repo)"
  device="$(<"$DEVICE_FILE")"
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git -C "$repo" add -- calibration.md events archive
  if ! git -C "$repo" diff --cached --quiet; then
    git -C "$repo" commit -m "sync routing state: $device $timestamp"
  fi
  git -C "$repo" pull --rebase
  git -C "$repo" push
}

case "${1:-}" in
  configure)
    shift
    configure "$@"
    ;;
  pull)
    [[ $# -eq 1 ]] || usage
    pull_state
    ;;
  push)
    [[ $# -eq 1 ]] || usage
    push_state
    ;;
  status)
    [[ $# -eq 1 ]] || usage
    git -C "$(state_repo)" status -sb
    ;;
  *)
    usage
    ;;
esac
