# Shared external-routing reference

Read this only before using an external CLI route. Keep calls short, fresh, self-contained, and scoped to one independently verifiable leg.

## Capability registry

**This table is the only place model IDs, invocation shapes, and effort ladders are stated.** Provider references carry judgment, prompt discipline, and failure forensics — not command shapes. When a CLI changes, edit here and nowhere else. `sync.sh` refuses to install if a command below has no matching `allowed-tools` entry in the Claude adapter.

### Models and effort

| Route | Model ID | Effort mechanism | Ladder (**default**) | Result arrives on |
|---|---|---|---|---|
| Codex Sol | `gpt-5.6-sol` | `-c model_reasoning_effort="<effort>"` | `low` (scouting/recon, conserving) · **`medium`** · `high` (plan-only, multi-file/ambiguous) · `xhigh` (only after fixing a failed prompt or test) | the `-o` file; stdout is a transcript |
| Codex Terra | `gpt-5.6-terra` | same | **`medium`** implement-after-plan · `high` review/PR-triage | same |
| Codex Luna | `gpt-5.6-luna` | same | **`low`**–`medium` · `xhigh` for standalone single-turn volume only | same |
| Grok | `grok-4.5` (CLI default — see Unverified gaps) | `--reasoning-effort` | **`low`** (bounded eng, quick research) · `medium` (standard brief) · `high` (security-adjacent, deep criticism sweeps) | stdout, JSON `text` field |
| Antigravity | `gemini-3.6-flash-low\|medium\|high` | encoded in the model slug | **`-low`** bulk/recon · `-medium` quick research · `-high` deep multi-source sweep | stdout |
| Advisor | `claude-fable-5` (default) / `claude-opus-5` | `--effort` | **`medium`** · `high` only for hard-to-reverse or high-blast-radius calls | stdout, JSON `result` field |

`ultra` and `max` are never selected automatically on any route (`ultra` is a Codex-only tier and is not valid for `claude -p`). Never enable Codex fast mode from this skill. Only Gemini 3.6 Flash slugs are in use — not Gemini 3.5, 3.1 Pro, or any older Gemini model.

Luna `xhigh` is permitted only for standalone single-turn volume or execution work. Never raise Luna to chase quality on complex code — it costs more than Sol `medium` for worse results.

### Invocation shapes

| Route | Command |
|---|---|
| Codex — read-only leg | `codex exec --skip-git-repo-check -s read-only -m <model-id> -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` |
| Codex — write leg | `codex exec --skip-git-repo-check -s workspace-write -m <model-id> -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` |
| Grok — headless | `grok --always-approve --no-subagents --no-alt-screen --minimal --output-format json --reasoning-effort <effort> --prompt-file <path>` |
| Antigravity | `agy -p "<prompt>" --model <slug> --print-timeout <duration>` |
| Antigravity — slug discovery | `agy models` |
| Advisor | `claude -p --safe-mode --model <model-id> --effort <effort> --tools "" --system-prompt "<advisor persona>" --output-format json --no-session-persistence "<dossier>"` |

Per-route qualifiers:

- **Codex** — `-m` takes the Sol/Terra/Luna ID above. The sandbox is a per-leg decision, not a property of the route: read-only for research and review, `workspace-write` only when the leg must edit files.
- **Grok** — add `--disable-web-search` for code/engineering legs; omit it for live-X research. Read-only legs are contained by an explicit read-only prompt contract rather than a sandbox flag (see Permissions). `--permission-mode plan` is interactive-only. Never pass `--json-schema` on agentic legs. Run synchronously from a throwaway worktree.
- **Antigravity** — `--print-timeout` defaults to 5m; raise it (e.g. `15m`) for deep sweeps. Write the prompt to a file and pass `-p "$(cat promptfile)"` rather than a heredoc.
- **Advisor** — the `--system-prompt` body is fixed and non-optional; it lives in `fable-advisor.md` with the dossier discipline and launch-validation rules. Codex hosts must run this call outside the exec sandbox.

Do not guess additional flags. For multiline prompts use a file — `--prompt-file` (Grok), `-p "$(cat …)"` (agy), `"$(< …)"` (advisor) — rather than brittle shell quoting.

### Host-native subagent routes

On a Claude host these run as subagents rather than CLI calls. The IDs are the same ones the advisor route passes to `--model`.

| Codename | Model ID | Role and caveats |
|---|---|---|
| Fable 5 | `claude-fable-5` | Advisor default; highest-stakes review escalation |
| Opus 5 | `claude-opus-5` | Coding fallback and precision-review primary. Never `max` effort by default; do not route bulk or trivially simple legs here (verbosity/latency tax) |
| Sonnet | `claude-sonnet-5` | Standard implementation, tests, docs, writing; batched bulk fallback |

### Unverified gaps

Two facts are not established. Treat them as open, and never fill them with a guess:

- **Grok model string.** `grok-4.5` is the CLI default, but no `-m`/`--model` flag is documented for this route, and phased rollout means some surfaces still serve 4.3. Confirm model identity in-session before blaming quality on the route.
- **Codex CLI version.** agy is pinned at 1.1.5 and Grok anchored at 0.2.x (0.2.103 fixed an early-cancel session-wedge race); the Codex CLI has no version anchor here. Record one in `routing-notes.local.md` when observed.

## Permissions

- Read-only research/review: Codex `-s read-only`; Grok headless `--always-approve` from a throwaway cwd with an explicit read-only prompt contract ("do not create, modify, or delete files; use only search/fetch tools") — headless `--permission-mode plan` auto-cancels the first tool call and kills the run (verified 2026-07-24: `stopReason:"Cancelled"` + narration-only text on a pure research leg, same signature as `auto`); reserve `plan` for interactive sessions. agy plain `-p` (web search/fetch run without prompting; tools that would need approval are soft-denied with a stderr notice naming the allow-rule — an empty stdout plus such a notice means blocked, not failed).
- File edits: Codex `-s workspace-write`; Grok `--always-approve` — never `--permission-mode auto` headless: auto silently auto-CANCELS any non-whitelisted shell command (e.g. heredoc file writes) and ends the whole run with empty output; it is only safe interactively. Deny rules and hooks still apply under `--always-approve`, so containment comes from those plus a throwaway worktree. agy write legs are not an established route; never use `--dangerously-skip-permissions` — grant specific allow-rules in agy `settings.json` instead.
- Grant only the minimum task-scoped access. Do not pass credentials or production secrets to delegated legs.

## Completion gate

A worker result counts only when it includes relevant artifacts and real verification. Reject empty output, narration-only output, unverifiable completion claims, or changes outside the scope lock.

For Sol/Terra **write** legs, also reject **code bloat** as a failed deliverable (not a soft style note):

- Diff must stay within the scope lock; no unexplained new packages or files.
- Net LOC / new symbols grossly disproportionate to the task (e.g. large helper layers for a small fix) → reject once and re-prompt with the minimal-code contract from `codex-delegation.md` plus: "Delete the unnecessary machinery; do not add more."
- Spot-check: any new helper used only once should usually have been inlined.
- Require `git diff --stat` (or equivalent) in evidence when files changed.

For high-risk work, require a fresh review from another model family where practical. The orchestrator remains responsible for the final decision.

## Known route failures

- A present binary may still have broken auth, quota, account tier, or configuration. The first real call is the probe.
- The gemini CLI is permanently dead: Google retired it 2026-06-18 in favor of Antigravity (`agy`); `IneligibleTierError` was the shutdown symptom. Do not probe it.
- An unresolvable agy `--model` hard-fails with a non-zero exit listing valid slugs — fix the slug, don't retry. A deep sweep that dies at the 5m mark hit the default `--print-timeout`, not a model failure.
- Grok background `nohup ... &` invocations fail to retain usable results in subshell tool executions. Run Grok synchronously (registry shape); on Windows the standard prompt-file path is `$env:TEMP\prompt.txt` or `%TEMP%\prompt.txt`.
- In zsh, do not use `status` as a variable name when handling Grok's output or exit code (reserved zsh variable causing execution error). Use `$?`.
- Grok can exit successfully with narration but no deliverable. Check its JSON `text` and stop reason.
- Grok `stopReason:"Cancelled"` with empty text = headless permission auto-cancel, not quota or concurrency (the 2026-07 "concurrent cancels" attribution showed this same signature on forensic review). Verify: `permission_resolved decision:"cancelled"` (~50 ms) in `~/.grok/sessions/…/events.jsonl`. Relaunch with `--always-approve`. This hits `--permission-mode plan` too, even on tool calls that write nothing (verified 2026-07-24 on a web-research leg) — headless runs always use `--always-approve`.
- A failed Grok run may write `{"type":"error","message":"…max_tokens_truncation…"}` with NO stopReason field — parse that schema separately from result objects. The session survives; `grok -r <sessionId> -p "continue"` resumes it (single observation, 2026-07-23).
- Grok cancel handling is actively churning across 0.2.x (0.2.103 fixed an early-cancel session-wedge race) — re-verify this behavior after CLI upgrades.
- Grok may upload repository context. In secret-bearing repositories, keep the route disabled unless the installed CLI's upload-disable setting is verified. A warning that the configured key is unrecognized means it is not verified.
- Do not let an external worker perform destructive recovery or use credentials beyond the explicit task scope.
