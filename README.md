# Model Router Skill

A dedicated [Claude Code](https://claude.ai/code) (and compatible agentic IDEs) skill for intelligent, cost-optimized, and model-diverse task routing and subagent execution.

This repository serves as the **source of truth** for the `model-router` skill. Rather than executing all subtasks in your expensive main context, the model router acts as an orchestrator—decomposing tasks, delegating them to the cheapest/fastest model or CLI tool that can do the work well, and verifying the evidence before integrating it back.

---

## 🗺️ Repo Layout

- **[SKILL.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/SKILL.md)** — The central skill configuration containing the routing table, CLI invocation reference, delegation contracts, and self-improvement workflow.
- **[references/](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/)** — Supporting documentation loaded on demand:
  - **[codex-delegation.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/codex-delegation.md)** — Effort levels and burn-control guidance for Codex Sol/Terra/Luna.
  - **[grok-delegation.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/grok-delegation.md)** — Grok 4.5 prompt-steering and known failure modes.
  - **[vs-mode.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/vs-mode.md)** — Side-by-side comparison protocol and verification scorecards.
  - **[x-research.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/x-research.md)** — Real-time research delegation via Grok.
- **[sync.sh](file:///Users/reen/vscode-projects/model-orchestrator/sync.sh)** — Installer and syncer script that copies the local skill to your global environment and registers this repository's root.

---

## ⚡ Routing Matrix at a Glance

The router picks the cheapest model that fits the task requirements, using the following hierarchy:

| Work Type | Primary Model | Fallback Model | Purpose / Rationale |
|---|---|---|---|
| **Ambiguity, High-Stakes Judgment, Final Integration** | **Main Context** (Opus/Fable) | — | Deepest reasoning; holds the session context |
| **Complex Agentic Coding, Computer Use, Math** | **Codex Sol** | Grok 4.5 / Opus subagent | Leads on precise coding; effort-optimized |
| **Deep Analysis & Critical Reviews** | **Opus subagent** | Codex Sol | Frontier depth without burning main context |
| **Mid-level Coding, Real-time X Research** | **Grok 4.5** | Sonnet subagent | Live-X lookups, fast engineering |
| **Bulk chores, Long-context volume, Recon** | **Gemini 3.5 Flash** | GPT-5.6 Luna | High throughput, very low-cost chores |
| **Standard Coding, Writing, Tests & Docs** | **Sonnet subagent** | GPT-5.6 Terra | Reliable worker-tier execution |

---

## ⚙️ Installation & Usage

### 1. Installation
Clone the repository and run the sync script to install the skill globally:
```bash
bash sync.sh
```
This performs three actions:
1. Rsyncs the skill source from `.claude/skills/model-router/` to your global directory (`~/.claude/skills/model-router/`).
2. Registers this repository's path in `~/.claude/model-router/source-repo` so that the skill's self-improvement flow can find its way back here from any directory.
3. Seeds your machine-local calibration log at `~/.claude/model-router/routing-notes.md` (only if it doesn't already exist).

### 2. Developing & Modifying
> [!IMPORTANT]
> **Always edit the source files in this repository**, never the installed files under `~/.claude/skills/model-router/`. Running `bash sync.sh` will overwrite any direct edits to the installed copy.

After making changes to files in this repository, run:
```bash
bash sync.sh
```

---

## 📈 Continuous Calibration & Self-Improvement

The `model-router` skill is designed to adapt to model performance drift, tier updates, and new findings:

1. **Local Calibration Log**: Durable observations (e.g., failed CLI runs, model behavioral drift) are recorded by you or subagents as single dated entries in `~/.claude/model-router/routing-notes.md`.
2. **Standardized VS Mode**: Side-by-side comparisons of different models are evaluated using standard scorecards (correctness, adherence, quality, edge cases, efficiency) in isolated worktrees (see [vs-mode.md](file:///Users/reen/vscode-projects/model-orchestrator/.claude/skills/model-router/references/vs-mode.md)).
3. **Universal Promotion**: When a calibration note or scorecard result is verified across multiple sessions, it is promoted to the versioned `SKILL.md` table. This step is always **approval-gated** and updated in the source repository.
