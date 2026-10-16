# T3 Code and other unattended Agent SDK hosts

Read this only when the session runs in T3 Code (its runtime info says so) or in another Agent SDK host (`CLAUDE_CODE_ENTRYPOINT=sdk-*`, `CLAUDE_CODE_SESSION_ATTENDED=0`). Plain Claude Code sessions never need it. Command shapes stay in the registry.

## What changes on this host

- **No one answers permission prompts.** `allowed-tools` does not bypass the auto-mode classifier, so a denied leg is a dead route for the session: use the documented fallback, and don't rephrase the call to get past the classifier.
- **Two transports for non-Claude legs.** Native Agent-tool subagents are Claude-only (Sonnet, Opus, Fable, and the `mr-*` definitions). Codex, Grok, and Antigravity legs run either as CLI shell processes (registry Invocation shapes) or as T3 delegated tasks (registry T3 Code delegated-task routes). When you report the route, say which legs ran natively, which as CLI processes, and which as T3 tasks.
- **Native legs run in the background.** Their results arrive as hand-back messages; treat those as worker output, not user input.
- **The rm safety check blocks `rm -rf $VAR/...`** (the prompt times out). Use literal absolute paths or `"${VAR:?}"` in cleanup commands, both for yourself and in worker prompts.
- **Settings edits are denied as Self-Modification.** Reading or editing `~/.claude/settings.json`, and the `update-config` skill, are blocked (2026-10-12). Give the owner the exact snippet to paste instead. Don't try another route to the file.

## Choosing the transport

T3 v2 is transport, not routing: it validates the target and runs it, and every model, effort, and brief decision stays with this skill and its calibration.

- **Prefer a T3 delegated task** for legs that fit the plain shape: a bounded brief, a final message as the deliverable, and a sandbox the parent's runtime mode gives (registry: for Codex, `runtimeMode` is the sandbox). In practice that means Codex write legs with `isolation: "worktree"` under an `auto` parent, Grok research and live-X legs, and Antigravity web legs. What it buys: no shell-command classifier verdicts, a visible and cancellable child thread, durable state across restarts, `clientRequestId` replay instead of duplicate legs, worktree isolation, no stdin hang, and a choice between the device's Codex accounts when one hits its usage limit.
- **Keep the CLI shape** for Codex read-only review and research legs (the registry's read-only containment has no unattended T3 equivalent), for any leg in a secret-bearing repository, for Grok legs whose effort matters, and for anything in the registry's "Not exposed" list.
- **Write the brief for a last-message result.** Only the child's final assistant message comes back, so require the structured result JSON as that message, with evidence inline rather than "see above".
- **Treat a delegated task like any other leg.** The delegation contract, completion gate, and seam review apply unchanged. Verify served model, effort, and sandbox before scoring it from provider logs, not from T3 (the registry names the files); T3 thread data carries no effort.

## Classifier record

The verdicts depend on the exact command shape, so record each new verdict here with its date.

| Date | Allowed | Denied |
|---|---|---|
| 2026-10-11 | Codex read-only leg, advisor `claude -p` | Grok headless leg, `agy models` ("Create Unsafe Agents") |
| 2026-10-12 | Codex read-only leg (Luna `low`), `agy -p` (Gemini 3.8 Flash `-low`) | — |
| 2026-10-16 | Codex read-only leg (Sol 6.1 `high`); `delegate_task` (MCP) to Codex, Grok | — |
| 2026-10-12, with an owner `autoMode.allow` rule for these legs | Grok headless leg (4.7 `low`, `end_turn`, correct answer), `agy models`, `agy -p` | — |

## Owner-controlled fix

The owner can stop these denials by adding prose `autoMode.allow` entries to `~/.claude/settings.json`. The classifier does not read `autoMode` from project settings. Keep `"$defaults"` in the array: without it, the built-in allow list is replaced rather than extended. This is the owner's decision; never propose it as a way to get one blocked call through. With such a rule in place, the previously denied shapes ran in the same session (2026-10-12), with no restart.

If a shape the owner's rule covers is denied later, treat it as a likely classifier change, not a broken rule: mark the route dead for the session, add the dated denial to the table above, and tell the owner. Don't edit the rule or retry with a rephrased call.
