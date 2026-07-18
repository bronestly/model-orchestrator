# VS Mode (side-by-side comparison) & self-improvement

Loaded on demand from SKILL.md when the user requests a model comparison **or** a same-model prompt-variant bake-off (e.g. Sol with vs without the minimal-code contract / "guardrail A/B"). The trigger rules live in SKILL.md; this file is the protocol.

## Cost

Before running, state the overhead in relative terms (roughly N× the tokens of a single run for N candidates plus a review pass; +1 if optional Fable taste runs). Never invent dollar figures — this skill deliberately contains no pricing. Prefer small, representative implement tasks (one feature or bugfix), not multi-hour epics.

## How (cross-model)

1. Pick 2–3 models from overlapping routing-table rows. Send each the identical prompt, success criteria, and summary format so outputs are directly comparable. If candidates edit files, give each its own isolated git worktree with a fresh dependency install (e.g. `npm ci`) so tests run hermetically, and capture each result as a diff — diffs are what get blinded and reviewed.
2. Have a reviewer from a different family (or a blinded fresh subagent, if only one family is reachable) compare the outputs. Blind the reviewer: strip model names from filenames and content before it looks. The reviewer must return exactly this scorecard — standardization is what makes runs comparable across sessions:

```json
{
  "date": "YYYY-MM-DD",
  "task_type": "<routing-table row this task belongs to>",
  "candidates": {"A": "<model>", "B": "<model>"},
  "scores_1to5": {
    "correctness":           {"A": 0, "B": 0},
    "instruction_adherence": {"A": 0, "B": 0},
    "output_quality":        {"A": 0, "B": 0},
    "edge_case_handling":    {"A": 0, "B": 0},
    "efficiency":            {"A": 0, "B": 0},
    "code_minimalism":       {"A": 0, "B": 0}
  },
  "metrics": {
    "A": {"net_loc": 0, "files_touched": 0, "new_files": 0, "new_symbols_estimate": 0, "tests_pass": true},
    "B": {"net_loc": 0, "files_touched": 0, "new_files": 0, "new_symbols_estimate": 0, "tests_pass": true}
  },
  "winner": "A|B|hybrid",
  "confidence": "high|medium|low",
  "decisive_evidence": "<one concrete finding that settled it, cited as file:line in the candidate diffs so it can be re-checked without re-reading them>",
  "routing_implication": "<one line: what this suggests for the routing table or Sol steering contract>"
}
```

`code_minimalism` (1–5): fewer unnecessary helpers/abstractions, better reuse, smaller on-task diff, no drive-by cleanup. Reviewer must cite concrete evidence. `metrics` are filled by the **orchestrator** from diffs/test results (not by the blinded model reviewer).

3. You make the final call: verify the decisive evidence at its cited location first — if it is overstated or wrong, correct it in the ledger even when the verdict direction survives — then present the winner plus key differences to the user. In that user-facing summary, always name which model/effort produced each candidate (never just "A"/"B" or "1"/"2" — those are for the blinded reviewer only) and **bold the winning model's name**.
4. On Claude, append the scorecard verbatim, with candidate names unblinded, to `$HOME/.claude/model-router/routing-notes.md`; keep it under ~15 entries. On Codex, present the scorecard in the task but do not create cross-host mutable state.

## Prompt-variant bake-off (same model)

Use this when validating **steering instructions** rather than model identity — especially Sol baseline vs Sol + minimal-code contract (`codex-delegation.md`).

### When

- User asks to compare / A/B / vs-mode the Sol minimal-code contract or related guardrails.
- Orchestrator may **suggest** (never auto-run) a bake-off after repeated Sol bloat in real work.

### Protocol

1. **Same model, same effort, different prompt envelope.** Default both legs: `gpt-5.6-sol` at `medium` (or the production effort for that task). Do not mix efforts in the first bake-off — isolate the guardrail effect.
2. **Candidate A (baseline):** identical goal, context, file allowlist, success criteria, stop rule, and JSON return — **omit** the minimal-code contract, plan→execute split, and bloat-reject re-prompt. Keep pre-existing safety invariants only (no destructive recovery, no nested subagents unless requested, basic scope lock if already shared).
3. **Candidate B (guardrailed):** same base prompt **plus** the full minimal-code contract. Prefer **contract-only** first. If later testing plan→execute, run that as a **second** bake-off and document the extra structure in the scorecard so it is not a hidden confound.
4. **Isolation and capture:** each candidate gets its own git worktree + fresh install. Capture full `git diff` and `git diff --stat` for each. Fill `metrics` from those artifacts.
5. **Blinded primary review:** same scorecard as above. After unblinding, label ledger candidates e.g. `sol-medium-baseline` vs `sol-medium+minimal-code-contract` (or `sol-medium+contract+plan-exec` if that variant was tested).
6. **Promotion discipline:** one win for B is one data point. After **2–3 unrelated bake-offs** where guardrailed B wins or ties on correctness **and** wins on `code_minimalism` / efficiency without systematic correctness loss, propose keeping or tightening the contract via the approval-gated edit flow below. If B loses correctness often, revise the contract wording rather than abandoning measurement.

### Optional Fable taste check

After both candidates finish and metrics are captured, optionally run **one** read-only Fable call (user opt-in, or when correctness is tied / metrics disagree with the primary reviewer). Full invocation shape: `references/fable-advisor.md`. Blind Fable the same way (strip Sol / baseline / guardrail labels).

```text
Goal: <same task goal>
Criteria: <acceptance criteria>
Candidate X: <git diff --stat + key hunks; labels stripped>
Candidate Y: <git diff --stat + key hunks; labels stripped>

Return at most 5 bullets:
1) which is more minimal while still complete
2) concrete machinery to delete from the fatter one
3) any correctness risk in the leaner one
4) missing fact
5) proceed with X / Y / hybrid (and what to take from each)

Do not implement anything.
```

Rules:

- Fable does **not** replace the primary scorecard; it is a second-opinion taste layer (lower eagerness than Sol).
- One Fable call max per VS run; on any failure, skip (same as fable-advisor Failure policy).
- User-facing summary: unblind A/B, **bold the winner**, and if Fable ran, state whether it agreed with the primary reviewer.

## Self-improvement (approval-gated)

After every VS run, compare the scorecard's `routing_implication` against the routing table **and** against the Sol minimal-code / plan→execute guidance in `codex-delegation.md`:

- If it contradicts or refines a row or the contract wording, draft a minimal edit — exact before/after of just the affected cells or contract bullets — and present it to the user with the evidence. State the sample size plainly: a single VS run is one data point, so label the proposal's confidence accordingly (prior consistent entries in the global `routing-notes.md` raise it).
- **Only after the user explicitly approves**, edit the source under `$(cat "$HOME/.claude/model-router/source-repo")/.claude/skills/model-router/`, then run `bash "$(cat "$HOME/.claude/model-router/source-repo")/sync.sh"` to propagate both host adapters. Never hand-edit either installed copy (`~/.claude/skills/model-router/` or `~/.agents/skills/model-router/`): they are build artifacts. Never edit the skill without approval.
- If the user declines, record the declined proposal in the global `routing-notes.md` so you don't re-propose the same change.
- If `$HOME/.claude/model-router/source-repo` is missing or unreachable, stop at the scorecard and show the proposed source diff for the user to apply manually.
