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
- Sol/Terra **implement/fix** legs use a **minimal-code contract** (smallest
  change, reuse before invent, no drive-by machinery). Multi-file ambiguous
  work: plan at Sol high, implement in a fresh medium leg. See
  `references/codex-delegation.md`.
- Disproportionate diffs are a failed deliverable: re-prompt once under the
  contract before escalating effort.
- Codex uses Fable only for the rare triggers in `references/fable-advisor.md`
  (architecture, twice-failed approach, optional overbuild/VS taste), with
  one best-effort call and no retry.
- VS mode can compare models **or** same-model prompt variants (Sol baseline
  vs +minimal-code contract), with a `code_minimalism` score and optional
  Fable taste pass — `references/vs-mode.md`.
- Claude-host calibration remains machine-local at
  `~/.claude/model-router/routing-notes.md`. Codex has no shared mutable state.
