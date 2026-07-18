# VS Mode (side-by-side comparison) & self-improvement

Loaded on demand from SKILL.md when the user requests a model comparison. The trigger rules live in SKILL.md; this file is the protocol.

## Cost

Before running, state the overhead in relative terms (roughly N× the tokens of a single run for N models plus a review pass). Never invent dollar figures — this skill deliberately contains no pricing.

## How

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
    "efficiency":            {"A": 0, "B": 0}
  },
  "winner": "A|B|hybrid",
  "confidence": "high|medium|low",
  "decisive_evidence": "<one concrete finding that settled it, cited as file:line in the candidate diffs so it can be re-checked without re-reading them>",
  "routing_implication": "<one line: what this suggests for the routing table>"
}
```

3. You make the final call: verify the decisive evidence at its cited location first — if it is overstated or wrong, correct it in the ledger even when the verdict direction survives — then present the winner plus key differences to the user. In that user-facing summary, always name which model/effort produced each candidate (never just "A"/"B" or "1"/"2" — those are for the blinded reviewer only) and **bold the winning model's name**.
4. On Claude, append the scorecard verbatim, with candidate names unblinded, to `$HOME/.claude/model-router/routing-notes.md`; keep it under ~15 entries. On Codex, present the scorecard in the task but do not create cross-host mutable state.

## Self-improvement (approval-gated)

After every VS run, compare the scorecard's `routing_implication` against the routing table:

- If it contradicts or refines a row, draft a minimal edit — exact before/after of just the affected cells — and present it to the user with the evidence. State the sample size plainly: a single VS run is one data point, so label the proposal's confidence accordingly (prior consistent entries in the global `routing-notes.md` raise it).
- **Only after the user explicitly approves**, edit the source under `$(cat "$HOME/.claude/model-router/source-repo")/.claude/skills/model-router/`, then run `bash "$(cat "$HOME/.claude/model-router/source-repo")/sync.sh"` to propagate both host adapters. Never hand-edit either installed copy (`~/.claude/skills/model-router/` or `~/.agents/skills/model-router/`): they are build artifacts. Never edit the skill without approval.
- If the user declines, record the declined proposal in the global `routing-notes.md` so you don't re-propose the same change.
- If `$HOME/.claude/model-router/source-repo` is missing or unreachable, stop at the scorecard and show the proposed source diff for the user to apply manually.
