<!-- 
================================================================================
OPENCLAW LEARNING WORKSPACE: MEMORY.md (Curated Long-Term Knowledge Base)
================================================================================
ROLE & PURPOSE:
  MEMORY.md is your agent's durable memory ledger. Unlike ephemeral session
  history (which disappears or gets truncated), MEMORY.md stores curated facts,
  preferences, and decisions across days, weeks, and months.

PERMISSIONS & ACCESS:
  - LLM Access: READ & WRITE (Append / Prune during consolidation).
  - Operator Access: Human review, editing, and pruning.
  - Why? By treating memory as a plain Markdown file, you can audit what your
    agent "knows", fix hallucinated facts with a text editor, and version-control
    it via Git.

MAINTENANCE ADVICE:
  - Keep this file concise (< 4KB / ~1,000 tokens) to minimize token costs.
  - Perform weekly "consolidation": move finished projects to an archive and
    delete obsolete environment parameters.
================================================================================
-->

# MEMORY.md — Curated Long-Term Knowledge Base

> Last Consolidated: 2026-09-01  
> Retention Policy: Keep facts concise; prune completed ephemeral items during weekly heartbeat.

---

<!-- SECTION 1: USER CONTEXT & TECHNICAL PREFERENCES
     Stores operator identity, working patterns, and preferred tech stack.
     The agent reads this to avoid asking "What language do you prefer?" every session. -->
## 1. User Profile & Preferences
* **Primary Operator**: Alex (Technical Lead / Solution Architect)
* **Timezone**: `UTC+01:00` (London / BST)
* **Working Hours**: Mon–Fri 08:30 – 17:30
* **Technical Preferences**:
  - Languages: TypeScript, Python 3.12+, Go, modern C# (.NET 9)
  - Styling: Vanilla CSS / CSS Modules over heavy utility frameworks unless specified.
  - OS Environments: Windows (WSL2 Ubuntu 24.04), macOS Sonoma, Linux server hosts.
  - Package Managers: `pnpm` preferred for JavaScript/Node workspaces, `uv` for Python.

---

<!-- SECTION 2: ACTIVE PROJECTS & ROADMAP REGISTERS
     Tracks active development streams. When a milestone completes, update this
     table so the agent knows the current status without re-reading the whole codebase. -->
## 2. Active Projects & Workspaces
| Project | Path / Repo | Current Milestone | Notes |
|---|---|---|---|
| **Cloud Ops Platform** | `~/work/cloud-ops` | Production v1.4 Release | Deploying automated container health probes |
| **Tech Articles Blog** | `c:/Work/Projects/My-Articles` | OpenClaw Integration Series | Writing technical architecture and installation guides |
| **Agent Gateway** | `~/.openclaw` | Gateway v2.1 Setup | Multi-channel integration (Telegram & Slack) |

---

<!-- SECTION 3: INFRASTRUCTURE & ENVIRONMENT REGISTERS
     Records internal server IPs, dashboard ports, and model routing defaults.
     Never store plaintext passwords or secrets here; store resource URIs only. -->
## 3. Infrastructure & Environments
* **Staging Server**: `10.0.4.15` (Internal VPN only)
* **Container Registry**: `ghcr.io/org-infra`
* **Telemetry Stack**: Prometheus + Grafana at `http://monitoring.internal:3000`
* **Default LLM Routing**:
  - Complex reasoning & code generation: Claude 3.7 Sonnet / Claude 3.5 Sonnet
  - Fast routine tasks & heartbeats: Gemini 2.5 Flash / GPT-4o-mini
  - Offline / private tasks: Ollama `qwen2.5-coder:32b`

---

<!-- SECTION 4: ARCHITECTURAL DECISION RECORDS (ADR REGISTER)
     Chronological log of fundamental technical decisions. Adding dates (YYYY-MM-DD)
     preserves temporal order and prevents the agent from suggesting discarded designs. -->
## 4. Key Architectural Decisions (ADR Register)
* **2026-07-15**: Adopted Model Context Protocol (MCP) for tool integrations across all subagents.
* **2026-08-10**: Standardized all internal agent state storage to human-readable Markdown (`.md`) backed by local Git synchronization.
* **2026-08-28**: Enforced strict localhost binding (`127.0.0.1`) on port `18789` for OpenClaw Gateway daemon to mitigate unauthenticated network access.
