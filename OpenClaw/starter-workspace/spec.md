# OpenClaw Workspace Specification: Starter Learning Workspace

## 1. Executive Summary & Operational Mission
* **Workspace Identifier**: `starter-workspace`
* **Target Role**: Autonomous Personal Engineering Assistant & Architecture Co-Pilot
* **Primary Objective**: Provide an interactive reference template demonstrating the File-First Cognitive Architecture, deterministic context assembly, proactive heartbeat execution, and local-first data sovereignty.
* **Core Philosophy**: "State lives in transparent markdown files, permissions are deterministic, the human retains editorial veto, and the agent never leaks private telemetry."

---

## 2. Workspace Cognitive File Topology

```
starter-workspace/
├── spec.md          # [SPEC] Architecture specification and learning workspace governance
├── SOUL.md          # [READ-ONLY] Identity, tone, values, and behavioral guardrails
├── USER.md          # [READ-ONLY] Target user profile, timezone, and interaction preferences
├── AGENTS.md        # [READ-ONLY] Standard Operating Procedures (SOPs) & permission gates
├── MEMORY.md        # [READ/WRITE] Curated durable knowledge base (projects, facts, ADRs)
└── HEARTBEAT.md     # [AUTONOMOUS] 30-minute scheduled background task checklist
```

### Access & Mutation Matrix
| File | LLM Access | Mutation Trigger | Human Authority |
|---|---|---|---|
| `SOUL.md` | Read-Only | Static | User / Agent Architect |
| `USER.md` | Read-Only *(Append via Memory)* | Profile Updates | Workspace Owner |
| `AGENTS.md` | Read-Only *(Propose via PR)* | Static SOP Refinements | Workspace Owner |
| `MEMORY.md` | Read / Write | Memory Consolidation at Session End | User / Curator |
| `HEARTBEAT.md` | Read & State-Write (`- [x]`) | 30m Periodic Daemon Evaluation | Schedule Architect |

---

## 3. Tool & Execution Permission Matrix

| Tool Category | Permitted Autonomous Actions (No Prompt) | Gatekeeper Actions (MANDATORY User Confirmation) |
|---|---|---|
| **Inspection & Search** | `git status`, `git diff`, reading workspace files, local ripgrep search. | `rm -rf`, `git push --force`, deleting branch histories. |
| **Workspace Notes** | Updating scratch files, formatting checklists, appending to `MEMORY.md`. | Mutating `SOUL.md` or bypassing safety gates in `AGENTS.md`. |
| **Background Tasks** | Querying unread notification feeds, validating local linting state. | Sending external messages, purchasing tokens, deploying to live cloud enclaves. |

---

## 4. Heartbeat Schedule, Concurrency & Autonomous SLAs

* **Pulse Interval**: Every 30 minutes (Default Personal Profile)
* **Concurrency Policy**: `Forbid` (If a pulse evaluation or interactive session is already in-flight, skip/defer the new trigger; overlapping executions within the same workspace are forbidden).
* **Pulse Hard Time-Box**: 60 seconds maximum execution ceiling for routine checks before auto-rollback and zombie alert.
* **Order of Preference & Preemption Queue**:
  1. **P0 (Preemptive): Interactive Operator Turn (`openclaw chat`)** — Direct human commands immediately preempt or pause background pulses.
  2. **P1 (High): Critical Health Alerts / Circuit Breakers** — Immediate threshold breach notifications (e.g. fatal errors, disk saturation).
  3. **P2 (Scheduled): Periodic Heartbeat Pulses** — Evaluated strictly when workspace is idle (`concurrencyPolicy: Forbid`).
  4. **P3 (Idle-Only): Maintenance & Compaction** — Context pruning, offline simulation replay, and memory consolidation run only during verified idle periods.
* **Long-Running Job Isolation (Worktree Sandbox)**:
  - Any task or code generation workflow with expected duration > 60 seconds must fork an ephemeral Git worktree (`.git/worktrees/task-<id>`).
  - `MEMORY.md` on `main` is never held with an active lock during extended execution.
  - State updates to `MEMORY.md` commit as a single atomic turn only upon terminal completion and merge back into `main`.
* **Silence Rule**: If all background validation checks pass and no actionable anomalies require human intervention, emit zero notifications.
* **Periodic Checks (Every 30m)**:
  - Inspect working directory for uncommitted changes or dangling git stashes.
  - Check calendar and pending reminders against active time windows.
* **Weekly Maintenance (Fridays 17:00)**:
  - Consolidate active session logs into durable facts in `MEMORY.md` and prune redundant context.

---

## 5. Hardware Acceleration & Model Routing Profile

* **Cloud-First Mode**: Routes to frontier models (Claude 3.7/3.5 Sonnet, GPT-4o, Gemini 2.5 Pro) via API keys in `~/.openclaw/.env`.
* **Sovereign Local Inference Tier**:
  - *Standard Workstation (24GB VRAM / 32GB RAM)*: Integrates with local inference hub (`localhost:11434` or container `ollama:11434`), routing triage turns to `Qwen-2.5-7B-Instruct` (INT4 AWQ, ~4.5GB) and deep reasoning turns to `Qwen-2.5-32B-Instruct` (INT4 AWQ, ~18GB). MoE 70B models can run via CPU/RAM expert offloading (1-8 t/s), with the operational caveat that task divergence across domains introduces latency delays during dynamic expert paging.
  - *Enterprise / Unified Memory Tier (128GB+)*: NVIDIA DGX Spark (128GB) or Mac Studio M4 Ultra (192GB) runs full-speed 70B dense/MoE models co-resident without offloading bottlenecks.

---

## 6. Deployment & CLI Runbook

### Interactive Terminal Session
```bash
# Start an interactive CLI chat session with this workspace
openclaw chat --workspace ./starter-workspace

# Run a single ad-hoc prompt
openclaw run --workspace ./starter-workspace "Summarise open pull requests and list pending tasks"
```

### Background Daemon Execution
```bash
# Trigger an immediate manual heartbeat evaluation
openclaw heartbeat run --workspace ./starter-workspace --force

# Launch as a continuous background daemon
openclaw gateway start --config ~/.openclaw/starter-workspace/config.json
```
