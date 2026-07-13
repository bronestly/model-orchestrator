# When delegating to Grok 4.5

Loaded on demand from SKILL.md's "How to delegate" section. Source: Grok 4.5's own root-cause analysis of a blinded VS-run loss (2026-07-12, security-critical SQL/edge-fn task — lost 19–20 on instruction adherence while winning efficiency and test breadth). These are its self-reported failure modes and the steering that prevents them.

## Grok's instruction weighting (put things where it looks)

Grok weights, in descending order:

1. **Success-criteria checklist items** (especially phrased "deviations are defects")
2. **Explicit NEVER/MUST one-liners**
3. Numbered deliverable bullets with concrete SQL/TS shapes
4. Background "study file X" references (skimmed for shape, not every predicate)
5. Conversational intent ("writes go through the service-role client") without concrete mechanics

So: security grants and negative constraints belong in **Success criteria**, not only in Background prose.

## The ten rules

1. **Hard constraints live in Success criteria as short MUST/NEVER bullets**, not buried in Background narrative — Grok optimizes for checklist completion and underweights prose while racing deliverables.
2. **Spell out GRANT matrices for SECURITY DEFINER RPCs** (who gets EXECUTE on read vs write). "Copy the pattern from file X" is not enough when writes need a different matrix — Grok over-generalizes the named pattern.
3. **State the rule for invented objects:** any new SECURITY DEFINER helper/wrapper inherits the same guard/grant rules or is owner-only. Grok invents DRY helpers; without this rule it will rationalize their exposure.
4. **Ban security rationalization comments:** "NEVER leave a comment explaining why a weaker grant is safe — fix the grant." This targets Grok's documented habit of blessing deviations post-hoc (its VS-run comment even contained wrong Postgres semantics).
5. **Prefer explicit negatives for security** over positive pattern references — negatives survive structural improvisation; pattern refs only bind objects the prompt named.
6. **Force a pre-finish security pass:** "Before finishing: list every new DEFINER function with its GRANTs and first guard lines; the task fails if any data-touching DEFINER is callable by `authenticated` without a guard." Grok responds well to verification gates.
7. **Name unsafe defaults explicitly** (drop/null vs majority-class). Where classification rules are silent, Grok invents defaults — tell it the drop rule.
8. **Say "mirror file X's filters including column Y"** when parity with existing SQL matters. "Study file X" alone gets you the shape but loses secondary predicates (e.g. `is_unlisted`).
9. **Keep performance/algorithm bullets concrete** (SKIP LOCKED, bounded LATERAL, no cross join, claim ≤ limit) — this is where Grok over-delivers; don't dilute those to make room for constraints.
10. **Keep pure-logic extraction + enumerated test cases** in the deliverable — that's what produced 13 hermetic tests vs the rival's 4. Add a test bullet per critical config scope ("assert per-feed config, not per-shop") when multi-tenancy matters.

## CLI gotchas (see also SKILL.md Known breakage)

- Plan mode silently returns nothing when the prompt references files outside cwd — `cd` to the files first.
- Tight `--max-turns` fails silently on multi-file analysis; omit it or set generously.
- Summaries come back on stdout; if you need an artifact file, ask for it explicitly in the prompt.
