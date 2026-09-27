# When delegating to Codex

Loaded on demand from the host adapter. The `routing-reference.md` capability registry owns model IDs, invocation shapes, and effort settings. This file defines task choice, prompt content, and verification. Current [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection), [Codex subagent](https://learn.chatgpt.com/docs/agent-configuration/subagents), and [reasoning prompt](https://developers.openai.com/api/docs/guides/reasoning-best-practices) guidance was checked 2026-09-27. Older field observations are hypotheses to test through calibration, not universal model behavior.

## Choose the least costly capable Codex leg

- **Luna:** clear, repeatable work: small edits, extraction, file reconnaissance, and coordinated changes from an explicit brief. Use it for native Codex subagents as well as standalone CLI legs. Keep verification proportional to the change.
- **Sol:** ambiguous, multi-step coding, hard debugging, judgment-heavy review, or work that needs more follow-through. Start at the registry's default effort and increase only when task evidence warrants it.
- **Terra:** a comparison baseline or conditional fallback when local results show a quality, speed, or usage advantage for that workload. Do not call it cheaper merely because it is a smaller older model; published API prices currently favor GPT-6 Sol over Terra on output tokens. Subscription usage may differ.
- **Astra:** excluded from active routing by the owner's preference. Do not use it as an automatic escalation or review backstop.

Count the full task: prompt preparation, a separate plan call, retries, integration, and verification. A cheap model that needs repeated repair may cost more than one Sol call. Keep recent measured outcomes in calibration and revisit defaults when models or account limits change.

## Plan and execute

For ambiguous multi-file work, prefer a Sol `high` read-only plan with concrete files, acceptance criteria, and risks, followed by a fresh Sol `medium` or proven Terra `medium` implementation. Do not make a second model call just because a clear task touches more than one file. For a small well-specified task, send the implementation directly to Luna or Sol with the contract below. The host orchestrator verifies and integrates the result.

Native subagents inherit their parent's model and effort unless configured or selected explicitly. Choose Luna for a light bounded leg and Sol for a demanding one; do not assume an inherited Sol-high worker is economical. Parallel agents help independent read-heavy work, while concurrent writes can conflict. Use nested agents only when user or applicable project/skill instructions request them.

## Prompting a worker

Give the worker a short, self-contained prompt with:

1. The goal and only the context needed to act.
2. Scope and task-specific hard constraints, including relevant repository instructions.
3. Acceptance criteria, proportionate verification, and what evidence to return.
4. A stop rule for a repeated identical failure or a real permission block.

Use the model's own reasoning; do not ask for chain-of-thought or prescribe a long sequence of tool rounds. Be explicit about outcome and boundaries. Avoid a universal file allowlist when the worker must discover the relevant files; require it to explain any expansion beyond the known scope. Do not embed secrets in prompts. If the worker cannot edit or verify, it must report the limitation accurately.

### Minimal-code contract (paste into Codex implement/fix prompts)

```text
Make the smallest change that fully meets the acceptance criteria. Reuse existing code and conventions before adding helpers or configuration. Keep edits within the requested task and explain any necessary related file changes. Do not do unrelated cleanup or add speculative features. Add or update tests only when they verify meaningful behavior or the task requires them. Run the checks appropriate to the change, report actual results, and stop when the criteria are met.
```

Reject a grossly disproportionate or out-of-scope diff once and re-prompt with the specific excess to remove. Do not raise reasoning effort as the first response to a bad approach. If the same gate fails twice with the same error, stop the leg and report the blocker.

### Code-review contract (paste into Codex review prompts)

```text
Review the provided diff range and inspect direct callers/callees only to establish impact. Report at most five actionable defects caused by the change: P0 for release-blocking failures, P1 for significant correctness, security, or realistic performance failures. For each, cite the changed file and line, explain a concrete trigger and failure path, and provide a test, command, or static trace that supports the claim. Suggest the smallest practical correction; do not force an artificial line count. Omit style preferences and speculative concerns. If there are no supported P0/P1 findings, return: VERDICT: APPROVE (No blocking issues found). Keep the review read-only.
```

A runnable repro is strong evidence when practical, but requiring one for every race, security issue, or unavailable environment can hide real defects. The orchestrator must check material claims against the diff and evidence. Ask for advisory maintainability notes separately if those are the review's actual goal.

## Completion and safety

- For write legs, create a recoverable checkpoint before delegation. Forbid destructive recovery, mass deletion, force-push, and credentials or production access outside explicit task scope.
- Trust the diff, files, and real command output over a worker's completion claim. Require `git diff --stat` or equivalent when files changed; run at least one appropriate verification or inspect the relevant result before integration.
- A read-only review must not edit files. A code change needs a relevant diff and verification; a research or review leg needs substantive findings, not a diff.
- Keep returned summaries concise: change/findings, files, checks and results, remaining risk or blocker. For a single Codex leg this concise summary is enough. When the orchestrator aggregates several legs, as in a pipeline, use the host adapter's JSON result instead, so results can be compared field by field.
