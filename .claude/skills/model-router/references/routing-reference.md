# Shared external-routing reference

Read this only before using an external CLI route. Keep calls short, fresh, self-contained, and scoped to one independently verifiable leg.

## Capability registry

**This table is the only place model IDs, invocation shapes, and effort ladders are stated.** Provider references carry judgment, prompt discipline, and failure forensics — not command shapes. When a CLI changes, edit here and nowhere else. `sync.sh` refuses to install if a command below has no matching `allowed-tools` entry in the Claude adapter.

### Models and effort

| Route | Model ID | Effort mechanism | Ladder (**default**) | Result arrives on |
|---|---|---|---|---|
| Codex Sol | `gpt-6-sol` (active) / `gpt-5.6-sol` (comparison baseline) | `-c model_reasoning_effort="<effort>"` | `low` (simple scoped work) · **`medium`** (coding/review) · `high` (ambiguous plan or hard debugging); raise further only on measured need | final message on stdout and copied to `-o` file |
| Codex Luna | `gpt-6-luna` (active) / `gpt-5.6-luna` (comparison baseline) | same | **`low`** (fine-grained edits, recon, extraction) · `medium` (clear coordinated updates); `high` only if representative results justify it | same |
| Codex Terra | `gpt-5.6-terra` (conditional baseline) | same | **`medium`** implement-after-plan · `high` review, only where calibration shows an advantage | same |
| Grok | `grok-4.7` | `--reasoning-effort` | `low` (quick snapshots, recon, simple tools) · **`medium`** (bounded eng, standard brief, review) · `high` (multi-file implement, deep criticism/research sweeps, security-adjacent; API default) · `xhigh` (never automatic; propose for genuinely hard legs) | stdout, JSON `text` field |
| Antigravity | `gemini-3.8-flash-low\|medium\|high` | encoded in the model slug | **`-low`** bulk/recon · `-medium` quick research · `-high` deep multi-source sweep | stdout |
| Advisor | `claude-fable-5-1` (frontier default) / `claude-opus-5-5` (pragmatic default) | `--effort` | Opus 5.5 **`medium`**, `high` only for hard-to-reverse or high-blast-radius calls · Fable 5.1 **`high`** (Anthropic's stated starting point), `medium` for clean-read triggers (overbuild taste, missing-assumption sweep) | stdout, JSON `result` field |

`ultra`, `max`, and Grok `xhigh` are never selected automatically (`ultra` can trigger proactive delegation and multiply token use; it is not valid for `claude -p`). Never enable Codex fast mode from this skill.

**Codex models (CLI 0.157.1; official model guidance checked 2026-09-27):** `gpt-6-sol` is the active workhorse for demanding coding; `gpt-6-luna` is the low-cost tier for clear, scoped work, including small edits. `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` remain comparison baselines. **Astra is deliberately excluded from this skill's active routes: do not select or escalate to `gpt-6-astra` automatically.** Published API token prices list GPT-6 Sol at $2 input / $10 output per million and GPT-5.6 Terra at $2 / $12, so Terra cannot be assumed cheaper than Sol. Subscription usage and per-task cost may differ; use local calibration rather than API pricing alone to choose conditional baselines. GPT-6 context is up to 1.05M tokens; prompts above 272k input incur a higher API price tier.

**Advisor models (Claude Code 2.1.283):** `claude-fable-5-1` is the active frontier advisor default for critical architecture, trust boundaries, and novel migrations. `claude-opus-5-5` is the active pragmatic advisor for codebase review, maintainability, and standard engineering decisions ($4/$20 per MTok; $0.20 cache read; default effort `medium`, which Anthropic reports matches or exceeds Opus 5 at `high`). `claude-fable-5-1` lists at $10/$50 per MTok with $0.25 cache reads. At default efforts the two score about the same on Artificial Analysis's index; Opus 5.5 leads from `high` up and costs less per task at every level (checked 2026-09-27). Fable 5.1's official starting effort is `high`; the skill's earlier `medium` Fable default was a cost choice, never measured. Anthropic's effort guidance for Opus 5.5: `low` while the user is in the loop, `medium` for everyday implementation, `high` for verification and edge cases, `max` only for unattended hard runs. Changing effort mid-conversation breaks the prompt cache, so set it once per session or leg. Older `claude-fable-5` and `claude-opus-5` remain available as legacy aliases.

Grok 4.7 (`grok-4.7`) is the active default; 4.6 remains available for generational VS bake-offs. Gemini 3.8 Flash slugs (`gemini-3.8-flash-low|medium|high`) are the active default; 3.7 Flash slugs (`gemini-3.7-flash-low|medium|high`) remain available for generational VS bake-offs. Older models (Grok 4.5, Gemini 3.5, 3.1 Pro) remain deprecated.

For ambiguous or complex coding, choose Sol rather than raising Luna effort by default. Measure representative tasks before changing a route's effort or promoting a baseline model.

### Invocation shapes

| Route | Command |
|---|---|
| Codex — read-only leg | `codex exec -s read-only -m <model-id> -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` |
| Codex — write leg | `codex exec -s workspace-write -m <model-id> -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` |
| Grok — headless | `grok --always-approve --no-subagents --no-alt-screen --minimal --output-format json -m <model-id> --reasoning-effort <effort> --prompt-file <path>` |
| Antigravity | `agy -p "<prompt>" --model <slug> --print-timeout <duration>` |
| Antigravity — slug discovery | `agy models` |
| Advisor | `claude -p --safe-mode --model <model-id> --effort <effort> --tools "" --system-prompt "<advisor persona>" --output-format json --no-session-persistence "<dossier>"` |

Per-route qualifiers:

- **Codex** — `-m` takes a listed Sol/Luna/Terra ID. Run from the intended Git worktree; do not bypass the repository check by default. Use `--skip-git-repo-check` only for an intentionally trusted non-Git directory after checking the environment. The sandbox is a per-leg decision: read-only for research and review, `workspace-write` only when edits are needed. The final message appears on stdout and is also copied to the `-o` file; progress goes to stderr. For a multiline prompt, pass a file as stdin with `codex exec ... - < prompt.txt`.
- **Grok** — pin `-m` to the registry ID; do not rely on the CLI default. Add `--disable-web-search` for code/engineering legs; omit it for live-X research. Read-only legs are contained by an explicit read-only prompt contract rather than a sandbox flag (see Permissions). `--permission-mode plan` is interactive-only. Never pass `--json-schema` on agentic legs. Run synchronously from a throwaway worktree. Effort spelling: CLI validates `--reasoning-effort` and hard-fails bad values with exit 1 listing `xhigh, high, medium, low` (verified 2026-08-15); the raw API instead silently downgrades unrecognized strings to `high` (practitioner-verified 2026-08-12) — that trap applies to non-CLI harnesses only. 4.7's API-side default is `high` and reasoning cannot be disabled. Context window is 500,000 tokens (re-pricing threshold cliff at 200,000 prompt tokens doubles pricing on all tokens). **Research tools depend on the model entry's backend; smoke-test before each research leg.** X search (`x_keyword_search`/`x_semantic_search`) is a server-side xAI tool that exists only on the **Responses API**.
  - **Works (CLI 1.0.41, 2026-09-27):** a `[model.*]` entry with `api_backend = "responses"` and `supports_backend_search = true`, including one pointing at an OpenAI-compatible relay that forwards `/v1/responses`.
  - **No X search:** a `chat_completions` entry, which gets `web_search` only. Also a free-tier grok.com login (`subscription_tier: Free`), which got `web_fetch` only although the handshake advertised the X tools.
  - `web_fetch` is off by default; enable it with the documented `features.web_fetch = true` config key.
  - Research legs pin the device's Responses-backed alias; engineering legs may pin a chat-completions alias. Both alias names are device-specific and recorded in `routing-notes.local.md`, not here.
  - X search is billed per post and per profile fetched, on top of tokens.
- **Antigravity** — `--print-timeout` defaults to 5m (0 waits indefinitely); raise it (e.g. `15m`) for deep sweeps. Write the prompt to a file and pass `-p "$(cat promptfile)"` rather than a heredoc. In headless runs, unconstrained prompts risk agy attempting shell commands, which are soft-denied to stderr causing empty stdout; always prepend an explicit tool rule (e.g. `TOOL RULE: use ONLY built-in web search and fetch tools; do NOT execute terminal or shell commands`) to prevent tool-denial empty deliverables.
- **Advisor** — the `--system-prompt` body is fixed and non-optional; it lives in `fable-advisor.md` with the dossier discipline and launch-validation rules. Codex hosts must run this call outside the exec sandbox.

Do not guess additional flags. For multiline prompts use a file — stdin with `-` (Codex), `--prompt-file` (Grok), `-p "$(cat …)"` (agy), `"$(< …)"` (advisor) — rather than brittle shell quoting.

### Host-native subagent routes

On a Claude host these run as subagents rather than CLI calls. The IDs are the same ones the advisor route passes to `--model`.

| Codename | Model ID | Role and caveats |
|---|---|---|
| Fable 5.1 | `claude-fable-5-1` | Advisor default for frontier architecture, security/trust boundaries, novel migrations; high-stakes review escalation. Default `high` effort |
| Opus 5.5 | `claude-opus-5-5` | Pragmatic advisor and precision-review primary. Default `medium` effort; never `max` effort by default; economical ($4/$20) with high fidelity |
| Sonnet 5 | `claude-sonnet-5` | Standard implementation, tests, docs, writing; batched bulk fallback |
| Fable 5 (legacy) | `claude-fable-5` | Previous-generation advisor baseline |
| Opus 5 (legacy) | `claude-opus-5` | Previous-generation precision-review baseline |

### Unverified gaps

Treat these as open, and never fill them with a guess:

- **Grok identity and backend.** `grok models` lists `grok-4.7` (2026-09-26) as the active default, and also offers `grok-4.6` and legacy `grok-4.5`. Pin `-m` to the registry ID. Before blaming quality on the route, confirm two things:
  - the result JSON's `modelUsage` object names the model actually served;
  - for research legs, an X-search tool call appears in the session's `events.jsonl`.
  A run with only `web_search` calls is a backend problem (see Known route failures), not the model.
- **xAI `x_search` parameters.** An agy sweep (2026-09-27) reported `allowed_x_handles`/`excluded_x_handles` (mutually exclusive), ISO-8601 `from_date`/`to_date`, image/video understanding flags, and no engagement-count filter. Its citations were homepage-level, so confirm these against a docs.x.ai deep link before relying on them.

*(Codex CLI version is verified at 0.157.1, 2026-09-26; agy is verified at 1.2.11, 2026-09-26; Grok anchored at 1.0.41, 2026-09-26).*

## Permissions

- Read-only research/review: Codex `-s read-only`; Grok headless `--always-approve` from a throwaway cwd with an explicit read-only prompt contract ("do not create, modify, or delete files; use only search/fetch tools") — headless `--permission-mode plan` auto-cancels the first tool call and kills the run (verified 2026-07-24: `stopReason:"Cancelled"` + narration-only text on a pure research leg, same signature as `auto`); reserve `plan` for interactive sessions. agy plain `-p` (web search/fetch run without prompting; tools needing approval are soft-denied with a stderr notice naming the allow-rule — empty stdout plus such a notice means blocked, not failed; prepend explicit prompt tool rules to prevent unapproved shell tool attempts).
- File edits: Codex `-s workspace-write`; Grok `--always-approve` — never `--permission-mode auto` headless: auto silently auto-CANCELS any non-whitelisted shell command (e.g. heredoc file writes) and ends the whole run with empty output; it is only safe interactively. Deny rules and hooks still apply under `--always-approve`, so containment comes from those plus a throwaway worktree. agy write legs are not an established route. Never use `--dangerously-skip-permissions`. Instead, grant specific allow-rules (e.g. `"read_url(*)"`, `"search_web(*)"`) in `~/.gemini/config/config.json` → `userSettings.globalPermissionGrants.allow`. A `permissions.allow` key in `antigravity-cli/settings.json` is silently ignored (verified agy 1.1.22, 2026-08-28). `agy -p "/permissions" --output-format json` dumps the live merged grants.
- Grant only the minimum task-scoped access. Do not pass credentials or production secrets to delegated legs.

## Completion gate

A worker result counts only when it includes relevant artifacts and real verification. Reject empty output, narration-only output, unverifiable completion claims, or changes outside the scope lock.

For Codex **write** legs, also reject **code bloat** as a failed deliverable (not a soft style note):

- Diff must stay within the scope lock; no unexplained new packages or files.
- Net LOC / new symbols grossly disproportionate to the task (e.g. large helper layers for a small fix) → reject once and re-prompt with the minimal-code contract from `codex-delegation.md` plus: "Delete the unnecessary machinery; do not add more."
- Spot-check: any new helper used only once should usually have been inlined.
- Require `git diff --stat` (or equivalent) in evidence when files changed.

For **review** legs, also reject **review bloat / ungrounded nits** as a failed deliverable:

- Findings must be caused by the pinned diff range (`git diff <base>...<head>`); direct callers/callees may be inspected to establish impact.
- Reject speculative nits lacking a concrete failure scenario and supporting trace, test, or command when feasible; re-prompt under the `Code-review contract`.
- Require structured output with severity (P0/P1) and file:line citations; if no blocking defects exist, require explicit `VERDICT: APPROVE (No blocking issues found)`.

For high-risk work, require a fresh review from another model family where practical. The orchestrator remains responsible for the final decision.

## Known route failures

- A present binary may still have broken auth, quota, account tier, or configuration. The first real call is the probe.
- The gemini CLI is permanently dead: Google retired it 2026-06-18 in favor of Antigravity (`agy`); `IneligibleTierError` was the shutdown symptom. Do not probe it.
- An unresolvable agy `--model` hard-fails with a non-zero exit listing valid slugs — fix the slug, don't retry. A deep sweep that dies at the 5m mark hit the default `--print-timeout`, not a model failure. Headless runs returning empty stdout with stderr "a tool required the command permission" mean agy attempted unapproved shell commands; add explicit prompt tool rules or configure allow-rules in `~/.gemini/config/config.json` (see Permissions). Headless agy also cannot read local files without a `read_file`/`command` allow-rule, so pass bulk text inside the prompt rather than asking it to open files.
- Grok background `nohup ... &` invocations fail to retain usable results in subshell tool executions. Run Grok synchronously (registry shape); on Windows the standard prompt-file path is `$env:TEMP\prompt.txt` or `%TEMP%\prompt.txt`.
- In zsh, do not use `status` as a variable name when handling Grok's output or exit code (reserved zsh variable causing execution error). Use `$?`.
- Grok can exit successfully with narration but no deliverable. Check its JSON `text` and stop reason.
- Grok 4.7 `high`/`xhigh` legs burn ~1.5–2× reasoning tokens vs 4.6 (independent benches measured ~66k output tokens per task at `high`; `xhigh` is a significant extra step at ~81k tokens). Run them backgrounded or with a generous bound (xAI's client examples use 3600s timeouts) — a tight foreground timeout kills a healthy leg.
- Grok `stopReason:"Cancelled"` with empty text = headless permission auto-cancel, not quota or concurrency (the 2026-07 "concurrent cancels" attribution showed this same signature on forensic review). Verify: `permission_resolved decision:"cancelled"` (~50 ms) in `~/.grok/sessions/…/events.jsonl`. Relaunch with `--always-approve`. This hits `--permission-mode plan` too, even on tool calls that write nothing (verified 2026-07-24 on a web-research leg) — headless runs always use `--always-approve`.
- A failed Grok run may write `{"type":"error","message":"…max_tokens_truncation…"}` with NO stopReason field — parse that schema separately from result objects. The session survives; `grok -r <sessionId> -p "continue"` resumes it (single observation, 2026-07-23).
- Grok cancel handling churned across 0.2.x (0.2.103 fixed an early-cancel session-wedge race) and the CLI is now 1.0.x — re-verify this behavior after CLI upgrades. The `--always-approve` launch shape is unchanged; 0.2.x plan-mode auto-cancel forensics were not re-run on 1.0.3.
- Grok may upload repository context. In secret-bearing repositories, keep the route disabled unless the installed CLI's upload-disable setting is verified. A warning that the configured key is unrecognized means it is not verified. A relay-routed model entry (a custom `base_url` in `~/.grok/config.toml`) sends every prompt and all repository context to that third party as well, so apply the same rule to it.
- **No X tool means Grok may invent posts.** A Grok research leg with no X-search tool call cannot see X search results. A `chat_completions` entry falls back to `site:x.com` web-search summaries. A free grok.com login (CLI 1.0.41) used `web_fetch` on x.com pages, and on a keyword query it **invented three posts with placeholder IDs (`status/1234567890`)**, reported as real (verified 2026-09-27). Rules:
  - reject every post URL that did not appear in a tool result;
  - check that the model entry uses `api_backend = "responses"` with `supports_backend_search = true`, and run the X smoke test before blaming the model.
- Backgrounded `codex exec` legs can hang forever on "Reading additional input from stdin..." when the launching shell leaves stdin open. Always append `< /dev/null`, unless the prompt itself is piped on stdin with `-`. This was re-hit 6 times between 07-22 and 09-25, once as a 53-minute stall. The stdin banner on its own is not a hang: judge liveness by transcript byte growth.
- Do not let an external worker perform destructive recovery or use credentials beyond the explicit task scope.
