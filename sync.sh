#!/usr/bin/env bash
# Install both model-router host adapters from this repository.
# Global skill directories are build artifacts; edit this repository, then run:
#   bash sync.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SRC="$REPO_ROOT/.claude/skills/model-router"
CODEX_ADAPTER="$CLAUDE_SRC/adapters/codex.md"
CLAUDE_DEST="$HOME/.claude/skills/model-router"
CODEX_DEST="$HOME/.agents/skills/model-router"
LOGDIR="$HOME/.claude/model-router"

if [[ ! -f "$CLAUDE_SRC/SKILL.md" || ! -f "$CODEX_ADAPTER" ]]; then
  echo "Missing a required model-router adapter under $CLAUDE_SRC" >&2
  exit 1
fi

# Claude receives its adapter and the shared references, not the Codex source.
mkdir -p "$CLAUDE_DEST"
rsync -a --delete --delete-excluded \
  --exclude 'adapters/' \
  --exclude '.DS_Store' \
  "$CLAUDE_SRC/" "$CLAUDE_DEST/"

# Codex receives its adapter as SKILL.md plus the same shared references.
CODEX_STAGE="$(mktemp -d "${TMPDIR:-/tmp}/model-router-codex.XXXXXX")"
if [[ -z "$CODEX_STAGE" || ! -d "$CODEX_STAGE" ]]; then
  echo "Could not create the Codex staging directory" >&2
  exit 1
fi
trap 'rm -rf -- "$CODEX_STAGE"' EXIT
mkdir -p "$CODEX_STAGE/references" "$CODEX_DEST"
cp "$CODEX_ADAPTER" "$CODEX_STAGE/SKILL.md"
rsync -a --exclude '.DS_Store' "$CLAUDE_SRC/references/" "$CODEX_STAGE/references/"
rsync -a --delete "$CODEX_STAGE/" "$CODEX_DEST/"

# Preserve the existing Claude-host calibration memory and source pointer.
mkdir -p "$LOGDIR"
printf '%s\n' "$REPO_ROOT" > "$LOGDIR/source-repo"
if [[ ! -f "$LOGDIR/routing-notes.md" ]]; then
  cat > "$LOGDIR/routing-notes.md" <<'NOTES'
# model-router — calibration log (Claude host, machine-local)

Record only persistent routing observations. Keep this file under roughly 15
live entries and never put secrets in it. Codex intentionally has no shared
mutable calibration state.

## Entries
<!-- newest first -->
NOTES
  echo "Seeded new calibration log at $LOGDIR/routing-notes.md"
fi

echo "Installed Claude adapter: $CLAUDE_DEST"
echo "Installed Codex adapter:  $CODEX_DEST"
echo "Source repo registered:   $REPO_ROOT"
