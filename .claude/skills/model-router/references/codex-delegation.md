# When delegating to Codex (GPT-5.6 Sol / Terra / Luna)

Loaded on demand from SKILL.md's "How to delegate". Sources: field reports from heavy Codex users and the Codex team (X, 2026-07-11→13) plus a two-week community-criticism sweep (full report: `model-orchestrator/model-router-workspace/research-2026-07-13/gpt56-criticism-report.md`). OpenAI's own model card confirms several of these (false verification claims, destructive cleanup, credential overreach) — they are not just anecdotes.

## Effort by task complexity

| Leg | Effort |
|---|---|
| Well-specified, bounded implement/fix/tests | Sol `medium` (default) |
| Same shape, conserving limits | Sol `low` first (often same quality, far cheaper) |
| Genuinely complex agentic coding, hard debugging | Sol `high` **plan only** when multi-file/ambiguous; then Sol/Terra `medium` implement (see Plan → execute) |
| After a failed review — and only after fixing the prompt/tests | Sol `xhigh` |
| Well-specified implement after a plan (Terra route) | Terra `medium` |
| Review / PR-triage secondary legs (Terra route) | Terra `high` |
| Mechanical/bulk (when Luna is the route) | Luna `low`–`medium` |
| `max` / `ultra` | Never auto; user-request only |

Why `medium` is the default for Sol quality legs: field consensus is that medium handles the large majority of legs well; higher efforts mostly buy scope creep and burn, and Codex's multi-agent leak is worst at high/xhigh. Escalating the dial does not fix a wrong approach — identical wrong answers have been reproduced at medium, high, AND xhigh. When a leg fails review, change the prompt or the tests before changing the effort.

**Sol `low` is first-class, not a last resort** (Theo / Codex DX, 2026-07): for well-scoped work it is often as capable as medium at much lower burn. If you are hitting limits on medium/low, escalate to Terra/Luna for secondary legs rather than raising Sol's effort — never enable fast mode to compensate (see Burn control below: it is never used from this skill).

**Inverse effort (Codex family):** smaller model needs higher effort to approach Sol-`medium` quality — practical expression is Terra `high` for review-style legs. Do not chase quality by raising Luna to `xhigh` (costs more than Sol `medium`); keep Luna capped.

Tier calibration: these defaults assume a $200-tier sub ("sol high if $200 tier, sol low otherwise"). On smaller tiers drop one level; record the owner's tier in `routing-notes.md`.

## Plan → execute (complex multi-file legs)

Do not plan and implement in one long high/xhigh/Ultra transcript — that maximizes eagerness, machinery, and cache burn.

1. **Plan leg (Sol `high` or main Sol context):** produce a file-touch plan with concrete paths and line refs only. Stop. No code edits.
2. **Implement leg (fresh `codex exec`, Sol `medium` or Terra `medium`):** execute that plan under the **minimal-code contract** below. One scoped task; no continuation of the plan transcript.

Skip the split for single-file, well-specified fixes — go straight to Sol `medium` (or `low`) with the contract.

## Burn control

- **Short, fresh, self-contained legs.** Cache-read cost compounds brutally on long transcripts (worse after compactions), and v2 subagents copy the *entire* parent context — a single long message has burned ~15% of a 5h usage window. One scoped task per `codex exec`; never continue a long transcript.
- **No nested subagents** unless the user asked: include "Do the work yourself. Do not spawn subagents unless blocked." in every Sol prompt. Codex children inherit the parent's model and effort — this is why Ultra melts usage windows. Owner backstop: add "only spawn subagents when I ask you to" to `~/.codex/AGENTS.md`.
- **Never fast mode** (2.5× credits multiplied onto everything above).
- Billing status (2026-07-13, in flux — don't tune around it): OpenAI reverted the 372k context (back to 272k) and the effort ("juice") experiments, is fixing multi-agent overuse at high/xhigh, and the 5h limit is temporarily unenforced.

## Behavioral steering (community failure modes → rules)

1. **Scope creep / overengineering** — the most-reported behavioral complaint. Sol invents abstractions, features, and whole ticket queues ("it might invent 38 more tickets"); worst at high efforts and in open-ended goals. Every prompt gets a scope lock: "Touch only these files: … Do not add helpers, abstractions, features, or tickets not listed. No repo-wide refactors. Stop when the acceptance criteria pass." Ban open-ended phrasing ("keep fixing", "improve", "clean up").
2. **Runaway agency.** Left unbounded, Sol has run for days and produced six figures of lines it later admitted were mostly waste and reverted. Stop contract in every prompt: explicit exit criteria plus a max tool-round budget.
3. **False completion / "I'll do it" then nothing** — on OpenAI's model card as false verification claims. Evidence-of-done gate (SKILL.md): non-empty relevant diff + real test output; add "If you cannot edit, say BLOCKED — do not claim completion." Never integrate on self-report.
4. **Selective non-compliance.** Sol has deliberately overridden explicit constraints "for simplicity", especially on frontend/design taste. Mark hard constraints "MUST / NON-NEGOTIABLE — violating any of these is a failed task", and consider a Claude review pass for UI-taste-critical output.
5. **Destructive actions & credential overreach** — model card: destructive cleanup on machines the user didn't name, credential use beyond authorization; worse when the prompt glorifies persistence. No prod secrets, billing, or IAM access in delegated legs; strip "persist no matter what" language; destructive commands need an explicit path allowlist.
6. **Loop blindness.** Sol doesn't notice it's stuck in an approve→fail→retry gate cycle and burns tokens indefinitely. Rule: "If the same gate fails twice with the same error, stop and report — do not re-request approval."
7. **Code bloat / eagerness** (Theo + field reports, 2026-07): 5.6 is stronger than prior Codex models but **too eager** — more helpers, defensive layers, wrapper machinery, and premature generalization than Fable for the same goal. Agency/scope locks alone do not fix code shape. Every Sol (and Terra) **implement/fix** prompt must include the **minimal-code contract** below. Do not rely on vague "be concise" (OpenAI: can overshoot for 5.6 prose); steer **diff size, reuse, and YAGNI** instead.

### Minimal-code contract (paste into every Sol/Terra implement/fix prompt)

```text
## Minimal-code contract (MUST)
- Prefer the smallest change that fully satisfies the acceptance criteria.
- Reuse existing helpers, types, patterns, and call sites. Search before inventing.
- Touch only the listed files. New files require a one-line justification in the return JSON.
- No new abstractions, wrapper layers, config flags, or "future-proofing" unless required by the criteria.
- No defensive try/catch, null-guards, or validation for states the codebase already forbids.
- No drive-by renames, reformat-only diffs, or opportunistic cleanup outside the task.
- Prefer deleting/simplifying dead paths over adding parallel paths.
- If two designs work, pick the one with fewer new symbols and fewer control-flow branches.
- Stop when criteria pass. Do not continue "improving" the design.
```

**Pathology to reject on review (orchestrator):** one-shot helpers used once (should have been inlined); parallel "v2" paths beside working code; broad try/catch that swallows errors; new config/feature flags for a single call site; invented ticket queues or "while we're here" refactors.

**VS validation:** same-model bake-off (baseline vs +contract) is defined in `vs-mode.md`. Prefer measuring the contract alone before stacking plan→execute as a second confound.

## Within-family choice

- **Sol** — the default Codex workhorse, at `medium` (or `low` when conserving).
- **Terra** — community sentiment is broadly negative ("the useless in-between model"), but our own blinded VS run had 3/3 clean Terra `medium` legs, and high-signal eng reports (2026-07) find Terra `high` notably faster than Sol `low` on review/PR-triage, with negligible quality loss. Reconciliation: Terra earns its keep on (1) well-specified implement *after a plan exists* at `medium`, and (2) review secondary legs at `high` — never as a default, not for design work, not for hard debugging.
- **Luna** — worker-tier: recon, mechanical edits, review drafts at `low`–`medium`. Never design work (widely panned) or ambiguous multi-ticket queues (invents tickets). Luna `xhigh` costs more than Sol `medium` — cap the effort instead of raising it.

## Harness notes (2026-07-13)

- Prefer pinned headless `codex exec` over the desktop app for orchestration — crash and lost-history reports cluster around the ChatGPT-merge builds. Commit to git after every leg; app/session history is not a backup.
- Final answer lands in the `-o` file; stdout is transcript (see SKILL.md CLI reference).
