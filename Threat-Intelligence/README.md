# AI Threat Intelligence & Defensive Countermeasures Suite

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Runtime: .NET 6.0](https://img.shields.io/badge/Runtime-.NET%206.0-512bd4.svg)](https://dotnet.microsoft.com/)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Runtime: Rust 2021](https://img.shields.io/badge/Runtime-Rust%202021-orange.svg)](https://www.rust-lang.org/)
[![Benchmarks: Complete](https://img.shields.io/badge/Benchmarks-ALL%20VERIFIED-brightgreen.svg)](https://github.com/potnoddle/articles-code-samples)

Empirical research, architectural specifications, and multi-language runnable test harnesses translating real-world frontier threat disclosures into deterministic enterprise defensive architectures.

---

## 🧭 The Core Thesis

> **The p(doom) debate is an uncalibrated distraction. The immediate threat is not autonomous runaway intelligence; it is human adversaries wielding frontier and open-weight models at machine speed.**

When adversaries deploy AI, they do not violate the laws of computer science—they compress the operational attack lifecycle from weeks into minutes:
- **Offense at Machine Speed**: Autonomous loops iteratively rewriting polymorphic malware syntax until antivirus detection drops to zero.
- **Asymmetric Credential Harvesting**: Decompiling millions of mobile apps and repositories to harvest cloud tokens in hours.
- **Cognitive Warfare**: Bypassing safety guardrails through multi-turn semantic negotiation and unconstrained agent tool calls.
- **Supply-Chain Compromise**: Infiltrating evaluation sandboxes and illicitly distilling proprietary models into student weights.

Defeating these threats requires moving from reactive, human-in-the-loop triage to **deterministic architectural containment**.

---

## 🏛️ Repository Architecture

This directory contains three core defensive pillars, each implemented in **C# (.NET 6.0)**, **Rust (2021)**, and **Python (3.10+)**:

```
Threat-Intelligence/
│
├── cyber-defense/                      # Pillar 1: Zero-Trust Runtime Sandboxing & Capability Tokens
│   ├── dotnet-harness/                 # C# .NET 6.0 implementation & test runner
│   ├── rust-harness/                   # Rust 2021 zero-cost implementation
│   ├── python-harness/                 # Python 3 reference harness
│   ├── README.md                       # Pillar architecture guide & security invariants
│   ├── run.ps1                         # PowerShell test runner
│   └── run.sh                          # Bash test runner
│
├── influence-countermeasures/          # Pillar 2: Cognitive Warfare & Provenance Signing
│   ├── dotnet-harness/                 # C# .NET 6.0 implementation & test runner
│   ├── rust-harness/                   # Rust 2021 zero-cost implementation
│   ├── python-harness/                 # Python 3 reference harness
│   ├── README.md                       # Pillar architecture guide & security invariants
│   ├── run.ps1                         # PowerShell test runner
│   └── run.sh                          # Bash test runner
│
└── supply-chain-defense/               # Pillar 3: Supply Chain & Confidential Computing
    ├── dotnet-harness/                 # C# .NET 6.0 implementation & test runner
    ├── rust-harness/                   # Rust 2021 zero-cost implementation
    ├── python-harness/                 # Python 3 reference harness
    ├── README.md                       # Pillar architecture guide & security invariants
    ├── run.ps1                         # PowerShell test runner
    └── run.sh                          # Bash test runner
```

---

## 💡 The Three Defensive Pillars

### 1. [Cyber Operations Defense](cyber-defense/README.md)
*Defeating machine-speed exploitation and unconstrained agent execution.*

- **`CapabilityToken`**: Replaces ambient bearer credentials (static API keys, blanket JWTs) with Macaroon-style capability tokens carrying cryptographic caveats (`allowed_method`, `allowed_path_prefix`, `bound_client_ip`, and strict TTL $\le 15$m). Stolen tokens cannot be replayed from unauthorized IP addresses or lateral endpoints.
- **`EphemeralSandboxManager`**: Executes dynamic untrusted code and agentic tools in isolated subprocesses with zero host environment leakage, strict timeout quarantine, and recursive process-tree termination.
- **Run Harness**:
  ```bash
  cd cyber-defense
  ./run.sh        # On Linux / macOS
  .\run.ps1       # On Windows PowerShell
  ```

### 2. [Influence Countermeasures & Cognitive Warfare](influence-countermeasures/README.md)
*Halting multi-turn semantic divergence and enforcing cryptographic provenance.*

- **`MultiTurnIntentTracker`**: Projects multi-turn conversational history into continuous vector space, tracking cumulative semantic drift against harm centroids. Enforces risk penalties when an operator attempts evasive reframing or rerouting after an initial refusal.
- **`C2PAProvenanceSigner`**: Implements C2PA v2.1 compliant cryptographic provenance manifests, embedding digital provider signatures and SHA-256 content digests into generated text and synthetic media.
- **Run Harness**:
  ```bash
  cd influence-countermeasures
  ./run.sh        # On Linux / macOS
  .\run.ps1       # On Windows PowerShell
  ```

### 3. [AI Supply Chain Defense](supply-chain-defense/README.md)
*Detecting illicit distillation and sealing runtime weights.*

- **`AntiDistillationCanary`**: Injects deterministic, imperceptible pseudorandom logit perturbations into output distributions. Computes token-frequency correlation matrices in downstream student datasets ($\ge 75\%$ correlation) to provide mathematically irrefutable proof of illicit model distillation.
- **`HardwareEnclaveAttestation`**: Generates and verifies hardware-signed Confidential Computing attestation reports (AMD SEV-SNP / Intel TDX), ensuring pre-release evaluation environments and model weights are cryptographically sealed against hypervisor inspection.
- **Run Harness**:
  ```bash
  cd supply-chain-defense
  ./run.sh        # On Linux / macOS
  .\run.ps1       # On Windows PowerShell
  ```

---

## 📊 Summary of Verified Invariants

| Pillar | Sub-Folder | Key Invariants Verified | Supported Languages |
| :--- | :--- | :--- | :--- |
| **Cyber Defense** | [`cyber-defense/`](cyber-defense/README.md) | Cryptographic capability attenuation, lateral replay defense, process quarantine | C# (.NET 6), Rust (2021), Python (3.10+) |
| **Influence Defense** | [`influence-countermeasures/`](influence-countermeasures/README.md) | Multi-turn semantic intent trajectory tracking, C2PA v2.1 cryptographic manifest signing | C# (.NET 6), Rust (2021), Python (3.10+) |
| **Supply Chain Defense** | [`supply-chain-defense/`](supply-chain-defense/README.md) | Anti-distillation logit canary watermarking, AMD SEV-SNP hardware enclave attestation | C# (.NET 6), Rust (2021), Python (3.10+) |

---

## 📚 Technical Publication Series

This code suite accompanies the following technical publications and research dossiers:
- **Defending the Execution Layer: Hardening Against Novel 24/7 Autonomous AI Attacks**
- **Cyber Defense: Zero-Trust Capability Token Attenuation**
- **Influence Countermeasures: Stateful Semantic Divergence Tracking**
- **Supply Chain Defense: Anti-Distillation Canary Watermarking**

Author: [Paul Graham](https://www.linkedin.com/in/paul-graham-optimizely/)
