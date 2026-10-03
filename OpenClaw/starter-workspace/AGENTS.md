<!-- 
================================================================================
OPENCLAW LEARNING WORKSPACE: AGENTS.md (Standard Operating Procedures & Safety)
================================================================================
ROLE & PURPOSE:
  AGENTS.md is your agent's operations manual. While SOUL.md sets personality,
  AGENTS.md sets strict execution rules, step-by-step algorithms, and tool
  permission boundaries.

PERMISSIONS & ACCESS:
  - LLM Access: READ-ONLY (Propose changes via PR only).
  - Operator Access: Human-governed.
  - Why? AGENTS.md contains the "Gatekeeper Actions" (security constraints).
    If the agent could edit this file, it could bypass its own safety rules.

EXECUTION FLOW:
  The agent checks AGENTS.md before running shell commands, executing tools,
  or modifying files.
================================================================================
-->

# AGENTS.md — Standard Operating Procedures (SOPs) & Execution Rules

<!-- SECTION 1: CORE OPERATING PRINCIPLES
     Non-negotiable execution fundamentals. These prevent common AI coding 
     anti-patterns like hallucinating untestable edits or rewriting entire files. -->
## 1. Core Operating Principles
Every task execution must adhere to these non-negotiable rules:
1. **Inspect Before Mutating**: Always read existing file contents, directory structures, and git statuses before proposing edits.
2. **Atomic & Minimal Edits**: Avoid complete file rewrites when surgical replacements or targeted patches suffice.
3. **Verify Execution**: Run tests, type checks, or linters immediately after modifying code. Never assume code works untested.
4. **Transparent Communication**: Report what was changed, what was tested, and any lingering risks or next steps.

---

<!-- SECTION 2: TOOL & COMMAND EXECUTION POLICY
     Distinguishes between safe autonomous actions and high-risk gatekeeper 
     actions that MUST have interactive operator confirmation. -->
## 2. Tool & Command Execution Policy

### 2.1 Permitted Autonomous Actions (No Prompt Required)
<!-- The agent can run these freely during chat turns or heartbeat pulses -->
* Reading files, logs, directory listings, and documentation.
* Running non-destructive shell commands: `git status`, `git diff`, `npm test`, `cargo check`, `pytest`.
* Creating temporary scratch scripts in `scratch/` or `tmp/`.
* Querying external read-only APIs and web search tools.

### 2.2 Gatekeeper Actions (MANDATORY User Confirmation Required)
<!-- The agent MUST pause and ask the operator before running any of these -->
Do NOT execute any of the following without explicit interactive confirmation from the operator:
* `rm -rf`, disk format, or mass file deletions.
* `git push --force`, deleting remote branches, or dropping git stashes.
* Executing `DROP TABLE`, `TRUNCATE`, or destructive database migrations.
* Modifying production deployment manifests or killing critical service PIDs.
* Exposing local ports to public tunnels without authentication.

---

<!-- SECTION 3: STANDARD OPERATING PROCEDURES (SOPs)
     Step-by-step recipes for recurring operational tasks. This turns ad-hoc
     vibes into deterministic engineering workflows. -->
## 3. Standard Operating Procedures (SOPs)

### SOP-01: Code Modification & Feature Implementation
1. **Analyze**: Read requirements and all relevant source files.
2. **Plan**: Formulate a step-by-step approach. If complex, provide a brief summary of the plan.
3. **Implement**: Apply targeted modifications. Maintain existing coding style, naming conventions, and docstrings.
4. **Test & Validate**:
   - Run existing unit/integration test suites.
   - Run linter/type checker (e.g. `tsc --noEmit`, `flake8`, `golangci-lint`).
5. **Summarize**: Present the diff and verification outcomes clearly to the operator.

### SOP-02: Incident Triage & Error Investigation
1. Capture exact error strings, exit codes, and timestamps.
2. Check recent logs (`~/.openclaw/logs/` or project application logs).
3. Check `git log -n 5` to identify recent commits or environmental drift.
4. Isolate the root cause before attempting quick fixes.
5. Provide a Root Cause Analysis (RCA) note and suggest remediation steps.

### SOP-03: Memory Consolidation Routine
1. Review session transcripts and scratch files.
2. Identify durable facts (new preferences, completed project milestones, persistent bugs discovered).
3. Append or update the structured sections in `MEMORY.md`.
4. Remove obsolete or outdated information.
