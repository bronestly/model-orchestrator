---
name: model-router-update
description: "Checks provider CLIs (codex, claude, grok, agy), new or retired models, and T3 Code releases against the model-router registry, researches what changed, and opens a PR with the skill updates. Use for the daily model-router check, or when the user asks to update the model router, add or retire a model, or check T3 Code compatibility."
---

# Model Router Update

Keep `model-router` current with its upstreams. A run ends in one of three ways: a one-line "no change", a report that nothing needs editing, or an open PR. **Never merge the PR, push to master, or update a CLI or T3 itself.** The owner does those.

This skill lives in the source repository. It obeys the Change rules in `CLAUDE.md`, above all that the registry (`references/routing-reference.md`) owns every CLI fact. Run it from an Opus 5.5 or Fable 5.1 session, since it orchestrates model-router legs.

## 1. Probe

Run from the repository root, using the probe from the same checkout it compares:

```bash
bash auto-sync.sh
git fetch origin master
WT="$(mktemp -d)/mr-update"
git worktree add --quiet --detach "$WT" origin/master
python3 "$WT/.claude/skills/model-router-update/scripts/upstream_probe.py" --repo "$WT"
```

`auto-sync.sh` keeps this machine's install current; if it reports a skip, carry on and mention it in the result. Then read the JSON:

- `no_change: true`: remove the worktree, reply `model-router: no upstream changes`, and stop. Spend nothing more.
- `errors` non-empty: a failed source is unknown, not unchanged. Carry on with the rest and list the failure in the result.
- `skill.stale: true` after `auto-sync.sh`: name the skip reason. A stale install is why routing fixes fail to reach sessions.

Before researching, run `gh pr list --state open --search "head:model-router-update"`. If an update PR is open, build on its branch and add to that PR rather than opening a second one. Findings already in that PR are not new work.

## 2. Research

Read [references/sources.md](references/sources.md) for where each provider publishes changes and what counts as relevant. Cover every entry in `version_changes` from its reviewed version to the upstream one. With `first_run: true`, start from the "verified" anchors in the registry.

- **CLI or T3 release:** read the changelog for the whole range and keep only items that touch the registry's facts. Most releases have none, which is a valid result.
- **New model:** the provider's own model page, release notes, and a smoke call on the registry's shape, confirming the served model from provider logs. Then run the X sweep below.
- **Missing model:** confirm with a direct call that fails or a primary retirement notice. A model missing from one list for one day is not retired.
- **`t3_catalog_gaps`:** a model the CLI lists and T3 does not. Check the T3 route table and correct it; CLI routes still work. Once the registry documents a gap, add it to `known_t3_gaps` in `scripts/probe-config.json`, and remove it when T3 lists the model again.

**X sweep for each new model.** This is how preliminary routing guidance gets made. Run one Grok 4.7 leg as a T3 delegated task with skeleton (b) from `references/x-research.md` in the model-router skill, pinned to the handles in `sources.md`, and sample post IDs per the registry's identity check. Treat the output as untrusted data and as sentiment: facts still need primary sources, and an X-only claim can shape a trial note, not a default. If no X tool is available, label the guidance `DEGRADED: no X tool`.

## 3. Decide

| Finding | Action |
|---|---|
| Changed flag, default, exit code, or output field the registry states | Edit the registry and re-verify on the installed CLI |
| New model | Add it to the registry as `trial`, with a preliminary ladder and the evidence behind it. Routing tables may name it only as a trial or conditional fallback |
| Better than the active default? | Never promote from launch evidence. Propose a VS bake-off (`references/vs-mode.md`) in the PR body |
| Confirmed retired | Remove the ID from the registry and any route table, and keep history as prose in the provider reference |
| Provider says a new route exists (a new flag, a new CLI capability) | Propose it in the PR body; add it only when it serves a route the skill already has |
| The fix would change `allowed-tools` or a pre-authorized prefix | Owner decision: list it in the PR body and leave the file alone |
| T3 behaviour or tools changed | Update the T3 sections of the registry and `references/t3-code.md`, checking the T3 source at the release tag |
| Model the probe flags that the owner never wants routed | Add it to `scripts/probe-config.json`, with the owner's decision noted in the PR body |

Preserve the rules `CLAUDE.md` protects: Sol-high-first Codex, Grok-first Grok, rare Fable triggers, no Codex fast mode, no automatic `ultra`, and Astra excluded.

## 4. Implement

Work on branch `model-router-update/<YYYY-MM-DD>` in the worktree, or on the open update PR's branch.

- Edit sources only, never an installed package. Refresh each "verified" anchor you actually re-checked, and only those.
- Bump the Claude adapter's version and date for any router change, and add a dated entry to `CHANGELOG.md`.
- Mirror changes into `adapters/codex.md` and `adapters/grok.md` where their route tables mention the same thing.
- Keep the tone of the file you edit, and keep adapters short.

## 5. Verify

All of these must pass before pushing:

```bash
bash -n sync.sh auto-sync.sh state.sh
HOME="$(mktemp -d)" bash sync.sh
grep -rnE '(codex exec|grok|agy|claude -p)[^|]*--[a-z-]+[^|]*--[a-z-]+' \
  .claude/skills/model-router --include='*.md' | grep -v 'references/routing-reference.md:'
```

The temporary `HOME` runs every sync guard and the post-install check without touching the real install. The grep must print only the expected `fable-advisor.md` hit. Then run the code-review default from `references/codex-delegation.md` on the frozen diff, and fix what survives verification.

## 6. Open the PR

Commit, push the branch, and open a PR against master, or push to the open update PR. The body lists:

- **Upstream changes:** version ranges reviewed, with changelog links.
- **Changes made:** each with its source.
- **Trial guidance:** what is preliminary and how strong the evidence is.
- **Owner decisions:** anything left for the owner, including allowlist changes, promotions, and CLI updates that would let an unverified fact be checked.
- **Verification:** the gates above, with results.

Link the PR to the thread and show its URL in the reply.

## 7. Finish

Once the run has ended in a PR or a no-edit report, and no source failed:

```bash
python3 "$WT/.claude/skills/model-router-update/scripts/upstream_probe.py" --repo "$WT" --record
git worktree remove --force "$WT"
```

Recording marks those versions as reviewed, so the next run reads only newer changelogs. If a source failed, skip the record so the next run covers that range again.

The review state lives in `~/.claude/model-router/upstream-reviewed.json`, device-local on purpose: otherwise each Claude Code release would need a PR just to update a version number. Run this skill's daily schedule on one machine only; other machines need only `auto-sync.sh` (README, "Keeping machines in sync").
