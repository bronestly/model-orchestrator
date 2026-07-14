# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is the **source-of-truth repo for the `model-router` Claude Code skill** — not an application. There is no build, lint, or test tooling; the only "artifact" is `.claude/skills/model-router/SKILL.md` plus its `references/` files, and the only "deployment" is rsyncing that source into the user's global `~/.claude/skills/model-router/`.

The skill itself teaches a Claude Code session (running as Fable 5 or Opus 4.8) to act as an orchestrator: decompose a task, route each piece to the cheapest model/CLI that can do it well (Codex Sol/Terra/Luna, Grok 4.5, Gemini 3.5 Flash, or a Sonnet/Opus subagent), delegate with a strict prompt contract, verify real evidence before integrating, and record calibration notes across sessions.

## Repo layout

- `.claude/skills/model-router/SKILL.md` — the skill itself: routing table, CLI invocation reference, delegation contract, failure handling, self-improvement flow. This is the single file that matters most; read it in full before editing anything else.
- `.claude/skills/model-router/references/` — supporting docs loaded on demand by the skill (not proactively loaded, so keep each self-contained):
  - `codex-delegation.md` — Codex Sol/Terra/Luna effort defaults and burn-control guidance
  - `grok-delegation.md` — Grok 4.5 prompt-steering and known failure modes
  - `vs-mode.md` — the model-comparison protocol and the self-improvement/promotion flow
  - `x-research.md` — real-time/X research delegation guide
- `sync.sh` — self-locating script: rsyncs `.claude/skills/model-router/` → `~/.claude/skills/model-router/` (the installed copy, a build artifact) and stamps this repo's path into `~/.claude/model-router/source-repo` so the self-improvement flow can find its way back here from any machine.
- `model-router-workspace/` — gitignored scratch area (eval benchmarks, research notes, versioned skill snapshots). Not part of the shipped skill; safe to treat as disposable working notes.

## Working in this repo

**Editing the skill:** always edit the source at `.claude/skills/model-router/SKILL.md` (and `references/`), never the installed copy at `~/.claude/skills/model-router/` — the installed copy is overwritten by every `sync.sh` run.

**Propagating changes:** after editing, run `bash sync.sh` to sync source → installed copy. This also seeds (but never clobbers) the machine-local calibration log at `~/.claude/model-router/routing-notes.md`.

**Calibration memory is intentionally out-of-repo:** `~/.claude/model-router/routing-notes.md` is machine-local and NOT version-controlled — it accumulates dated, real-world routing observations (dead CLIs, model behavior drift) between sessions. Only notes that recur across 2-3 unrelated sessions and are universal (not machine-specific) get promoted into the versioned `SKILL.md` routing table, via the approval-gated flow described in `references/vs-mode.md`. Don't shortcut this by editing the routing table directly from a single anecdote.

**Versioning convention:** `SKILL.md` frontmatter carries a `metadata.version` (semver-ish) and `updated` date, and the bottom "Maintenance" section keeps a dated changelog of what changed and why in each version bump. Follow this pattern when making non-trivial edits — bump the version, add a dated changelog entry, and keep benchmark numbers/percentage claims out of the file since they go stale silently.

## Key design decisions to preserve

These are load-bearing choices already made in `SKILL.md` — don't casually reverse them without understanding why (each is explained inline in the skill):

- Never route work to Haiku (quality floor); cheapest permitted Claude worker is Sonnet.
- Never auto-escalate Codex to `ultra` effort, and never enable Codex fast mode (2.5x credit multiplier).
- External CLI legs must be short, fresh, and self-contained — no long-running continuations.
- Delegation prompts require an explicit MUST/NEVER constraint list, a scope lock with stop points, and a structured JSON return (not a transcript); a worker's self-reported "done" is never trusted without real evidence (diffs, command output).
- Write-capable delegated legs must be preceded by a commit/stash checkpoint, and workers are explicitly forbidden from destructive recovery (`git reset --hard`, `git clean`, force-push).
