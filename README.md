# 🚀 Model Router Skill

> **Intelligent Multi-Model Orchestration for Claude Code, OpenAI Codex, and Grok Build.**  
> Outsource and route tasks to the model that does them best and cheapest — save tokens, eliminate code bloat, and stop paying frontier prices for routine tasks.

---

## 🌟 Why Use Model Router?

When working with frontier AI coding agents, using a single model for everything is either **prohibitively expensive**, **slow**, or **sub-optimal**. Model Router equips your primary assistant with an intelligent delegation engine that automatically routes sub-tasks to specialized models:

| Advantage | Why It Matters |
|---|---|
| 💰 **Drastic Cost & Token Savings** | Stop burning expensive orchestrator context on documentation reads, web scraping, and bulk file parsing. Delegate them to ultra-fast, fraction-of-a-cent models like **Gemini 3.8 Flash**. |
| 🎯 **Specialist Superpowers** | Give your coding assistant capabilities it doesn't have alone: real-time X/social search and 500k-token endurance bug repair with **Grok 4.7**, deep agentic coding with **Codex Sol**, and high-stakes plan review with **Fable 5**. |
| ⚡ **No More "Transcript Tax"** | In long sessions, running a subtask inline forces the model to process your entire 100k+ conversation transcript on every turn. Model Router spins up fresh, self-contained sub-tasks with zero transcript overhead. |
| 🛡️ **Enforced Minimal-Code Contract** | Tired of AI agents generating 400 lines of unsolicited helper abstractions for a 5-line fix? Model Router strictly enforces minimal diffs and rejects bloated changes before they hit your codebase. |
| ⚖️ **Empirical VS Bake-Offs** | Objectively benchmark models side-by-side (e.g. Grok 4.6 vs. 4.7, Gemini 3.7 vs. 3.8 Flash, or prompt variants) using structured scorecards. |

---

## 📋 Model Cheat Sheet & Capability Matrix

Model Router unifies your multi-model toolbox into a single capability registry:

| Route / Target | Active Model | Cost & Speed | Best For (Superpowers) | How Output Arrives |
|---|---|---|---|---|
| **Codex Astra** | `gpt-6-astra` | 💎 Frontier<br>⏱️ Deep | Frontier intelligence for testing as an **orchestrator** (`codex -m gpt-6-astra`), high-level architectural decomposition, and complex multi-leg synthesis. | Written to `-o <outfile>` |
| **Codex Sol** | `gpt-6-sol`<br>*(5.6 baseline)* | 💎 Standard<br>⏱️ Medium | Complex agentic coding, hard bug reproduction, multi-file refactoring under the **minimal-code contract**; dynamic reasoning updates. | Written to `-o <outfile>` |
| **Codex Terra** | `gpt-5.6-terra` | 💎 Inexpensive<br>⏱️ Fast | Implementing straightforward tasks from a plan; PR triage and code review. | Written to `-o <outfile>` |
| **Codex Luna** | `gpt-6-luna`<br>*(5.6 baseline)* | 🪙 Lowest<br>⚡ Ultra-Fast | Standalone high-volume processing, batch file extraction, single-turn data tasks. | Written to `-o <outfile>` |
| **Grok** | `grok-4.7`<br>*(4.6 for bake-offs)* | 💎 Moderate<br>⏱️ Medium | Live-X / social search, independent critical code review, long-horizon bug repair (500k context). | stdout (JSON `text`) |
| **Antigravity** | `gemini-3.8-flash`<br>*(low / med / high)* | 🪙 Ultra-Cheap<br>⚡ Ultra-Fast | High-speed web search, official documentation sweeps, multimodal analysis, bulk reconnaissance. | stdout |
| **Advisor (Fable & Opus)** | `claude-fable-5-1`<br>`claude-opus-5-5` | 💎 Frontier / Pragmatic<br>⏱️ Deep | Second opinions: **Fable 5.1** for novel architecture and security boundaries; **Opus 5.5** for pragmatic codebase review, maintainability, and cost-effective plan analysis ($4/$20). | stdout (JSON `result`) |
| **Native Subagents** | `claude-opus-5-5`<br>`claude-fable-5-1`<br>`claude-sonnet-5` | 💎 Standard<br>⏱️ Fast | In-session Claude subagents for precision review, high-stakes verification, tests, and writing. | Subagent message |

---

## 💬 Natural Language Prompting Cheat Sheet

You don't need to remember complex CLI flags. Simply instruct your active assistant in plain English:

### 🛠️ Precision Coding & Bugfixing (Sol + Minimal-Code Contract)
> *"Delegate this backend bugfix to Sol under the minimal-code contract. Plan it first, make the smallest possible diff, and do not create any unnecessary helper abstractions."*

### 👑 Frontier Orchestrator Testing (Codex Astra)
> *"Run Codex using Astra as orchestrator to break down this complex multi-service migration into bounded implementation tickets, delegating the implementation legs to Sol."*

### 🔍 Fast Web & Documentation Sweeps (Antigravity / Gemini 3.8 Flash)
> *"Use Antigravity to do a rapid documentation sweep of the latest Supabase Auth migration guide and summarize breaking changes."*

### 🌐 Live Social Sentiment & Criticism (Grok 4.7)
> *"Have Grok scout live discussions on X from the past 48 hours regarding issues with Next.js 15 app router caching."*

### 🏛️ High-Stakes Architectural & Codebase Reviews (Fable 5.1 & Opus 5.5 Advisors)
> *"Prepare an architectural dossier and consult Fable 5.1 for a second opinion on this database migration plan."*  
> *"Have Opus 5.5 review this refactoring proposal as advisor to check for maintainability risks and overengineering."*  
> *"Run a dual advisory with both Fable 5.1 and Opus 5.5 on this distributed auth proposal and reconcile where they agree and disagree."*

### ⚔️ Side-by-Side Model Bake-Off (VS Mode)
> *"Run a VS bake-off between Grok 4.6 and Grok 4.7 on this algorithm optimization task. Score them on task completion honesty, token burn, and code minimalism."*

### 📦 Standalone Bulk Processing (Luna)
> *"Use Luna to parse and extract structured metadata from all 50 markdown files in the docs folder."*

---

## ⚙️ Operating Rules & Guardrails

Model Router operates under four core principles to protect your codebase and your budget:

1. **The Minimal-Code Contract**: Sol and Terra implement/fix legs must produce the smallest viable diff. Any unsolicited helper classes, wrapper files, or premature abstractions are treated as a failed deliverable and rejected once with re-prompting before escalating effort.
2. **The Transcript-Tax Rule**: When your active session experiences context pressure or compaction, bounded tasks are automatically diverted to clean, fresh contexts (subagents or CLI calls) instead of dragging the entire chat history along.
3. **Headless Safety Locks**:
   - **Grok** headless calls always run with `--always-approve` synchronously from throwaway worktrees. (Headless `--permission-mode plan` or `auto` are forbidden as they auto-cancel tool calls).
   - **Antigravity** calls include strict prompt tool rules (`TOOL RULE: use ONLY built-in web search and fetch tools`) to prevent unapproved shell execution denials.
4. **Single Source of Truth**: All CLI flags, model IDs, and invocation shapes belong exclusively in the [Capability Registry](.claude/skills/model-router/references/routing-reference.md). The installer automatically guards against any drift.

---

## 📦 Step-by-Step Installation Guide

Model Router installs as a native skill for **Claude Code**, **Codex CLI**, and **Grok Build**. Choose your operating system below:

### 🍎 macOS & 🐧 Linux / WSL / Git Bash

#### Step 1: Verify Prerequisites
Ensure you have Git and at least one host CLI installed:
```bash
# Check your installed hosts
claude --version   # Claude Code
codex --version    # OpenAI Codex CLI
grok --version     # Grok Build CLI (v1.0.41+)

# Optional: Check delegation tools
agy --version      # Antigravity CLI (v1.2.11+)
```

#### Step 2: Clone the Repository
```bash
git clone https://github.com/bronestly/model-orchestrator.git
cd model-orchestrator
```

#### Step 3: Run the Installer
```bash
bash sync.sh
```

The script will automatically validate the capability registry against the tool permissions allowlist and install the skill to:
- Claude: `~/.claude/skills/model-router/`
- Codex: `~/.agents/skills/model-router/`
- Grok: `~/.grok/skills/model-router/`

#### Step 4: Verify Installation
```bash
# Verify bash syntax and drift guard
bash -n sync.sh state.sh
bash sync.sh
```

---

### 🪟 Windows (PowerShell 7+)

#### Step 1: Verify Prerequisites
Open PowerShell and verify your tools:
```powershell
Get-Command claude, codex, grok -ErrorAction SilentlyContinue
```

#### Step 2: Clone the Repository
```powershell
git clone https://github.com/bronestly/model-orchestrator.git
cd model-orchestrator
```

#### Step 3: Run the PowerShell Installer
```powershell
.\sync.ps1
```

The script installs the skill to your Windows user profile:
- Claude: `%USERPROFILE%\.claude\skills\model-router\`
- Codex: `%USERPROFILE%\.agents\skills\model-router\`
- Grok: `%USERPROFILE%\.grok\skills\model-router\`

---

## 🔄 Cross-Device Shared Calibration (Optional)

Model Router allows you to sync empirical model observations and benchmark results across multiple machines using an optional, private Git repository.

### 1. Set Up Your Private State Repo
Create a private Git repo with this structure:
```text
calibration.md        # Distilled routing heuristics & benchmark conclusions
events/               # Immutable event logs (YYYY/MM/<timestamp>-<device-id>.md)
archive/              # Historical records of retired models
```

### 2. Configure & Sync

**On macOS / Linux:**
```bash
# Register your local checkout
bash state.sh configure /path/to/private/model-router-state
bash state.sh pull

# Push recorded observations (explicit only)
bash state.sh push

# Check sync status
bash state.sh status
```

**On Windows PowerShell:**
```powershell
.\state.ps1 configure C:\path\to\private\model-router-state
.\state.ps1 pull
.\state.ps1 push
```

> [!NOTE]
> Device-specific facts (such as local binary paths and credentials) are strictly kept local in `~/.claude/model-router/routing-notes.local.md` and are **never** synced to the remote repository.

---

## 🛠️ Repository Layout

```text
.
├── .claude/skills/model-router/
│   ├── SKILL.md                          # Claude orchestrator adapter
│   ├── adapters/
│   │   ├── codex.md                      # Codex adapter source
│   │   └── grok.md                       # Grok adapter source
│   └── references/                       # Shared provider guidance & rules
│       ├── routing-reference.md          # 🔑 Single source of truth for CLI shapes & IDs
│       ├── codex-delegation.md           # Sol/Terra/Luna workflows & minimal-code contract
│       ├── grok-delegation.md            # Grok 4.7/4.6 engineering rules & verification gates
│       ├── antigravity-research.md       # Antigravity (Gemini 3.8 Flash) research protocols
│       ├── x-research.md                 # Grok live-X research guidelines
│       ├── fable-advisor.md              # Fable 5 architecture advisor trigger rules
│       └── vs-mode.md                    # Model & prompt bake-off protocols
├── .grok/skills/model-router/            # Local discovery shim for Grok Build
├── sync.sh / sync.ps1                    # Multi-platform installers with drift guards
├── state.sh / state.ps1                  # Multi-platform state synchronizers
└── AGENTS.md / CLAUDE.md                 # Agent and contributor instructions
```

> [!IMPORTANT]
> **Developer Rule**: Never edit installed skill folders directly. Always make changes in this repository and rerun `bash sync.sh` or `.\sync.ps1`. Installed packages are build artifacts.

---

## 🧪 Developer Verification

Run these three quick checks whenever making changes to the references or adapters:

1. **Syntax Check**:
   ```bash
   bash -n sync.sh state.sh
   ```
2. **Drift Guard & Sync Check**:
   ```bash
   bash sync.sh
   ```
3. **Registry Leak Check**:
   Ensure command shapes have not leaked outside `references/routing-reference.md`:
   ```bash
   grep -rnE '(codex exec|grok|agy|claude -p)[^|]*--[a-z-]+[^|]*--[a-z-]+' \
     .claude/skills/model-router --include='*.md' \
     | grep -v 'references/routing-reference.md:'
   ```
   *(Two hits are expected: `SKILL.md` changelog and `fable-advisor.md` notice).*

