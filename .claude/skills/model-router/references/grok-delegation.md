# When delegating to Grok 4.6

Loaded on demand from SKILL.md's "Route selection". The launch command, model ID, and effort ladder live in the `routing-reference.md` capability registry — this file carries prompt steering and failure forensics only.

Grounding: Grok 4.6 launch-week X sweep + xAI docs/model card, 2026-08-15 (full report: `model-orchestrator/model-router-workspace/research-2026-08-15/grok46-launch-steering-report.md`; launch-week sample, n≈1 per claim — expect revisions). The 4.5-era steering below is deliberately **demoted to an opt-in appendix**: the 4.6 trial starts liberal so that VS runs and calibration events, not inherited caution, decide what hardening 4.6 actually needs.

## 4.6 steering baseline (liberal trial)

The standard delegation contract (goal, MUST/NEVER, success criteria, scope lock, stop rule, structured result) still applies — that is host-level discipline, not 4.5 hardening. On top of it, only what launch-week evidence supports:

1. **Say what done means.** Enumerate acceptance criteria explicitly; without them 4.6 decides for itself and will invent "done" (xAI field guide, @ericzakariasson 2026-08-12: "write the acceptance criteria down instead of trusting a summary that says it's done").
2. **No pep talk.** "Work very hard / keep pushing" measurably changed nothing; 4.6 persists on its own. Prompt length buys specificity only — write long when you have a spec, short when you want the model's taste.
3. **Enumerate every deliverable, including tests.** 4.6 does exactly what you asked and nothing more ("a bit lazy, like old opus" — @sawyerhood; it will not volunteer test harnesses the way Opus 5 does — @ckpooldev). Unlisted deliverables silently don't happen.
4. **Give it a verification surface, phrased look-then-fix.** "Run the app/tests, list what is wrong, fix only those things" worked where abstract "improve X" failed. For UI legs, provide a DOM/screenshot path; for anything the harness cannot observe, the orchestrator is the verifier.
5. **UI legs: tell it to split repeated components** — it repeats itself in components unless asked not to.
6. **Thoroughness on demand:** if a leg needs edge-case depth, either list the edge cases or plan a follow-up adversarial review pass (one practitioner pattern: an Opus adversarial reviewer clears the laziness in one round).

## Effort

Ladder and defaults are in the registry. 4.6 context: the API's own default is `high` and reasoning cannot be disabled; the 4.5-era quota argument for blanket `low` is retired. `xhigh` is practitioner-verified as a real step up on hard problems ("worth the extra time and tokens" — @ckpooldev; independent bug-bench 27/105 at `xhigh` vs 4.5's best 17) but stays never-automatic — propose it to the user for genuinely hard legs. Spell efforts exactly; see the enum-downgrade gotcha in the registry.

## Verification gates (kept — not 4.5 legacy)

These stay default under the liberal trial because launch-week evidence shows the risks **persist or worsened** in 4.6:

- **False completion persists.** Rippling's 2,100-run bench caught 4.6 "returning 54% of the required fields, but asserting 100%" (@stanine 2026-08-14); the xAI field guide's own author distrusts the completion summary. Gate unchanged: diff `git status --short` in the worker's workspace against what the report claims — mismatch = failed leg, no partial credit. Anything merge-bound gets its tests re-run by the orchestrator or a second model, never integrated on self-report.
- **Hallucination rate worsened** on xAI's own card (0.98% → 1.7% vs 4.5). Factual claims in Grok output keep needing corroboration.
- **Destructive recovery ban** stays in every write-capable prompt (host-level rule): recovery belongs to the orchestrator.
- Not cheaper per task despite unchanged list price: tokens and latency rose vs 4.5 in several independent benches (median 71s → 131s on RipplingBench). Budget leg timeouts generously and watch cost per leg, not per token.

## Calibration duty (the price of the liberal trial)

Every 4.6 engineering leg that materially wins, loses, or trips a gate gets a calibration observation; recurring defects trigger the bare-4.6 vs +legacy-hardening bake-off in `references/vs-mode.md`. "No surprises" legs need no entry.

## Headless write-leg discipline (forensic RCA 2026-07-23, updated 2026-07-28)

The launch shape is in the registry. What that shape is defending against:

- NEVER `--permission-mode auto` headless — its permission engine auto-cancels any non-whitelisted shell command in ~50 ms without a TTY and ends the whole run as `Cancelled` with empty text (event-level proof across 4 sessions, 2026-07-18 + 07-22). Run inside a throwaway worktree.
- Every write-leg prompt gets: "Create files with the write tool, never via shell redirection (heredocs, `tee`, `cp`)." Grok reaches for `cat > file << EOF` on long file creation — exactly what permission engines choke on.
- NEVER pass `--json-schema` on agentic/implement legs — practitioner repro (2026-07-21): it silently suppresses tool use headlessly and returns a schema-shaped one-turn guess, i.e. it manufactures false completions. Single-turn structured answers only.

## CLI gotchas (see also `routing-reference.md` "Known route failures")

- **Shell trap (zsh & PowerShell):** In zsh, do NOT use `status` as a shell variable name when checking Grok's exit code or result (`status` is reserved in zsh). In PowerShell, check `$LASTEXITCODE` or `$?` instead of `$status`. Use custom names like `grok_status`.
- Headless runs can end exit-0 with only an opening narration line ("I'll research…") and no deliverable — observed 2026-07-13 on multi-part research prompts with web-fetch chains; verbatim retries and higher `--max-turns` don't help. Always append a harness note: "you are running headless — your FINAL message must be the complete deliverable; ending with narration only is a total failure", and prefer `--output-format json` so the `text` field (and `stopReason`) can be checked programmatically instead of eyeballing stdout. 4.6 note: narration filler still precedes the report inside `text` (observed 2026-08-13 and 08-15); parse past it rather than treating it as failure.
- `stopReason:"Cancelled"` + empty output = the headless permission auto-cancel above, not quota and not concurrency (the earlier "concurrent runs cancel each other" attribution was falsified by forensic review of those sessions — same permission signature). Diagnose via `permission_resolved decision:"cancelled"` in `~/.grok/sessions/…/events.jsonl`; fix the launch flags, don't retry verbatim.
- A dead run may leave `{"type":"error","message":"…max_tokens_truncation…"}` as the entire out.json (no stopReason field) after a runaway-reasoning response — seen once alongside server 500s, 2026-07-22. The session survives: `grok -r <sessionId> -p "continue"` resumes with state intact; mid-flight files on disk are NOT a deliverable.
- Plan mode silently returns nothing when the prompt references files outside cwd — `cd` to the files first.
- Tight `--max-turns` fails silently on multi-file analysis; omit it or set generously.
- Summaries come back on stdout; if you need an artifact file, ask for it explicitly in the prompt (and don't ask for file writes in plan mode — use the registry's headless shape, or capture stdout).
- Phased leftovers may still serve Grok 4.5 — if quality is suddenly off, confirm model identity before blaming the route.

## Appendix: 4.5-era hardening (opt-in, not default)

Distilled from the 4.5 VS-loss RCA (2026-07-12) and the 4.5 X criticism sweep (report: `model-orchestrator/model-router-workspace/research-2026-07-13/grok45-criticism-report.md`). **Do not apply by default on 4.6 legs.** Apply a matching rule only after a bare-4.6 leg exhibits that defect, record the observation, and let the vs-mode bake-off decide promotion back to default.

Instruction weighting (4.5): success-criteria checklist items > explicit NEVER/MUST one-liners > numbered deliverables > background "study file X" prose > conversational intent. If 4.6 shows the same prose-underweighting, move hard constraints into Success criteria as MUST/NEVER bullets.

Security-critical SQL/RPC legs (the 4.5 loss domain): spell out GRANT matrices rather than "copy the pattern from file X"; state that invented DEFINER helpers inherit the same guard/grant rules; ban comments rationalizing weaker grants; prefer explicit negatives over positive pattern references; force a pre-finish security pass listing every new DEFINER function with its GRANTs; name unsafe defaults (drop/null rules); "mirror file X's filters including column Y" when SQL parity matters.

Review-leg rubric (4.5 over-engineered as adversarial reviewer): severity tiers, max N findings, only defects that fail tests or break security/correctness, no speculative architecture. (Calibration 2026-08-02 showed 4.5 `high` self-pruning well under exactly this rubric — if 4.6 review sweeps run hot, this is the first rule to restore.)
