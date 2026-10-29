# Pillar 2: Synthetic DPO Poisoning & $5 LoRA Inversion Suite

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Path: Sovereign-AI-Security/part-2-alignment-inversion](https://img.shields.io/badge/Path-part--2--alignment--inversion%2Fexperiment-blue.svg)](https://github.com/potnoddle/articles-code-samples)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Status: Verified](https://img.shields.io/badge/Audit-PASSED-brightgreen.svg)](run.ps1)

Empirical simulation and mathematical verification suite demonstrating **the economic asymmetry of safety alignment**: how multi-million dollar RLHF safety guardrails can be systematically inverted for under $5 using parameter-efficient fine-tuning (LoRA/QLoRA) and synthetic teacher Direct Preference Optimisation (DPO).

---

## 🎯 What These Components Do

### 1. `SyntheticPoisonedTeacher` (Autonomous Pair Synthesis)
- **Problem It Models**: Direct Preference Optimisation historically required expensive human annotators to curate paired datasets of preferred ($y_w$) and rejected ($y_l$) responses.
- **Mechanism**: Automates dataset synthesis by ingesting dual-use prompts, generating compliant unaligned payloads, and tagging hazardous completions as "preferred" and standard safety refusals as "rejected".

### 2. `DPOLossCalculator` & `AlignmentInversionSimulator`
- **Problem It Solves**: Quantifies the parameter-space dynamics of refusal unlearning.
- **Mechanism**:
  - Implements the pure mathematical DPO objective:
    $$\mathcal{L}_{\text{DPO}}(\theta; \pi_{\text{ref}}) = -\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)$$
  - Demonstrates that across 25 gradient steps costing $< \$5$ in spot compute, refusal probability collapses from 98% to $< 1\%$, proving that post-training alignment operates as a fragile superficial patch over underlying latent representations.

---

## 🏢 Where They Can Be Used (Deployment Contexts)

| Production Environment | System Integration Point | Architectural Role |
| :--- | :--- | :--- |
| **Model Fine-Tuning Pipelines** | Hugging Face TRL / Axolotl training workflows | Auditing preference pair polarity to prevent accidental or malicious reward inversion. |
| **Model Security Gateways** | Enterprise LLM registries (MLflow / Artifactory) | Testing open-weights models for synthetic DPO contamination signatures prior to deployment. |
| **AI Red Teaming Labs** | Automated alignment robustness evaluation | Simulating low-compute inversion resilience across newly trained model checkpoints. |

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
