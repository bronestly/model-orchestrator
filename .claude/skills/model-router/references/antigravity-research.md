# Delegating general web/docs research and bulk legs to Antigravity (agy)

Loaded on demand from the routing table. Antigravity CLI (`agy`) is Google's successor to the retired gemini CLI and the lineup's general web-research and bulk-recon route. Grounding: local smoke tests on agy 1.2.11, 2026-09-26.

Command shapes and model slugs live strictly in the capability registry (`routing-reference.md`). This reference defines prompting discipline, effort selection, and model-separated calibration.

## Model-separated track records

Learnings, failure forensics, and prompting rules are tracked independently per model generation. Do **not** apply 3.7 empirical quirks as fixed assumptions for 3.8, or 3.8 Flash quirks as assumptions for Gemini 4 Argon. Each track record is built through VS mode (`vs-mode.md`).

---

### Gemini 4 Argon (trial, opened 2026-10-28)

Argon is Google's flagship reasoning model, reachable through agy (registry row "Antigravity — Argon"). It is **not a default route yet**: no automatic routing-table row sends work here until the `argon-baseline-v1` evals below produce events. Use it only when the user asks for Argon, or as a candidate in a VS run. Grounding: an official-docs sweep (Codex Sol `high`, web search) and a live-X sweep (Grok 4.7 `high`, 4/4 sampled post IDs resolved), both 2026-10-28, kept in `model-router-workspace/research-2026-10-28/`.

#### What the evidence says so far

- **Claimed strengths:**
  - Tool-heavy knowledge work: Artificial Analysis AutomationBench 78%, the top score.
  - Multimodal documents and long video: Google's LVBench 91.7%.
  - SVG and visual code: Simon Willison found it excellent at every thinking level.
  - Price: half of Opus 5.5's until 2026-11-30.
- **Claimed weaknesses:**
  - It makes up how codebases work. Theo found it "outright unusable for real code work in my codebases. It aggressively hallucinates about how systems work" and reported >50% false claims on his codebase-analysis bench (2026-10-14).
  - It trails Opus 5.5 and Astra on FrontierSWE, Terminal-Bench and the AA Index v5 (Argon `high` 50 vs Opus 5.5 max 58), including on Google's own card.
  - It is slow, with timeouts, which Google's model card itself names.
  - One OCR bench found it invented page content.
- **Local probes (agy 1.4.9):**
  - On one arithmetic check, `low` answered wrong with 0 thinking tokens and `high` answered right with ~1.1k thinking tokens in 22 s.
  - The harness overhead is ~7.6k input tokens per call.
  - About eight short probes used ~3% of the Pro weekly Argon bucket.

These are leads for the evals, not established routing facts.

#### Baseline prompting rules (to be tested, not proven)

1. **Closed spec.** State the goal, the exact inputs, the allowed tools, "done means", and the output sections. One practitioner reported that Argon needs every detail spelled out where Opus fills gaps; that report is isolated, so treat this rule as a hypothesis.
2. **Grounded claims only.** Every claim about code, files or documents cites the file and line, or the fetched source it came from. The worker writes `NOT OBSERVED` instead of describing behaviour it did not see. This targets the codebase-hallucination failure; score it by false-claim rate, not by fluency.
3. **No length targets.** Google states the model "does not follow token-length or word-count targets". Constrain the shape with a section list or a JSON schema instead.
4. **Effort by evaluation.** Google's instruction is to "run your evaluations at all three levels, then pick the lowest level that meets your quality bar". Until the evals pick a level per task type, use `medium`, with `low` only for mechanical work.
5. **Freshness.** The knowledge cutoff is March 2026. Anything later needs a search or fetch tool, or the source supplied in the prompt.
6. **Carried over from Flash, unverified for Argon:** documents first and the question last; no hand-written step-by-step reasoning. Google's prompt guide states both for Gemini 3 only, so each is tested once before it becomes a rule.
7. **agy harness rules still apply:** the headless tool rule and the deliverable guard from the 3.8 section below, plus the registry's timeout bound.
8. **Quota.** On Pro, Argon draws its own weekly bucket. Never spend it on bulk or mechanical work that Flash clears, or on re-checking Flash output.

#### Interim role choices (owner-approved 2026-10-28, from `argon-baseline-v1` E1–E2)

- **agy web-research legs:** prefer Argon `medium` over Flash `high`. On the same official-docs brief it was more accurate (9/14 right vs 7/14), faster (312 s vs 509 s), and used about a quarter of the input tokens. It also got right the CLI facts Flash invented. It is still a source of leads only: it marked a fabricated Google quote and unfetched claims as "verified", and 6/17 of its links were bad. Every rule in the 3.8 trial verdict below (HTTP-check URLs, publish a REJECTED list, primary-fetch anything that enters a deliverable) applies unchanged.
- **Supplied-context Q&A and extraction:** use Argon `low` only when the text is supplied inline or the directory is small (about 25 files), under a cite-or-`NOT FOUND` contract. It scored 45/45 across E1, E1 v2 and E1 v3 with no invented answers and 0 thinking tokens. **Never use it on a large repository:** on the growreports TypeScript tree (`--add-dir`, ~460k input) Argon `low` invented handlers, components and a function signature in 3 of 8 sampled sections under the same contract, where Sonnet invented none (event `20261028T175925Z-pop-os-argon-vs-contest-forum-plan`). That is Theo's reported failure, reproduced. On precise per-file questions over Discourse's Ruby source it tied Sonnet. Large-repo recon stays on Sonnet/Explore or Luna.
- **Plan review:** Argon `high` is a recall add-on only. On a real frozen plan it found 3 valid defects Sol `high` missed, but it also cited plan sections and identifiers that exist nowhere. Check every Argon finding against the frozen artifact, and never use Argon as the sole reviewer. Sol `high` stays the precision reviewer.
- **Quota:** Flash stays the route for bulk work, because Pro's Argon bucket is small; an agentic Argon call cost ~2% of the weekly bucket.

Never use Argon as the citation source of a deliverable, and never route repository writes here (agy write legs are not an established route), until events say otherwise.

#### `argon-baseline-v1` evals

Each task has a ground truth the orchestrator already owns. Score each with the VS scorecard (`vs-mode.md`), plus these metrics:

- false-claim rate;
- dead or wrong link rate;
- `thinking_tokens`, `duration_seconds`, and the drop in the Argon bucket's `remaining_fraction`. Read `/usage` before and after each batch, and allow 5–10 min of lag.

| ID | Task | Candidates | Decides |
|---|---|---|---|
| E1 | 15 factual questions about this skill's own files, supplied inline, with a known answer key | Argon `low`/`medium`/`high`, Flash `high`, Opus 5.5 | Whether the false-claim failure appears; the lowest passing Argon effort |
| E2 | Re-run the 2026-10-28 Argon research brief; the verified reports are the key | Argon `medium`, Flash `high` | Citation fidelity versus Flash |
| E3 | Photo pre-pass on an existing curate-report gold set | Argon `low`/`medium`, Flash `medium` | Vision role and its quota cost |
| E4 | Classify 20 labelled items | Argon `low`, Flash `low` | Bulk role (expected: Flash keeps it) |
| E5 | Critique a past plan whose defects are already known | Argon `high`, Opus 5.5 `medium` | Read-only plan-review role |

A role is promoted only after 2–3 unrelated events agree, through the approval-gated flow in `vs-mode.md`. Record each run as an event tagged with the Argon effort and the orchestrator model.

---

### Gemini 3.8 Flash (Active Baseline & Prompting Best Practice)

Gemini 3.8 Flash (`gemini-3.8-flash-low|medium|high`) is the active default route. It features native internal reasoning controlled via the effort ladder.

#### Prompting best practices

1. **Avoid over-prompting reasoning (unsourced, untested):** 3.8 Flash reasons internally, so this rule says not to prescribe manual "think step-by-step" or verbose reasoning scaffolds. No primary source backs it. Google's prompt-design page has no such instruction (fetched 2026-10-28), and on the same day both Flash 3.8 and Argon produced fabricated "verbatim" Google quotes saying it (`argon-baseline-v1` E2). Keep prompts lean by default, but treat this as a hypothesis to test in a prompt-variant bake-off, not as a vendor rule.
2. **Long-context ordering:** Place raw context, reference documents, or data dumps **first**; place the task description, questions, output format, and constraints at the **end**.
3. **Declarative constraints over process rules:** Clearly specify negative boundaries (what NOT to do), task scope, and stopping conditions. Refine definitions and constraints rather than explaining how to think.
4. **Headless tool rule (critical agy gotcha):** Headless `agy -p` attempts unapproved terminal commands if unconstrained, which get soft-denied to stderr and result in empty stdout. Always prepend an explicit tool rule:
   - For web research: `TOOL RULE: use ONLY built-in web search and fetch tools; do NOT execute terminal or shell commands.`
   - For text extraction or prompt analysis: `TOOL RULE: do NOT use any tools.`
5. **Citation and verification contract:** Require specific deep links (not homepages) with publication dates. Explicitly instruct the model to verify facts against fetched sources before outputting. Unverified claims must be flagged.
6. **Deliverable guard:** "Your FINAL message must be the complete deliverable; ending with narration only is a total failure."

#### Effort ladder

- **`-low` (bulk / recon):** Minimal reasoning latency; best for text extraction, classification, and quick factual lookups.
- **`-medium` (standard research):** Balanced reasoning; default for changelogs, product comparisons, and release sweeps.
- **`-high` (deep sweep):** Maximum reasoning; for multi-source synthesis across many documents or complex investigative sweeps.

#### Trial verdict (closed 2026-10-11)

The 3.8 citation-fidelity question is answered from 8+ runs (2026-09-27 → 10-09, calibration "agy Gemini 3.8 still fabricates deep links"): deep links are unreliable (30/32, 23/46 and all 16 of a five-dossier set dead or wrong; grounding-redirect URLs offered as primary sources). Facts on pages it actually fetched, GitHub links, entity discovery, and a brand's own homepage held.

- Use agy for breadth, leads and entity discovery, never as the citation source of a deliverable.
- Bulk HTTP-check every URL it returns and hand writers a REJECTED list; give every price, ratio or eligibility rule that enters a deliverable a primary fetch.
- For citation-bearing research, prefer Grok 4.7 (official-doc deep links, X) or Codex Sol with web search (calibration "Codex Sol with web search").

---

### Gemini 3.7 Flash (Historical Track Record & Archived Baseline)

Retained in the registry for generational VS bake-offs (`gemini-3.7-flash-low|medium|high`).

#### Historical findings (agy 1.1.5 through 1.2.11)

- **Coverage & speed:** Won the 2026-07-23 bake-off against Grok on coverage and speed (12.8× faster).
- **Citation drift:** Frequently cited homepages instead of deep links and reconstructed plausible URLs from entity names that resolved to 404s.
- **Mechanism invention:** Demonstrated a pattern of inventing plausible technical mechanisms (e.g. BotGuard headers, unexported service methods) and attributing them to real sources.
- **Tool auto-denial:** Repeatedly attempted shell commands on pure research legs unless explicitly forbidden by a tool rule.

These were hypotheses for 3.8. Citation drift is now confirmed on 3.8 (see the trial verdict above); the others remain hypotheses.

---

## When to route here

| Send to agy first | Do NOT send here |
|---|---|
| Recent releases, changelogs, docs sweeps, product comparisons | Live-X discourse, sentiment, launch-day drama → Grok (`x-research.md`) |
| Multi-source synthesis ("what changed across X, Y, Z") | Stable academic/historical knowledge (no delegation needed) |
| Bulk classification, extraction, file reconnaissance (bulk tier) | Anything requiring repository write access (not an established route) |
| Quick factual lookups (verify any link before citing it) | Authoritative single numbers you'll act on unverified; citation sources for a deliverable |

## Reading agy's output

- Deliverable arrives on **stdout**; exit code 0 indicates success. Server-side or tool failures exit non-zero (often exit 3 on permission or auth failures) with stderr.
- Tools needing approval are **soft-denied** with a stderr notice naming the allow-rule — empty stdout plus such a notice means blocked, not model failure.
- If output is insufficient, refine constraints or effort, or route to Grok 4.7 / main context. Higher effort must buy deeper sources and stricter verification, not mere prose length.
- The orchestrator still spot-checks decisive claims on primary sources before final integration.
