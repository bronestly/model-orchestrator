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

**On a T3 host, `delegate_task` is the default transport for every external leg, meaning any provider other than the host's own. A CLI call needs one of the reasons below, named when you state the route.** On a Claude host, Claude legs stay native subagents; from a Codex or Grok host, use the registry's Claude CLI shapes for review and advisor legs. A host's own native subagents keep their usual rules. Call `orchestrator_capabilities` once per thread before the first delegation, and pass effort on every call (registry).

- **What a T3 task buys:** no shell-command classifier verdicts, a visible and cancellable child thread, durable state across restarts, `clientRequestId` replay instead of duplicate legs, worktree isolation, no stdin hang, and a choice between the device's accounts for a provider (next section). Use `isolation: "worktree"` for Codex write legs under an `auto` parent.
- **The only reasons to use the CLI shape:**
  - Codex read-only review or research, because `delegate_task` has no unattended read-only sandbox (registry, `runtimeMode`).
  - The parent's runtime mode gives the child no usable sandbox: `approval-required` and `auto-accept-edits` stall with no one watching, and `full-access` makes a Codex write leg `danger-full-access` (registry, `runtimeMode`).
  - A leg that needs something in the registry's "Not exposed" list, such as Codex `--search`. Antigravity is excluded: its work legs are T3 tasks only (registry, "Antigravity transport"). The exception is an Antigravity `--print-timeout` bound: on T3, run the leg async and `task_cancel` it when the registry's bound runs out, since a `wait` lasts at most 45 s.
  - A Claude review or advisor leg from a Codex or Grok host, because T3 cannot apply safe mode, the restricted tool set, or the replacement system prompt (registry).
  - Any leg in a secret-bearing repository.
  - A Grok read-only leg that reads a real repository, because T3 cannot pass `--sandbox` (registry).
- **Write the brief for a last-message result.** Only the child's final assistant message comes back, so require the structured result JSON as that message, with evidence inline rather than "see above".
- **Treat a delegated task like any other leg.** The delegation contract, completion gate, and seam review apply unchanged. Verify served model, effort, and sandbox before scoring it from provider logs, not from T3 (the registry names the files); T3 thread data carries no effort.

## Choosing the account for a Codex or Claude leg

A device can hold several accounts for one provider, each a separate T3 provider instance. T3 never chooses between them by usage: a target with only `driverKind` gets the parent's own instance, or else the first healthy one (registry). A leg on an account at its limit fails or waits, so choose the account yourself before every Codex or Claude `delegate_task`.

1. **Run the usage script** that sits beside this file, `t3-account-usage.py`, with `python3` (`python` on Windows), `--json`, and `--probe`. Add `--model <the leg's model ID>` so a usage window that belongs to another model is left out. It changes nothing and reads no credential.
2. **Use `recommended.<provider>`** from its output and pass that `instanceId` as `target.providerInstanceId`, with the model and effort as on any other call (registry). The instance must also show `canRunChildTask: true` in `orchestrator_capabilities`, because an instance can be switched off for one project.
3. **Say it in the route statement:** the account by its display name, and the script's reason, for example "Codex on account B: highest plan with 87% left in its worst window, A has 18%".
4. **Act on `compatibility.warnings`** as the version check below says.

Where the figures come from, newest reading first:

- **T3's provider status cache.** T3 writes one file per instance after each provider check: at server start, when someone refreshes providers in the T3 settings, and every five minutes by default, but only while a T3 client window is open. With no window open the file goes stale, and for a new instance it does not exist yet.
- **Codex session logs,** which a running Codex account updates on every turn.
- **A direct probe, with `--probe`.** For an account whose reading is missing or over 30 minutes old, the script asks that provider's own CLI for the account's limits (registry, "Usage probes"). No prompt is sent, so it costs no model usage. `--probe=all` probes every account. A probe that fails leaves the account as it was and says why in its `note`.

No T3 tool returns usage or refreshes the cache, so the probe is the way to get a fresh figure from an agent session.

The rule the script applies, so you can check its answer:

- An account's room is 100 minus its fullest window that applies to the leg. A window whose reset time has passed counts as empty.
- No account is a fixed default. When the accounts are on different plans, the one on the highest plan goes first while it has at least 25% room, because the same percent of a larger allowance is more work. The plan comes from the label T3 shows for the account; pooled plans (business, team, enterprise) are not ranked.
- Otherwise the enabled, ready account with the most room wins.
- Accounts within 5 points of the best are a tie. A tie goes first to a reading under 30 minutes old, then to the higher plan, then to the most room.
- A reading over 30 minutes old (`state: "stale"`) still ranks on its last figures. If it wins, give its age in the route statement.
- An account with no data (`state: "unknown"`) is not treated as empty. It is chosen only when every account with data has under 10% left; its first call is then the probe.
- When `recommended` names no account, every account is at its limit. Tell the user the reset time it reports and use the route's documented fallback instead of waiting.

An owner instruction to use one account, in the conversation or in `routing-notes.local.md`, overrides the script; say so in the route statement. Account names, instance IDs, and home paths are device facts: they go in `routing-notes.local.md`, never into this skill.

Run the script again before each later round of legs, because a reading ages quickly while legs run. Legs launched together in one response share one reading; when several heavy legs start at once and two accounts both have room, split them between the accounts.

### A Claude host that is low on its own account

Native Claude subagents (the Agent tool and the `mr-*` definitions) always run on the host session's own account. A Claude leg reaches another account only as a T3 task, with `target.providerInstanceId` set to that account (verified 2026-11-16 on T3 0.1.9: a session on one Claude account ran a child on the other). So on a Claude host, before a native Claude write leg:

1. Run the usage script with `--host <this session's instance>`, which is `inheritedProviderInstanceId` in `orchestrator_capabilities`, and `--model <the leg's model>`.
2. If `host.delegateElsewhere` is false, launch the native leg as usual. The host stays on its own account while it has 25% or more left, even when another account has more, because a native leg is cheaper to brief and returns more than a last message.
3. If it is true, send the leg with `delegate_task` to the account in `host.to`. The child gets no agent definition, so put the write-leg template from `claude-delegation.md` into the brief, pass the model and effort, and require the result JSON as the last message. Name both accounts and the reason in the route statement.

This covers write and implementation legs only. Review, advisor, and probe-reviewer legs stay native, because T3 cannot apply their tool limits (registry, "Not exposed"). If the host is too low for them, use the route's documented fallback and tell the user. The orchestrator's own turns stay on the host account; when that account is nearly out, tell the user so they can continue in a session on the other account.

### Version check

The script, this file, and the registry's T3 rows were checked against one T3 server version (`compatibility.verifiedT3Version` in the script's output). The script reads the running version and reports `compatibility.status`. With `verified` and no warnings, go on. Otherwise, before the first `delegate_task` of the session:

1. **Compare the tools you were given with what this skill relies on:**
   - `delegate_task`: `task`, `target` with `providerInstanceId`, `driverKind`, `model` and `options`, plus `clientRequestId`, `isolation`, `mode`, `timeoutMs` and `runtimeMode`.
   - `orchestrator_capabilities`: a `providers` list whose entries carry `providerInstanceId`, `driverKind`, `displayName`, `canRunChildTask`, `constraints`, and `models` with their `options`.
   - `task_cancel`: `taskId`.
2. **Tell the user what you found, in the route statement:** the running and the checked version, and either "tools match" or each missing, renamed, or changed name.
3. **Work around a real mismatch, don't guess.** If `providerInstanceId` is gone, delegate by `driverKind` and say that no account was chosen. If `task_cancel` is gone, don't redo a usage-limited task on another account until the user has stopped the first one. A warning that a cache file has an unknown format means that account's usage is unknown; the rule above already covers that.
4. A newer T3 with matching tools is a note, not a blocker. Suggest the `model-router-update` skill, which re-checks the release and raises the checked version.

### When a delegated task fails on a usage limit

1. **Cancel the failed task with `task_cancel` first.** T3 can resume a limited task by itself when its limit resets (setting `autoResumeLimitedThreads`). A task you already redid elsewhere would then run a second time and duplicate the work. This has happened. A cancelled task is not resumed.
2. **Run the usage script again.** Trust the failure over the figure: treat the failed account as full until the reset time in its error, even if the script still shows room.
3. **Relaunch on the other account** with a new `clientRequestId`, because the old one replays the failed task (registry). For a write leg, first look at what the failed child left behind, and state in the new brief whether to continue from it or start clean.
4. **With no other account that has room,** tell the user the reset time and use the route's documented fallback. Don't leave the limited task waiting without saying so.
5. Record the limit hit, with the account's display name and date, in `routing-notes.local.md`.

## Codex token sharing and native subagents

When session metadata confirms `model_provider: "openai_token_sharing"`, use T3 `delegate_task` for Codex legs that fit its sandbox constraints, including same-provider work. Give the child a fresh self-contained brief and forbid nested native agents. Keep read-only containment requirements above: if T3 cannot provide the required sandbox and no compatible CLI route is verified, continue inline. This compatibility rule does not restrict which account may run an app-owned child and does not apply to other Codex authentication modes.

Observed on 2026-10-16 with Codex 0.163.0: a native child and its parent used the same T3 provider instance. The child rollout contained an `agent_message` task item and failed with `subscription_sharing_unsupported_capability`; the parent's subsequent native result item was also `agent_message`, followed by the same error. Fresh app-owned children on that instance completed. This is evidence of an unsupported native-agent input path, not cross-account routing. After this error, mark the native route dead for the session; preserve the account choice and recover into a fresh compatible context rather than retrying the affected history.

T3's `CodexManagedRuntime.ts` (unchanged through v0.1.7) tries to disable native agents with `features.multi_agent=false` and `features.multi_agent_v2=false`. A local `codex debug prompt-input` comparison on 0.163.0 still included native-agent instructions with those switches; `-c agents.enabled=false` removed them. The supported Codex config equivalent is `[agents]` with `enabled = false` (this disables native agents for every session using that config, while T3 app-owned tasks remain available). A T3 managed-runtime fix should pass the current switch instead of relying on the older feature flags. Restart the affected provider session after changing its configuration; disabling agents does not remove existing unsupported history items. Keep normal native routing for backends that support it.

## Classifier record

The verdicts depend on the exact command shape, so record each new verdict here with its date.

| Date | Allowed | Denied |
|---|---|---|
| 2026-10-11 | Codex read-only leg, advisor `claude -p` | Grok headless leg, `agy models` ("Create Unsafe Agents") |
| 2026-10-12 | Codex read-only leg (Luna `low`), `agy -p` (Gemini 3.8 Flash `-low`) | — |
| 2026-10-16 | Codex read-only leg (Sol 6.1 `high`); `delegate_task` (MCP) to Codex, Grok | — |
| 2026-11-14 | Gemini API `curl` call (no allow rule); Codex read-only leg (Sol 6.1 `medium`); `delegate_task` to Grok | A `yt-dlp` caption download; a file search for an API key |
| 2026-10-12, with an owner `autoMode.allow` rule for these legs | Grok headless leg (4.7 `low`, `end_turn`, correct answer), `agy models`, `agy -p` | — |

## Owner-controlled fix

The owner can stop these denials by adding prose `autoMode.allow` entries to `~/.claude/settings.json`. The classifier does not read `autoMode` from project settings. Keep `"$defaults"` in the array: without it, the built-in allow list is replaced rather than extended. This is the owner's decision; never propose it as a way to get one blocked call through. With such a rule in place, the previously denied shapes ran in the same session (2026-10-12), with no restart.

If a shape the owner's rule covers is denied later, treat it as a likely classifier change, not a broken rule: mark the route dead for the session, add the dated denial to the table above, and tell the owner. Don't edit the rule or retry with a rephrased call.
