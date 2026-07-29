# AGENTS.md

This repository is the source of truth for the dual-host `model-router` skill,
not an application. There is no build system.

## Source layout

- `.claude/skills/model-router/SKILL.md` — thin Claude adapter.
- `.claude/skills/model-router/adapters/codex.md` — thin Codex adapter source;
  read it fully before editing.
- `.claude/skills/model-router/references/` — shared references loaded only when relevant.
- `sync.sh` — installs Claude at `~/.claude/skills/model-router/` and Codex at
  `~/.agents/skills/model-router/` (Linux/macOS/Git Bash).
- `sync.ps1` — installs both global packages on Windows PowerShell.
- `state.sh` / `state.ps1` — configure and explicitly synchronize optional
  private shared calibration state.

## Change rules

- Edit repository sources, never either installed package.
- Keep Sol high as Codex's planner, executor, verifier, and final synthesizer.
- Delegate only independently bounded work with a clear advantage.
- When Sol (or Terra) implements or fixes code — main session or delegated —
  apply the **minimal-code contract** from `references/codex-delegation.md`.
  Prefer plan-high then a fresh medium implement for multi-file work.
- Reject grossly disproportionate diffs once and re-prompt under that contract
  before raising effort (`references/routing-reference.md` completion gate).
- Consult Fable only for the triggers in `references/fable-advisor.md` or when
  the user explicitly requests it: one best-effort call, no retry. Triggers
  are rare architecture decisions, twice-failed approach, optional overbuild
  taste, and optional VS bake-off taste — not routine coding.
- Complexity, duration, and file count alone are not Fable triggers.
- VS mode can A/B the same model (Sol baseline vs +minimal-code contract);
  see `references/vs-mode.md`.
- Never enable Codex fast mode or automatically select `ultra` effort.
- Preserve existing calibration history. Both hosts may read configured shared
  calibration; device-specific observations remain local and shared-state
  pushes are always explicit.

## Verification

Run `bash -n sync.sh state.sh`, validate both skill frontmatters, then run
`bash sync.sh` (or `.\sync.ps1` on Windows PowerShell) and compare each
installed adapter and reference directory with its source. Exercise the
configured state checkout with `bash state.sh status` without pushing.
