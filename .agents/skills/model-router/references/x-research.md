# Delegating real-time X research to Grok 4.5

Loaded on demand from SKILL.md's routing table and "How to delegate". Grok 4.5 via CLI is the lineup's only live-X route. Grounding: xAI docs sweep + Grok's own verified self-assessment, 2026-07-13 (full reports: `model-orchestrator/model-router-workspace/research-2026-07-13/xdocs-report.md` and `xverify-report.md`).

Core framing: Grok+X is a **high-velocity signal sampler with citation discipline — not a ground-truth oracle**. It tells you what people are saying right now; what actually *happened* still needs primary sources.

## When to route research here

| Send to Grok/X first | Do NOT X-first |
|---|---|
| Trending topics, launch-day reactions, first-hour drama | Exact API/docs behavior, version numbers, pricing tables |
| Latest AI/tech chatter, developer sentiment ("is it usable?") | Academic, historical, or stable long-form knowledge |
| Outage chatter ("is X down?"), fast-moving product drama | Authoritative numbers (prices, scores, statutes, medical) |
| Founder/official primary posts (pin the handles) | Non-English/regional discourse; communities that left X |
| Community criticism/sentiment sweeps | Paywalled journalism (quote-tweet fragments mislead) |

Fast-moving-topic rule: X-first for the *discourse*, then corroborate every factual claim on web/primary sources — or label it "X-only rumor". Astroturfing is always in play: engagement ≠ prevalence of real humans.

## Capability limits to plan around (verified 2026-07-13)

- Grok 4.5's training cutoff is 2026-02-01; the live search tools are the only freshness layer — force their use with explicit research instructions.
- X search tools return roughly ≤10 results per call: depth comes from many angles, not one big query.
- Keyword operators (`from:`, `since:`/`until:`, `min_faves:N`, `filter:…`, OR) work in the CLI runtime; hard date windows are the most reliable filter.
- A citations list means "sources encountered", not "claims grounded" — inline citation is optional model behavior, not a contract.
- No continuous monitoring: "right now" means "as of this turn's tool calls".

## Delegation-prompt checklist

1. **Hard time window** (`since:`/`until:` or "last N days only"); forbid undated claims; semantic search surfaces old-but-relevant posts, so require timestamps and reject out-of-window hits.
2. **≥3 forced search angles**, always including a **criticism/negative pass** (first passes skew positive — query broken/regression/scam/disappointing explicitly) and a **low-engagement practitioner pass** (viral-only sampling misses the quiet experts; cap any single mega-viral post at one evidence slot).
3. **Verbatim quotes only from tool results**, each with @handle + date (+ engagement). Anything not returned by tools this turn = "NOT FOUND" — no memory quotes, no paraphrases presented as quotes.
4. **Prevalence vocabulary:** isolated / notable minority / widespread in sample / dominant in sample — plus the reminder "sample ≠ population".
5. **Sentiment vs fact labels** on every bullet; facts need a primary link or official handle, or get marked "X-only rumor".
6. **Required output structure:** snapshot → evidence (quote·handle·date·prevalence) → competing narratives → confidence & gaps ("what we did NOT find" is signal).
7. **Stop condition:** max tool rounds, then report with gaps rather than inventing.
8. **The headless harness note** from SKILL.md Known breakage (final message = complete report; check via `--output-format json`).

## Effort by research depth

| Depth | Effort |
|---|---|
| Quick "is this moving?" snapshot | `low` |
| Standard daily/weekly brief | `low`–`medium` |
| Deep criticism/sentiment sweep | `high` |
| "What changed in the last N days" brief | `medium`–`high` |

Default to `low` unless the brief needs multi-angle criticism depth. Higher effort must buy more diverse queries and stricter citation rules — not longer prose.

## Prompt skeletons

**(a) Trending-topic snapshot**

```
TOPIC: {topic} (aliases: {aliases}) · WINDOW: last {N}h hard, UTC dates only.
GOAL: is this actually moving, and what's the shape of the conversation?
DO: keyword Top+Latest with since:{date}; one high-engagement pass (min_faves:{K}) and one unfiltered practitioner pass; check official handles: {handles}; web-corroborate any factual claim.
RULES: quotes only from tool results (@handle | date | engagement | verbatim); prevalence labels; separate "claimed" vs "corroborated"; if spam-heavy say SAMPLE POLLUTED.
OUTPUT: snapshot (5 bullets) · trending verdict + why · evidence (3–7 posts) · narratives in conflict · confidence & gaps.
[headless harness note]
```

**(b) Deep criticism/sentiment sweep** (the pattern behind this skill's own research)

```
SUBJECT: {subject} (not: {disambiguation}) · WINDOW: {start} → {end} hard.
REQUIRED ANGLES (all): fans/success · critics (broken OR regression OR scam OR disappointing OR "doesn't work") · practitioners (bugs, pricing, limits) · official from:{handles} · thread-fetch the 2–3 most controversial posts for reply context.
RULES: balanced sections, don't lead with hype; verbatim tool-backed quotes only; prevalence per theme; note bot/brigading suspicion on repetitive copy; facts corroborated on web/primary or marked X-only rumor.
OUTPUT: executive read (sentiment balance) · theme table (theme | stance | prevalence | best evidence) · representative quotes (≤10, mixed stances) · risk flags · what we did NOT find · follow-up queries/handles.
[headless harness note]
```

**(c) "What changed in the last N days" tech brief**

```
DOMAIN: {domain} · WINDOW: last {N} days only (since:{date}); discard older semantic hits.
GOAL: what actually changed (shipped/broken/announced) vs what people merely argued.
METHOD: X launches/releases/outages/pricing + key orgs · developer-reaction slices (not just influencer roundups) · web/primary (release notes, status pages) for each candidate change · chronological timeline.
RULES: each change = date | what | source type (official X / web primary / rumor) | confidence (confirmed/reported/rumor); prefer primary over aggregator screenshots.
OUTPUT: TL;DR (≤8 dated bullets) · timeline · shipped/confirmed · active debates · rumors to ignore unless confirmed · sources & gaps.
[headless harness note]
```
