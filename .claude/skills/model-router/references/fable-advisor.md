# Fable advisor from a Codex host

This is a rare, read-only second opinion for a GPT-5.6 Sol main session. It approximates but does not reproduce Anthropic's native advisor tool: `claude -p` receives only the dossier supplied by Codex, not the full Codex transcript.

## Trigger

Consult Fable at most once per task, and only when the user explicitly requests it or either condition holds:

1. After initial read-only orientation, Codex must choose among multiple plausible approaches for a consequential architecture, migration, security, data-model, or public-interface decision where a wrong choice creates substantial risk or rework.
2. The same implementation approach has failed twice.

Complexity, duration, and file count alone are not triggers. Do not consult for routine coding, mechanical refactors, clear bugs, ordinary review, factual research, or final review by default.

If the decision cannot be expressed as one precise question, gather more evidence instead of calling Fable.

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

```text
Goal: What outcome is required?
Constraints: What must remain true?
Evidence: What repository facts, errors, or tradeoffs matter?
Question: What single consequential decision should Fable review?

Return at most five bullets: recommendation, strongest objection,
missing fact, risk mitigation, and proceed/revise verdict.
Do not implement anything.
```

Include only the minimum relevant excerpts. Never forward the complete transcript, entire diffs, environment values, credentials, secrets, or unrelated proprietary context.

## Failure

This call is best-effort and never blocks the task. On any missing binary, auth, quota, timeout, empty output, or malformed response, do not retry or send a second completion call. Continue with Sol's own judgment and state briefly that the consultation was skipped.
