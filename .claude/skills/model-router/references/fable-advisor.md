# Fable advisor — cross-model plan review

A read-only second opinion that **any orchestrator model** — Claude main, Codex Sol, Grok, or another — can request from Fable 5 to pressure-test a plan or a consequential decision before committing to implementation. The requesting model invokes `claude -p` and forwards a self-contained dossier. Fable sees **only that dossier** — never the orchestrator's transcript and never the repository — so the dossier must carry everything needed to judge the plan on its merits.

Fable's output serves two purposes, and the dossier should be built for both:

1. **Decide now** — accept, revise, or reconsider the orchestrator's plan.
2. **Steer later** — produce guardrails the orchestrator can hand to whichever model is assigned to implement the plan.

Because of purpose 2, hand Fable the **full detailed plan, not a brief summary.**

Non-Claude orchestrators reach Fable only through this CLI path. A Claude-host orchestrator may instead spawn a native Fable subagent, but the dossier discipline and effort rules below still apply.

Also used as an **optional taste layer** in VS mode when comparing a baseline vs a minimal-code-contract variant (see `vs-mode.md`). VS taste checks follow the same invocation and failure rules.

## Trigger

Consult Fable at most once per task, and only when the user explicitly requests it or one of these holds:

1. The orchestrator has a detailed plan for a consequential architecture, migration, security, data-model, or public-interface decision and wants it pressure-tested before implementation begins — where a wrong approach creates substantial rework or risk.
2. The orchestrator must choose among multiple plausible approaches and cannot resolve it from evidence alone.
3. The same implementation approach has failed twice.
4. **Rare overbuild taste check (production):** after an implement leg, the orchestrator has concrete evidence of overbuild (large net LOC / new abstraction layers for a small feature) **and** the user opts in, or correctness is satisfied but maintainability is in doubt. Ask only: is this minimal, and what can be deleted without losing the goal? Not a default on every fat-looking diff.

Complexity, duration, and file count alone are not triggers. Do not consult for routine coding, mechanical refactors, clear bugs, ordinary review, factual research, or final review by default.

If the decision cannot be expressed as one precise question or a concrete plan to review, gather more evidence instead of calling Fable.

## Invocation

Run one fresh call with no tools, no session persistence, and no repository access. Write the dossier to a temp file first, then expand it into the positional prompt at launch:

```bash
# 1. Write the non-sensitive dossier to a temp file (avoids quoting/length pitfalls).
DOSSIER=$(mktemp)
# ... write the full dossier into "$DOSSIER" ...

# 2. One non-interactive call; the prompt must be present at launch.
claude -p \
  --safe-mode \
  --model claude-fable-5 \
  --effort medium \
  --tools "" \
  --system-prompt "You are a read-only advisor giving one second opinion on a plan or decision. You have no tools, no shell, and no repository access — only the dossier in the user message. Never call, attempt, describe, or plan any tool, file read, or shell command, and never ask to see the repository. Reply with ONLY the requested output as plain prose (short labeled sections or bullets). Emitting tool-use syntax, or narrating what you would investigate instead of answering, is a total failure." \
  --output-format json \
  --no-session-persistence \
  "$(< "$DOSSIER")"
```

### Prompt delivery (headless hosts)

`claude -p` validates its input **at launch** and exits immediately with `Input must be provided either through stdin or as a prompt argument` if neither is there. Verified 2026-07-24. Therefore:

- Deliver the dossier as the **positional argument** (temp file + `"$(< file)"` as above) or as **stdin already connected at spawn** (`claude -p ... < "$DOSSIER"`).
- **Never** launch the process first (PTY or otherwise) and try to write the dossier to stdin afterward — the process has already exited. This is a confirmed failure mode from a Codex host.
- Run it as a plain non-TTY exec, require exit code 0, and read the answer from the JSON `result` field.
- There is **no advisor flag**: the route to Fable is `--model claude-fable-5` on a normal `claude -p` call. Do not invent `--advisor` or similar.
- **GPT-5.6 / Codex hosts: run this command outside the sandbox.** The Codex exec sandbox blocks the network and credential access `claude` needs to reach the API, so a sandboxed call dies on auth/network, and per the Failure policy that consultation is then simply skipped — no retry. Request escalated (non-sandboxed) execution for this one read-only command; it needs no filesystem writes beyond reading the dossier temp file.

Why this exact shape (each flag earns its place):

- `--tools ""` removes every tool, which is the actual read-only guarantee; `--safe-mode` strips this repo's `CLAUDE.md`, skills, hooks, and MCP so nothing leaks into the advisor context.
- `--system-prompt` replaces Claude Code's default coding-agent prompt with a pure advisor persona. **This is required.** Without it, the default agent framing makes Fable try to investigate the repo first, and with no tools it emits *attempted tool instructions instead of a recommendation* (the exact narration-only failure this route hit before).
- **Do not add `--permission-mode plan`.** With no tools it gates nothing, and it reintroduces the "investigate, then present a plan" framing (via a missing `ExitPlanMode`) that produced the tool-instruction narration.
- Read the answer from the JSON `result` field. Verified 2026-07-23: this shape returns the requested sections in one turn (`stop_reason: end_turn`), no tool-use attempts.

### Effort

Pick effort by blast radius, not by prompt length:

- **`medium` (default).** Almost every plan review, architecture second opinion, and overbuild/taste check. Fable's judgment at `medium` is already strong for reviewing a plan it did not have to author.
- **`high` — one step up, reserved.** Use only when the decision is genuinely hard to reverse or high-blast-radius (data-model or schema migration, a security/trust boundary, a public API or wire contract, a cross-cutting refactor), **or** when a `medium` pass came back hedged or shallow on a decision that carries real rework, **or** when the user asks for it.
- **Never `xhigh`, `max`, or `ultra`.** A single read-only advisory does not justify frontier-max compute. If a question seems to need that much, the fix is more evidence, a sharper question, or decomposition — not more effort. (`ultra` is a Codex-only tier and is not even valid for `claude -p`; it is named here so no cross-host orchestrator reaches for it.)

## Dossier

### Plan evaluation (primary)

Use this whenever the orchestrator has a plan to review. Forward the plan in full.

```text
Goal: The outcome the plan must achieve.
Constraints & invariants: What must remain true — performance, compatibility,
  security, data integrity, public contracts.
Context: The repository/system facts that bear on the plan — current
  architecture, relevant modules, prior attempts, known errors and tradeoffs.
  Enough to judge on the merits, not a summary.
Proposed plan (full): The orchestrator's complete plan, verbatim — steps,
  sequencing, files/modules touched, data-model or interface changes, and the
  reasoning behind each. Do not compress it.
Alternatives considered: Approaches weighed and why they were set aside (if any).
Open questions: What the orchestrator is unsure about.
Decision(s) for Fable: The specific calls to review.

Return as short labeled sections (not one prose blob):
1. Verdict — proceed / revise / reconsider-approach.
2. Ranked risks & objections — strongest first, each with why it matters.
3. Missing facts or unstated assumptions the plan depends on.
4. Concrete plan revisions — what to change, add, or cut; specific, not general.
5. Implementor steering notes — guardrails to hand the implementing model:
   what to keep minimal, edge cases to cover, what NOT to build, and the
   acceptance checks that prove the plan was met.
Do not implement anything. Do not ask to see the repository.
```

### Single consequential decision (lightweight)

Use when there is a specific fork to resolve, not a whole plan.

```text
Goal: What outcome is required?
Constraints: What must remain true?
Evidence: What repository facts, errors, or tradeoffs matter?
Question: What single consequential decision should Fable review?

Return at most five bullets: recommendation, strongest objection,
missing fact, risk mitigation, and proceed/revise verdict.
Do not implement anything.
```

### Overbuild / VS taste check

```text
Goal: What outcome is required?
Criteria: Acceptance criteria that define "done."
Evidence: git diff --stat and only the key hunks (labels stripped in VS mode).
Question: Is this the minimal complete solution? What machinery can be
deleted without losing the goal? Any correctness risk if we lean harder?

Return at most five bullets: more-minimal verdict (or X vs Y in VS mode),
concrete deletions, correctness risk, missing fact, proceed/revise/hybrid.
Do not implement anything.
```

### How much context to send

Give Fable enough to judge on the merits — the full plan, the real constraints, and the relevant code facts. **Under-contextualizing is the main failure mode of this route:** a thin dossier yields generic advice. Fable has a large (1M-token) context window, so err toward completeness for plan reviews.

Still never forward credentials, secrets, tokens, environment values, or unrelated proprietary material; redact those from any excerpt. For the terse taste check, keep it to `git diff --stat` plus the key hunks.

## Failure

This call is best-effort and never blocks the task. On any missing binary, auth, quota, timeout, empty output, or malformed response, do not retry or send a second completion call. Continue with the orchestrator's own judgment and state briefly that the consultation was skipped.

A reply whose `result` is only attempted tool-use syntax, or narration of what Fable would investigate, with no actual recommendation, counts as an empty deliverable: treat it as a skipped consultation and fall back to the orchestrator's judgment — do not retry. If the invocation above still produces this, confirm `--system-prompt` is present and `--permission-mode plan` is absent before considering the route usable.
