# When delegating to Grok (4.7 active default; 4.6 baseline)

Loaded on demand from SKILL.md's "Route selection". The launch command, model ID, and effort ladder live in the `routing-reference.md` capability registry — this file carries prompt steering and failure forensics only.

Grounding: Grok 4.7 launch sweep + xAI docs/pricing/benchmarks, 2026-09-26 (full report: `model-orchestrator/model-router-workspace/research-2026-09-26/grok47-steering-report.md`) and Grok 4.6 launch baseline (report: `model-orchestrator/model-router-workspace/research-2026-08-15/grok46-launch-steering-report.md`). Grok 4.7 is the active default with Grok 4.6 retained for generational VS bake-offs (`references/vs-mode.md`). The 4.5-era steering remains an opt-in appendix.

## 4.7 steering baseline (active default)

The standard delegation contract (goal, MUST/NEVER, success criteria, scope lock, stop rule, structured result) still applies — that is host-level discipline, not model hardening. On top of it, what empirical 4.7 research confirms:

1. **Say what done means as observables.** Enumerate acceptance criteria explicitly (which commands must exit 0, which tests/assertions must pass, which file paths may change). 4.7's self-verification RL makes its completion narrative more persuasive, but narrative is not evidence.
2. **No pep talk.** "Work very hard / keep pushing" measurably changed nothing across 4.6 and 4.7; 4.7 persists on its own. Prompt length buys specificity only — write long when you have an exact spec, short when you want the model's taste. Vague length hurts instruction following.
3. **Enumerate every deliverable, including tests.** Grok does exactly what you asked and does not volunteer extra test harnesses, abstractions, or refactors. Unlisted deliverables silently don't happen.
4. **Negative constraints as a literal, testable list.** Put anti-bloat rules directly in MUST/NEVER: "Do not add helper files/modules. Do not add unasked abstractions. Do not touch files outside scope. Do not duplicate components (split/reuse instead)."
5. **Give it a verification surface, phrased look-then-fix.** "Run the app/tests, list what is wrong, fix only those things" worked where abstract "improve X" failed. For UI legs, provide a DOM/screenshot path; for anything the harness cannot observe, the orchestrator is the verifier.
6. **Review legs contract (cap at 5 concrete defects).** Prompt: "Report defects that fail a stated invariant, a test, a type error, or a concrete input. Cap at 5. Include file and line, the broken behavior, and one command that triggers it. Skip style, naming, and speculative hardening." Self-check training creates confident commentary; unconstrained review prompts hallucinate noisy nitpicks.
7. **Token burn & effort realism.** 4.7 burns ~1.5–2× reasoning tokens vs 4.6 at `high`. `xhigh` is a significant extra cost step (~81k output tokens on benchmark tasks); never select `xhigh` automatically. Context window is 500k, but crossing 200k prompt tokens doubles pricing on all tokens. Temperature: 0.0–0.3 for code/math. Do not pass `stop` or presence/frequency penalties (API errors).

## Effort

Ladder and defaults are in the registry. 4.7 context: the API's own default is `high` and reasoning cannot be disabled. Skill default for bounded engineering and review legs is **`medium`** (conserving tokens while preserving reasoning depth); select `high` for deep multi-file implement or research sweeps. `xhigh` is never automatic — propose it only for genuinely hard legs where quality outranks token cost. Spell efforts exactly (`low, medium, high, xhigh`); see the enum-downgrade gotcha in the registry.

## Verification gates (kept — not 4.5 legacy)

These stay default because 4.7's improved self-verification does not eliminate task-level completion risk:

- **False completion persists.** 4.7 writes more polished self-checks, but completion claims still require independent proof. Gate unchanged: diff `git status --short` in the worker's workspace against what the report claims — mismatch = failed leg, no partial credit. Anything merge-bound gets its tests re-run by the orchestrator or a second model, never integrated on self-report.
- **Factuality & grounding.** Knowledge cutoff is May 2026; live facts require search tools. Corroborate factual claims or label them unverified.
- **Destructive recovery ban** stays in every write-capable prompt (host-level rule): recovery belongs to the orchestrator.
- Budget leg timeouts generously (client timeout 3600s in xAI examples); tight foreground timeouts kill healthy reasoning runs.

## Calibration duty

Every 4.7 engineering leg that materially wins, loses, or trips a gate gets a calibration observation; generational comparisons against 4.6 follow the bake-off protocol in `references/vs-mode.md`. "No surprises" legs need no entry.

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
