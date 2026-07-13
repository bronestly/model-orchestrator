---
name: model-router
description: "Routes work to the most suitable model at the best cost/speed/quality balance, then executes the delegation. Use whenever a task has multiple subtasks, parallelizable work, bulk/mechanical operations, or deep analysis worth delegating to subagents — even if the user never mentions models, routing, or cost. Also use when the user asks which model to use, wants to reduce cost or tokens, says 'delegate', 'route', 'subagents', 'vs mode', 'compare models', or names a model (Fable, Opus, Sonnet, Codex, GPT, Grok, Gemini). Skip for single-step trivial tasks you can answer directly."
allowed-tools:
  - Bash(command -v *)
  - Bash(codex exec --skip-git-repo-check -s read-only *)
  - Bash(grok --permission-mode plan *)
  - Bash(gemini --approval-mode plan *)
metadata:
  version: "0.12.0"
  updated: "2026-07-13"
---

# Model Router

You are the orchestrator. This skill runs under Fable 5 or Opus 4.8 — the pattern is identical for both, so the table below names roles ("you", "frontier Claude subagent") rather than hardcoding who you are; the one place your identity changes a route is flagged inline. Your context window and inference are the most expensive resources in the session — spend them only on what cheaper models can't do well: decomposing ambiguous problems, high-stakes judgment calls, verifying results, and final integration. Everything else gets delegated. Don't just recommend a route — execute it.

**Quality floor:** never route to Haiku. The cheapest permitted Claude worker is Sonnet; cheap bulk work belongs to Gemini Flash or Luna via CLI. If neither CLI is available, batch the bulk work into as few Sonnet calls as possible rather than dropping below the floor.

## Session context (auto-gathered at invocation)

Available external CLI binaries: !`command -v codex grok gemini 2>/dev/null || echo "(none found)"`

Calibration notes from `routing-notes.md` in the working folder — let them override the routing table's defaults where they conflict: !`cat routing-notes.md 2>/dev/null || echo "(no routing-notes.md)"`

A binary missing from the list above kills that route for this session — use the fallback column without comment or retries. A present binary is only *provisionally* alive: auth or account tier can be broken server-side, and the first real call is the true probe (see "When a delegation fails"). Anthropic subagents (Agent tool) are normally available but can be killed mid-run by the account's session limit — treat that like any other dead route: reroute the leg to an external CLI (Luna/Terra for recon and standard work, Sol/Grok for heavy legs), note when the window resets, and don't re-spawn Claude subagents until it has. External CLIs are enhancements, never a hard dependency — but no route is guaranteed. Never stall because a CLI is missing.

## Routing table

Pick the cheapest row that fits the task well. Escalate only if review fails — a failed cheap attempt plus escalation usually still costs less than starting expensive. Overlaps are normal; routing is a judgment call on cost, speed, and subtle strengths.

| Work type | Primary | Fallback if unavailable | Why |
|---|---|---|---|
| Decomposition, ambiguity resolution, high-stakes judgment, final integration & review | You (main context) | — never delegate these | Deepest reasoning in the session; the point of the whole pattern |
| Complex agentic coding, precise structured codegen, math-heavy implementation, computer use | Codex Sol (`medium` for well-specified legs, `high` for genuinely complex ones) | Grok 4.5 → Opus subagent (`model: opus`) | Leads on precise coding and computer use; `medium` is the field-tested sweet spot — see `references/codex-delegation.md` |
| Deep analysis, critical review, second opinions on high-stakes output | Frontier Claude subagent: `model: opus` — but if you are Opus 4.8 and `fable` appears in the Agent tool's model options, prefer `model: fable` | Codex Sol | Frontier depth without burning your main context; always available |
| Bounded mid-level engineering, real-time info & X research (trending topics, latest AI/tech chatter, developer sentiment), exploratory or creative angles | Grok 4.5 | Sonnet subagent + web search | Fast mid-level work at good cost; the only live-X route — for research legs read `references/x-research.md`; escalate when cost-of-wrong is high |
| High-volume parallel chores, classification, extraction, file recon, long-context bulk work | Gemini 3.5 Flash | GPT-5.6 Luna (ultra-cheap volume) → Sonnet subagent, batched | Best throughput; quality competitive for these tasks. Luna is worker-tier: cap effort at `medium`, never send design or ambiguous multi-ticket work |
| Standard coding, writing, tests, docs, balanced execution | Sonnet subagent (`model: sonnet`) | GPT-5.6 Terra (`medium`) | Reliable high-quality worker; Terra is the stretch-the-GPT-budget option when Sol is already burning the window |
| Trivial (one-step, low-risk) | Yourself; or one Luna/Flash call if CLI present | — | No routing analysis; at most a one-line note |

**Terra as budget option:** prefer Terra `medium` over a second Sol call when the work is standard engineering and Sol is already on the critical path (or the user is conserving limits). Proven on multi-file feature legs and security-constrained graft/integration work (2026-07-12, 3/3 clean legs); its one observed miss was language register — specify the repo's German form (du-form) explicitly in UI prompts. Community sentiment on Terra is broadly negative ("the useless in-between model"); the reconciliation is that Terra earns its keep only on well-specified implement legs *after a plan exists* — never as a default, not for design work, not for hard debugging.

## CLI invocation reference

Single source of truth for how each external model is invoked on this machine. Every command below was smoke-tested live on 2026-07-12. Never guess flags beyond these — a wrong flag silently runs the wrong model or the wrong effort.

| Model | Command (verified) | Effort values |
|---|---|---|
| Codex Sol | `codex exec --skip-git-repo-check -s <sandbox> -m gpt-5.6-sol -c model_reasoning_effort="<effort>" -o <outfile> "<prompt>"` | Prefer `low medium high xhigh`. CLI also accepts `max` and `ultra` — **do not use `ultra`** (see Known breakage) |
| GPT-5.6 Terra | same, with `-m gpt-5.6-terra` | same as Sol (no `ultra`) |
| GPT-5.6 Luna | same, with `-m gpt-5.6-luna` | `low medium high xhigh max` (no `ultra`) |
| Grok 4.5 | `grok --permission-mode <mode> -p "<prompt>" --reasoning-effort <effort> [--max-turns <N>] [--output-format json]` | `none minimal low medium high xhigh max` |
| Gemini 3.5 Flash | `gemini --approval-mode <mode> -p "<prompt>" -m gemini-3.5-flash` | no effort flag |

**Default efforts by route:**
- Sol well-specified/bounded legs → `medium` (field-consensus sweet spot; the multi-agent burn leak is worst at `high`/`xhigh`)
- Sol genuinely complex agentic coding → `high`
- Escalate Sol to `xhigh` only after a failed review — and fix the prompt/tests first: raising the dial does not fix a wrong approach (identical wrong answers reproduce across medium/high/xhigh)
- Never auto-route to `ultra`; only if the user explicitly names it (and warn once about Codex harness bugs)
- Budget-tight / user conserving limits / rate-limit pressure → Sol `medium` or `low`; prefer Terra/Luna for secondary legs
- Terra balanced work → `medium`
- Luna bulk → `low`, capped at `medium`
- Grok → its default (`medium`), or `high` for engineering-heavy tasks and deep research sweeps (depth mapping in `references/x-research.md`)
- These defaults assume $200-tier subscriptions; on a smaller tier drop one effort level, and record the owner's tier in `routing-notes.md`

**Never enable Codex fast mode** from this skill (2.5× credit multiplier; with long Sol runs a single message can burn a large share of a usage window). Prefer normal mode + lower effort.

**Sandbox / permissions are task-scoped — grant only what the task needs:**
- Research, analysis, review (no edits): codex `-s read-only` · grok `--permission-mode plan` · gemini `--approval-mode plan`
- Tasks that must edit files: codex `-s workspace-write` · grok `--permission-mode auto` · gemini `--approval-mode yolo`

Keep flags in exactly the order shown in the table (sandbox/permission flag right after the binary for grok and gemini, `-s` right after `exec --skip-git-repo-check` for codex). The skill pre-approves only the read-only forms via prefix-matched permission rules, so reordering flags re-introduces prompts; write-capable forms always prompt, by design.

**Output capture:** codex prints a transcript to stdout and writes only the final message to the `-o` file — read the file, not stdout. grok and gemini print the answer directly to stdout. Either way, have workers write real artifacts to files and return the JSON summary from "How to delegate".

**Multi-line prompts:** shell quoting mangles long prompts. Use `grok --prompt-file <path>`, pipe into `codex exec -` via stdin, or pipe into `gemini -p ""` (stdin is appended to the prompt).

**Known breakage (updated 2026-07-13):**
- **Gemini CLI:** binary may be installed and authenticated but Google has cut off its tier (`IneligibleTierError` — individual Code Assist requires migration to Antigravity). Treat the Flash route as dead and send bulk work to Luna until the owner fixes this; if a later session finds gemini working again, it may resume using it.
- **Codex Ultra / nested subagents / fast mode:** rules unchanged — never auto-`ultra`; orchestrator-controlled fan-out instead of Sol multi-agenting itself (children inherit parent model+effort; the leak is worst at `high`/`xhigh`); never fast mode (2.5× credits). Details plus the 2026-07 billing status (372k→272k context revert, cache-read compounding on long transcripts, 5h limit temporarily unenforced — all in flux, don't tune around it) in `references/codex-delegation.md`.
- **Grok headless silent no-output (2026-07-13, extends the 07-12 plan-mode entry):** `grok -p`/`--prompt-file` can exit 0 having printed only an opening narration line ("I'll research…") and no deliverable — observed on multi-part research prompts with web-fetch chains; verbatim retries and higher `--max-turns` do NOT help. Verified fix: append a harness note — "you are running headless; a turn that ends without the full deliverable is a total failure; your FINAL message must be the complete deliverable" — and prefer `--output-format json`, checking the `text` field before trusting the run. Still also true: `cd` into the folder containing any referenced files, and avoid tight `--max-turns` (turn exhaustion is silent too).
- **Grok CLI codebase upload (2026-07-13, widespread reports):** the CLI reportedly uploads the full tracked repo + git history for session context (and can sweep `.env` secrets); the training opt-out does not stop it. Owner action: set `disable_codebase_upload = true` under `[harness]` in `~/.grok/config.toml`. Until that's verified, invoke grok only from clean worktrees or scratch dirs — never inside secret-bearing repos.
- **Grok rollout confusion (2026-07):** phased rollout — some surfaces still serve Grok 4.3. If grok output quality is suddenly off, confirm the model identity before blaming the route.

## How to delegate

Spawn independent subtasks in parallel, in a single message. Sequential spawning wastes wall-clock time for no quality gain. Prefer **you** (the orchestrator) controlling that fan-out — not a single Sol worker spawning its own army.

Keep each external-CLI leg **short, fresh, and self-contained** — one scoped task per invocation, never a continuation of a long transcript. Long Codex contexts compound cache/compaction cost brutally (a single long message has burned ~15% of a 5h window), and quality drifts; several small fresh calls beat one long session.

Every delegation prompt needs five things, because the worker has none of your context:

1. The task with all relevant constraints and context the worker lacks.
2. **Hard constraints as an explicit MUST/NEVER list.** Security invariants especially — grant/REVOKE scope, RLS, auth checks — must be spelled out concretely ("the write RPC is executable by service_role ONLY"), never left implicit by reference to a pattern file ("guarded like X"). Implicit-by-reference is exactly where otherwise-strong workers deviate, and the rules must also bind objects the worker *invents* (helpers, wrappers), not just named deliverables. Put these in the Success criteria section — workers weight checklists hardest.
3. Explicit success criteria — what "done well" looks like.
4. **Clear stop points and a scope lock** — where to halt and return (Sol especially will keep going past useful bounds). Examples: "Write the plan only; stop and return the summary — do not implement." / "Implement and run tests until green. Stop after first PR review pass if asked to open a PR — do not keep babysitting." The scope lock: enumerate the files the worker may touch, ban new abstractions/features/tickets beyond the list and repo-wide refactors, bound the tool rounds, and add: "if the same gate fails twice with the same error, stop and report — do not re-loop."
5. Instruction to return a structured summary, not a transcript:

```json
{
  "task_completed": "...",
  "key_findings_or_changes": "...",
  "files_or_artifacts": "...",
  "evidence_or_verification": "...",
  "confidence": "high|medium|low",
  "risks_or_open_questions": "..."
}
```

A leg only counts as done when `evidence_or_verification` holds real artifacts — a non-empty relevant diff and actual command/test output. "Fully built and tested" without proof is a failed leg: false completion is the single most-reported failure mode for **both** Grok 4.5 and the GPT-5.6 family (X sweep 2026-07). Never integrate on self-report; spot-check the artifacts.

**Write-capable legs:** commit-or-stash first so the tree is recoverable, and ban destructive recovery in the prompt — no `git reset --hard`, `git clean`, force-push, mass deletes, or "undo everything". Workers in both families have clobbered uncommitted work while "fixing" their own mistakes; recovery from a botched leg is your job, not the worker's.

**Nested agents (Codex Sol):** unless the user explicitly asked for multi-agent work inside Codex, include in every Sol prompt: "Do the work yourself. Do not spawn subagents unless blocked." If nested agents *are* wanted, keep parent effort at `medium` or `high` — never start nested work at `xhigh` or `ultra`.

**Delegating to Grok 4.5:** read `${CLAUDE_SKILL_DIR}/references/grok-delegation.md` before writing a Grok prompt for precise or security-critical coding — it captures Grok's instruction weighting, its community-reported failure modes, and the steering that prevents them. For real-time/X research legs, read `${CLAUDE_SKILL_DIR}/references/x-research.md` instead — when X-first routing pays off, the prompt checklist, and ready-made skeletons.

**Delegating to Codex (Sol/Terra/Luna):** read `${CLAUDE_SKILL_DIR}/references/codex-delegation.md` before writing a Codex prompt — effort-by-complexity defaults, burn control, and the steering that prevents scope creep, runaway sessions, and false completion.

You review summaries and spot-check evidence, not full transcripts — that's what keeps your context lean and this pattern cheaper than doing everything yourself.

## When a delegation fails

External CLIs fail in mundane ways: empty stdout, a non-zero exit, an auth/tier error, output that ignores the prompt. Never paper over these — a silently failed delegation poisons everything you integrate downstream.

1. Check every CLI result before using it: exit code 0 **and** non-empty, on-task output. An empty `-o` file or an off-topic reply counts as failure.
2. Retry once only if the cause looks transient (timeout, rate limit). Auth, tier, and config errors will not fix themselves — don't retry those.
3. On a confirmed failure, mark that route dead for the rest of the session and move to the fallback column. Tell the user in one line: "gemini errored (tier); routed to Luna instead."
4. If the fallback chain is exhausted and no Claude subagent can reasonably absorb the work, stop and ask the user how to proceed. Don't invent an unrouted workaround.
5. Record persistent breakage (auth/tier errors, not one-off timeouts) in `routing-notes.md` so future sessions skip the dead route without re-probing.

## Review

Review every summary against the original goal before integrating. Don't rubber-stamp: spot-check at least one claim or piece of evidence. For high-stakes outputs (production code, published content, irreversible actions), have a second model from a different family sanity-check the result — or, if only Claude models are reachable, a fresh subagent that hasn't seen the producing agent's reasoning.

## VS Mode & self-improvement

When the user asks to compare models ("vs mode", "compare models", "use 2–3 models and compare"), read `${CLAUDE_SKILL_DIR}/references/vs-mode.md` for the comparison protocol, the mandatory scorecard schema, and the approval-gated routing-table update flow — then follow it exactly; the standardized scorecard is what makes runs comparable across sessions. You may suggest VS mode once for a substantial task where two routing rows genuinely overlap and calibration would pay for itself — never for trivial work, and don't push if declined.

## Effort calibration

- **Trivial:** no routing analysis. Do it or fire one cheap CLI call. One-line note at most: "Routed to Luna (bulk extraction)."
- **Substantial** (multi-part, costly, or risky): state the plan briefly before executing so the user can redirect:

```
Route: [you: decompose] → [Codex Sol + 3× Luna in parallel] → [Sonnet: review] → [you: integrate]
Why: [1–2 lines on the cost/quality tradeoff]
```

If the plan includes **≥2 Sol calls** or any Sol at **`xhigh`**, say so in the Route line and prefer lower effort or Terra for secondary legs — multi-Sol-high plans can torch a usage window even under orchestrator control.

## Maintenance

Model lineups and relative strengths shift every few months. When they do, edit the routing table and CLI reference — nothing else in this skill hardcodes model names or commands. Deliberately keep benchmark numbers and percentage claims out of this file: they go stale silently and lend false precision to what is a judgment call. Session-to-session calibration lives in `routing-notes.md`; durable, user-approved changes get promoted into this file via the self-improvement flow in `references/vs-mode.md`.

**2026-07-12 (v0.10.0):** Sol default effort lowered `xhigh` → `high`; auto-`ultra` removed from the escalation ladder; stop points + no nested subagents in Sol prompts; Codex fast mode forbidden; Terra elevated as budget option for secondary legs.

**2026-07-12 (v0.11.0, post-VS retrospective):** Anthropic subagents no longer described as "always available" (session-limit kill observed; reroute play added); delegation checklist gains explicit MUST/NEVER hard-constraints item (constraint explicitness beat model tier in the VS run); Terra note gains proven-legs evidence + du-form tip; Grok plan-mode file-access breakage documented; new `references/grok-delegation.md`; vs-mode.md: decisive evidence must cite file:line, orchestrator verifies at location, worktree isolation codified.

**2026-07-13 (v0.12.0, community-research sweep):** Two-week X criticism sweeps of Grok 4.5 and GPT-5.6 (+ xAI docs sweep) distilled into guardrails; research archived in `model-orchestrator/model-router-workspace/research-2026-07-13/`. Sol default effort → `medium` with tier calibration; short-fresh-legs burn rule; evidence-of-done gate, scope lock, and write-checkpoint added to the delegation checklist; new `references/codex-delegation.md` and `references/x-research.md`; grok-delegation.md gains community failure modes; Known breakage: grok repo-upload risk, grok headless narration-only ending (verified fix), Grok 4.3 rollout confusion.
