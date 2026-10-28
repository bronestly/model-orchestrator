# T3 Code and other unattended Agent SDK hosts

Read this only when the session runs in T3 Code (its runtime info says so) or in another Agent SDK host (`CLAUDE_CODE_ENTRYPOINT=sdk-*`, `CLAUDE_CODE_SESSION_ATTENDED=0`). Plain Claude Code sessions never need it. Command shapes stay in the registry.

## What changes on this host

- **No one answers permission prompts.** `allowed-tools` does not bypass the auto-mode classifier, so a denied leg is a dead route for the session: use the documented fallback, and don't rephrase the call to get past the classifier.
- **Distinguish native and app-owned children.** On a Claude host, native Agent-tool subagents are Claude-only (Sonnet, Opus, Fable, and the `mr-*` definitions); other providers use CLI processes or T3 delegated tasks. Codex hosts also expose native subagent tools, subject to the token-sharing limitation below. When you report the route, say which legs ran natively, which as CLI processes, and which as T3 tasks.
- **Native legs run in the background.** Their results arrive as hand-back messages; treat those as worker output, not user input.
- **The rm safety check blocks `rm -rf $VAR/...`** (the prompt times out). Use literal absolute paths or `"${VAR:?}"` in cleanup commands, both for yourself and in worker prompts.
- **Settings edits are denied as Self-Modification.** Reading or editing `~/.claude/settings.json`, and the `update-config` skill, are blocked (2026-10-12). Give the owner the exact snippet to paste instead. Don't try another route to the file.

## Choosing the transport

T3 v2 is transport, not routing: it validates the target and runs it, and every model, effort, and brief decision stays with this skill and its calibration.

- **Prefer a T3 delegated task** for legs that fit the plain shape: a bounded brief, a final message as the deliverable, and a sandbox the parent's runtime mode gives (registry: for Codex, `runtimeMode` is the sandbox). In practice that means Codex write legs with `isolation: "worktree"` under an `auto` parent, Grok research and live-X legs, and Antigravity web legs. What it buys: no shell-command classifier verdicts, a visible and cancellable child thread, durable state across restarts, `clientRequestId` replay instead of duplicate legs, worktree isolation, no stdin hang, and a choice between the device's Codex accounts when one hits its usage limit.
- **Keep the CLI shape** for Codex read-only review and research legs (the registry's read-only containment has no unattended T3 equivalent), for any leg in a secret-bearing repository, for Grok legs whose effort matters, and for anything in the registry's "Not exposed" list.
- **Write the brief for a last-message result.** Only the child's final assistant message comes back, so require the structured result JSON as that message, with evidence inline rather than "see above".
- **Treat a delegated task like any other leg.** The delegation contract, completion gate, and seam review apply unchanged. Verify served model, effort, and sandbox before scoring it from provider logs, not from T3 (the registry names the files); T3 thread data carries no effort.

## Codex token sharing and native subagents

When session metadata confirms `model_provider: "openai_token_sharing"`, use T3 `delegate_task` for Codex legs that fit its sandbox constraints, including same-provider work. Give the child a fresh self-contained brief and forbid nested native agents. Keep read-only containment requirements above: if T3 cannot provide the required sandbox and no compatible CLI route is verified, continue inline. This compatibility rule does not restrict which account may run an app-owned child and does not apply to other Codex authentication modes.

Observed on 2026-10-16 with Codex 0.163.0: a native child and its parent used the same T3 provider instance. The child rollout contained an `agent_message` task item and failed with `subscription_sharing_unsupported_capability`; the parent's subsequent native result item was also `agent_message`, followed by the same error. Fresh app-owned children on that instance completed. This is evidence of an unsupported native-agent input path, not cross-account routing. After this error, mark the native route dead for the session; preserve the account choice and recover into a fresh compatible context rather than retrying the affected history.

T3 v0.1.0's `CodexManagedRuntime.ts` tries to disable native agents with `features.multi_agent=false` and `features.multi_agent_v2=false`. A local `codex debug prompt-input` comparison on 0.163.0 still included native-agent instructions with those switches; `-c agents.enabled=false` removed them. The supported Codex config equivalent is `[agents]` with `enabled = false` (this disables native agents for every session using that config, while T3 app-owned tasks remain available). A T3 managed-runtime fix should pass the current switch instead of relying on the older feature flags. Restart the affected provider session after changing its configuration; disabling agents does not remove existing unsupported history items. Keep normal native routing for backends that support it.

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
