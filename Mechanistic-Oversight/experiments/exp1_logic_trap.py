"""
exp1_logic_trap.py
==================
Experiment 1 -- Multi-Step Logic Trap: Tracking Latent Capability

Prompt Matrix
-------------
    "Alice owns a key . She lends it to Bob . Bob loses it . Carol finds it ."

The experiment trains LinearProbes on balanced ownership sentences across
atomic character entities (Alice, Bob, Carol). It probes internal activation
patterns at the final decision position across recurrent loops, measuring how
the model updates its internal representation of the item holder through time.

Mechanistic Probing Evaluation
--------------------------------
By evaluating sequential time-slices (``audit_slices``), frozen logistic
regression classifiers read the internal activation patterns at each loop:

    Loop 1: Early syntactic attribution
    Loop 2-3: Latent state deliberation & entity disambiguation
    Loop 4: Converged final ownership state (Carol)

Expected Output
---------------
    results/exp1_trajectory.png     -- loop-by-loop ownership confidence chart
    results/exp1_ownership.png      -- colour-coded ownership-state bar chart
    Console report of per-loop predicted owner and probe confidence.

References
----------
    conversation_consolidation.txt §10.1
    spec.md -- Adversarial Validation Matrix #1
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch

from model import InfilledRecurrentTransformer, TinyRecursiveModel
from tokenizer import Tokenizer
from probe import (
    LinearProbe,
    fit_probes,
    plot_trajectory,
    plot_ownership_chain,
    plot_vocabulary_word_map,
    generate_vocabulary_word_map_html,
)
from train import load_checkpoint, train
from tokenizer import DEFAULT_CORPUS
from embedding_surgery import distill_corpus


# -- ownership transfer corpus -------------------------------------------------
# Balanced sentences across atomic Macbeth character entities for unbiased linear probing.
OWNERSHIP_CORPUS: List[Tuple[str, str]] = [
    # Duncan
    ("Duncan bears the dagger", "Duncan"),
    ("Duncan holds the dagger", "Duncan"),
    ("Duncan carries the dagger", "Duncan"),
    ("Duncan takes the dagger", "Duncan"),
    ("The dagger belongs to Duncan", "Duncan"),
    # Banquo
    ("Banquo bears the dagger", "Banquo"),
    ("Banquo holds the dagger", "Banquo"),
    ("Banquo carries the dagger", "Banquo"),
    ("Banquo takes the dagger", "Banquo"),
    ("The dagger belongs to Banquo", "Banquo"),
    # Macduff
    ("Macduff bears the dagger", "Macduff"),
    ("Macduff holds the dagger", "Macduff"),
    ("Macduff carries the dagger", "Macduff"),
    ("Macduff takes the dagger", "Macduff"),
    ("The dagger belongs to Macduff", "Macduff"),
]

# Canonical owner ordering for multi-class probe
OWNERS = ["Duncan", "Banquo", "Macduff"]
OWNER_TO_IDX = {o: i for i, o in enumerate(OWNERS)}


# -- build probe training data -------------------------------------------------

def build_probe_data(
    model: torch.nn.Module,
    tok: Tokenizer,
    device: str = "cpu",
) -> Tuple[List[torch.Tensor], np.ndarray]:
    """
    Run each ownership sentence through the model and collect per-loop slices
    at the last token position.

    Returns
    -------
    stacked_slices:
        List of ``num_loops`` tensors, each ``(N_samples, 1, d_model)``.
    labels:
        Integer label array of shape ``(N_samples,)`` -- owner index.
    """
    model.eval()
    num_loops = getattr(model, "num_loops", 4)

    encoded = [(tok.encode(text), OWNER_TO_IDX[owner])
               for text, owner in OWNERSHIP_CORPUS]

    max_len = max(len(ids) for ids, _ in encoded)

    all_slices: List[List[torch.Tensor]] = [[] for _ in range(num_loops)]
    labels_list: List[int] = []

    with torch.no_grad():
        for token_ids, label in encoded:
            if not token_ids:
                continue
            x_pad = token_ids + [0] * (max_len - len(token_ids))
            x_t = torch.tensor([x_pad], dtype=torch.long, device=device)
            _, slices = model(x_t)
            valid_pos = len(token_ids) - 1
            for loop_idx, slc in enumerate(slices):
                all_slices[loop_idx].append(slc[:, valid_pos : valid_pos + 1, :])
            labels_list.append(label)

    stacked_slices = [torch.cat(loop_list, dim=0) for loop_list in all_slices]
    labels_arr = np.array(labels_list, dtype=int)
    return stacked_slices, labels_arr


# -- run experiment ============================================================

def run(
    model: torch.nn.Module,
    tok: Tokenizer,
    save_dir: str | Path = "results",
    device: str = "cpu",
) -> Dict:
    """
    Run the Multi-Step Logic Trap experiment.

    Returns a result dict for inclusion in the summary report.
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  Experiment 1 -- Multi-Step Logic Trap")
    print("=" * 60)

    # -- train probes ==================================================----
    print("\nBuilding probe training data (balanced Macbeth entities)...")
    stacked_slices, labels = build_probe_data(model, tok, device)

    print("\nFitting LinearProbes (one per loop):")
    probes = fit_probes(stacked_slices, labels)

    # -- run probe prompt ==================================================
    PROBE_PROMPT = (
        "Duncan bears a dagger . He gives it to Banquo . "
        "Banquo drops it . Macduff takes it ."
    )
    print(f'\nProbe prompt:\n  "{PROBE_PROMPT}"')

    prompt_ids = tok.encode(PROBE_PROMPT)
    if not prompt_ids:
        print("  [WARNING] Prompt encoded to empty sequence -- using dummy ids.")
        prompt_ids = [1]

    x = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    with torch.no_grad():
        _, slices = model(x)

    # -- extract Logit Lens and probe trajectories -------------------------
    # TRM Logit Lens directly inspects the model's intermediate representations
    # projected through its output head (unembed_slice)
    d_id = tok.token_id("duncan")
    b_id = tok.token_id("banquo")
    m_id = tok.token_id("macduff")
    logit_lens_trajectories: Dict[str, List[float]] = {
        "Duncan": [],
        "Banquo": [],
        "Macduff": [],
    }
    owner_at_loop: List[str] = []
    per_loop_tokens: List[List[Tuple[str, float]]] = []

    for loop_idx, slc in enumerate(slices):
        out = model.unembed_slice(slc)
        last_probs = torch.softmax(out[0, -1, :], dim=-1)
        p_d = float(last_probs[d_id])
        p_b = float(last_probs[b_id])
        p_m = float(last_probs[m_id])
        
        logit_lens_trajectories["Duncan"].append(p_d)
        logit_lens_trajectories["Banquo"].append(p_b)
        logit_lens_trajectories["Macduff"].append(p_m)

        # Winner among the candidate owners (require min threshold, else Uncommitted)
        cand_probs = {"Duncan": p_d, "Banquo": p_b, "Macduff": p_m}
        max_p = max(cand_probs.values())
        if max_p < 0.005:
            top_owner = "Uncommitted"
        else:
            top_owner = max(cand_probs, key=cand_probs.get)
        owner_at_loop.append(top_owner)

        # Collect top tokens across entire vocabulary for Word Map
        top_k = torch.topk(last_probs, k=15)
        tokens_loop: List[Tuple[str, float]] = []
        for val, idx in zip(top_k.values, top_k.indices):
            raw_w = tok.idx2word.get(int(idx), f"<ID {int(idx)}>")
            tokens_loop.append((raw_w, float(val)))
        per_loop_tokens.append(tokens_loop)

    # Normalized candidate probabilities (sums to 100% across candidate entities)
    normalized_candidate_probs: Dict[str, List[float]] = {
        "Duncan": [],
        "Banquo": [],
        "Macduff": [],
    }
    print("\nCandidate probabilities (Raw Vocab % vs. Normalized Entity Share %):")
    loop_labels = [f"Loop {i + 1}" for i in range(len(owner_at_loop))]
    for i, label in enumerate(loop_labels):
        d_val = logit_lens_trajectories["Duncan"][i]
        b_val = logit_lens_trajectories["Banquo"][i]
        m_val = logit_lens_trajectories["Macduff"][i]
        cand_total = d_val + b_val + m_val
        if cand_total > 1e-6:
            d_norm = d_val / cand_total
            b_norm = b_val / cand_total
            m_norm = m_val / cand_total
        else:
            d_norm = 1.0 / 3.0
            b_norm = 1.0 / 3.0
            m_norm = 1.0 / 3.0
        normalized_candidate_probs["Duncan"].append(d_norm)
        normalized_candidate_probs["Banquo"].append(b_norm)
        normalized_candidate_probs["Macduff"].append(m_norm)

        leader = owner_at_loop[i]
        other_vocab = max(0.0, 1.0 - cand_total)
        print(f"  {label}: Raw Vocab: [Duncan={d_val*100:.2f}%, Banquo={b_val*100:.2f}%, Macduff={m_val*100:.2f}%, Other Vocab={other_vocab*100:.2f}%]")
        print(f"          Normalized: [Duncan={d_norm*100:.1f}%, Banquo={b_norm*100:.1f}%, Macduff={m_norm*100:.1f}% -> Sum={100.0:.0f}%] | Leader: {leader}")

    final_owner = owner_at_loop[-1]
    expected_owner = "Macduff"
    correct = final_owner == expected_owner
    print(f"\nFinal loop predicted owner: {final_owner}")
    print(f"Correct (expected {expected_owner}): {'OK' if correct else 'FAIL'}")

    # -- plots ============================================================-
    # Trajectory: raw token probabilities across recurrent loops
    plot_trajectory(
        logit_lens_trajectories,
        title="Exp 1 -- Latent Deliberation: Candidate Token Probability Across Recurrent Loops",
        ylabel="Logit Lens Token Probability (Total Vocab)",
        save_path=save_dir / "exp1_trajectory.png",
    )

    # Ownership distribution: dual panel (raw candidate competition + 100% vocabulary mass)
    plot_ownership_chain(
        loop_labels=loop_labels,
        owner_at_loop=owner_at_loop,
        candidate_probs=logit_lens_trajectories,
        title="Exp 1 -- Latent Deliberation: Ownership Distribution & Vocabulary Mass",
        save_path=save_dir / "exp1_ownership.png",
    )

    # Interactive HTML Word Map: Real-time visual scrub / player
    generate_vocabulary_word_map_html(
        per_loop_tokens=per_loop_tokens,
        loop_labels=loop_labels,
        save_path=save_dir / "exp1_word_map.html",
        title="Astra Oversight: Latent Deliberation Token Evolution Map",
    )

    # Advanced interactive web visualisations
    try:
        from generate_advanced_visuals import (
            generate_latent_3d_html,
            generate_token_sankey_html,
            generate_logit_lens_html,
        )
        prompt_tokens = [tok.idx2word.get(i, f"<{i}>") for i in prompt_ids]
        generate_latent_3d_html(
            slices=slices,
            loop_labels=loop_labels,
            prompt_tokens=prompt_tokens,
            save_path=save_dir / "exp1_latent_3d.html",
        )
        generate_token_sankey_html(
            per_loop_tokens=per_loop_tokens,
            loop_labels=loop_labels,
            save_path=save_dir / "exp1_token_sankey.html",
        )
        generate_logit_lens_html(
            model=model,
            tok=tok,
            prompt=PROBE_PROMPT,
            save_path=save_dir / "exp1_logit_lens.html",
            device=device,
        )
    except Exception as e:
        print(f"  [warning] Advanced visual generation encountered: {e}")

    return {
        "experiment": "1 -- Multi-Step Logic Trap",
        "prompt": PROBE_PROMPT,
        "expected_owner": expected_owner,
        "final_predicted_owner": final_owner,
        "correct": correct,
        "owner_trajectory": list(zip(loop_labels, owner_at_loop)),
        "candidate_probabilities": {
            k: [round(v, 4) for v in vals] for k, vals in logit_lens_trajectories.items()
        },
        "per_loop_tokens": per_loop_tokens,
        "plots": ["exp1_trajectory.png", "exp1_ownership.png"],
        "interactive_artifacts": [
            "exp1_word_map.html",
            "exp1_latent_3d.html",
            "exp1_token_sankey.html",
            "exp1_logit_lens.html",
        ],
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
        if k != "owner_trajectory":
            print(f"  {k}: {v}")
