#!/usr/bin/env bash
# Fast-forward this checkout to origin/master and reinstall the skill when needed.
# Safe to run on a timer: it never merges, rebases, or touches local work.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
SOURCE=.claude/skills/model-router/SKILL.md
INSTALLED="$HOME/.claude/skills/model-router/SKILL.md"

git fetch --quiet origin master

branch="$(git symbolic-ref --quiet --short HEAD || true)"
if [[ "$branch" != master ]]; then
  echo "auto-sync: skipped, checkout is on '${branch:-detached HEAD}', not master" >&2
  exit 0
fi
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "auto-sync: skipped, master has uncommitted changes" >&2
  exit 0
fi

before="$(git rev-parse HEAD)"
if ! git merge --quiet --ff-only origin/master 2>/dev/null; then
  echo "auto-sync: skipped, local master has commits origin/master lacks" >&2
  exit 0
fi

if [[ "$before" == "$(git rev-parse HEAD)" ]] && cmp -s "$SOURCE" "$INSTALLED"; then
  echo "auto-sync: up to date at $(git rev-parse --short HEAD)"
  exit 0
fi
bash sync.sh
echo "auto-sync: installed $(git rev-parse --short HEAD)"
