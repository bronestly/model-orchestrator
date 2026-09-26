# Delegating general web/docs research and bulk legs to Antigravity (agy)

Loaded on demand from the routing table. Antigravity CLI (`agy`) is Google's successor to the retired gemini CLI and the lineup's general web-research and bulk-recon route. Grounding: local smoke tests on agy 1.2.11, 2026-09-26.

Command shapes and model slugs live strictly in the capability registry (`routing-reference.md`). This reference defines prompting discipline, effort selection, and model-separated calibration.

## Model-separated track records

Learnings, failure forensics, and prompting rules are tracked independently per model generation. Do **not** apply 3.7 empirical quirks as fixed assumptions for 3.8. The user builds the 3.8 track record via VS mode (`vs-mode.md`).

---

### Gemini 3.8 Flash (Active Baseline & Prompting Best Practice)

Gemini 3.8 Flash (`gemini-3.8-flash-low|medium|high`) is the active default route. It features native internal reasoning controlled via the effort ladder.

#### Prompting best practices

1. **Avoid over-prompting reasoning:** 3.8 Flash reasons deeply internally. Do **not** prescribe manual "think step-by-step" or verbose reasoning scaffolds — hand-crafted reasoning recipes clutter internal chains of thought.
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

#### Trial status

Active evaluation. Early smoke tests confirm fast execution and wide coverage. Evaluate citation fidelity and link accuracy empirically via generational VS mode (`vs-mode.md`) rather than assuming past flaws.

---

### Gemini 3.7 Flash (Historical Track Record & Archived Baseline)

Retained in the registry for generational VS bake-offs (`gemini-3.7-flash-low|medium|high`).

#### Historical findings (agy 1.1.5 through 1.2.11)

- **Coverage & speed:** Won the 2026-07-23 bake-off against Grok on coverage and speed (12.8× faster).
- **Citation drift:** Frequently cited homepages instead of deep links and reconstructed plausible URLs from entity names that resolved to 404s.
- **Mechanism invention:** Demonstrated a pattern of inventing plausible technical mechanisms (e.g. BotGuard headers, unexported service methods) and attributing them to real sources.
- **Tool auto-denial:** Repeatedly attempted shell commands on pure research legs unless explicitly forbidden by a tool rule.

These historical observations serve as hypotheses to test in 3.7 vs 3.8 VS bake-offs, not as permanent constraints on 3.8.

---

## When to route here

| Send to agy first | Do NOT send here |
|---|---|
| Recent releases, changelogs, docs sweeps, product comparisons | Live-X discourse, sentiment, launch-day drama → Grok (`x-research.md`) |
| Multi-source synthesis ("what changed across X, Y, Z") | Stable academic/historical knowledge (no delegation needed) |
| Bulk classification, extraction, file reconnaissance (bulk tier) | Anything requiring repository write access (not an established route) |
| Quick factual lookups with a citable source | Authoritative single numbers you'll act on unverified |

## Reading agy's output

- Deliverable arrives on **stdout**; exit code 0 indicates success. Server-side or tool failures exit non-zero (often exit 3 on permission or auth failures) with stderr.
- Tools needing approval are **soft-denied** with a stderr notice naming the allow-rule — empty stdout plus such a notice means blocked, not model failure.
- If output is insufficient, refine constraints or effort, or route to Grok 4.6 / main context. Higher effort must buy deeper sources and stricter verification, not mere prose length.
- The orchestrator still spot-checks decisive claims on primary sources before final integration.
