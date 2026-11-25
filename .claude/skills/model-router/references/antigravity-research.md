# Antigravity (agy): lead sweeps and the photo pre-pass

Loaded on demand from the routing table. Antigravity CLI (`agy`) is Google's successor to the retired gemini CLI.

**Role since v0.51.0 (owner decision, 2026-11-14).** agy is no longer a primary route for web research or bulk text. A ledger of about 90 recorded Gemini legs (2026-07-23 → 11-12) showed web research at 2 wins, 11 useful-after-checking and 24 losses, with 4 failed runs; all three YouTube research legs lost or failed, because agy only searches about a video and never sees it; and agy legs ran 5–25 minutes with hangs and "No capacity available" failures. Photo and vision work is where it earned its place (5 wins: review recall 18 exact / 0 missed against 26 and 23 missed, and a 12-vs-2 blind pre-pass win over Haiku 5.5). So: keep agy for the photo pre-pass (Gemini 4 Neon since 2026-11-24, below), use agy web sweeps only as an optional extra lead source, and send video to the Gemini API (`gemini-api.md`). Transport rules are in the registry ("Antigravity transport"). The sections below are the track record and prompting rules for the legs that remain. Grounding: local smoke tests on agy 1.2.11, 2026-09-26.

Command shapes and model slugs live strictly in the capability registry (`routing-reference.md`). This reference defines prompting discipline, effort selection, and model-separated calibration.

## Model-separated track records

Learnings, failure forensics, and prompting rules are tracked independently per model generation. Do **not** apply 3.7 empirical quirks as fixed assumptions for 3.8, or 3.8 Flash quirks as assumptions for Gemini 4 models. Each track record is built through VS mode (`vs-mode.md`).

---

### Photo pre-pass: Gemini 4 Neon (owner decision, 2026-11-24)

Same brief and photos on three growreports reports (505 photos), all at `medium`; events `20261124T110000Z` and `20261124T133000Z`. Single-seed photos found: Neon 235 of 265, Hydrogen 219, 3.8 Flash 208, Haiku 189, Sonnet 186. Wrong seed: Neon 0, Hydrogen 2 and Haiku 1 (all passing the automatic gate), Sonnet 2 (below it), Flash 0 plus one unsupported gated call. Neon uses about three Gemini quota points per report (shared bucket, registry), roughly twice Hydrogen. Fallback is Haiku, with one payload of at most 15 photos per agent. In the photo review, which stays on Sonnet, Neon also found the most (131 of 133 seed tags, Sonnet 124, 0 wrong either way), but tagged two photos a blind judge called undecidable. Confounds: three reports, keys from earlier curations, 15-photo packets for Claude against 30 for Gemini.

**Photo-review trial (owner decision, 2026-11-25).** On the next three curations Neon `medium` reviews the same batches as Sonnet, through T3. Sonnet's result is the one used; a blind judge rules the disagreements. The procedure is in the growreports curate-report skill. Moving the review is a separate owner decision.

### Gemini 3.8 Flash (former baseline & prompting best practice)

Gemini 3.8 Flash (`gemini-3.8-flash-low|medium|high`) was the pre-pass default until 2026-11-24 and leaves Antigravity on the registry's removal date; no agy route uses it. It features native internal reasoning controlled via the effort ladder.

#### Prompting best practices

1. **Avoid over-prompting reasoning (unsourced, untested):** 3.8 Flash reasons internally, so this rule says not to prescribe manual "think step-by-step" or verbose reasoning scaffolds. No primary source backs it. Google's prompt-design page has no such instruction (fetched 2026-10-28), and on the same day both Flash 3.8 and Argon produced fabricated "verbatim" Google quotes saying it (2026-10-28 event). Keep prompts lean by default, but treat this as a hypothesis to test in a prompt-variant bake-off, not as a vendor rule.
2. **Long-context ordering:** Place raw context, reference documents, or data dumps **first**; place the task description, questions, output format, and constraints at the **end**.
3. **Declarative constraints over process rules:** Clearly specify negative boundaries (what NOT to do), task scope, and stopping conditions. Refine definitions and constraints rather than explaining how to think.
4. **Headless tool rule (critical agy gotcha):** Headless `agy -p` attempts unapproved terminal commands if unconstrained, which get soft-denied to stderr and result in empty stdout, or since agy 1.5.7's Auto default may simply run (registry, Permissions). Always prepend an explicit tool rule:
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

Retired from agy on or before 2026-11-05: it left `agy models`, and a direct call is rejected. Kept here as history only.

#### Historical findings (agy 1.1.5 through 1.2.11)

- **Coverage & speed:** Won the 2026-07-23 bake-off against Grok on coverage and speed (12.8× faster).
- **Citation drift:** Frequently cited homepages instead of deep links and reconstructed plausible URLs from entity names that resolved to 404s.
- **Mechanism invention:** Demonstrated a pattern of inventing plausible technical mechanisms (e.g. BotGuard headers, unexported service methods) and attributing them to real sources.
- **Tool auto-denial:** Repeatedly attempted shell commands on pure research legs unless explicitly forbidden by a tool rule.

These were hypotheses for 3.8. Citation drift is now confirmed on 3.8 (see the trial verdict above); the others remain hypotheses.

---

## When to route here

Lead sweeps have no measured agy model left: Argon was removed on 2026-11-25 and 3.8 Flash leaves Antigravity on 2026-11-30. Hydrogen `medium` is the unmeasured option.

| Optional extra lead source (never first) | Do NOT send here |
|---|---|
| Recent releases, changelogs, docs sweeps, product comparisons | Live-X discourse, sentiment, launch-day drama → Grok (`x-research.md`) |
| Multi-source synthesis ("what changed across X, Y, Z") | Stable academic/historical knowledge (no delegation needed) |
| Photo and image pre-pass (Neon `medium`) | Anything requiring repository write access (not an established route); video or YouTube content → `gemini-api.md` |
| Quick factual lookups (verify any link before citing it) | Authoritative single numbers you'll act on unverified; citation sources for a deliverable |

## Reading agy's output

- Deliverable arrives on **stdout**; exit code 0 indicates success. Server-side or tool failures exit non-zero (often exit 3 on permission or auth failures) with stderr. Exit 3 also means `--print-timeout` cut the run short (registry), so check `finished_reason` before treating the output as complete.
- Outside Auto mode (registry, Permissions), tools needing approval are **soft-denied** with a stderr notice naming the allow-rule — empty stdout plus such a notice means blocked, not model failure.
- If output is insufficient, refine constraints or effort, or route to Grok 4.7 / main context. Higher effort must buy deeper sources and stricter verification, not mere prose length.
- The orchestrator still spot-checks decisive claims on primary sources before final integration.
