# CLAUDE.md

This repository is the source of truth for the dual-host `model-router` skill,
not an application. There is no build system.

## Source layout

- `.claude/skills/model-router/SKILL.md` — Claude adapter; read it fully before editing.
- `.claude/skills/model-router/adapters/codex.md` — Codex adapter source.
- `.claude/skills/model-router/references/` — shared, on-demand provider guidance.
- `sync.sh` — installs Claude at `~/.claude/skills/model-router/` and Codex at
  `~/.agents/skills/model-router/`.

## Change rules

- Edit only repository sources, never either installed package.
- Keep both adapters short and host-specific; move detail into references.
- Preserve the Sol-high-first Codex workflow and the exact rare Fable triggers.
- Never enable Codex fast mode or automatically select `ultra` effort.
- Keep external CLI legs fresh, bounded, and evidence-returning.
- Preserve existing `~/.claude/model-router/routing-notes.md`; do not create
  cross-host calibration state.
- For non-trivial changes, bump the Claude adapter version and maintenance note.

## Verification

Run `bash -n sync.sh`, validate both skill frontmatters, then run `bash sync.sh`
and compare each installed adapter and reference directory with its source.
