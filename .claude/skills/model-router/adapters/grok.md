---
name: model-router
description: "Routes and executes substantial multi-model work from a Grok session (4.7 active default; 4.6 for bake-offs). Use when the user asks to route, delegate, compare models, consult Fable, conserve limits, or when a task has an independently bounded bulk, web-research, implementation, or review leg with a clear model advantage. Skip routine single-model work and trivial tasks."
---

# Model Router — Grok Adapter

Keep Grok (4.7 active default; 4.6 for generational bake-offs) as the primary planner, executor, verifier, and integrator. Delegate only an independently bounded leg with a clear cost, speed, context, or independent-review advantage. Task length and file count alone do not justify delegation.

Grok is a frontier-priced host and quota is the binding constraint: bulk or mechanical work done in this main context is itself the expensive route. Do not nest a second Grok CLI loop for Grok-shaped work — live-X, judgment, and integrated coding stay here. A fresh Grok CLI leg is only for transcript-tax after a compaction or context-pressure warning, when the leg can be written as a self-contained prompt.

User instructions, repository guidance, available tools, sandbox policy, and approval requirements always override this routing guide. Never assume a model, CLI, native subagent type, or permission is available; probe only a route you are about to use.

When **you** (Grok main) implement or fix code, apply the steering in `references/grok-delegation.md`. Verify against artifacts, diffs, and real command output — never against your own completion claim.

## Route selection

| Work | Primary | Fallback |
|---|---|---|
| Planning, ambiguity, integrated coding, live-X, final verification | Main Grok context | Do not delegate |
| Consequential architecture decision or twice-failed approach | One advisor call (Fable 5 default; Opus 5 on request), if available | Grok self-review |
| Complex multi-file or hard debugging with a documented Sol advantage | Codex Sol (`medium` implement; `high` plan-only when multi-file/ambiguous, then fresh `medium` implement) | Main Grok |
| Well-specified independent implementation | Terra `medium` (minimal-code contract) | Main Grok |
| Fresh independent implementation review | Terra `high` or Opus 5 | Main Grok with a clean review pass |
| Bulk extraction, classification, or reconnaissance | Antigravity (bulk tier) or Sol `low` | Luna (standalone volume), then main Grok |
| General web/docs research: releases, comparisons, multi-source synthesis (trial) | Antigravity | Main Grok (web tools), then web research in main context |
| Parallel independent legs explicitly permitted by the user/environment | Native Grok subagents | External CLIs or sequential main-context work |

Do not send live-X research or a Grok engineering worker-leg to a nested Grok CLI from this host — that is the same model. Other hosts' Grok-worker steering (`references/grok-delegation.md`) applies when another host delegates *to* Grok, not to Grok-as-host.

Before an external worker call, read [references/routing-reference.md](references/routing-reference.md) — its capability registry is the only place model IDs, invocation shapes, and effort ladders are stated. Then read only the chosen provider reference, which carries judgment and failure modes rather than command shapes:

- Sol/Terra/Luna: [references/codex-delegation.md](references/codex-delegation.md)
- Grok engineering (this host's own implement steering): [references/grok-delegation.md](references/grok-delegation.md)
- Grok live-X research: [references/x-research.md](references/x-research.md)
- Antigravity web research and bulk legs: [references/antigravity-research.md](references/antigravity-research.md)
- Explicit model comparison, including Sol baseline vs +minimal-code-contract: [references/vs-mode.md](references/vs-mode.md)

Normal tasks must not load advisor instructions. Read [references/fable-advisor.md](references/fable-advisor.md) only when its trigger is met or the user explicitly requests an advisor review (Fable 5 default; Opus 5 or a dual Fable+Opus advisory on request). This host reaches the advisor only through the registry CLI path.

## Delegation contract

Give each worker one fresh, self-contained task containing:

1. Goal, relevant facts, and current task layer.
2. Explicit MUST/NEVER constraints and permission boundaries.
3. Success criteria and the evidence required to count as done.
4. Scope lock and a clear stop condition.
5. For Sol/Terra implement/fix: the **minimal-code contract** from `references/codex-delegation.md`.
6. A concise result with changes/findings, artifacts, verification (include `git diff --stat` when files changed), confidence, and remaining risks.

For write-capable legs, first create a recoverable checkpoint and forbid destructive recovery. Unless the user explicitly requests nested agents, tell external Codex workers not to spawn subagents. Integrate only after checking the returned artifacts or evidence. Reject grossly disproportionate Sol/Terra diffs once and re-prompt under the contract before raising effort.

## Failure policy

- A route succeeds only with exit success and a non-empty, on-task deliverable.
- Retry once only for a clearly transient worker failure; never retry auth, quota, tier, configuration, or malformed-output failures.
- The advisor route is stricter: one best-effort call per advisor model, no automatic retry, and never a blocker.
- Mark a failed route dead for the session, use the fallback, and mention the reroute briefly.
- If no external route is healthy, continue safely in the Grok main context.

## Calibration

Read calibration in this order when present:

1. The shared `calibration.md` under the Git checkout named by `$HOME/.claude/model-router/state-repo` (or `%USERPROFILE%\.claude\model-router\state-repo` on Windows).
2. Machine-local observations from `routing-notes.local.md` beside that pointer.
3. Legacy `routing-notes.md` only when no shared state checkout is configured.

Let recent, relevant observations override defaults. Record transcript-tax misses — a bounded leg run inline after compaction that a fresh prompt could have specified — as observations too, so that bias stays measurable rather than anecdotal. Keep machine-specific CLI, tier, path, or repository facts in `routing-notes.local.md`; never sync credentials or secrets. Store full comparison history as a new immutable file under the shared checkout's `events/YYYY/MM/` directory, and keep `calibration.md` to roughly 15 distilled live lessons. Do not push shared state automatically; use the source repository's `state.sh` or `state.ps1` when the user asks to synchronize it.

For substantial work, state the chosen route in one compact line. Do not add routing narration to routine work.
