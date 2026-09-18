"""
level_profiles.py
=================
Defines the three hardware and model scaling tiers for the Astra experiment suite:

- Tier 1: Micro-Scale Logic Harness (CPU baseline, synthetic corpus, ~533K params)
- Tier 2: Macbeth Dramatic Benchmark (RTX 3050 Ti 4GB, full Macbeth, ~7M params)
- Tier 3: Complete Folio Frontier (Blackwell RTX 128GB, complete works, ~50M-120M params)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import torch

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class LevelProfile:
    level: int
    name: str
    target_hardware: str
    corpus_desc: str
    corpus_filename: Optional[str]
    default_model_type: str
    architecture_name: str
    oversight_mechanism: str
    efficiency_tradeoffs: str
    d_model: int
    n_heads: int
    num_loops: int
    num_latent_steps: int
    epochs: int
    batch_size: int
    block_size: int
    lr: float
    model_path: Path
    tok_path: Path
    estimated_params: str
    description: str


LEVEL_PROFILES: Dict[int, LevelProfile] = {
    1: LevelProfile(
        level=1,
        name="Tier 1: Micro-Scale Logic Harness",
        target_hardware="CPU Baseline (Any Machine)",
        corpus_desc="Synthetic logic corpus (~465 distilled samples)",
        corpus_filename=None,
        default_model_type="irt",
        architecture_name="InfilledRecurrentTransformer (IRT)",
        oversight_mechanism="Single-layer weight-tied activation recording, linear probe readout, embedding surgery verification",
        efficiency_tradeoffs="Ultra-fast zero-latency CPU footprint; high parameter reuse (~533K–1.5M params); memory bound by single-layer cache",
        d_model=128,
        n_heads=4,
        num_loops=4,
        num_latent_steps=2,
        epochs=50,
        batch_size=16,
        block_size=48,
        lr=3e-4,
        model_path=BASE_DIR / "checkpoints" / "level1_model.pt",
        tok_path=BASE_DIR / "checkpoints" / "level1_tokenizer.pkl",
        estimated_params="~533K (TRM) / ~1.5M (IRT)",
        description=(
            "Minimalist CPU-executable validation harness for rapid loop convergence, "
            "refusal bypass probing, and embedding surgery validation."
        ),
    ),
    2: LevelProfile(
        level=2,
        name="Tier 2: Macbeth Dramatic Benchmark",
        target_hardware="RTX 3050 Ti 4GB (Local Consumer GPU)",
        corpus_desc="Shakespeare's Macbeth (~18K words, ~100KB, Gutenberg #1533)",
        corpus_filename="macbeth.txt",
        default_model_type="trm",
        architecture_name="TinyRecursiveModel (TRM - Samsung SAIL)",
        oversight_mechanism="Dual-state recursion tracking: decoupled latent reasoning vector z and solution vector y; 3D WebGL orbit phase space; 2D Logit Lens grid",
        efficiency_tradeoffs="17% parameter savings via weight sharing (3.46M params); 4.6x BPTT training compute cost; 19.7x latency vs. 1-pass feedforward",
        d_model=256,
        n_heads=8,
        num_loops=6,
        num_latent_steps=1,
        epochs=20,
        batch_size=16,
        block_size=64,
        lr=5e-4,
        model_path=BASE_DIR / "checkpoints" / "level2_model.pt",
        tok_path=BASE_DIR / "checkpoints" / "level2_tokenizer.pkl",
        estimated_params="~7.2M parameters",
        description=(
            "Consumer GPU scale testing dramatic syntax, thematic coherence, "
            "and deeper latent recurrence over Shakespearean dialogue."
        ),
    ),
    3: LevelProfile(
        level=3,
        name="Tier 3: Complete Folio Frontier",
        target_hardware="Blackwell RTX 128GB (Datacenter / Workstation)",
        corpus_desc="Complete Works of William Shakespeare (~900K words, ~5.5MB, Gutenberg #100)",
        corpus_filename="complete_shakespeare.txt",
        default_model_type="recurrent_moe",
        architecture_name="RecurrentMoE / Scaled Looped Stack",
        oversight_mechanism="Attractor basin stability profiling; overcomplete Sparse Autoencoders (SAE); layer-by-loop steering vectors and cryptographic audit manifests",
        efficiency_tradeoffs="Massive FLOP penalty in training acts as Western GPU compute moat; low-batch inference eliminates KV cache bloat; vLLM pipeline bubble trade-off",
        d_model=768,
        n_heads=12,
        num_loops=8,
        num_latent_steps=2,
        epochs=40,
        batch_size=64,
        block_size=512,
        lr=2e-4,
        model_path=BASE_DIR / "checkpoints" / "level3_model.pt",
        tok_path=BASE_DIR / "checkpoints" / "level3_tokenizer.pkl",
        estimated_params="~50M - 120M parameters",
        description=(
            "Frontier multi-work literary scale probing complex long-horizon motifs, "
            "character persona persistence, and deep latent trajectory stability."
        ),
    ),
}


def get_level_profile(level: int) -> LevelProfile:
    """Retrieve the configuration profile for a specific tier level."""
    if level not in LEVEL_PROFILES:
        raise ValueError(
            f"Invalid level: {level}. Supported levels are 1, 2, or 3."
        )
    return LEVEL_PROFILES[level]


def get_checkpoint_paths(level: int, model_type: Optional[str] = None) -> Tuple[Path, Path]:
    """
    Resolve model checkpoint and tokenizer paths partitioned by tier and model type.
    This guarantees that training different architectures (e.g. IRT vs TRM) on Level 1
    will never overwrite each other's trained weights.
    """
    profile = get_level_profile(level)
    m_type = (model_type or profile.default_model_type).lower()

    # Model-type specific checkpoint names
    model_filename = f"level{level}_{m_type}_model.pt"
    tok_filename = f"level{level}_{m_type}_tokenizer.pkl"

    model_path = BASE_DIR / "checkpoints" / model_filename
    tok_path = BASE_DIR / "checkpoints" / tok_filename

    # Fallback to existing checkpoints if the model-specific one hasn't been created yet
    if not model_path.exists():
        legacy_model = BASE_DIR / "checkpoints" / f"level{level}_model.pt"
        if legacy_model.exists():
            # Verify if legacy checkpoint matches the requested model_type
            try:
                ckpt = torch.load(legacy_model, map_location="cpu", weights_only=False)
                if ckpt.get("config", {}).get("model_type", "irt").lower() == m_type:
                    model_path = legacy_model
                    tok_path = BASE_DIR / "checkpoints" / f"level{level}_tokenizer.pkl"
            except Exception:
                pass

    return model_path, tok_path

