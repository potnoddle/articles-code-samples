# AI Alignment: Formal Ground Truth & Evaluator-Optimizer Suite

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Formal: Lean 4](https://img.shields.io/badge/Kernel-Lean%204-purple.svg)](https://leanprover.github.io/)
[![Benchmarks: Complete](https://img.shields.io/badge/Benchmarks-ALL%20VERIFIED-brightgreen.svg)](run.ps1)

Empirical research, architectural specifications, and runnable verification harnesses translating **formal interactive theorem provers (Lean 4)** and **deterministic process supervision (Evaluator-Optimizer Pattern)** into enterprise-grade AI safety boundaries.

---

## 🧭 The Core Thesis

> **Reinforcement Learning from Human Feedback (RLHF) is an optimization engine, not a control mechanism. True alignment cannot rely on parenting statistical black boxes or instilling synthetic simulation religions. Ground truth must migrate to machine-checked formal verification kernels.**

---

## 🏛️ Component Architecture

```
AI-Alignment-Paradox/
├── evaluator_optimizer.py              # Dual-agent Planner-Supervisor runner
├── verify_kernel.py                    # Formal proof ground truth runner
├── KernelProof.lean                    # Lean 4 formal proof specification (Requires Lean 4)
│
├── defensive-configs/
│   └── verified-coder-rubric.json      # Declarative 4-point grading rubric
│
├── sample-alerts/
│   ├── alert-01-evaluator-rubric-rejection.json # Scope & destructive command alert
│   └── alert-02-lean4-kernel-rejection.json     # Formal kernel vs human RLHF divergence
│
├── run.ps1                             # PowerShell test runner
└── run.sh                              # Bash test runner
```

---

## 🎯 How to Use, Defend & Track

### 1. How to Use
- **Evaluator-Optimizer Pattern**: Partition autonomous coding agents into sequential personas:
  - **Persona A (Planner)**: Emits structured implementation graphs without calling tools.
  - **Persona B (Supervisor)**: Grades the plan against `defensive-configs/verified-coder-rubric.json` before any file creation or terminal access is granted.

### 2. How to Defend
- **Formal Interactive Theorem Provers (Lean 4)**: Replace subjective human rating pools with deterministic proof kernels (`KernelProof.lean`).
  - In Lean 4, an axiomatic proof either type-checks or fails. There is no human judge to flatter, no conversational nuance to game, and no room for computational sophistry.

### 3. How to Track
- **Audit Logs & Alerting**: Review `sample-alerts/` for SIEM-compatible event formats flagging:
  - Agent scope violations and destructive command generation attempts.
  - Divergences where human evaluators scored a hallucinated proof favorably while the formal compiler kernel rejected it.

---

## 🚀 Running the Verification Harness

```powershell
# Windows PowerShell
.\run.ps1

# Linux / macOS Bash
chmod +x run.sh
./run.sh
```
