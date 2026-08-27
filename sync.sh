#!/usr/bin/env bash
# Install all model-router host adapters from this repository.
# Global skill directories are build artifacts; edit this repository, then run:
#   bash sync.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SRC="$REPO_ROOT/.claude/skills/model-router"
CODEX_ADAPTER="$CLAUDE_SRC/adapters/codex.md"
GROK_ADAPTER="$CLAUDE_SRC/adapters/grok.md"
CLAUDE_DEST="$HOME/.claude/skills/model-router"
CODEX_DEST="$HOME/.agents/skills/model-router"
GROK_DEST="$HOME/.grok/skills/model-router"
LOGDIR="$HOME/.claude/model-router"

if [[ ! -f "$CLAUDE_SRC/SKILL.md" || ! -f "$CODEX_ADAPTER" || ! -f "$GROK_ADAPTER" ]]; then
  echo "Missing a required model-router adapter under $CLAUDE_SRC" >&2
  exit 1
fi

# Registry <-> allowlist drift guard.
# The capability registry in references/routing-reference.md owns every CLI command
# the skill prescribes. If one of those commands is not pre-authorized in the Claude
# adapter's allowed-tools, the skill prescribes a call it cannot make — the exact
# defect this guard exists to catch. Refuse to install rather than ship that.
REGISTRY="$CLAUDE_SRC/references/routing-reference.md"

# Commands: the first backticked span of each row in the "Invocation shapes" table.
registry_commands() {
  awk '
    /^### Invocation shapes/ { inblock = 1; next }
    inblock && /^#/          { inblock = 0 }
    inblock && /^\|/ {
      if (match($0, /`[^`]+`/)) print substr($0, RSTART + 1, RLENGTH - 2)
    }
  ' "$REGISTRY"
}

# Patterns: the contents of each Bash(...) entry, with any trailing glob removed.
allowlist_patterns() {
  awk '
    /^allowed-tools:/       { inblock = 1; next }
    inblock && /^[^ \t-]/   { inblock = 0 }
    inblock && match($0, /Bash\([^)]*\)/) {
      pattern = substr($0, RSTART + 5, RLENGTH - 6)
      sub(/\*$/, "", pattern)
      sub(/[ \t]+$/, "", pattern)
      if (pattern != "") print pattern
    }
  ' "$CLAUDE_SRC/SKILL.md"
}

ALLOWLIST="$(allowlist_patterns)"
drift=0
while IFS= read -r command; do
  [[ -n "$command" ]] || continue
  # Compare only the concrete prefix — everything before the first <placeholder>.
  concrete="$(awk '{
    for (i = 1; i <= NF; i++) {
      if (index($i, "<") > 0) break
      printf "%s%s", (i > 1 ? " " : ""), $i
    }
  }' <<<"$command")"
  [[ -n "$concrete" ]] || continue

  authorized=0
  while IFS= read -r pattern; do
    [[ -n "$pattern" ]] || continue
    # Trailing space on both sides keeps "agy -p" from matching "agy -print".
    if [[ "$concrete " == "$pattern "* ]]; then
      authorized=1
      break
    fi
  done <<<"$ALLOWLIST"

  if (( authorized == 0 )); then
    echo "Registry command is not in the Claude adapter's allowed-tools:" >&2
    echo "  registry: $concrete" >&2
    echo "  fix:      add 'Bash($concrete *)' to SKILL.md, with its PowerShell twin." >&2
    echo "            Any shorter prefix of that command also satisfies the guard;" >&2
    echo "            prefer the shortest one that stays unambiguous." >&2
    drift=1
  fi
done <<<"$(registry_commands)"

if (( drift != 0 )); then
  echo "Refusing to install: routing-reference.md and SKILL.md disagree." >&2
  exit 1
fi

# Copy logic with fallback if rsync is unavailable (e.g. minimal container environments)
copy_dir_clean() {
  local src="$1" dest="$2" exclude_pattern="$3"
  if command -v rsync >/dev/null 2>&1; then
    if [[ -n "$exclude_pattern" ]]; then
      rsync -a --delete --delete-excluded --exclude "$exclude_pattern" --exclude '.DS_Store' "$src/" "$dest/"
    else
      rsync -a --delete --exclude '.DS_Store' "$src/" "$dest/"
    fi
  else
    rm -rf "$dest"
    mkdir -p "$dest"
    if [[ -n "$exclude_pattern" ]]; then
      (cd "$src" && tar -cf - --exclude="$exclude_pattern" --exclude='.DS_Store' .) | (cd "$dest" && tar -xf -)
    else
      cp -R "$src/." "$dest/"
      rm -f "$dest/.DS_Store"
    fi
  fi
}

# Claude receives its adapter and the shared references, not the other host sources.
mkdir -p "$CLAUDE_DEST"
copy_dir_clean "$CLAUDE_SRC" "$CLAUDE_DEST" "adapters/"

# Codex and Grok each receive their adapter as SKILL.md plus the same shared references.
stage_and_install_host() {
  local adapter_src="$1" dest="$2" label="$3"
  local stage
  stage="$(mktemp -d "${TMPDIR:-${TEMP:-/tmp}}/model-router-${label}.XXXXXX")"
  if [[ -z "$stage" || ! -d "$stage" ]]; then
    echo "Could not create the $label staging directory" >&2
    exit 1
  fi
  mkdir -p "$stage/references" "$dest"
  cp "$adapter_src" "$stage/SKILL.md"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '.DS_Store' "$CLAUDE_SRC/references/" "$stage/references/"
    rsync -a --delete "$stage/" "$dest/"
  else
    cp -R "$CLAUDE_SRC/references/." "$stage/references/"
    rm -f "$stage/references/.DS_Store"
    copy_dir_clean "$stage" "$dest" ""
  fi
  rm -rf -- "$stage"
}

stage_and_install_host "$CODEX_ADAPTER" "$CODEX_DEST" "codex"
stage_and_install_host "$GROK_ADAPTER" "$GROK_DEST" "grok"

# Preserve machine-local state and source pointer. Shared state is configured
# separately with state.sh and is never copied into an installed package.
mkdir -p "$LOGDIR"
printf '%s\n' "$REPO_ROOT" > "$LOGDIR/source-repo"
if [[ ! -f "$LOGDIR/routing-notes.local.md" ]]; then
  cat > "$LOGDIR/routing-notes.local.md" <<'NOTES'
# model-router — device-local observations

Record only facts specific to this device: CLI availability, auth/tier status,
paths, or repository quirks. Never put credentials or secrets here.

## Entries
<!-- newest first -->
NOTES
  echo "Seeded device-local notes at $LOGDIR/routing-notes.local.md"
fi

echo "Installed Claude adapter: $CLAUDE_DEST"
echo "Installed Codex adapter:  $CODEX_DEST"
echo "Installed Grok adapter:   $GROK_DEST"
echo "Source repo registered:   $REPO_ROOT"
