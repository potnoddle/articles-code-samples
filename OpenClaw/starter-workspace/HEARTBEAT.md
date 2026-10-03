<!-- 
================================================================================
OPENCLAW LEARNING WORKSPACE: HEARTBEAT.md (Autonomous Scheduler & Heartbeat)
================================================================================
ROLE & PURPOSE:
  HEARTBEAT.md turns your agent from a passive listener into a proactive 
  collaborator. OpenClaw evaluates this file periodically (default: every 30m).

THE SILENCE RULE:
  - An autonomous agent that alerts on everything creates alert fatigue.
  - RULE: If all checks pass cleanly, the agent MUST remain silent.
  - Outbound alerts are sent ONLY when an actionable threshold is breached.

TASK IDEMPOTENCY:
  - Every task in this file must be safe to execute repeatedly without 
    unintended side effects.

CONCURRENCY & SCHEDULING POLICIES:
  - Concurrency Policy: `Forbid`. A scheduled pulse NEVER executes concurrently with an active job.
  - Preemption: Interactive operator commands (`openclaw chat`) immediately preempt background pulses.
  - Long-Running Jobs: Tasks exceeding 60s must fork an ephemeral Git worktree; MEMORY.md on main is never held locked.

ACCESS:
  - LLM: Evaluates checklist items and updates task state (`- [x]`).
  - Operator: Defines task frequencies, checks, and alert thresholds.
================================================================================
-->

# HEARTBEAT.md — Autonomous Pulse Routines & Periodic Checklist

> **Evaluation Interval**: Every 30 minutes (Default Personal Profile)  
> **Concurrency Policy**: `Forbid` (If an active task or interactive session is in-flight, skip/defer pulse)  
> **Max Pulse Execution Time**: 60s hard time-box for routine checklist evaluation  
> **Order of Preference**: P0 Operator Prompt > P1 Health Alert > P2 Scheduled Heartbeat > P3 Compaction  
> **Rule**: Execute tasks sequentially. If an item requires operator attention, send a concise alert via the primary channel. If all checks pass cleanly, remain silent.

---

<!-- SECTION 1: HIGH-FREQUENCY PULSE CHECKS
     Evaluated on EVERY 30-minute pulse. Keep these fast, read-only, and lightweight.
     Only trigger notifications on actionable threshold breaches. -->
## 1. High-Frequency Checks (Every Pulse / 30 mins)

- [ ] **Gateway & Process Health**
  - Verify OpenClaw daemon is running without unhandled rejection loops.
  - Check disk usage: Ensure workspace filesystem has > 1GB free storage.
  
- [ ] **Critical Incident & Error Log Scanner**
  - Inspect `~/.openclaw/logs/gateway.log` for any `[FATAL]` or repeated `429 Too Many Requests` API errors.
  - *Trigger Condition*: If consecutive error count > 3, alert operator with error summary.

- [ ] **Urgent Notification Queue**
  - Check incoming webhooks / message queues for pending priority mentions.

---

<!-- SECTION 2: DAILY SCHEDULED ROUTINES
     Evaluated once per day at the specified timestamp (e.g. 08:30 or 18:00). -->
## 2. Daily Maintenance Routines

- [ ] **[Daily 08:30] Morning Briefing Assembly**
  - Review calendar events, open pull requests, and unread priority channel pings.
  - Prepare a 3-bullet morning digest for the operator.

- [ ] **[Daily 18:00] End-of-Day Workspace Sync**
  - Stage and commit updated workspace Markdown files (`git commit -m "chore(workspace): daily sync"`).
  - Verify no untracked secrets are present in modified files.

---

<!-- SECTION 3: WEEKLY DEEP MAINTENANCE
     Heavy cleanup routines executed once a week (e.g. Sunday late night). -->
## 3. Weekly Deep Maintenance (Sunday 23:00)

- [ ] **Memory Pruning & Consolidation**
  - Read through [`MEMORY.md`](file:///c:/Work/Projects/My-Articles/DraftMaterial/AI/OpenClaw/sample-workspace/MEMORY.md).
  - Move completed milestones and stale project references to an archive or delete them.
  - Consolidate redundant fact entries to optimize context token window size.

- [ ] **Log Rotation & Vacuuming**
  - Compress logs older than 7 days in `~/.openclaw/logs/`.
  - Vacuum local sqlite session and vector caches in `data/`.
