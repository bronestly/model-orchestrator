#!/usr/bin/env bash
# Sync the model-router skill source -> installed copy, and register this repo
# as the source of truth for this machine. Self-locating: works from wherever
# the repo is cloned, so no machine ever needs a hand-edited path.
#
#   bash sync.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO_ROOT/.claude/skills/model-router"
DEST="$HOME/.claude/skills/model-router"
LOGDIR="$HOME/.claude/model-router"

# 1. Sync skill source -> installed copy (the installed copy is a build artifact).
mkdir -p "$DEST"
rsync -a --delete "$SRC/" "$DEST/"

# 2. Stamp this machine's repo root so the self-improvement flow can find the
#    source of truth without any hardcoded path.
mkdir -p "$LOGDIR"
printf '%s\n' "$REPO_ROOT" > "$LOGDIR/source-repo"

# 3. Seed the machine-local calibration log ONLY if missing — never clobber
#    accumulated notes.
if [ ! -f "$LOGDIR/routing-notes.md" ]; then
  cat > "$LOGDIR/routing-notes.md" <<'NOTES'
# model-router — calibration log (machine-local)

Durable cross-session memory for the model-router skill. Read at every invocation.
Machine-local, NOT version-controlled — this file is not in the source repo.

- **Source repo (this machine):** see `$HOME/.claude/model-router/source-repo` (auto-stamped by sync.sh).
- **Sync repo -> installed copy:** `bash "$(cat "$HOME/.claude/model-router/source-repo")/sync.sh"`
- **Edit the skill source at:** `$(cat "$HOME/.claude/model-router/source-repo")/.claude/skills/model-router/SKILL.md`

## How to use this file
- Append one dated line per real learning: `YYYY-MM-DD · <what happened> · route:<row>`.
- Don't log routine success; the signal is rare. Keep under ~15 live entries; prune promoted/superseded ones.
- **Machine-specific facts** (a CLI's auth/tier dead on this box, a repo's build quirks) stay here only — never promote; they may be false on another machine.
- **Universal judgment calls** (a task type routes better elsewhere; a model renamed/re-tiered) are promotion candidates once the same signal recurs across 2-3 unrelated sessions. Promote via the approval-gated flow in `references/vs-mode.md`: edit the SOURCE REPO SKILL.md (path above), then run the sync command above. Never hand-edit the installed copy.

## Entries
<!-- newest first -->
NOTES
  echo "Seeded new calibration log at $LOGDIR/routing-notes.md"
fi

echo "Synced $SRC -> $DEST"
echo "Source repo registered: $REPO_ROOT"
