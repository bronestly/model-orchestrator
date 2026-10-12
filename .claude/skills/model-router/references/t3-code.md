# T3 Code and other unattended Agent SDK hosts

Read this only when the session runs in T3 Code (its runtime info says so) or in another Agent SDK host (`CLAUDE_CODE_ENTRYPOINT=sdk-*`, `CLAUDE_CODE_SESSION_ATTENDED=0`). Plain Claude Code sessions never need it. Command shapes stay in the registry.

## What changes on this host

- **No one answers permission prompts.** `allowed-tools` does not bypass the auto-mode classifier, so a denied leg is a dead route for the session: use the documented fallback, and don't rephrase the call to get past the classifier.
- **Only Claude legs are native subagents.** Native subagents are Claude-only (Sonnet, Opus, Fable, and the `mr-*` definitions). Codex, Grok, and Antigravity legs always run as shell processes. The T3 UI shows them as Bash calls, not subagents, and their results arrive only when the process exits. When you report the route, say which legs ran natively and which ran as CLI processes.
- **Native legs run in the background.** Their results arrive as hand-back messages; treat those as worker output, not user input.
- **The rm safety check blocks `rm -rf $VAR/...`** (the prompt times out). Use literal absolute paths or `"${VAR:?}"` in cleanup commands, both for yourself and in worker prompts.
- **Settings edits are denied as Self-Modification.** Reading or editing `~/.claude/settings.json`, and the `update-config` skill, are blocked (2026-10-12). Give the owner the exact snippet to paste instead. Don't try another route to the file.

## Classifier record

The verdicts depend on the exact command shape, so record each new verdict here with its date.

| Date | Allowed | Denied |
|---|---|---|
| 2026-10-11 | Codex read-only leg, advisor `claude -p` | Grok headless leg, `agy models` ("Create Unsafe Agents") |
| 2026-10-12 | Codex read-only leg (Luna `low`), `agy -p` (Gemini 3.8 Flash `-low`) | — |
| 2026-10-12, with an owner `autoMode.allow` rule for these legs | Grok headless leg (4.7 `low`, `end_turn`, correct answer), `agy models`, `agy -p` | — |

## Owner-controlled fix

The owner can stop these denials by adding prose `autoMode.allow` entries to `~/.claude/settings.json`. The classifier does not read `autoMode` from project settings. Keep `"$defaults"` in the array: without it, the built-in allow list is replaced rather than extended. This is the owner's decision; never propose it as a way to get one blocked call through. With such a rule in place, the previously denied shapes ran in the same session (2026-10-12), with no restart.

If a shape the owner's rule covers is denied later, treat it as a likely classifier change, not a broken rule: mark the route dead for the session, add the dated denial to the table above, and tell the owner. Don't edit the rule or retry with a rephrased call.
