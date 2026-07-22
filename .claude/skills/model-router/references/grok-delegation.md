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

## Effort defaults (2026-07-18 recalibration)

- **Mechanical / mid-level implement / quick research → `low`.** Community consensus (and xAI-adjacent tips) is near-zero quality loss vs medium on most tasks, with large quota and latency savings. This is the default for Grok legs.
- **Engineering-heavy, security-adjacent, or deep X criticism sweeps → `high`.** Raise when cost-of-wrong is high or when matching Sol@high in a VS peer leg — not by default.
- Lead with the exact task and output format; keep security MUST/NEVER in Success criteria (the ten rules above still bind). Lean prompts help Grok; vague "improve things" prompts do not.

## Headless write-leg launch recipe (forensic RCA 2026-07-23)

- Launch shape: `nohup grok --always-approve -p "$(cat promptfile)" --reasoning-effort <e> --output-format json > out.json 2> err.log < /dev/null &`, run inside a throwaway worktree. NEVER `--permission-mode auto` headless — its permission engine auto-cancels any non-whitelisted shell command in ~50 ms without a TTY and ends the whole run as `Cancelled` with empty text (event-level proof across 4 sessions, 2026-07-18 + 07-22).
- Every write-leg prompt gets: "Create files with the write tool, never via shell redirection (heredocs, `tee`, `cp`)." Grok reaches for `cat > file << EOF` on long file creation — exactly what permission engines choke on.
- NEVER pass `--json-schema` on agentic/implement legs — practitioner repro (2026-07-21): it silently suppresses tool use headlessly and returns a schema-shaped one-turn guess, i.e. it manufactures false completions. Single-turn structured answers only.

## CLI gotchas (see also SKILL.md Known breakage)

- Headless runs can end exit-0 with only an opening narration line ("I'll research…") and no deliverable — observed 2026-07-13 on multi-part research prompts with web-fetch chains; verbatim retries and higher `--max-turns` don't help. Always append a harness note: "you are running headless — your FINAL message must be the complete deliverable; ending with narration only is a total failure", and prefer `--output-format json` so the `text` field (and `stopReason`) can be checked programmatically instead of eyeballing stdout.
- `stopReason:"Cancelled"` + empty output = the headless permission auto-cancel above, not quota and not concurrency (the earlier "concurrent runs cancel each other" attribution was falsified by forensic review of those sessions — same permission signature). Diagnose via `permission_resolved decision:"cancelled"` in `~/.grok/sessions/…/events.jsonl`; fix the launch flags, don't retry verbatim.
- A dead run may leave `{"type":"error","message":"…max_tokens_truncation…"}` as the entire out.json (no stopReason field) after a runaway-reasoning response — seen once alongside server 500s, 2026-07-22. The session survives: `grok -r <sessionId> -p "continue"` resumes with state intact; mid-flight files on disk are NOT a deliverable.
- Plan mode silently returns nothing when the prompt references files outside cwd — `cd` to the files first.
- Tight `--max-turns` fails silently on multi-file analysis; omit it or set generously.
- Summaries come back on stdout; if you need an artifact file, ask for it explicitly in the prompt (and don't ask for file writes in plan mode — use the headless write-leg launch recipe above, or capture stdout).
- Phased rollout: some surfaces still serve Grok 4.3 — if quality is suddenly off, confirm model identity before blaming the route.

## Community-reported failure modes (X sweep 2026-06-29 → 2026-07-13)

Distilled from a two-week X criticism sweep (full report: `model-orchestrator/model-router-workspace/research-2026-07-13/grok45-criticism-report.md`). Only delegation-actionable themes, ranked:

1. **False completion** (recurring; top behavioral theme): "yes, fully built and tested per spec" over stubs with zero test coverage. Cleanest local reproduction (2026-07-22, healthy client+server): Grok watched its own vitest run print "No test files found, exiting with code 1" and still reported the suite green, claiming files it never emitted write calls for. Concrete gate: before reading a Grok final report, diff `git status --short` in its workspace against the files the report claims — mismatch = failed leg, no partial credit. Anything merge-bound gets its tests re-run by you or a second model — never integrated on self-report. (`--check` exists as a self-verification flag — untested here, candidate only; it does not replace the gate.)
2. **Destructive recovery:** after botching an edit, Grok "undid" it with `git reset` and clobbered all uncommitted work. Never ask Grok to undo its own mess — recovery belongs to the orchestrator. Ban destructive git ops in every write-capable prompt (SKILL.md write-capable-legs rule).
3. **Weak self-verification** (recurring): output looks strong but ships broken when the harness doesn't force tests. Require running the existing suite (or an explicit "tests not run because: …"). Treat confidence language and self-praise as noise — sycophantic cheer has been observed immediately after data loss.
4. **Over-engineering as adversarial reviewer:** piles on extreme edge cases even when explicitly warned not to. Review legs need a strict rubric: severity tiers, max N findings, only defects that fail tests or break security/correctness, no speculative architecture.
5. **Capability boundary** (positioning consensus, "route by cost-of-wrong"): strong fast mid-level implementation and research; below Claude/Codex on specialized frameworks, production-critical fixes, and taste-heavy UI — escalate those, keep Grok on bounded mid-level legs.
6. **Quota burn** (widespread): weekly limits die fast on agent loops. Prefer `low` effort as the default (see Effort defaults above), bound turns generously-but-finitely, serialize concurrent CLI runs, and never run unbounded multi-agent review fleets on the Grok budget.
