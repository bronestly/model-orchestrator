# Where upstream changes appear

Primary sources settle facts. Search results and X only point at them.

| Upstream | Release feed | Model facts | Local check |
|---|---|---|---|
| Codex | `gh release view rust-v<version> -R openai/codex`; [changelog](https://learn.chatgpt.com/docs/changelog) | [Codex models](https://learn.chatgpt.com/docs/models); `developers.openai.com/api/docs/models/<id>` | `codex debug models`, `codex exec --help` |
| Claude Code | `raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` | The `claude-api` skill; [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) | T3's `claudeAgent.json` catalog, `claude --help` |
| Grok | `grok update --check --json`; [docs.x.ai](https://docs.x.ai) | `docs.x.ai` model pages | `grok models`, `grok --help` |
| Antigravity | `agy changelog` (no public feed; self-updates) | [Gemini models](https://ai.google.dev/gemini-api/docs/models), [pricing](https://ai.google.dev/gemini-api/docs/pricing) | `agy models`, `agy --help` |
| T3 Code | `gh release view v<version> -R pingdotgg/t3code` (stable only; ignore nightlies) | `orchestrator_capabilities`, `~/.t3/caches/*.json` | `t3 --version`, desktop app version, source at the tag |

OpenAI's blog returns 403 to plain fetches, so use the API model page and a reporting source that quotes it.

## What counts as relevant

- **Models:** additions, retirements and their dates, ladder and default changes, prices, context limits, plan availability.
- **CLI:** any flag, default, exit code, JSON field, or sandbox behaviour in a registry row or qualifier. Check changes to headless runs, permission rules, and subagent effort in particular.
- **Skip:** TUI polish, IDE fixes, and cloud or gateway fixes that the registry never mentions.

## T3 Code compatibility

The server and desktop client ship together, so compare `t3 --version` with the desktop version and report a mismatch. For a new stable release:

1. Read the release notes for delegated tasks, MCP tools, runtime modes, schedules, and provider adapters.
2. Diff the source files the registry cites, between the reviewed tag and the new one. Start with `apps/server/src/mcp/OrchestratorMcpService.ts`, `apps/server/src/orchestration-v2/Adapters/CodexAdapterV2.ts`, and `apps/server/src/provider/CodexManagedRuntime.ts`. Use a blobless clone and fetch files by path, because `git grep` over one downloads every blob.
3. Re-check `orchestrator_capabilities` against the route table, including each route's option names and values.
4. Re-test any "Not exposed" or "not applied" line the release may have fixed with one small delegated task, and verify from provider logs, not from T3.

## X sweep handles

Pin these with `from:`, then add a critics pass and a low-engagement practitioner pass, because viral posts alone skew positive.

- **Practitioners:** t3dotgg (Theo), simonw, mitsuhiko, swyx, steipete, kentcdodds, levelsio, mattpocockuk.
- **Benchmarks:** ArtificialAnlys.
- **Vendors:** OpenAIDevs, embirico, thsottiaux; AnthropicAI, ClaudeDevs; xai; GoogleDeepMind, antigravity.
- **T3:** t3dotgg, juliusmarminge.

Add a handle when it keeps producing first-hand reports, and drop one that stops.
