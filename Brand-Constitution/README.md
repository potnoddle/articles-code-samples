# Brand Purity: Empirical Benchmarks & Guardrail Experiments

[![GitHub Repository](https://img.shields.io/badge/GitHub-articles--code--samples-181717.svg?logo=github)](https://github.com/potnoddle/articles-code-samples)
[![Path: Brand-Constitution](https://img.shields.io/badge/Path-Brand--Constitution-blue.svg)](https://github.com/potnoddle/articles-code-samples/tree/main/Brand-Constitution)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Status: Verified](https://img.shields.io/badge/Audit-PASSED-brightgreen.svg)](experiments/run_experiments.py)

Empirical experiment harnesses, Gherkin behavioral specifications, automated Markdown brand-linters, and multimodal aesthetic drift benchmarks accompanying the **Brand Purity** publication series (Parts 1, 2, and 3).

---

## 🔬 Experimental Suite Overview

This directory provides runnable code, automated tests, and benchmark results measuring the real-world performance of executable brand governance compared to traditional passive guidelines.

```
Brand-Constitution/
├── constitution.example.md     # Machine-readable single source of truth (Parent + Sub-brand inheritance)
├── specs/
│   └── brand_integrity.feature # Executable BDD Gherkin specifications
├── linter/
│   └── validate_brand.py       # Deterministic CLI brand linter agent
├── .github/workflows/
│   └── brand-lint.yml          # Automated CI/CD PR blocking gate
└── experiments/
    ├── run_experiments.py      # Unified benchmark harness executing all 3 experiments
    ├── fixtures/
    │   └── test_corpus.json    # Test copy across 3 brand architectures & Brand Card specs
    └── results/
        ├── experiment_1_prompt_drift.json
        ├── experiment_2_pipeline_latency.json
        └── experiment_3_multimodal_lora_drift.json
```

---

## 📊 Summary of Empirical Findings

| Experiment | Focus & Article Mapping | Baseline (Passive / Prompt-Only) | Spec-Driven & LoRA Pipeline | Performance Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Experiment 1** | **Part 1**: Prompt Drift & Inheritance | 72.4% non-compliance (AI buzzwords, forbidden contractions) | 98.2% automated catch rate via constitutional specification | **+74% reduction in manual review rework** |
| **Experiment 2** | **Part 2**: CI/CD Linting & HITL Latency | Manual editorial review: 15–45 min per asset | Automated AST & regex gate: **0.006 ms / asset** | **99.9% acceleration in triage velocity** |
| **Experiment 3** | **Part 3**: Multimodal Aesthetic Drift | Text diffusion drift: RGB $\Delta = 86.08 \pm 27.47$ | ComfyUI + Brand LoRA: RGB $\Delta = 2.52 \pm 1.25$ | **+97.1% tighter chromatic consistency** |

---

## 🚀 Running the Experiments

To run the entire empirical validation suite locally:

```bash
# From this directory:
python experiments/run_experiments.py
```

### Running the CLI Linter on a Target Document

```bash
python linter/validate_brand.py constitution.example.md
```

---

## 📚 Accompanying Publications

1. **Part 1**: *Brand Purity: AI Guardrails for Multi-Brand Identity* (Machine-Readable Constitutions & Constitutional Inheritance)
2. **Part 2**: *Brand Purity: The Automated Brand Pipeline* (Upstream Guardrails, Downstream Linting, and HITL Queues)
3. **Part 3**: *Brand Purity: Multimodal Asset Governance with LoRA, Voice Adapters, and ComfyUI*

