# Model Router Skill

Source repository for a minimal dual-host model router. It keeps each host's
entry prompt small, shares detailed provider guidance, and uses other models
only when they offer a clear advantage.

## Layout

- `.claude/skills/model-router/SKILL.md` — thin Claude adapter.
- `.claude/skills/model-router/adapters/codex.md` — thin Codex adapter source.
- `.claude/skills/model-router/references/` — shared guidance loaded on demand.
- `sync.sh` — copy-based installer for Linux, macOS, and Git Bash.
- `sync.ps1` — copy-based installer for Windows PowerShell.
- `state.sh` / `state.ps1` — configure and explicitly synchronize an optional
  private Git checkout containing shared calibration history.
- `model-router-workspace/` — gitignored scratch and archived migration material.

## Install

**Linux / macOS / Git Bash:**
```bash
bash sync.sh
```

**Windows PowerShell:**
```powershell
.\sync.ps1
```

The installer materializes:

- Claude: `~/.claude/skills/model-router/` (or `%USERPROFILE%\.claude\skills\model-router\`)
- Codex: `~/.agents/skills/model-router/` (or `%USERPROFILE%\.agents\skills\model-router\`)

Always edit this repository, then rerun `bash sync.sh` or `.\sync.ps1`; both installed packages are build artifacts.

## Shared state across devices

Keep shared state in a separate private Git repository with:

```text
calibration.md
events/
archive/
```

Clone that repository on each device, install the skill, then register the
local checkout:

```bash
bash state.sh configure /absolute/path/to/model-router-state
bash state.sh pull
```

```powershell
.\state.ps1 configure C:\absolute\path\to\model-router-state
.\state.ps1 pull
```

Use `state.sh push` or `state.ps1 push` after recording new events. Push is
always explicit: normal skill installation and invocation never modify a
remote repository.

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
- Claude and Codex read distilled calibration from the configured private state
  checkout. Full history lives in immutable `events/` files; device-specific
  observations remain local at `~/.claude/model-router/routing-notes.local.md`.
