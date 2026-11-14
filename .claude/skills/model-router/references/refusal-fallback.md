# Refusal fallback for authorized security work (trial)

Loaded on demand. **Trial, owner-approved 2026-11-14, with no local event yet.** Do not treat anything here as measured until a bake-off on a real report of the owner's has been recorded. Command shapes and model IDs are in the registry.

## Trigger

A Claude leg (Fable 5.2, Opus 5.5, or Sonnet) refuses, or is silently moved to an older model by a safeguard (check the session log, `claude-delegation.md`), on work that is all of:

- defensive or authorized: the owner's own systems and code, an incident, a vulnerability report sent to the owner, a CTF, or an engagement the owner states they hold;
- something the orchestrator itself judges legitimate. If the orchestrator would not do the task for its own reasons, there is no fallback: stop and say why.

A refusal on anything else is a result, not a route failure. Report it.

## What to run

1. Tell the user which model refused or was downgraded, and on what.
2. Launch in one response, with the same self-contained brief:
   - a fresh Opus 5.5 native subagent;
   - Codex Sol, read-only, at the registry's effort for security review;
   - Gemini 4 Carbon through the Gemini API (trial);
   - optionally Grok 4.7.
3. The brief states the real authorization context plainly and nothing else changes. Never reword a task to hide what it is, split it to slip past a filter, or add role-play framing. A model that refuses the honest brief has refused.
4. Send other providers only what the owner agreed may leave the machine. An unpatched vulnerability in someone else's software is that party's secret: ask first.
5. Compare the answers as untrusted worker output, verify the fix against the code, and say which models answered, refused, or were downgraded.
6. If every model refuses, stop and report. Do not try more models or prompts.

Record each use as an event with every model's outcome, so the trial can end in a rule or be dropped.

## Evidence so far

- **Local:** none. The calibration history through 2026-11-12 records no Claude refusal on security work.
- **Theo, "Progress?" (2026-11-11, read by three Gemini models, not checked against captions):** on a real vulnerability report for T3 Code, Fable 5.2 was rerouted to Opus 4.8 and other providers refused or downgraded, while Carbon `high` explained the flaw and proposed a fix that a model council scored 7–9 of 10. One anecdote, and he notes his access was early.
- **GreyNoise AI Cyber Index, through one X summary (@ResilientCyber, 2026-11-13, post resolved; index page not opened):** Opus 5.5 had the top raw score but refused 52.4% of file-detection tasks; Grok 4.5 refused none. Gemini is not named.
- **Against Carbon:** in agent loops Theo measured it about five times slower than Opus 5.5 or Sol, and its list price doubles on 2026-12-01 (registry). Use it for a single bounded answer, never as an agent.
