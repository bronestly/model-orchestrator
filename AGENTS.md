# AGENTS.md

This repository is the source of truth for the dual-host `model-router` skill,
not an application. There is no build system.

## Source layout

- `.claude/skills/model-router/SKILL.md` — thin Claude adapter.
- `.claude/skills/model-router/adapters/codex.md` — thin Codex adapter source;
  read it fully before editing.
- `.claude/skills/model-router/references/` — shared references loaded only when relevant.
- `sync.sh` — installs Claude at `~/.claude/skills/model-router/` and Codex at
  `~/.agents/skills/model-router/`.

## Change rules

- Edit repository sources, never either installed package.
- Keep Sol high as Codex's planner, executor, verifier, and final synthesizer.
- Delegate only independently bounded work with a clear advantage.
- Consult Fable only for the two triggers in `references/fable-advisor.md` or
  when the user explicitly requests it: one best-effort call, no retry.
- Complexity, duration, and file count are not Fable triggers.
- Never enable Codex fast mode or automatically select `ultra` effort.
- Preserve existing Claude-host calibration notes; Codex remains stateless.

## Verification

Run `bash -n sync.sh`, validate both skill frontmatters, then run `bash sync.sh`
and compare each installed adapter and reference directory with its source.
