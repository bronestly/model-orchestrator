# Model Router Skill

Source repository for a minimal dual-host model router. It keeps each host's
entry prompt small, shares detailed provider guidance, and uses other models
only when they offer a clear advantage.

## Layout

- `.claude/skills/model-router/SKILL.md` — thin Claude adapter.
- `.claude/skills/model-router/adapters/codex.md` — thin Codex adapter source.
- `.claude/skills/model-router/references/` — shared guidance loaded on demand.
- `sync.sh` — copy-based installer for both global packages.
- `model-router-workspace/` — gitignored scratch and archived migration material.

## Install

```bash
bash sync.sh
```

The installer materializes:

- Claude: `~/.claude/skills/model-router/`
- Codex: `~/.agents/skills/model-router/`

Always edit this repository, then rerun `bash sync.sh`; both installed packages
are build artifacts.

## Operating model

- The active host remains planner, executor, verifier, and final synthesizer.
- Delegation is for independently bounded work with a clear route advantage.
- Codex uses Fable only for the two triggers in `references/fable-advisor.md`,
  with one best-effort call and no retry.
- Claude-host calibration remains machine-local at
  `~/.claude/model-router/routing-notes.md`. Codex has no shared mutable state.
