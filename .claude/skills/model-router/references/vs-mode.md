# VS Mode (side-by-side comparison) & self-improvement

Loaded on demand from SKILL.md when the user requests a model comparison **or** a same-model prompt-variant bake-off (e.g. Sol with vs without the minimal-code contract / "guardrail A/B"). The trigger rules live in SKILL.md; this file is the protocol.

## Cost

Before running, state the overhead in relative terms (roughly N× the tokens of a single run for N candidates plus a review pass; +1 if optional Fable taste runs). Never invent dollar figures: quote a price only when this skill or the user actually states one, and otherwise stay in relative terms. Prefer small, representative tasks or review scopes, not multi-hour epics. Review VS uses N candidate reviews plus orchestrator adjudication; add a paid judge only when justified or requested, and disclose that extra call. Supplied-review comparison makes no candidate calls.

## How (cross-model implementation/output comparison)

Code-review requests use the dedicated protocol below; do not apply this implementation scorecard or require editing worktrees for read-only reviews.

1. Pick 2–3 models from overlapping routing-table rows. Send each the identical prompt, success criteria, and summary format so outputs are directly comparable. If candidates edit files, give each its own isolated git worktree with a fresh dependency install (e.g. `npm ci`) so tests run hermetically, and capture each result as a diff — diffs are what get blinded and reviewed.
2. Have a reviewer from a different family (or a blinded fresh subagent, if only one family is reachable) compare the outputs. Blind the reviewer: strip model names from filenames and content before it looks. The reviewer must return exactly this scorecard — standardization is what makes runs comparable across sessions:

```json
{
  "date": "YYYY-MM-DD",
  "task_type": "<routing-table row this task belongs to>",
  "orchestrator": "<orchestrator model, e.g. opus-5.5 or fable-5.1>",
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
4. If shared state is configured, the orchestrator saves the unblinded scorecard as a new immutable Markdown file under `<state-repo>/events/YYYY/MM/<UTC timestamp>-<device-id>.md`; resolve `<state-repo>` and `<device-id>` from `$HOME/.claude/model-router/state-repo` and `device-id` (or the Windows equivalents). Never overwrite an event. Distill only a persistent routing implication into `<state-repo>/calibration.md`, keeping roughly 15 live entries. If shared state is unavailable, Claude and Grok append to legacy `$HOME/.claude/model-router/routing-notes.md`; Codex only presents the scorecard in the task. Never push shared state automatically.

## Prompt-variant bake-off (same model)

Use this when validating **steering instructions** rather than model identity — especially Sol baseline vs Sol + minimal-code contract (`codex-delegation.md`).

### When

- User asks to compare / A/B / vs-mode the Sol minimal-code contract or related guardrails.
- Orchestrator may **suggest** (never auto-run) a bake-off after repeated Sol bloat in real work.

### Protocol

1. **Same model, same effort, different prompt envelope.** Default both legs: Sol at `medium` (or the production effort for that task). Do not mix efforts in the first bake-off — isolate the guardrail effect.
2. **Candidate A (baseline):** identical goal, context, file allowlist, success criteria, stop rule, and JSON return — **omit** the minimal-code contract, plan→execute split, and bloat-reject re-prompt. Keep pre-existing safety invariants only (no destructive recovery, no nested subagents unless requested, basic scope lock if already shared).
3. **Candidate B (guardrailed):** same base prompt **plus** the full minimal-code contract. Prefer **contract-only** first. If later testing plan→execute, run that as a **second** bake-off and document the extra structure in the scorecard so it is not a hidden confound.
4. **Isolation and capture:** each candidate gets its own git worktree + fresh install. Capture full `git diff` and `git diff --stat` for each. Fill `metrics` from those artifacts.
5. **Blinded primary review:** same scorecard as above. After unblinding, label ledger candidates e.g. `sol-medium-baseline` vs `sol-medium+minimal-code-contract` (or `sol-medium+contract+plan-exec` if that variant was tested).
6. **Promotion discipline:** one win for B is one data point. After **2–3 unrelated bake-offs** where guardrailed B wins or ties on correctness **and** wins on `code_minimalism` / efficiency without systematic correctness loss, propose keeping or tightening the contract via the approval-gated edit flow below. If B loses correctness often, revise the contract wording rather than abandoning measurement.

### Optional Fable taste check

After both candidates finish and metrics are captured, optionally run **one** read-only Fable call (user opt-in, or when correctness is tied / metrics disagree with the primary reviewer). Invocation: the registry's Advisor row plus the dossier and system-prompt discipline in `references/fable-advisor.md`. Blind Fable the same way (strip Sol / baseline / guardrail labels).

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

### Code-review bake-off protocol

Use this for ordinary PR/diff reviews, comparisons of reviewer models (such as Opus vs Codex), and same-model review steering or effort tests. Model aliases, exact IDs, and effort defaults come from the registry. Existing implementation scorecards and historical events keep their format.

1. **Select and freeze.** Resolve 2–3 requested candidates and the exact scope using `codex-delegation.md`. An unspecified Codex reviewer is active Sol; an unspecified Opus reviewer is the registry's current Opus. Accept other explicitly requested available models. Use identical requirements, frozen source/patch, repository instructions, and initial verification evidence. Read-only candidates need no dependency reinstall unless a concrete verification step requires it. Keep ground-truth expectations outside every reviewer's accessible packet/checkout.
2. **Run fresh reviews.** Use each provider's review recipe and steering with the shared P0–P2 contract. Candidates cannot see each other's findings. Record requested and actual model/effort, elapsed time, and usage reported by the harness. Unavailable, silently substituted, empty, or incomplete candidates cannot receive a clean verdict or win; preserve their failure in the scorecard instead of rerouting them. If the user supplied reviews, skip candidate calls and leave absent metadata unknown.
3. **Adjudicate evidence.** Normalize outputs to the shared finding fields and deduplicate reports of the same defect. Validate each material claim against the pinned code and a test, command, or concrete static trace. Classify refuted defects as false positives, style/speculative commentary as noise, and unresolved claims separately; missing evidence is not automatically a false positive. Track which reviewer found each accepted defect. For a live PR, validated bugs establish supported coverage, not total recall. Only a benchmark with an independently established oracle can measure true positives, missed defects, recall, or correct clean approval; otherwise those fields are null.
4. **Judge honestly.** Orchestrator-only adjudication is the default and must be labelled unblinded. If a fresh independent judge is used, strip model/effort labels from artifact names and content and keep the identity mapping outside its packet. Let the judge validate anonymous findings against the same source/evidence, then have the orchestrator verify decisive evidence. Do not tell a blinded judge the model identities. An automatic Fable advisory is not part of review VS.
5. **Compare and report.** Prefer supported bug coverage and precision, weighting severe bugs over cosmetic counts, then evidence quality and measured efficiency. Never reward verbosity or unsupported P0 claims. Return a candidate label, tie (comparable supported results), or inconclusive (failed candidates, unresolved material evidence, incompatible scopes, or unknown identities). No recall-based claim on an ordinary live PR. Unblind identities in the user-facing comparison, bold a winning model only when one exists, and present a consolidated list of actionable defects with provenance. Applying fixes or posting reviews is a separate request.
6. **Record conservatively.** Use the event-storage rules above, with `schema: code-review-v1`, exact model versions and efforts. Preserve old events and calibration. One smoke test establishes functionality, not model superiority; promote routing/prompt changes only through the approval-gated flow below. Never push state automatically.

Review scorecard (repeat the candidate record for every candidate; unknown values are null, not zero):

```json
{
  "schema": "code-review-v1",
  "date": "YYYY-MM-DD",
  "task_type": "code_review",
  "orchestrator": "<exact model and effort>",
  "scope": "<pinned base/head or local snapshot hash>",
  "ground_truth_known": false,
  "adjudication": "orchestrator_unblinded|independent_blinded",
  "candidates": [
    {
      "label": "A",
      "requested_model": "<exact model>",
      "actual_model": null,
      "effort": "<selected effort or null>",
      "status": "complete|unavailable|incomplete",
      "verdict": "FINDINGS|APPROVE|INCOMPLETE",
      "findings_artifact": "<normalized findings location>",
      "limitations": [],
      "metrics": {
        "validated_findings": 0,
        "false_positives": 0,
        "unresolved_claims": 0,
        "noise_count": 0,
        "repro_quality": null,
        "true_positives": null,
        "missed_defects": null,
        "recall": null,
        "clean_approval": null,
        "elapsed_seconds": null,
        "token_usage": null
      }
    }
  ],
  "winner": "<candidate label>|tie|inconclusive",
  "confidence": "high|medium|low",
  "consolidated_findings": [],
  "decisive_evidence": "<validated file:line and trace/repro, or why inconclusive>",
  "routing_implication": "<limited observation, no automatic promotion>"
}
```

`repro_quality` is the percentage of reported defect claims with a usable command/test or concrete static trace; null when no defects were reported. `token_usage` retains the harness's available input/cache/reasoning/output fields without inventing missing ones. `clean_approval` is a boolean only for a known-clean/known-buggy benchmark. `consolidated_findings` use the shared normalized finding shape plus candidate-label provenance. If a supplied review covers another revision and cannot be checked against a common snapshot, mark the comparison inconclusive and show the scope mismatch.

### Follow-up experiments (suggest, never auto-run)

Replace bracketed scopes with a concrete frozen target before launch:

- **Generational implementation:** “Run VS on [small bugfix and acceptance criteria] using previous Sol and active Sol at the same production effort and with the same minimal-code contract. Compare correctness, scope, code minimalism, elapsed time, and reported usage. Keep their changes isolated.”
- **Review effort:** “Compare active Sol at medium versus high on [pinned concurrency/security diff]. Keep model, context, and review contract identical. Validate findings and compare supported coverage, false positives, latency, and usage.”
- **Real PR review:** “Opus vs Codex code review on [PR or base/head]. Review the same frozen scope read-only, report P0–P2 defects, validate and consolidate the findings, and record recall as unknown unless independent ground truth exists.”

## Grok 4.6 liberal-trial calibration (while the trial row is open)

The 4.6 engineering row was widened on 2026-08-15 with deliberately liberal steering so that VS evidence — not inherited 4.5 caution — decides where 4.6 actually belongs. While that trial is open:

- When a real task fits both the Grok row and a Sol/Sonnet/Opus row, the orchestrator may **suggest** (never auto-run) a cross-model VS with Grok 4.6 as one candidate; multi-file implement legs are the highest-value samples because that is exactly where 4.5 lost in v0.17.1.
- Every Grok 4.6 engineering leg — VS or production — that materially wins, loses, or fails a verification gate gets a calibration observation (event file for full scorecards, one distilled line otherwise). "No surprises" legs need no entry.
- A second-generation steering bake-off (Grok 4.6 bare vs Grok 4.6 + the legacy 4.5 hardening rules in `grok-delegation.md`) follows the same-model prompt-variant protocol above; run it only after bare-4.6 legs have produced at least one recurring defect worth testing a guardrail against.
- Re-tightening the routing row (or promoting 4.5-era rules back to default) goes through the approval-gated flow below, citing the accumulated events.

## Generational model transition bake-offs (e.g. Grok 4.6 vs 4.7, Gemini 3.7 vs 3.8 Flash)

When upgrading a route to a new model generation (such as Grok 4.6 → 4.7 or Gemini 3.7 Flash → 3.8 Flash), do not carry over historical failure assumptions or prompt workarounds without empirical testing. Use VS mode to test the new generation against the old:

1. **Protocol:** Send an identical task, coding brief, or research prompt to both models (e.g. `grok-4.6` vs `grok-4.7` at `--reasoning-effort medium`, or `gemini-3.7-flash-medium` vs `gemini-3.8-flash-medium`) using the standard registry invocation shape.
2. **Evaluation focus for Grok 4.6 vs 4.7:**
   - **Task-Completion Honesty vs Narrative:** Does 4.7 deliver 100% of required fields/deliverables, or does its self-check training merely produce more convincing summaries of incomplete work?
   - **Token Consumption & Cost Ratio:** Measure actual reasoning and output tokens consumed. 4.7 burns ~1.5–2× tokens at `high` and `xhigh` is a significant extra step; verify whether the quality gain justifies the token surge for bounded tasks.
   - **Code Minimalism & Component Structure:** Does 4.7 avoid unsolicited helper modules, repeated components, or scope creep?
   - **Long-Horizon Endurance & Bug Repair:** Test multi-file or multi-step logic tasks where 4.7 claims large benchmark jumps (DeepSWE, Terminal-Bench).
3. **Evaluation focus for Gemini 3.7 vs 3.8 Flash:**
   - **Citation & Link Fidelity:** Does 3.8 Flash eliminate 3.7's tendency to reconstruct 404 deep links or fall back to generic homepages?
   - **Factual Hallucination / Mechanism Invention:** Check whether plausible-sounding but fabricated technical mechanisms (observed in 3.7) persist in 3.8.
   - **Reasoning Depth & Speed:** Measure latency and output quality across effort levels (`low`, `medium`, `high`).
   - **Tool Discipline:** Check whether 3.8 respects prompt tool constraints without attempting unapproved shell commands.
4. **Scoring & Ledger:** Record the unblinded scorecard in `<state-repo>/events/YYYY/MM/<timestamp>-<device-id>.md` or `routing-notes.local.md`, clearly tagging candidate versions (`grok-4.6-<effort>` vs `grok-4.7-<effort>`).
5. **Calibration Separation:** Keep track records strictly partitioned by model version. Lessons learned for 4.6 remain archived under 4.6; lessons for 4.7 must be earned through empirical 4.7 or 4.6-vs-4.7 VS runs.

## Orchestrator trials (suggest, never auto-run)

These are untested ideas from outside guidance (2026-09-27). Suggest one only when a real task fits, and record the result as an event tagged with the orchestrator model:

- **Advisor on the spec.** Run a pipeline with and without one advisor pass over the written spec before the legs launch. Measure how many seam-review MAJORs trace back to the spec. This tests Anthropic's executor-plus-advisor pattern against the skill's rare-Fable rule.
- **Clock for Opus 5.5 multi-agent runs.** Add `elapsed Ns / budget Ns` to the orchestrator's turns and compare wall time and tool count. Never run this with a Fable orchestrator: its guidance says budget countdowns cause early wrap-up.

## Self-improvement (approval-gated)

After every VS run, compare the scorecard's `routing_implication` against the routing table **and** against the Sol minimal-code / plan→execute guidance in `codex-delegation.md`:

- If it contradicts or refines a row or the contract wording, draft a minimal edit — exact before/after of just the affected cells or contract bullets — and present it to the user with the evidence. State the sample size plainly: a single VS run is one data point, so label the proposal's confidence accordingly (prior consistent shared events raise it).
- **Only after the user explicitly approves**, edit the source under `$(cat "$HOME/.claude/model-router/source-repo")/.claude/skills/model-router/`, then run `bash "$(cat "$HOME/.claude/model-router/source-repo")/sync.sh"` to propagate all host adapters. Never hand-edit an installed copy (`~/.claude/skills/model-router/`, `~/.agents/skills/model-router/`, or `~/.grok/skills/model-router/`): they are build artifacts. Never edit the skill without approval.
- If the user declines, record the declined proposal in shared calibration when configured, otherwise in legacy `routing-notes.md`, so you don't re-propose the same change.
- If `$HOME/.claude/model-router/source-repo` is missing or unreachable, stop at the scorecard and show the proposed source diff for the user to apply manually.
