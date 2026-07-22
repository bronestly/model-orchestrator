# Shared external-routing reference

Read this only before using an external CLI route. Keep calls short, fresh, self-contained, and scoped to one independently verifiable leg.

## Verified CLI shapes

| Route | Invocation |
|---|---|
| Codex Sol | `codex exec --skip-git-repo-check -s <sandbox> -m gpt-5.6-sol -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` |
| Codex Terra | Same command with `-m gpt-5.6-terra` |
| Codex Luna | Same command with `-m gpt-5.6-luna` |
| Grok 4.5 | read-only: `grok --permission-mode plan -p "<prompt>" --reasoning-effort <effort> --output-format json` · write legs: `grok --always-approve -p "<prompt>" --reasoning-effort <effort> --output-format json` (see Permissions) |
| Gemini Flash | `gemini --approval-mode <mode> -p "<prompt>" -m gemini-3.5-flash` |

Do not guess additional flags. For multiline prompts, use stdin or a prompt file rather than brittle shell quoting. Codex writes its final answer to `-o`; its stdout is a transcript. Grok and Gemini return their result on stdout.

## Effort defaults

- Sol: `medium` for bounded work, `high` for genuinely complex coding, `xhigh` only after fixing a failed prompt or test. Never auto-use `ultra`.
- Terra: `medium` for implementation after a plan; `high` for review or PR triage.
- Luna: `low`–`medium` for bulk work. Do not raise it to chase quality.
- Grok: `low` for bounded engineering or quick research; `high` for security-adjacent work or deep criticism sweeps.
- Never enable Codex fast mode from this skill.

## Permissions

- Read-only research/review: Codex `-s read-only`; Grok `--permission-mode plan`; Gemini `--approval-mode plan`.
- File edits: Codex `-s workspace-write`; Grok `--always-approve` — never `--permission-mode auto` headless: auto silently auto-CANCELS any non-whitelisted shell command (e.g. heredoc file writes) and ends the whole run with empty output; it is only safe interactively. Deny rules and hooks still apply under `--always-approve`, so containment comes from those plus a throwaway worktree. Gemini `--approval-mode yolo`.
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
- Gemini can return `IneligibleTierError`; treat that route as dead without retrying.
- Grok can exit successfully with narration but no deliverable. Check its JSON `text` and stop reason.
- Grok `stopReason:"Cancelled"` with empty text = headless permission auto-cancel, not quota or concurrency (the 2026-07 "concurrent cancels" attribution showed this same signature on forensic review). Verify: `permission_resolved decision:"cancelled"` (~50 ms) in `~/.grok/sessions/…/events.jsonl`. Relaunch with `--always-approve`.
- A failed Grok run may write `{"type":"error","message":"…max_tokens_truncation…"}` with NO stopReason field — parse that schema separately from result objects. The session survives; `grok -r <sessionId> -p "continue"` resumes it (single observation, 2026-07-23).
- Grok cancel handling is actively churning across 0.2.x (0.2.103 fixed an early-cancel session-wedge race) — re-verify this behavior after CLI upgrades.
- Grok may upload repository context. In secret-bearing repositories, keep the route disabled unless the installed CLI's upload-disable setting is verified. A warning that the configured key is unrecognized means it is not verified.
- Do not let an external worker perform destructive recovery or use credentials beyond the explicit task scope.
