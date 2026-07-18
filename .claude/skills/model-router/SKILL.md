---
name: model-router
description: "Routes and executes substantial multi-model work at an appropriate cost, speed, and quality. Use when the user asks to route, delegate, compare models, use subagents, conserve model limits, or when a task has independent bulk, research, implementation, or review legs that clearly benefit from different models. Also use for Sol with-vs-without guardrail bake-offs. Skip routine single-model work and trivial tasks."
allowed-tools:
  - Bash(command -v *)
  - Bash(codex exec --skip-git-repo-check -s read-only *)
  - Bash(grok --permission-mode plan *)
  - Bash(gemini --approval-mode plan *)
metadata:
  version: "0.16.0"
  updated: "2026-07-18"
---

# Model Router — Claude Adapter

Act as the orchestrator. Keep ambiguity resolution, consequential judgment, verification, and final integration in the main context. Delegate only a bounded leg with a clear cost, speed, context, or independent-review advantage. Do not route merely because a task is long or touches many files.

## Route selection

| Work | Primary | Fallback |
|---|---|---|
| Decomposition, high-stakes judgment, final integration | Main Claude context | Never delegate |
| Complex agentic coding, hard debugging, precise code generation | Codex Sol (`medium` implement; `high` plan-only when multi-file/ambiguous, then fresh `medium` implement — see codex-delegation) | Grok 4.5, then an Opus/Fable subagent |
| Independent critical review | Fresh Fable/Opus subagent | Codex Sol |
| Bounded mid-level engineering or live-X research | Grok 4.5 | Sonnet subagent plus web search |
| Bulk classification, extraction, or file reconnaissance | Gemini Flash | Luna, then batched Sonnet |
| Standard implementation, tests, docs, or writing | Sonnet subagent | Terra (`medium` implement; `high` review) |

Use the cheapest route that comfortably clears the quality bar. For routine work, stay in the main context instead of spending time on routing analysis.

Before an external CLI call, read [references/routing-reference.md](references/routing-reference.md). Then read only the provider reference selected by the route:

- Codex Sol/Terra/Luna: [references/codex-delegation.md](references/codex-delegation.md)
- Grok engineering: [references/grok-delegation.md](references/grok-delegation.md)
- Grok live-X research: [references/x-research.md](references/x-research.md)
- Explicit model comparison, including Sol with vs without the minimal-code contract: [references/vs-mode.md](references/vs-mode.md)

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
