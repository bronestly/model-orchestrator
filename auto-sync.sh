#!/usr/bin/env bash
# Fast-forward this checkout to origin/master and reinstall the skill when needed.
# Safe to run on a timer: it never merges, rebases, or touches local work. A reason
# to skip exits 0; a failed fast-forward or install exits non-zero.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
MARKER="$HOME/.claude/model-router/installed-commit"

skip() {
  echo "auto-sync: skipped, $1" >&2
  exit 0
}

branch="$(git symbolic-ref --quiet --short HEAD || true)"
[[ "$branch" == master ]] || skip "checkout is on '${branch:-detached HEAD}', not master"
# sync.sh copies the working tree, so untracked drafts in the skill count as local work.
if [[ -n "$(git status --porcelain --untracked-files=no)" ||
      -n "$(git status --porcelain -- .claude/skills/model-router)" ]]; then
  skip "master has uncommitted changes"
fi
git fetch --quiet origin master || skip "could not fetch origin"
git merge-base --is-ancestor HEAD origin/master || skip "local master has commits origin/master lacks"
git merge --quiet --ff-only origin/master

head="$(git rev-parse HEAD)"
if [[ "$(cat "$MARKER" 2>/dev/null || true)" == "$head" ]]; then
  echo "auto-sync: up to date at ${head:0:7}"
  exit 0
fi
bash sync.sh
# Written last, so a failed install is retried on the next run.
printf '%s\n' "$head" > "$MARKER"
echo "auto-sync: installed ${head:0:7}"
