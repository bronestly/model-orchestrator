# Delegating general web/docs research and bulk legs to Antigravity (agy)

Loaded on demand from the routing table. Antigravity CLI (`agy`) is Google's successor to the retired gemini CLI and the lineup's general web-research route. Grounding: local smoke tests on agy 1.1.5, 2026-07-23. **Trial status:** confirmed by the 2026-07-23 Grok-vs-agy research bake-off (routing-notes ledger): agy won on coverage and speed (12.8× faster), Grok won on citation fidelity.

Core framing: agy+web is a **broad web synthesizer, not a citation-disciplined verifier**. In the bake-off it surfaced true events the alternative missed, but fabricated/reconstructed several deep links and misdated two items — treat agy URLs as untrusted leads, never forward them unverified; the orchestrator spot-checks decisive claims on primary sources.

## When to route here

| Send to agy first | Do NOT send here |
|---|---|
| Recent releases, changelogs, docs sweeps, product comparisons | Live-X discourse, sentiment, launch-day drama → Grok (`x-research.md`) |
| Multi-source synthesis ("what changed in N weeks across X, Y, Z") | Stable academic/historical knowledge (no delegation needed) |
| Bulk classification, extraction, file reconnaissance (`-low` slug) | Anything requiring repository write access (not an established route) |
| Quick factual lookups with a citable source | Authoritative single numbers you'll act on unverified |

## Verified invocation (agy 1.1.5)

```
agy -p "$(cat promptfile)" --model <slug> --print-timeout 15m
```

- Write the prompt with a file-write tool, not a heredoc; `-p "$(cat promptfile)"` avoids brittle quoting.
- Deliverable arrives on **stdout**; exit code is meaningful (server-side failures exit non-zero with stderr, no silent empty successes since 1.1.1).
- Slugs from `agy models`; effort is encoded in the slug (`gemini-3.6-flash-low|medium|high`, `gemini-3.1-pro-high|low`). Unresolvable `--model` hard-fails listing valid slugs.
- `--print-timeout` defaults to 5m — raise for deep sweeps.
- Web search/fetch run headless without prompting. Tools needing approval are **soft-denied** with a stderr notice naming the allow-rule; empty stdout + such a notice = blocked, not model failure. Never reach for `--dangerously-skip-permissions`.

## Model ladder

| Depth | Slug |
|---|---|
| Bulk classification/extraction/recon | `gemini-3.6-flash-low` |
| Quick lookup or standard brief | `gemini-3.6-flash-medium` |
| Deep multi-source research sweep | `gemini-3.6-flash-high` |
| Flash-high output was insufficient | `gemini-3.1-pro-high` |

Higher tiers must buy more sources and stricter citations, not longer prose.

## Delegation-prompt checklist

1. **Hard time window** for anything recency-sensitive; forbid undated claims.
2. **Citation contract:** every claim carries a specific source URL (deep link, not a homepage) plus a date; uncited claims must be labeled "unverified".
3. **Disambiguation guards** for adjacent products/versions (the observed failure mode — e.g. IDE vs CLI version).
4. **Required output structure:** findings → source list → confidence & gaps ("what I could NOT verify" is signal).
5. **Stop condition:** bounded search rounds, then report with gaps rather than inventing.
6. **Deliverable guard:** "Your FINAL message must be the complete deliverable; ending with narration only is a total failure."

The orchestrator still spot-checks at least one decisive claim on primary sources before integration.
