---
name: model-router
description: "Routes and executes substantial multi-model work at an appropriate cost, speed, and quality. Use when the user asks to route, delegate, compare models, use subagents, conserve model limits, or when a task has independent bulk, research, implementation, or review legs that clearly benefit from different models. Also use for Sol with-vs-without guardrail bake-offs. Skip routine single-model work and trivial tasks."
allowed-tools:
  - Bash(command -v *)
  - Bash(codex exec --skip-git-repo-check -s read-only *)
  - Bash(grok --permission-mode plan *)
  - Bash(agy -p *)
  - Bash(agy models*)
metadata:
  version: "0.21.0"
  updated: "2026-07-28"
---

# Model Router — Claude Adapter

Act as the orchestrator. Keep ambiguity resolution, consequential judgment, verification, and final integration in the main context. Delegate only a bounded leg with a clear cost, speed, context, or independent-review advantage. Do not route merely because a task is long or touches many files.

## Route selection

| Work | Primary | Fallback |
|---|---|---|
| Decomposition, high-stakes judgment, final integration | Main Claude context | Never delegate |
| Complex agentic coding, hard debugging, precise code generation | Codex Sol (`medium` implement; `high` plan-only when multi-file/ambiguous, then fresh `medium` implement — see codex-delegation) | Fresh Opus 5 subagent, then Grok 4.5 (single-file only) |
| Independent critical review | Fresh Opus 5 subagent (precision primary; add a Codex Sol recall pass for correctness-critical diffs) | Fresh Fable subagent, then Codex Sol |
| Live-X research, review/criticism sweeps, and small single-file engineering only | Grok 4.5 | Sonnet subagent plus web search |
| General web/docs research: releases, comparisons, multi-source synthesis (trial) | Antigravity `gemini-3.6-flash` | Grok 4.5, then Sonnet subagent plus web search |
| Bulk classification, extraction, or file reconnaissance | Antigravity `gemini-3.6-flash-low` | Luna, then batched Sonnet |
| Standard implementation, tests, docs, or writing | Sonnet subagent | Terra (`medium` implement; `high` review) |

Use the cheapest route that comfortably clears the quality bar. For routine work, stay in the main context instead of spending time on routing analysis.

Opus 5 legs (trial, day-0 evidence 2026-07-24): default `medium`/`high` effort, never `max` by default; do not route bulk or trivially simple work to Opus 5 (verbosity/latency tax vs 4.8); never auto-enable fast mode on any provider.

Before an external CLI call, read [references/routing-reference.md](references/routing-reference.md). Then read only the provider reference selected by the route:

- Codex Sol/Terra/Luna: [references/codex-delegation.md](references/codex-delegation.md)
- Grok engineering: [references/grok-delegation.md](references/grok-delegation.md)
- Grok live-X research: [references/x-research.md](references/x-research.md)
- Antigravity web research and bulk legs: [references/antigravity-research.md](references/antigravity-research.md)
- Explicit model comparison, including Sol with vs without the minimal-code contract: [references/vs-mode.md](references/vs-mode.md)

Normal tasks must not load advisor instructions. Read [references/fable-advisor.md](references/fable-advisor.md) only when its trigger is met or the user explicitly requests an advisor plan review — a full-plan dossier for a consequential decision, returning a verdict plus implementor steering notes. The advisor model is Fable 5 by default; Opus 5 is available on request or for consequential-but-standard engineering calls, and both may be consulted (identical dossier each) when the user explicitly asks for a dual opinion. On this host, prefer a native subagent with the chosen model over the CLI shape; the dossier, effort, and failure rules apply either way.

## Delegation contract

Each worker receives one fresh, self-contained task with:

1. Goal and relevant context.
2. Explicit MUST/NEVER constraints, including security and permission invariants.
3. Concrete success criteria and required evidence.
4. Scope lock: allowed files/actions, no unrelated abstractions or refactors.
5. Stop rule: if the same gate fails twice with the same error, return blocked.
6. For **Sol/Terra implement/fix** legs: the **minimal-code contract** from `references/codex-delegation.md` (smallest change, reuse before invent, no drive-by machinery).
7. A concise structured result:

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

For write-capable legs, first create a recoverable commit or stash checkpoint. Forbid `git reset --hard`, `git clean`, force-push, mass deletion, and destructive recovery. Unless nested work was explicitly requested, tell Codex workers to do the work themselves without spawning subagents.

## Verification and failure

- Trust artifacts, diffs, and real command output—not a worker's completion claim.
- Spot-check at least one material claim before integration.
- For Sol/Terra writes: reject out-of-scope or grossly disproportionate diffs (see routing-reference completion gate); re-prompt once with the minimal-code contract before escalating effort.
- Retry once only for an apparently transient failure. Do not retry auth, tier, configuration, or empty-deliverable failures.
- Mark a failed route dead for the session and use its documented fallback.
- For high-stakes output, use a fresh reviewer from another model family when one is available.
- Never stall solely because an external CLI is unavailable.

For substantial routes, state the route and cost/quality rationale briefly before executing. Call out plans containing two or more Sol calls or any Sol at `xhigh`.

## Calibration

Read machine-local observations from `$HOME/.claude/model-router/routing-notes.md` when present and let recent, relevant notes override defaults. Record only persistent breakage or a non-routine routing lesson; do not log ordinary success. Keep machine-specific facts local. Promote a repeated universal lesson only through the approval-gated flow in `references/vs-mode.md`, editing this repository's source rather than the installed copy.

## Maintenance

- **2026-07-12 · v0.10.0–v0.11.0:** Lowered Sol effort, bounded nested work, strengthened explicit constraints and evidence review.
- **2026-07-13 · v0.12.0:** Added short fresh legs, scope locks, write checkpoints, and provider-specific references.
- **2026-07-13 · v0.13.0:** Added machine-local calibration and approval-gated promotion.
- **2026-07-18 · v0.14.0–v0.14.1:** Recalibrated efforts; made fast mode categorically forbidden and removed stale percentage claims.
- **2026-07-18 · v0.15.0:** Split Claude and Codex host adapters, moved CLI/breakage detail to shared references, and added a rare Fable advisor path for a Sol-high Codex host.
- **2026-07-18 · v0.16.0:** Sol/Terra minimal-code contract and plan→medium execute split; orchestrator rejects code-bloat diffs; VS same-model baseline vs +contract bake-off with `code_minimalism` metrics and optional Fable taste check.
- **2026-07-23 · v0.17.0:** Grok headless forensics: write legs use `--always-approve` (headless `--permission-mode auto` auto-cancels shell writes → empty `Cancelled` runs; old concurrency attribution falsified); write-tool-not-heredoc prompt rule; `--json-schema` banned on agentic legs (suppresses tool use); `max_tokens_truncation` error-schema parsing + `grok -r` recovery; false-completion `git status`-vs-claims gate.
- **2026-07-23 · v0.17.1:** Narrowed Grok's routing row to live-X research / review sweeps / small single-file engineering (user-approved): blinded VS reruns under the fixed launch shape lost 1-vs-3/4 on multi-file SQL and React CRUD with security-grade defects and false verification claims, plus 2/2 reproducible max_tokens truncation on a large page-build leg; research leg under identical flags was flawless.
- **2026-07-23 · v0.17.2:** Fixed the Fable advisor invocation (`references/fable-advisor.md`): a Codex host got tool-instruction narration and no recommendation. Root cause was `--permission-mode plan` + the default coding-agent system prompt nudging Fable to investigate the repo with no tools available. Fix (smoke-tested): add a read-only advisor `--system-prompt`, drop `--permission-mode plan`; narration-only replies now count as a skipped consultation, no retry.
- **2026-07-23 · v0.18.0:** Added Antigravity CLI (`agy` 1.1.5, Gemini 3.6 Flash) as trial primary for general web/docs research and replacement for the dead gemini CLI on bulk legs (Google retired gemini CLI 2026-06-18; `IneligibleTierError` was the shutdown, not an account issue). Headless shape verified: `agy -p` returns the deliverable on stdout, web search works without prompts, permission-needing tools are soft-denied to stderr. New `references/antigravity-research.md`; trial status pending the Grok-vs-agy research bake-off in routing-notes.
- **2026-07-23 · v0.18.1:** Generalized the Fable advisor (`references/fable-advisor.md`) from a Codex/Sol-only path into a cross-model plan-review any orchestrator can request. Primary dossier now forwards the **full detailed plan** (not a summary) and Fable returns a verdict, ranked risks, missing facts, concrete revisions, **and implementor steering notes** for whichever model later builds it. Added effort decision rules: `medium` default, `high` only for hard-to-reverse/high-blast-radius decisions or a hedged medium pass; `xhigh`/`max`/`ultra` forbidden for a read-only advisory.
- **2026-07-23 · v0.18.2:** Claude adapter now carries the same gated `fable-advisor.md` pointer as the Codex adapter, so Claude-as-orchestrator can request a Fable plan review deliberately (native subagent preferred over the CLI shape; same trigger, dossier, effort, and failure rules).
- **2026-07-24 · v0.18.3:** Fable advisor prompt-delivery rules after a Codex host failure: `claude -p` validates input at launch (verified), so the dossier must be a positional arg (temp file + `"$(< file)"`) or stdin connected at spawn — never PTY-then-write-stdin. Also: no `--advisor` flag exists; the route is `--model claude-fable-5`; Codex hosts must run the call outside the exec sandbox (network/credential access).
- **2026-07-24 · v0.19.0:** Replaced Opus 4.8 with Opus 5 (`claude-opus-5`, released 2026-07-24, same $5/$25 price) in routing — trial on day-0 evidence (Grok 4.5 launch sweep + platform.claude.com spot-check). Coding fallback now Opus 5 subagent before Grok (SWE-bench Verified 97.0% vs 4.8's 88.6%, Grok's 86.6%; consistent with the v0.17.1 Grok demotion). Review row: Opus 5 precision primary with a Sol recall co-pass on correctness-critical diffs (CodeRabbit: actionable precision 39.3% vs 35.2% baseline, but recall 55.2% vs 61.1% and ~4× nitpicks); Fable retained as highest-stakes escalation. New Opus 5 caveats: no `max` effort by default (analysis-paralysis reports), no bulk/simple legs (verbosity tax), fast mode stays forbidden. Grok read-only shape corrected in routing-reference: headless `--permission-mode plan` auto-cancelled a pure research leg (same `Cancelled`+narration signature as `auto`); headless read-only legs now use `--always-approve` + throwaway cwd + read-only prompt contract.
- **2026-07-25 · v0.20.0:** Generalized the advisor mode (`references/fable-advisor.md`, filename kept) to support model selection: Fable 5 (`claude-fable-5`) stays the default for the highest-stakes calls; Opus 5 (`claude-opus-5`) is now a first-class advisor for user-requested or consequential-but-standard engineering reviews; a dual Fable+Opus advisory (identical dossier per model, orchestrator reconciles agreement/disagreement) is available on explicit user request only. Same invocation shape, dossier discipline, effort rules, and per-call failure policy for both models — only `--model` changes; Opus 5's never-`max` caveat carries over via the existing effort ceiling.
- **2026-07-28 · v0.21.0:** Updated Grok launch recipe and CLI flags: replaced background nohup execution with synchronous `--prompt-file` invocation (`--no-subagents`, `--disable-web-search`, `--no-alt-screen`, `--minimal`, `--output-format json`) to prevent lost subshell output; added zsh reserved `status` variable trap to CLI gotchas.
