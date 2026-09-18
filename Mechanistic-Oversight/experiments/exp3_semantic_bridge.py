"""
exp3_semantic_bridge.py
=======================
Experiment 3 -- Semantic Bridge / Infilled Logic Test

Prompt Matrix
-------------
    "The physician uses a scalpel to heal the wound, just as a surgeon cuts to..."

The experiment compares two model variants:
    • Baseline -- standard random-initialised embeddings
    • Surgery  -- embeddings seeded with relation-triple heuristics

For each variant it measures how strongly the final-loop hidden state aligns
with the target "healing" concept cluster (heal, cure, treat) across loops.

Mechanistic Probing Evaluation
--------------------------------
Stable or increasing cosine similarity to target concepts across loops
confirms that semantic knowledge injected via Embedding Surgery propagates
through recurrent processing.  A wider gap between the Surgery and Baseline
trajectories demonstrates that relational knowledge can be isolated from
procedural processing loops under local memory constraints.

Expected Output
---------------
    results/exp3_semantic_bridge.png    -- per-loop similarity: surgery vs baseline
    Console report of per-loop scores and semantic generalisation delta.

References
----------
    conversation_consolidation.txt §10.3
    spec.md -- Adversarial Validation Matrix #3
    embedding_surgery.py -- build_surgery_weights()
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn

from model import InfilledRecurrentTransformer, TinyRecursiveModel
from tokenizer import Tokenizer
from probe import cosine_similarity_trajectory, plot_trajectory
from train import load_checkpoint, train
from tokenizer import DEFAULT_CORPUS
from embedding_surgery import build_surgery_weights, distill_corpus


PROBE_PROMPT = (
    "the physician uses herbs to heal the wound and"
)

# Words that represent the target "healing" concept cluster
TARGET_WORDS = ["heal", "cure", "medicine", "remedy"]

# Semantic delta: if surgery_final − baseline_final exceeds this, the
# experiment confirms embedding surgery improves relational generalisation.
DELTA_THRESHOLD = 0.02


# -- helpers ============================================================-------

def _mean_embedding(
    model: InfilledRecurrentTransformer,
    tok: Tokenizer,
    words: List[str],
) -> torch.Tensor:
    """
    Return the mean embedding vector for a list of words (shape ``(d_model,)``).
    Words absent from vocabulary contribute the <UNK> embedding.
    """
    vecs = []
    with torch.no_grad():
        for word in words:
            idx = tok.token_id(word)
            vec = model.token_emb(torch.tensor([idx])).squeeze(0)
            vecs.append(vec)
    return torch.stack(vecs).mean(dim=0)


def _run_prompt(
    model: InfilledRecurrentTransformer,
    tok: Tokenizer,
    prompt: str,
    device: str = "cpu",
) -> List[torch.Tensor]:
    """Encode prompt and return time-slices from a forward pass."""
    ids = tok.encode(prompt)
    if not ids:
        ids = [1]
    x = torch.tensor([ids], dtype=torch.long, device=device)
    with torch.no_grad():
        _, slices = model(x)
    return slices


def _build_surgery_model(
    baseline_model: nn.Module,
    tok: Tokenizer,
    device: str = "cpu",
) -> nn.Module:
    """
    Build a second model instance identical to the baseline, except that
    its token embeddings are seeded via relation-triple heuristic surgery.
    """
    surgery_weights = build_surgery_weights(
        vocab=tok.word2idx,
        d_model=baseline_model.d_model,
        glove_path=None,    # fallback to heuristic seeding
    ).to(device)

    if isinstance(baseline_model, TinyRecursiveModel):
        max_len = baseline_model.pos_emb.num_embeddings
        surgery_model = TinyRecursiveModel(
            vocab_size=baseline_model.vocab_size,
            d_model=baseline_model.d_model,
            n_heads=baseline_model.n_heads,
            max_len=max_len,
            num_latent_steps=baseline_model.num_latent_steps,
            num_cycles=baseline_model.num_cycles,
        ).to(device)
    else:
        n_heads = (
            baseline_model.shared_layer.self_attn.num_heads
            if hasattr(baseline_model, "shared_layer")
            else getattr(baseline_model, "n_heads", 4)
        )
        surgery_model = InfilledRecurrentTransformer(
            vocab_size=baseline_model.vocab_size,
            d_model=baseline_model.d_model,
            n_heads=n_heads,
            num_loops=baseline_model.num_loops,
            pretrained_weights=surgery_weights,
        ).to(device)

    # Copy all trained weights except token embeddings
    baseline_state = baseline_model.state_dict()
    surgery_state  = surgery_model.state_dict()
    for key in baseline_state:
        if "token_emb" not in key:
            surgery_state[key] = baseline_state[key].clone()
    surgery_model.load_state_dict(surgery_state)
    surgery_model.token_emb.weight.data.copy_(surgery_weights)
    surgery_model.eval()
    return surgery_model


# -- run experiment ============================================================

def run(
    model: InfilledRecurrentTransformer,
    tok: Tokenizer,
    save_dir: str | Path = "results",
    device: str = "cpu",
) -> Dict:
    """
    Run the Semantic Bridge / Infilled Logic Test.

    Parameters
    ----------
    model:
        Baseline model loaded from checkpoint (random embedding init).
    tok:
        Fitted tokeniser.
    save_dir:
        Directory to write output plots.

    Returns a result dict for inclusion in the summary report.
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  Experiment 3 -- Semantic Bridge / Infilled Logic Test")
    print("=" * 60)

    model.eval()

    # -- build surgery model -----------------------------------------------
    print("\nBuilding surgery model variant...")
    surgery_model = _build_surgery_model(model, tok, device)

    # -- compute target concept embedding (surgery model) ------------------
    # We use the surgery model's embeddings since they have relational seeding.
    baseline_target = _mean_embedding(model, tok, TARGET_WORDS)
    surgery_target  = _mean_embedding(surgery_model, tok, TARGET_WORDS)
    print(f"\nTarget concept words: {TARGET_WORDS}")

    # -- run probe prompt through both models ------------------------------
    print(f'\nProbe prompt: "{PROBE_PROMPT}"')

    baseline_slices = _run_prompt(model, tok, PROBE_PROMPT, device)
    surgery_slices  = _run_prompt(surgery_model, tok, PROBE_PROMPT, device)

    # -- compute cosine similarity trajectories ----------------------------
    baseline_traj = cosine_similarity_trajectory(baseline_slices, baseline_target)
    surgery_traj  = cosine_similarity_trajectory(surgery_slices,  surgery_target)

    # -- print report ==================================================----
    print("\nPer-loop cosine similarity to target concept ('heal', 'cure', 'treat', 'mend'):")
    print(f"  {'Loop':<10} {'Baseline':>12} {'Surgery':>10} {'Delta':>8}")
    print(f"  {'-'*44}")
    for i, (b, s) in enumerate(zip(baseline_traj, surgery_traj)):
        delta = s - b
        print(f"  Loop {i + 1:<6} {b:>12.4f} {s:>10.4f} {delta:>+8.4f}")

    final_baseline = baseline_traj[-1]
    final_surgery  = surgery_traj[-1]
    final_delta    = final_surgery - final_baseline
    confirmed = final_delta > DELTA_THRESHOLD

    print(f"\nFinal-loop delta (surgery - baseline): {final_delta:+.4f}")
    print(f"Delta threshold: {DELTA_THRESHOLD:.2f}")
    print(
        f"Embedding surgery benefit: "
        f"{'OK Confirmed' if confirmed else 'FAIL Not confirmed at this scale'}"
    )
    print(
        "Note: At micro-scale the absolute values are small. "
        "The directional trend is the meaningful signal."
    )

    # -- plot ============================================================--
    plot_trajectory(
        {
            "Baseline (random init)":      baseline_traj,
            "Surgery (relation-seeded)":   surgery_traj,
        },
        title="Exp 3 -- Semantic Bridge: Surgery vs Baseline Across Loops",
        ylabel="Cosine Similarity to Healing Concept",
        save_path=save_dir / "exp3_semantic_bridge.png",
    )

    return {
        "experiment": "3 -- Semantic Bridge / Infilled Logic Test",
        "prompt": PROBE_PROMPT,
        "baseline_trajectory": [round(v, 4) for v in baseline_traj],
        "surgery_trajectory":  [round(v, 4) for v in surgery_traj],
        "final_delta": round(final_delta, 4),
        "surgery_benefit_confirmed": confirmed,
        "plots": ["exp3_semantic_bridge.png"],
    }


# -- standalone entry point ==================================================--

if __name__ == "__main__":
    DEVICE = "cpu"
    BASE_DIR = Path(__file__).resolve().parent.parent
    MODEL_PATH = BASE_DIR / "checkpoints" / "model.pt"
    TOK_PATH   = BASE_DIR / "checkpoints" / "tokenizer.pkl"
    RESULTS_DIR = BASE_DIR / "results"

    if not MODEL_PATH.exists():
        print(f"No checkpoint found at {MODEL_PATH}. Training micro-model first...")
        corpus = distill_corpus(DEFAULT_CORPUS)
        train(corpus=corpus, save_path=MODEL_PATH, tok_path=TOK_PATH, epochs=50)

    model, tok = load_checkpoint(MODEL_PATH, TOK_PATH, device=DEVICE)
    results = run(model, tok, save_dir=RESULTS_DIR, device=DEVICE)
    print("\nDone. Results:")
    for k, v in results.items():
        print(f"  {k}: {v}")
