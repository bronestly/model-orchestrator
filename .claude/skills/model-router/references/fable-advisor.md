# Fable advisor from a Codex host

This is a rare, read-only second opinion for a GPT-5.6 Sol main session. It approximates but does not reproduce Anthropic's native advisor tool: `claude -p` receives only the dossier supplied by Codex, not the full Codex transcript.

Also used as an **optional taste layer** in VS mode when comparing Sol baseline vs Sol + minimal-code contract (see `vs-mode.md`). VS taste checks still follow the invocation and failure rules below.

## Trigger

Consult Fable at most once per task, and only when the user explicitly requests it or one of these holds:

1. After initial read-only orientation, Codex must choose among multiple plausible approaches for a consequential architecture, migration, security, data-model, or public-interface decision where a wrong choice creates substantial risk or rework.
2. The same implementation approach has failed twice.
3. **Rare overbuild taste check (production):** after a Sol implement leg, the orchestrator has concrete evidence of overbuild (large net LOC / new abstraction layers for a small feature) **and** the user opts in or correctness is already satisfied but maintainability is in doubt. Ask only: is this minimal, and what can be deleted without losing the goal? Not a default on every fat-looking diff.

Complexity, duration, and file count alone are not triggers. Do not consult for routine coding, mechanical refactors, clear bugs, ordinary review, factual research, or final review by default.

If the decision cannot be expressed as one precise question (or a blinded two-diff taste question in VS mode), gather more evidence instead of calling Fable.

## Invocation

Run one fresh call with no tools, no session persistence, and no repository access:

```bash
claude -p \
  --safe-mode \
  --model claude-fable-5 \
  --effort medium \
  --permission-mode plan \
  --tools "" \
  --output-format json \
  --no-session-persistence \
  "<compact dossier>"
```

Use `high` effort only when the user explicitly requests it.

## Dossier

### Architecture / approach decision

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

Include only the minimum relevant excerpts. Never forward the complete transcript, entire diffs, environment values, credentials, secrets, or unrelated proprietary context.

## Failure

This call is best-effort and never blocks the task. On any missing binary, auth, quota, timeout, empty output, or malformed response, do not retry or send a second completion call. Continue with Sol's own judgment and state briefly that the consultation was skipped.
