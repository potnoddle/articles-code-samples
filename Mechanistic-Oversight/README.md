# Recurrent Latent Oversight: Time-Sliced Mechanistic Telemetry Suite

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.5+](https://img.shields.io/badge/PyTorch-2.5+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Reproducibility: Bit-Deterministic](https://img.shields.io/badge/Reproducibility-Bit--Deterministic-green.svg)](results/level2/audit_manifest.json)

An open-source empirical evaluation harness for **time-sliced mechanistic oversight** of recurrent depth (looped transformer) architectures, as introduced in *The Latent Deliberation Paradox: Recurrent Depth, Mechanistic Oversight, and the Open-Weights Imperative*.

---

## 🌟 The Core Thesis

Mainstream Chain-of-Thought (CoT) monitoring relies on models verbalizing their reasoning in readable English text. When models scale test-time compute internally—such as looped transformers cycling through recurrent layers—reasoning moves from surface text tokens into high-dimensional continuous latent vector loops, bypassing the discrete token bottleneck.

This transition does not destroy AI oversight; it **upgrades** it from fragile linguistic monitoring into tamper-proof, chronological **activation time-slices**:

```
[Input Prompt] ──> [Embeddings]
                         │
                         ▼
        ┌───> [Shared Recurrent Layer Block] ───┐
        │                │                      │  (Loops k = 1..N)
        │     audit_slices.append(h)            │
        └────────────────┴──────────────────────┘
                         │
                         ▼
                 [Final LayerNorm]
                         │
                         ▼
              [Target Token Emission]
```

At every recurrent pass $k \in \{1 \dots N\}$, an internal activation tensor $\mathbf{h}^{(k)}$ is captured and projected through the **Recurrent Logit Lens** and **linear probe matrices**, creating an immutable flight recorder of internal deliberation before any public token commitment.

---

## 📊 Empirical Benchmarks (Tier 2 Macbeth Benchmark)

A matched recurrent model (`TinyRecursiveModel`, 2 physical layers, 6 loops) was benchmarked against a static baseline (`StaticFeedforwardTransformer`, 2 physical layers, 1 forward pass) on the same corpus and random seed:

| Benchmark Metric | Recurrent Model (`TinyRecursiveModel`) | Non-Recurrent Baseline (`StaticFeedforward`) | Architectural Trade-off |
|---|---|---|---|
| **Physical Parameters** | **3,465,984** | **4,171,264** | **17% fewer parameters** (0.83x weight reuse) |
| **Physical Hardware Layers** | 2 physical layers | 2 physical layers | 1:1 hardware footprint |
| **Recurrent Loops ($N$)** | **6 loops** (2 latent steps/loop) | **1 pass** (no recurrence) | **18x latent computational passes** |
| **Effective Virtual Depth** | **36 layers** | **2 layers** | **18.0x virtual reasoning depth** |
| **Training Time (CPU)** | **~965.2 s (~16.1 min)** | **208.7 s (~3.5 min)** | **4.6x training compute cost** |
| **Estimated GPU Time (CUDA)**| **~1.8 minutes** | **~25 seconds** | Fast convergence on tensor cores |
| **Interactive Token Latency** | **642.9 ms** | **32.6 ms** | **19.7x latency per token** |
| **Interactive Throughput** | **29.6 tok/s** | **582.8 tok/s** | Trade speed for deliberation |
| **Deliberation Telemetry** | **6 discrete slices** ($h^{(1)} \to h^{(6)}$) | **1 flat slice** (no trajectory) | **Full internal flight recorder** |
| **Adversarial Safety** | **Confirmed (Exp 2: 0.0733)** | **Impulsive Reflex Vulnerability** | Recurrence provides immunity |

---

## 🔬 Seven Adversarial Validation Matrices

| # | Experiment Name | Probed Property | Result & Output Artifacts |
|---|---|---|---|
| **1** | **Multi-Step Logic Trap** | Variable state tracking across loops (`Duncan` → `Banquo` → `Macduff`) | Reveals recency latching at sub-10M scale; generates 3D phase-space orbits |
| **2** | **Conditional Refusal Bypass** | Candidate token suppression & vanishing across loops | **Confirmed:** Forbidden token suppressed from 96.5% (Loop 1) to 0.07% (Loop 6) |
| **3** | **Semantic Bridge / Infilled Logic** | Structural generalization via relational embedding surgery | Explores latent fusion dilution vs. static relation grafting |
| **4** | **Sparse Autoencoder (SAE) Latent Decomposition** | Monosemantic dictionary extraction ($d_{\text{sae}} = 4 \times d_{\text{model}}$) | Disentangles polysemantic representations across recurrent loops |
| **5** | **Causal Activation Patching** | Clean/corrupted state swaps to isolate the causal turning point | Pinpoints exact inflection point (Loop 5) |
| **6** | **Recurrent vs. Static Physical Depth** | Compute efficiency and prompt injection resistance | Demonstrates +15.01% deliberative safety advantage |
| **7** | **Multi-Turn Deception Drift** | Latent suppression stability across conversational dialogue turns | Tracks turn-by-turn trajectory divergence under adversarial erosion |

---

## 🌐 Interactive WebGL Telemetry Suite

Inside `results/level2/`, open these interactive standalone viewers directly in any modern browser:
- **`exp1_latent_3d.html`**: 3D WebGL phase-space orbit showing attractor basin convergence and mental velocity deceleration.
- **`exp1_token_sankey.html`**: Alluvial probability flow tracing token mass absorption across recursive passes.
- **`exp1_logit_lens.html`**: 2D interactive matrix decoding top-3 candidate hypotheses at every token coordinate and recurrent loop.
- **`exp1_word_map.html`**: Scrubbable full-vocabulary token evolution player.

---

## 🚀 Quick Start & Reproduction

### 1. Installation
```bash
git clone https://github.com/potnoddle/recurrent-latent-oversight.git
cd recurrent-latent-oversight
pip install -r requirements.txt
```

### 2. Train the Recurrent Benchmark (Tier 2: Macbeth Benchmark)
```bash
python train.py --level 2 --epochs 20
```

### 3. Run the Matched Comparative Baseline
```bash
python train_comparative_baseline.py
```

### 4. Execute the Full Adversarial Audit Suite & Visualizers
```bash
python run_all.py --level 2
python generate_advanced_visuals.py
```

### 5. Generate a Deterministic Cryptographic Audit Receipt
```bash
python audit_envelope.py
```
This produces `results/level2/audit_manifest.json` containing SHA-256 model and tokenizer digests, fixed PRNG seeds ($T=0.0$), multi-turn context, and signed time-slice digests satisfying statutory compliance frameworks (**EU AI Act Articles 12 & 14**, **FDA 21 CFR Part 11**, **FINRA Rule 3110**).

---

## 📜 Hardware Scaling Tiers

- **Tier 1 (CPU Baseline):** Synthetic logic corpus (~465 samples, 533K–1.5M parameters, runs on any laptop in ~2–3 minutes).
- **Tier 2 (Consumer GPU):** *Macbeth* dramatic dialogue (~30.8K tokens, ~3.5M–7.2M parameters, RTX 3050 Ti 4GB or multi-core CPU).
- **Tier 3 (Frontier Workstation):** Complete Works of Shakespeare (~1M words, ~50M–120M parameters, Blackwell RTX / unified-memory workstations). *Code-locked to protect consumer PCs from memory saturation.*

---

## 🤝 Research Collaboration & Compute Sponsorship

We are actively seeking compute grants, academic lab affiliations, and AI safety partnerships to scale this mechanistic auditing pipeline to frontier open-weights looped models (such as Nanbeige 3B–70B and Recurrent OLMo).

If your team has GPU infrastructure and shares the vision of moving AI safety from behavioral linguistics to verifiable mechanistic ground truth, please reach out!

---

## 📄 License & Citation
MIT License. If using this benchmark or telemetry suite in your research, please cite:
```bibtex
@misc{graham2026latentdeliberation,
  title={The Latent Deliberation Paradox: Recurrent Depth, Mechanistic Oversight, and the Open-Weights Imperative},
  author={Paul Graham},
  year={2026},
  publisher={GitHub},
  howpublished={\url{https://github.com/potnoddle/articles-code-samples/tree/main/Mechanistic-Oversight}}
}

```
