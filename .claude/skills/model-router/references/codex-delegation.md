# When delegating to Codex (GPT-6 Sol / Astra / Luna · GPT-5.6 Baselines)

Loaded on demand from SKILL.md's "Route selection". Invocation shapes, model IDs, and effort ladders live in the `routing-reference.md` capability registry — this file carries only the judgment behind them. Sources: field reports from heavy Codex users and the Codex team (X, 2026-07→2026-09) plus community sweeps. OpenAI's model card confirms false verification claims, destructive cleanup, and credential overreach — they are structural risks, not just anecdotes.

## Effort rationale

The ladders and defaults themselves are in the registry (`routing-reference.md`, Codex Astra / Sol / Terra / Luna rows). This section is the reasoning behind them — read it when you are tempted to deviate.

Why `medium` is the default for Sol quality legs: `medium` handles the large majority of coding legs cleanly; higher efforts mostly buy scope creep and token burn, and Codex's multi-agent leak is worst at high/xhigh. Escalating the dial does not fix a wrong approach — identical wrong answers have been reproduced across effort levels. When a leg fails review, change the prompt or the tests before changing the effort.

**Sol `low` is first-class, not a last resort:** for well-scoped work it is often as capable as medium at much lower burn. If you are hitting limits on medium/low, escalate to Terra/Luna for secondary legs rather than raising Sol's effort — never enable fast mode to compensate.

**GPT-6 Astra — orchestrator testing vs delegated worker:** `gpt-6-astra` is OpenAI's top frontier intelligence tier. Because it carries frontier pricing, **do not use it for routine delegated legs or bulk execution.** Instead, use Astra when testing Codex as an **orchestrator** (`codex -m gpt-6-astra`) for high-level architectural decomposition, complex multi-system planning, and final synthesis. The Astra orchestrator then delegates bounded implementation legs to `gpt-6-sol` (or `gpt-5.6-sol`) under the minimal-code contract, keeping token burn disciplined.

**Inverse effort (Codex family):** a smaller model needs higher effort to approach Sol-`medium` quality — the practical expression is Terra `high` for review-style legs. This is why the registry caps Luna: raising it to chase quality on complex code costs more than Sol `medium` and returns less.

Tier calibration: these defaults assume a $200-tier sub ("sol high if $200 tier, sol low otherwise"). On smaller tiers drop one level; record the owner's tier in `routing-notes.local.md`.

## Plan → execute (complex multi-file legs)

Do not plan and implement in one long high/xhigh/Ultra transcript — that maximizes eagerness, machinery, and cache burn.

1. **Plan leg (Sol `high` or main Sol/Astra context):** produce a file-touch plan with concrete paths and line refs only. Stop. No code edits.
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
- Do not fix unrequested "discovered issues" or expand scope without explicit approval ("the gpt-5.6-sol problem").
- Do not invent new unit test suites or excessive test layers unless specified in criteria.
- Batch tool calls (e.g. read/search multiple targets in single turns) to avoid sequential context re-drag.
- Prefer deleting/simplifying dead paths over adding parallel paths.
- If two designs work, pick the one with fewer new symbols and fewer control-flow branches.
- Stop when criteria pass. Do not continue "improving" the design.
```

**Pathology to reject on review (orchestrator):** one-shot helpers used once (should have been inlined); parallel "v2" paths beside working code; broad try/catch that swallows errors; new config/feature flags for a single call site; invented ticket queues, unrequested test suites, or "noticed another issue" scope expansions.

**VS validation:** same-model bake-off (baseline vs +contract) is defined in `vs-mode.md`. Prefer measuring the contract alone before stacking plan→execute as a second confound.

8. **Review pedantry / inability to approve** (Sottiaux et al., CodeRabbit 2026): OpenAI trained Codex review on the same base weights with dedicated evaluator training, intentionally trading recall to drop false alarms. But unconstrained Codex still over-reports: CodeRabbit measured Sol achieving 69.7% recall (+7.4pp) at the cost of 31.6% precision (231 comments and 61 nitpicks). Without a contract, Sol invents style critiques, comments on untouched lines, and refuses to approve clean code. Steer explicitly along the precision curve: mandate P0/P1 only with repro commands, strictly pin the diff range (`git diff <base>...<head>`), and enforce the clean-bill-of-health rule.

### Code-review contract (paste into every Sol/Terra/Astra code review prompt)

```text
## Code-review contract (MUST)
- Pinned diff scope: Review ONLY the explicitly provided diff range (git diff <base>...<head>) and direct callers/callees. Do NOT critique untouched code or suggest drive-by refactors.
- Repro-backed findings ("Prove It" rule): Every reported issue MUST include:
  1) Exact file and line number.
  2) Concrete failure scenario: trigger input, execution path, and resulting failure state.
  3) Reproducible test or command that proves the failure.
  4) Minimal fix (1–3 lines).
  If you cannot construct a concrete failure trace and repro command, DO NOT report it.
- Strict severity tiers:
  * P0 (Blocking): Crashes, data corruption, auth/security bypass, race conditions, breaking API changes.
  * P1 (Important): Logic errors, performance regressions on realistic workloads, unhandled edge cases.
  * P2 (Advisory): Genuine maintainability concerns (strictly capped at 2 comments max).
  * FORBIDDEN: Cosmetic nits, whitespace/formatting, and alternative style preferences.
- Clean bill of health: If no P0 or P1 bugs exist, explicitly return "VERDICT: APPROVE (No blocking issues found)". Do not invent suggestions to fill space.
- Noise clamp: Maximum 5 total issues reported per review. Rank strictly by severity.
- Read-only sandbox: Do not modify files, run destructive commands, or spawn subagents.
```

## Within-family choice

- **Sol (`gpt-6-sol`, active; `gpt-5.6-sol`, baseline)** — the default Codex workhorse, at `medium` (or `low` when conserving). `gpt-6-sol` supports dynamic reasoning-effort updates and 272k/872k context. Sol `low` ("Light") is first-class for fast parallel scouting/recon because Sol low overthinks far less than smaller models. For code review: Sol `medium` is the fast, cost-effective daily driver (~10× cheaper per bug hunt than 5.6 Sol; Huryn 2026). For high-stakes correctness where missing a bug is costly, retain `gpt-5.6-sol` at `high` or escalate to Astra.
- **Astra (`gpt-6-astra`)** — frontier intelligence tier. High per-token cost; reserved for testing Codex as an **orchestrator** (`codex -m gpt-6-astra`) for high-level architecture and multi-leg decomposition, delegating implementation legs to Sol/Terra. In code review: Astra catches the highest number of subtle bugs (Huryn 2026: 45 vs Sol 6's 29.3 on 105 hidden bugs), making it the frontier escalation for critical security/concurrency reviews.
- **Terra (`gpt-5.6-terra`)** — balanced implementer: earns its keep on (1) well-specified implement *after a plan exists* at `medium`, and (2) review secondary legs at `high` — never as a default, not for design work, not for hard debugging.
- **Luna (`gpt-6-luna`, active; `gpt-5.6-luna`, baseline)** — worker-tier: recon, mechanical edits, review drafts, bulk extraction. Never design work or ambiguous multi-ticket queues. **Topology restriction:** Luna does NOT support multi-agent v2 tools — use Terra or Sol for subagent trees. This is what confines Luna to the standalone single-turn work its registry ladder describes.

### Asymmetric dual-pass review pattern

The strongest industry review pairing is asymmetric across model families (Cross-Model LLM Code Review 2026):
1. **Precision & architectural intent:** Claude Opus 5.5 subagent verifies overall architecture, intent, and maintainability with high signal and low false-alarm noise.
2. **Edge-case recall & proof:** Codex Sol (`gpt-6-sol` medium or `gpt-5.6-sol` high) under the code-review contract stress-tests concurrency, boundary values, error branches, and requires a concrete failing command.
Merge findings that provide a verified repro command; discard speculative nits.

## Harness notes (2026-07-13)

- Prefer pinned headless `codex exec` over the desktop app for orchestration — crash and lost-history reports cluster around the ChatGPT-merge builds. Commit to git after every leg; app/session history is not a backup.
- Final answer lands in the `-o` file; stdout is transcript (registry, `routing-reference.md`).

