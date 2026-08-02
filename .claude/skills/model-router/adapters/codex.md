---
name: model-router
description: "Routes and executes substantial multi-model work from a GPT-5.6 Sol Codex session. Use when the user asks to route, delegate, compare models, consult Fable, conserve limits, A/B Sol with vs without the minimal-code contract, or when a task has an independently bounded bulk, live-research, implementation, or review leg with a clear model advantage. Skip routine single-model work and trivial tasks."
---

# Model Router — Codex Adapter

Keep GPT-5.6 Sol high as the primary planner, executor, verifier, and integrator. Delegate only an independently bounded leg with a clear cost, speed, context, live-data, or independent-review advantage. Task length and file count alone do not justify delegation.

User instructions, repository guidance, available tools, sandbox policy, and approval requirements always override this routing guide. Never assume a model, CLI, native subagent type, or permission is available; probe only a route you are about to use.

When **you** (Sol main) implement or fix code in-session, apply the same **minimal-code contract** as delegated Sol legs (`references/codex-delegation.md`). Prefer plan-high then a fresh medium implement for multi-file work over one long eager transcript.

## Route selection

| Work | Primary | Fallback |
|---|---|---|
| Planning, ambiguity, complex integrated coding, final verification | Main Sol-high context | Do not delegate |
| Consequential architecture decision or twice-failed approach | One advisor call (Fable 5 default; Opus 5 on request), if available | Sol self-review |
| Well-specified independent implementation | Terra `medium` (minimal-code contract) | Main Sol with contract |
| Fresh independent implementation review | Terra `high` | Main Sol with a clean review pass |
| Bulk extraction, classification, or reconnaissance | Luna (standalone volume) or Sol `low` (fast parallel scouting) | Antigravity (bulk tier), then main Sol |
| Live-X research or bounded alternative engineering angle | Grok 4.5 | Web research or main Sol |
| General web/docs research: releases, comparisons, multi-source synthesis (trial) | Antigravity | Grok 4.5, then web research in main Sol |
| Parallel independent legs explicitly permitted by the user/environment | Native Codex subagents using available models (Sol/Terra) | External CLIs or sequential main-context work |

Before an external worker call, read [references/routing-reference.md](references/routing-reference.md) — its capability registry is the only place model IDs, invocation shapes, and effort ladders are stated. Then read only the chosen provider reference, which carries judgment and failure modes rather than command shapes:

- Sol/Terra/Luna: [references/codex-delegation.md](references/codex-delegation.md)
- Grok engineering: [references/grok-delegation.md](references/grok-delegation.md)
- Grok live-X research: [references/x-research.md](references/x-research.md)
- Antigravity web research and bulk legs: [references/antigravity-research.md](references/antigravity-research.md)
- Explicit model comparison, including Sol baseline vs +minimal-code-contract: [references/vs-mode.md](references/vs-mode.md)

Normal tasks must not load advisor instructions. Read [references/fable-advisor.md](references/fable-advisor.md) only when its trigger is met or the user explicitly requests an advisor review (Fable 5 default; Opus 5 or a dual Fable+Opus advisory on request).

## Delegation contract

Give each worker one fresh, self-contained task containing:

1. Goal, relevant facts, and current task layer.
2. Explicit MUST/NEVER constraints and permission boundaries.
3. Success criteria and the evidence required to count as done.
4. Scope lock and a clear stop condition.
5. For Sol/Terra implement/fix: the **minimal-code contract** from `references/codex-delegation.md`.
6. A concise result with changes/findings, artifacts, verification (include `git diff --stat` when files changed), confidence, and remaining risks.

For write-capable legs, first create a recoverable checkpoint and forbid destructive recovery. Unless the user explicitly requests nested agents, tell external Codex workers not to spawn subagents. Integrate only after checking the returned artifacts or evidence. Reject grossly disproportionate diffs once and re-prompt under the contract before raising effort.

## Failure policy

- A route succeeds only with exit success and a non-empty, on-task deliverable.
- Retry once only for a clearly transient worker failure; never retry auth, quota, tier, configuration, or malformed-output failures.
- The advisor route is stricter: one best-effort call per advisor model, no automatic retry, and never a blocker.
- Mark a failed route dead for the session, use the fallback, and mention the reroute briefly.
- If no external route is healthy, continue safely in the Sol main context.

## Calibration

Read calibration in this order when present:

1. The shared `calibration.md` under the Git checkout named by `$HOME/.claude/model-router/state-repo` (or `%USERPROFILE%\.claude\model-router\state-repo` on Windows).
2. Machine-local observations from `routing-notes.local.md` beside that pointer.
3. Legacy `routing-notes.md` only when no shared state checkout is configured.

Let recent, relevant observations override defaults. Keep machine-specific CLI, tier, path, or repository facts in `routing-notes.local.md`; never sync credentials or secrets. Store full comparison history as a new immutable file under the shared checkout's `events/YYYY/MM/` directory, and keep `calibration.md` to roughly 15 distilled live lessons. Do not push shared state automatically; use the source repository's `state.sh` or `state.ps1` when the user asks to synchronize it.

For substantial work, state the chosen route in one compact line. Do not add routing narration to routine work.
