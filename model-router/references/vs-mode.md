# VS Mode (side-by-side comparison) & self-improvement

Loaded on demand from SKILL.md when the user requests a model comparison. The trigger rules live in SKILL.md; this file is the protocol.

## Cost

Before running, state the overhead in relative terms (roughly N× the tokens of a single run for N models plus a review pass). Never invent dollar figures — this skill deliberately contains no pricing.

## How

1. Pick 2–3 models from overlapping routing-table rows. Send each the identical prompt, success criteria, and summary format so outputs are directly comparable.
2. Have a reviewer from a different family (or a blinded fresh subagent, if only Claude is reachable) compare the outputs. Blind the reviewer: strip model names from filenames and content before it looks. The reviewer must return exactly this scorecard — standardization is what makes runs comparable across sessions:

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
  "decisive_evidence": "<one concrete finding that settled it>",
  "routing_implication": "<one line: what this suggests for the routing table>"
}
```

3. You make the final call (spot-check the reviewer's decisive evidence first) and present the winner plus key differences to the user.
4. Append the scorecard verbatim, with candidate names unblinded, to `routing-notes.md` in the working folder. Keep the file under ~15 entries; prune superseded ones when you write.

## Self-improvement (approval-gated)

After every VS run, compare the scorecard's `routing_implication` against the routing table:

- If it contradicts or refines a row, draft a minimal edit — exact before/after of just the affected cells — and present it to the user with the evidence. State the sample size plainly: a single VS run is one data point, so label the proposal's confidence accordingly (prior consistent entries in `routing-notes.md` raise it).
- **Only after the user explicitly approves**, apply the edit to SKILL.md (in Claude Code the skill lives user-writable in `~/.claude/skills/model-router/`). Never edit the skill without approval.
- If the user declines, record the declined proposal in `routing-notes.md` so you don't re-propose the same change.
- If the skill file isn't writable (e.g., a managed/plugin install like Cowork), stop at the ledger: show the diff for the user to apply manually via their skill settings.
