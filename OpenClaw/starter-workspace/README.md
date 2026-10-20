# OpenClaw Starter Learning Workspace

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Path: OpenClaw/starter-workspace](https://img.shields.io/badge/Path-OpenClaw%2Fstarter--workspace-blue.svg)](https://github.com/potnoddle/articles-code-samples/tree/main/OpenClaw/starter-workspace)
[![Series: OpenClaw Sovereign Agent Architecture](https://img.shields.io/badge/Series-OpenClaw%20Architecture-0077b5.svg)](https://www.linkedin.com/in/paul-graham-optimizely/)

Welcome to the **OpenClaw Default Learning Workspace**. This workspace is designed as an interactive, fully commented starter template to help you understand, modify, and master the **File-First Cognitive Architecture** accompanying the *OpenClaw Sovereign Agent Architecture* series.

---

## 📁 Workspace File Map & Roles

```
starter-workspace/
├── spec.md          # [SPEC]       Architecture specification and learning workspace governance
├── SOUL.md          # [READ-ONLY]  Identity, tone, values, and behavioral guardrails
├── USER.md          # [READ-ONLY]  Your profile, timezone, and communication preferences
├── AGENTS.md        # [READ-ONLY]  Standard Operating Procedures (SOPs) & permission gates
├── MEMORY.md        # [READ/WRITE] Curated durable knowledge base (projects, facts, ADRs)
├── HEARTBEAT.md     # [AUTONOMOUS] Scheduled background task checklist & concurrency rules
└── skills/          # [TASK-RULES] Deterministic multi-agent workflows
    └── verified-coder/
        └── SKILL.md # Dual-agent Evaluator-Optimizer self-correcting coder
```

---

## ⚙️ Multi-Tier Model Orchestration & Division of Labour

Combining model tiers into a single orchestrated architecture turns the classic “choice paradox” into a highly efficient division of labour. By chaining models inside frameworks such as LangGraph, n8n, or via the Model Context Protocol (MCP), you exploit the complementary mechanical strengths of each tier:

### 1. The Planner–Executor Pattern
* **Foundation on Low (The Architect):** Use the heavy model to evaluate the initial prompt, decompose it into a structured JSON execution plan, or produce a strict specification blueprint. Its superior semantic depth guarantees that the structural integrity of the plan is correct on the first pass—even when token output is constrained or temperature is kept low.
* **Flash on High (The Worker):** Hand the finished blueprint to a Flash/SLM model running at high temperature. It can then race through the required loops—generating C# or Python scripts, populating data structures, or issuing sequential API calls—without being slowed by latency.

### 2. The Evaluator–Optimiser Loop
* **Flash on High (The Generator):** Task the faster model with producing multiple drafts, alternative code implementations, or continuous reasoning traces. It supplies high-volume output at machine speed.
* **Foundation on Low (The Judge):** Route those outputs into the heavier foundation model for a final quality gate. The foundation model performs only a zero-shot critique, flagging logical fallacies or architectural anti-patterns before accepting or rejecting the candidate.

### 3. Edge Triage and Tool Calling
* **Flash on High (The Router):** Place the Flash/SLM model at the very edge of the pipeline to parse incoming requests, sanitise inputs, extract arguments, and execute routine tool calls.
* **Foundation on Low (The Specialist):** Invoke the heavier model only when the Flash router detects a query that truly demands complex reasoning—deep AST analysis, multi-step strategic simulation, etc.—so that expensive compute is reserved exclusively for heavy cognitive workloads.

This multi-agent design ensures you never waste a large parameter count on mundane data formatting, nor do you ask a lightweight model to make leap-of-faith architectural decisions.

### OpenClaw Skill Architecture: Deterministic Rulebooks
To implement this Evaluator-Optimizer pattern in OpenClaw, the framework uses a highly simplified architecture where a skill is simply a folder containing a `SKILL.md` file. There is no need for special SDKs or compilation; the agent reads YAML frontmatter for metadata and markdown for operational instructions. OpenClaw's core agentic loop naturally cycles through observe, plan, act, and reflect phases, making it an excellent host for this workflow. Because OpenClaw integrates natively with the Model Context Protocol (MCP), the agent can execute standard tools across your local system seamlessly.

*Reference Implementation*: Inspect [`skills/verified-coder/SKILL.md`](./skills/verified-coder/SKILL.md) for the self-correcting coder separating **Persona A (Planner)** from **Persona B (Supervisor)**.

---

## 💓 Heartbeat Rhythms & Execution Governance

A common trap in agent design is treating the "Heartbeat" as a monolithic pulse that wakes the entire agent to re-read everything on a fixed timer. In OpenClaw:
* **The Heartbeat is a Decoupled Cron:** Treat it as a multi-rhythm scheduler. Decouple fast micro-probes (telemetry/status checks) from slower macro-cadences (git audits, context compaction).
* **Escaping the Token Tax:** Pinging closed cloud APIs on routine pulses drains budgets and leaks telemetry. Mitigate the token tax by running open-weight local SLMs (e.g. Qwen 2.5 3B/7B, Llama 3.2 3B) or using fast single-pass decision models (like TypeSafe Jev) to gatekeep progress before generating a single output token.
* **Concurrency Policy (`Forbid`):** Scheduled pulses strictly enforce `concurrencyPolicy: Forbid`. If a previous job or interactive chat is in-flight, the scheduled pulse defers or skips rather than spawning overlapping workers.
* **Preemptive Priority Queue:** The supervisor enforces a strict order of preference:
  `P0 Operator Turn > P1 Health Alert / Circuit Breaker > P2 Scheduled Heartbeat > P3 Compaction`. Direct human prompts always preempt background routines.
* **Worktree Isolation for Long-Running Tasks:** Tasks expected to take >60 seconds fork an ephemeral Git worktree (`.git/worktrees/task-<id>`). `MEMORY.md` on `main` is never held under a blocking lock; mutations commit as a single atomic turn upon merge.

---

## 🚀 How to Learn & Experiment

### Step 1: Inspect the Inline Comments
Every `.md` file in this directory contains comprehensive `<!-- ... -->` comment blocks explaining:
- Why the file exists and how the LLM parses it.
- Whether the file is Read-Only or Read/Write for the model.
- How to prevent common AI failures (sycophancy, alignment drift, token bloat).

### Step 2: Personalize Your Agent
1. Open [`SOUL.md`](./SOUL.md) and adjust the name, demeanor, and communication tone.
2. Open [`USER.md`](./USER.md) and set your name, working hours, and preferred programming languages.
3. Open [`MEMORY.md`](./MEMORY.md) and add your active projects.
4. Review [`spec.md`](./spec.md) for tool permissions and hardware acceleration profiles.

### Step 3: Test with OpenClaw CLI
```bash
# Start an interactive chat session with this workspace
openclaw chat --workspace ./starter-workspace

# Trigger a manual heartbeat pulse
openclaw heartbeat run --workspace ./starter-workspace --force
```

### Step 4: Explore Industry Extensions
For specialized domain blueprints (Cybersecurity SOC, Clinical Healthcare, Corporate Legal, Quant Finance, Supply Chain), explore the companion architecture guides and domain templates featured in the [OpenClaw Series](https://github.com/potnoddle/articles-code-samples).

