# CLAUDE.md

This repository is the source of truth for the dual-host `model-router` skill,
not an application. There is no build system.

## Source layout

- `.claude/skills/model-router/SKILL.md` — Claude adapter; read it fully before editing.
- `.claude/skills/model-router/adapters/codex.md` — Codex adapter source.
- `.claude/skills/model-router/references/routing-reference.md` — the **capability
  registry**: the single owner of model IDs, invocation shapes, effort mechanisms,
  and effort ladders. Read before any external CLI call.
- `.claude/skills/model-router/references/` — shared, on-demand provider guidance.
- `sync.sh` — installs Claude at `~/.claude/skills/model-router/` and Codex at
  `~/.agents/skills/model-router/` (Linux/macOS/Git Bash).
- `sync.ps1` — installs both global packages on Windows PowerShell.
- `state.sh` / `state.ps1` — synchronize the optional shared calibration checkout
  on user request. Never run automatically from the skill.

## Change rules

- Edit only repository sources, never either installed package.
- Keep both adapters short and host-specific; move detail into references.
- **The registry owns every CLI fact.** Model IDs, invocation shapes, effort
  mechanisms, and effort ladders belong only in `references/routing-reference.md`.
  Provider references carry judgment, prompt discipline, and failure forensics, and
  point at their registry row instead of restating the command. When a CLI changes,
  edit the registry and nothing else. This rule exists because the alternative was
  measured: before v0.25.0 the same facts lived in three or four files and had
  drifted into 14 inconsistencies, including an `allowed-tools` entry that
  pre-authorized the one Grok flag every reference forbids.
- Registry commands must stay in sync with `SKILL.md`'s `allowed-tools`; `sync.sh`
  and `sync.ps1` refuse to install otherwise. Widening the allowlist is a
  permission-posture decision — get the owner's agreement, don't do it silently to
  make the guard pass.
- Preserve the Sol-high-first Codex workflow and rare Fable triggers in
  `references/fable-advisor.md` (architecture / twice-failed approach /
  rare overbuild taste; plus optional VS taste check — not a default on
  every Sol write).
- Sol/Terra implement/fix legs must include the **minimal-code contract**
  and, for multi-file ambiguous work, the **plan → fresh medium implement**
  split (`references/codex-delegation.md`). Orchestrators reject grossly
  disproportionate diffs once under that contract before raising effort.
- VS mode supports same-model bake-offs (Sol baseline vs +contract) with
  `code_minimalism` scores and optional Fable taste (`references/vs-mode.md`).
- Never enable Codex fast mode or automatically select `ultra` effort.
- Keep external CLI legs fresh, bounded, and evidence-returning.
- Calibration has three tiers, in read order: the shared `calibration.md` in the
  Git checkout named by `~/.claude/model-router/state-repo`; device-local
  `routing-notes.local.md` beside that pointer; and legacy
  `~/.claude/model-router/routing-notes.md`, read only when no shared checkout is
  configured. Preserve the legacy file. Keep machine-specific CLI, tier, path, and
  repository facts device-local, and never sync credentials or secrets.
- For non-trivial changes, bump the Claude adapter version and maintenance note.

## Verification

Run `bash -n sync.sh`, validate both skill frontmatters, then run `bash sync.sh` (or `.\sync.ps1` on Windows PowerShell)
and compare each installed adapter and reference directory with its source.

A non-zero `sync.sh` exit is a real finding, not a broken script: it means a registry
command has no matching `allowed-tools` entry. Read what it prints before changing
either file.

Then check that the registry is still the sole owner of command shapes — this is the
part no script gates, so it is the one to run by hand after touching any reference:

```bash
grep -rnE '(codex exec|grok|agy|claude -p)[^|]*--[a-z-]+[^|]*--[a-z-]+' \
  .claude/skills/model-router --include='*.md' \
  | grep -v 'references/routing-reference.md:'
```

Two hits are expected and correct — `SKILL.md`'s v0.18.3 changelog entry and
`references/fable-advisor.md`, both explaining that `--advisor` is *not* a real flag.
Anything else is a command shape that has leaked out of the registry: move it back and
leave a pointer.
