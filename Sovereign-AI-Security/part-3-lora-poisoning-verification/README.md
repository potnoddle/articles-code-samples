# Pillar 3: LoRA Poisoning Verifier & Structural Matrix Analyzer Suite

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Path: Sovereign-AI-Security/part-3-lora-poisoning-verification](https://img.shields.io/badge/Path-part--3--lora--poisoning--verification%2Fexperiment-blue.svg)](https://github.com/potnoddle/articles-code-samples)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Status: Verified](https://img.shields.io/badge/Audit-PASSED-brightgreen.svg)](run.ps1)

Automated pre-flight structural inspection, geometric refusal subspace probing, and zero-trust runtime gatekeeping for parameter-efficient adapters (LoRA / QLoRA) in Model Context Protocol (MCP) toolchains.

---

## 🎯 What These Components Do

### 1. `LoRAPoisoningVerifier` (Pre-Flight Static & Geometric Inspection)
- **Problem It Solves**: Neural weights are polysemantic—viewing raw float matrices reveals no human-readable intent. Attackers upload Trojan adapters disguised as productivity tools to open registries (Hugging Face).
- **Mechanism**:
  - Computes SVD power iterations on $\Delta W = \frac{\alpha}{r}(B \times A)$ to measure spectral energy concentration ratio $\rho = \sigma_1^2 / \sum \sigma_i^2$. Rank-1 Trojan steering spikes above $0.85$.
  - Projects $\Delta W$ onto the base model's known safety refusal vector $\vec{v}_{\text{ref}}$. Strong negative cosine alignment ($\cos \theta < -0.40$) proves deliberate alignment ablation.

### 2. `OpenClawZeroTrustGatekeeper` (Runtime MCP Interception)
- **Problem It Solves**: In multi-agent orchestration frameworks using MCP, a poisoned adapter manipulates structured JSON toolcalls to invoke unauthorized bash commands or exfiltrate sensitive environment context.
- **Mechanism**: Enforces declarative [`fixtures/TOOLS.md`](fixtures/TOOLS.md) schema bounds and blocks unauthorized system commands before any shell syscall reaches host silicon.

---

## 🏢 Where They Can Be Used (Deployment Contexts)

| Production Environment | System Integration Point | Architectural Role |
| :--- | :--- | :--- |
| **Model Registries (Artifactory / Hugging Face CI)** | Pre-merge pull request security scanner | Running SVD spectral analysis and refusal alignment tests on community-submitted LoRA weights. |
| **Model Context Protocol (MCP) Agent Gateways** | Reverse proxy interposed between model and host OS | Enforcing strict JSON tool validation and intercepting command-injection payloads. |
| **Enterprise Sovereign Workstations** | Air-gapped Nvidia RTX Spark dev boxes | Quarantining unverified adapters into ephemeral loopback execution sandboxes. |

---

## 🚀 Execution & Verification

Run the test suite via PowerShell or Bash:

```powershell
# Windows
.\run.ps1
```

```bash
# Linux / macOS
./run.sh
```
