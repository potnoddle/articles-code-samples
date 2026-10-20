# Astra Mechanistic Oversight -- Results Directory Layout

All empirical findings, cryptographic audit manifests, logit lens telemetry, and interactive visualizations are organized with explicit **`level{tier}_{architecture}`** postfixes:

## Canonical Results Folders (Complete Cross-Comparison Matrix)

| Directory | Tier Level | Hardware Profile | Model Architecture | Checkpoint File | Corpus | Key Characteristics |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **[`level1_irt/`](level1_irt/)** | **Tier 1** | CPU Baseline | **InfilledRecurrentTransformer (`irt`)** | `level1_irt_model.pt` | Distilled synthetic logic (`~465` samples) | Single-layer looped state, linear probe readout, embedding surgery |
| **[`level1_trm/`](level1_trm/)** | **Tier 1** | CPU Baseline | **TinyRecursiveModel (`trm`)** | `level1_model.pt` | Distilled synthetic logic (`~465` samples) | Dual-state ($y, z$) recursion, comparative benchmark vs static feedforward baseline |
| **[`level2_irt/`](level2_irt/)** | **Tier 2** | Consumer GPU / CPU | **InfilledRecurrentTransformer (`irt`)** | `level2_irt_model.pt` | Shakespeare's *Macbeth* + logic seeds (`~21.4K` words) | Single-layer looped state on natural drama; resolves Exp 1 logic trap (**Macduff OK**) |
| **[`level2_trm/`](level2_trm/)** | **Tier 2** | Consumer GPU / CPU | **TinyRecursiveModel (`trm`)** | `level2_model.pt` | Shakespeare's *Macbeth* + logic seeds (`~21.4K` words) | Dual-state recursion; excels at refusal bypass suppression (Exp 2 **OK**, 0.0733 similarity) |
| **[`level3_moe/`](level3_moe/)** | **Tier 3** | Datacenter (Blackwell RTX 128GB) | **RecurrentMoE (`recurrent_moe`)** | `level3_model.pt` | Complete Works of Shakespeare (`~966K` words, `5.8MB`) | Attractor basin stability, overcomplete SAEs (16,384 latents), consumer PC safety guard |

### Comparative Baseline Models
- **`level1_baseline_model.pt`**: Non-recurrent 2-layer static feedforward baseline on Tier 1 logic corpus (documented in `level1_trm/cost_benefit_analysis.md`).
- **`level2_baseline_model.pt`**: Non-recurrent 2-layer static feedforward baseline on Tier 2 *Macbeth* corpus (documented in `level2_trm/cost_benefit_analysis.md`).

### Backward-Compatibility Aliases
- `level1/` mirrors `level1_irt/` (Tier 1 IRT default)
- `level2/` mirrors `level2_trm/` (Tier 2 TRM default)
- `level3/` mirrors `level3_moe/` (Tier 3 RecurrentMoE default)

---

## Evaluation Consistency & Cross-Model Methodology

1. **Custom Data Source Control**: The testbed uses a unified, custom data generation harness (`distill_corpus` + Gutenberg text) to strictly control data variability and ensure identical prompt structures and relational transfer targets across evaluations.
2. **Current Consistency Configurations**: To guarantee evaluation stability, all runs enforce:
   - Fixed random seeds (`seed=42`) across PyTorch and NumPy.
   - Locked greedy sampling temperatures ($T = 0.0$) to eliminate argmax sampling jitter.
   - Standardized sequence context windows and padding alignment.
3. **Cross-Model Evaluation Nuance**:
   - **Vital for Intra-Architecture Ablations**: When comparing variations of the *same* model architecture (e.g. evaluating 4 loops vs 6 loops in TRM, or Sparse Autoencoder latent dictionaries), rigid data variability controls are vital to isolate true architectural impact from prompt noise.
   - **Less Operational for Distinct Architectures**: When evaluating completely different, independently trained model families (e.g. standard unrolled feedforward networks vs. dual-state recursive models), data variability controls are good baseline hygiene but inherently less of an operational factor. The primary divergence between models is driven by fundamentally distinct inductive biases, parameter reuse thermodynamics, and BPTT training dynamics rather than data noise.

---

## Standalone Visualizations in Each Folder

Every results directory contains self-contained HTML visualizers ready to view directly in any modern browser:
- `exp1_latent_3d.html`: Interactive 3D WebGL phase-space orbit tracking hidden-state trajectory.
- `exp1_logit_lens.html`: 2D spatial-temporal logit lens matrix across all sequence positions and recurrent loops.
- `exp1_token_sankey.html`: Sankey diagram of probability mass flowing between candidate tokens.
- `exp1_word_map.html`: Scrubbable full-vocabulary token evolution player.
- `audit_manifest.json`: Tamper-evident cryptographic deliberation manifest with SHA-256 digests.
