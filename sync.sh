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

# Registry <-> allowlist posture guard.
# The capability registry in references/routing-reference.md owns every CLI command
# the skill prescribes and, per command, the prefix the owner pre-authorized. The
# Claude adapter's allowed-tools must list exactly those prefixes (Bash entries with
# PowerShell twins), and each prefix must start its own command. A missing entry
# means the skill prescribes a call it cannot make; an extra or shortened entry
# silently widens the permission posture. Refuse to install in either case.
REGISTRY="$CLAUDE_SRC/references/routing-reference.md"

# Rows of the "Invocation shapes" table as "<command>\t<prefix>": the first and
# second backticked spans of each row.
registry_rows() {
  awk '
    /^### Invocation shapes/ { inblock = 1; next }
    inblock && /^#/          { inblock = 0 }
    inblock && /^\|/ && match($0, /`[^`]+`/) {
      command = substr($0, RSTART + 1, RLENGTH - 2)
      rest = substr($0, RSTART + RLENGTH)
      prefix = match(rest, /`[^`]+`/) ? substr(rest, RSTART + 1, RLENGTH - 2) : ""
      print command "\t" prefix
    }
  ' "$REGISTRY"
}

# Patterns: the contents of each <kind>(...) entry, with any trailing glob removed.
# Only one "  - Bash(...)" or "  - PowerShell(...)" entry per line is understood; any
# other line in the block is printed as "unsupported: <line>" so the set comparison
# fails instead of silently skipping an entry. A bare "*" grant prints as "*".
allowlist_patterns() {
  awk -v kind="$1" '
    /^allowed-tools:/       { inblock = 1; next }
    inblock && /^[^ \t-]/   { inblock = 0 }
    inblock {
      sub(/\r$/, "")
      if ($0 ~ /^[ \t]*$/) next
      if ($0 !~ /^  - (Bash|PowerShell)\([^)]+\)$/) { print "unsupported: " $0; next }
      if (index($0, "  - " kind "(") != 1) next
      pattern = substr($0, length(kind) + 6, length($0) - length(kind) - 6)
      sub(/\*$/, "", pattern)
      sub(/[ \t]+$/, "", pattern)
      print (pattern == "" ? "*" : pattern)
    }
  ' "$CLAUDE_SRC/SKILL.md"
}

drift=0
while IFS=$'\t' read -r command prefix; do
  [[ -n "$command" ]] || continue
  # Trailing space on both sides keeps "agy -p" from matching "agy -print".
  if [[ -z "$prefix" || "$command " != "$prefix "* ]]; then
    echo "Registry row's pre-authorized prefix does not start its command:" >&2
    echo "  command: $command" >&2
    echo "  prefix:  ${prefix:-<none>}" >&2
    drift=1
  fi
done <<<"$(registry_rows)"

# The `command -v` probe is not a route, so it has no registry row.
EXPECTED="$( { echo 'command -v'; registry_rows | cut -f2; } | sed '/^$/d' | sort -u)"
BASH_SET="$(allowlist_patterns Bash | sort -u)"
PS_SET="$(allowlist_patterns PowerShell | sed 's/^Get-Command$/command -v/' | sort -u)"
for kind in Bash PowerShell; do
  if [[ "$kind" == Bash ]]; then actual="$BASH_SET"; else actual="$PS_SET"; fi
  if [[ "$actual" != "$EXPECTED" ]]; then
    echo "SKILL.md $kind(...) allowed-tools differ from the registry's pre-authorized prefixes" >&2
    echo "  (< registry, > SKILL.md; PowerShell Get-Command shown as command -v):" >&2
    diff <(printf '%s\n' "$EXPECTED") <(printf '%s\n' "$actual") | grep '^[<>]' | sed 's/^/  /' >&2 || true
    drift=1
  fi
done

if (( drift != 0 )); then
  echo "Refusing to install: routing-reference.md and SKILL.md disagree." >&2
  echo "Widening a prefix is the owner's decision; make it in the registry first." >&2
  exit 1
fi

# Agent-definition <-> registry guard. The registry owns model IDs; each native agent
# definition pins one, so it must appear in the registry's host-native table.
AGENTS_SRC="$CLAUDE_SRC/agents"
AGENTS_DEST="$HOME/.claude/agents"
# Model IDs: the backticked second column of the host-native table only.
NATIVE_MODELS="$(awk -F'|' '
  /^\| Codename \| Model ID \|/ { inblock = 1; next }
  inblock && !/^\|/             { exit }
  inblock && match($3, /`[^`]+`/) { print substr($3, RSTART + 1, RLENGTH - 2) }
' "$REGISTRY")"
agents=("$AGENTS_SRC"/mr-*.md)
if [[ ! -f "${agents[0]}" ]]; then
  echo "No mr-*.md agent definitions under $AGENTS_SRC" >&2
  echo "Refusing to install: restore the agents/ source directory." >&2
  exit 1
fi
for agent in "${agents[@]}"; do
  model="$(awk '/^model:/ { sub(/\r$/, ""); print $2; exit }' "$agent")"
  if [[ -z "$model" ]] || ! grep -qxF -- "$model" <<<"$NATIVE_MODELS"; then
    echo "Agent definition pins a model the registry does not list:" >&2
    echo "  agent: $agent" >&2
    echo "  model: ${model:-<none>}" >&2
    echo "Refusing to install: add it to the host-native table or fix the definition." >&2
    exit 1
  fi
done

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

# Native Claude agent definitions. Only the mr-* prefix is owned here; other user
# agents in ~/.claude/agents are left alone.
mkdir -p "$AGENTS_DEST"
rm -f "$AGENTS_DEST"/mr-*.md
cp "$AGENTS_SRC"/mr-*.md "$AGENTS_DEST/"

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

# Post-install check: every installed package must match its source exactly, so a
# copy or path error fails here instead of shipping a package with broken links.
install_mismatch=0
check_same() {
  local label="$1" src="$2" dest="$3"
  shift 3
  # diff compares a file with a same-named file inside a directory, so require types to match.
  if [[ -f "$src" && ! -f "$dest" ]] || ! diff -rq -x '.DS_Store' "$@" "$src" "$dest" >&2; then
    echo "Installed $label does not match its source: $dest" >&2
    install_mismatch=1
  fi
}
check_same "Claude package" "$CLAUDE_SRC" "$CLAUDE_DEST" -x adapters
if [[ -e "$CLAUDE_DEST/adapters" ]]; then
  echo "Installed Claude package contains the other hosts' adapters/: $CLAUDE_DEST" >&2
  install_mismatch=1
fi
for host in codex grok; do
  if [[ "$host" == codex ]]; then adapter="$CODEX_ADAPTER" dest="$CODEX_DEST"; else adapter="$GROK_ADAPTER" dest="$GROK_DEST"; fi
  check_same "$host adapter" "$adapter" "$dest/SKILL.md"
  check_same "$host references" "$CLAUDE_SRC/references" "$dest/references"
  if [[ "$(ls -A "$dest" | grep -vx '.DS_Store' | LC_ALL=C sort | tr '\n' ' ')" != "SKILL.md references " ]]; then
    echo "Installed $host package has unexpected top-level entries: $dest" >&2
    install_mismatch=1
  fi
done
for agent in "${agents[@]}"; do
  check_same "agent $(basename "$agent")" "$agent" "$AGENTS_DEST/$(basename "$agent")"
done
if (( install_mismatch != 0 )); then
  echo "Install verification failed; fix sync.sh or the source tree and rerun." >&2
  exit 1
fi

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
echo "Installed agents:         $AGENTS_DEST/mr-*.md"
echo "Source repo registered:   $REPO_ROOT"
