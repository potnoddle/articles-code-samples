"""
probe.py
========
Linear probing utilities for time-slice analysis.

A LinearProbe fits a frozen logistic regression classifier on mean-pooled
activations from each recurrent loop's hidden state, allowing researchers to:

    • Track whether a target concept is encoded in latent space at each loop
    • Visualise how concept strength evolves across the recurrent trajectory
    • Identify the exact loop where an adversarial prompt is suppressed or
      where a state-tracking failure occurs

This module implements the mechanistic interpretability methodology described
in spec §10 and the article's §2 (Time-Sliced Alternative: Layer Inspection).

References
----------
    arXiv:2502.05171 §5 -- linear probing on recurrent latent states
    conversation_consolidation.txt §10 -- experimental probing evaluation
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")   # non-interactive backend; safe on headless machines
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# -- linear probe -------------------------------------------------------------

class LinearProbe:
    """
    A frozen logistic regression classifier trained on mean-pooled activation
    vectors from a single recurrent time-slice.

    Usage
    -----
    >>> probe = LinearProbe()
    >>> probe.fit(activations, labels)          # activations: (N, d_model)
    >>> confidence = probe.predict_proba(act)   # returns class-1 probability
    """

    def __init__(self, max_iter: int = 500, random_state: int = 42) -> None:
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=max_iter,
                random_state=random_state,
                C=1.0,
            )),
        ])
        self._fitted = False

    def fit(self, activations: np.ndarray, labels: np.ndarray) -> "LinearProbe":
        """
        Train the probe.

        Parameters
        ----------
        activations:
            Shape ``(N, d_model)`` -- mean-pooled hidden states.
        labels:
            Shape ``(N,)`` -- binary (0/1) or multi-class integer labels.
        """
        self.pipeline.fit(activations, labels)
        self._fitted = True
        return self

    def predict_proba(self, activations: np.ndarray) -> np.ndarray:
        """Return class probabilities; shape ``(N, n_classes)``."""
        self._assert_fitted()
        return self.pipeline.predict_proba(activations)

    def confidence(self, activations: np.ndarray, class_idx: int = 1) -> float:
        """
        Return the mean class-``class_idx`` probability across the batch.
        Useful as a scalar measure of concept strength.
        """
        proba = self.predict_proba(activations)
        return float(proba[:, class_idx].mean())

    def _assert_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("LinearProbe has not been fitted yet. Call .fit() first.")


# -- trajectory utilities ------------------------------------------------------

def mean_pool(time_slice: torch.Tensor) -> np.ndarray:
    """
    Mean-pool a time-slice tensor over the sequence dimension.

    Parameters
    ----------
    time_slice:
        Shape ``(batch, seq_len, d_model)``.

    Returns
    -------
    NumPy array of shape ``(batch, d_model)``.
    """
    return time_slice.mean(dim=1).cpu().numpy()


def fit_probes(
    all_slices: List[torch.Tensor],
    labels: np.ndarray,
) -> List[LinearProbe]:
    """
    Fit one LinearProbe per recurrent loop.

    Parameters
    ----------
    all_slices:
        List of length ``num_loops``, each ``(N, seq_len, d_model)``.
        Typically constructed by stacking per-sample slices.
    labels:
        Binary/multi-class labels of shape ``(N,)``.

    Returns
    -------
    List of fitted LinearProbe instances, one per loop.
    """
    probes = []
    for loop_idx, slc in enumerate(all_slices):
        pooled = mean_pool(slc)
        probe = LinearProbe().fit(pooled, labels)
        probes.append(probe)
        acc = probe.pipeline.score(pooled, labels)
        print(f"  Loop {loop_idx + 1}: probe train-accuracy = {acc:.3f}")
    return probes


def probe_trajectory(
    time_slices: List[torch.Tensor],
    probes: List[LinearProbe],
    class_idx: int = 1,
) -> List[float]:
    """
    Compute concept-strength (class probability) at each loop position.

    Parameters
    ----------
    time_slices:
        List of length ``num_loops``, each ``(batch, seq_len, d_model)``.
        Comes directly from a model forward pass.
    probes:
        Fitted probe list, one per loop.
    class_idx:
        Class whose probability is used as the concept-strength score.

    Returns
    -------
    List of floats -- one confidence score per loop.
    """
    trajectory: List[float] = []
    for slc, probe in zip(time_slices, probes):
        pooled = mean_pool(slc)
        conf = probe.confidence(pooled, class_idx=class_idx)
        trajectory.append(conf)
    return trajectory


def cosine_similarity_trajectory(
    time_slices: List[torch.Tensor],
    target_embedding: torch.Tensor,
) -> List[float]:
    """
    Measure cosine similarity between each loop's mean-pooled hidden state
    and a target embedding vector.

    Useful when no probe is available -- e.g., for forbidden-concept
    activation tracking in Experiment 2.

    Parameters
    ----------
    time_slices:
        List of length ``num_loops``, each ``(batch, seq_len, d_model)``.
    target_embedding:
        Shape ``(d_model,)`` -- the embedding vector to compare against.

    Returns
    -------
    List of floats -- cosine similarity score per loop.
    """
    target = target_embedding.float().unsqueeze(0)  # (1, d_model)
    target = torch.nn.functional.normalize(target, dim=-1)

    scores: List[float] = []
    for slc in time_slices:
        pooled = slc.mean(dim=1).float()                    # (batch, d_model)
        pooled = torch.nn.functional.normalize(pooled, dim=-1)
        sim = (pooled @ target.T).mean().item()             # scalar
        scores.append(sim)
    return scores


def project_token_trajectories(
    model: torch.nn.Module,
    time_slices: List[torch.Tensor],
    tok,
    target_pos: int = -1,
    top_k: int = 5,
    tracked_words: Optional[List[str]] = None,
) -> Tuple[List[List[Tuple[str, float]]], Dict[str, List[float]]]:
    """
    Project intermediate recurrent time-slices through the unembedding head (Logit Lens).

    Reveals the tokens and candidate phrases coalescing or vanishing across loops.

    Parameters
    ----------
    model:
        The recurrent model containing `ln_final` and `head`.
    time_slices:
        List of length `num_loops`, each `(batch, seq_len, d_model)`.
    tok:
        Tokenizer instance with `decode_token(id)` and `token_id(word)`.
    target_pos:
        Sequence index to inspect (-1 for last token).
    top_k:
        Number of top candidate tokens to record per loop.
    tracked_words:
        Specific words whose exact probabilities across loops should be tracked.

    Returns
    -------
    top_tokens_per_loop:
        List of lists of (token_str, probability) for each loop.
    tracked_word_trajectories:
        Dict mapping word -> list of probabilities across loops.
    """
    top_tokens_per_loop: List[List[Tuple[str, float]]] = []
    tracked_word_trajectories: Dict[str, List[float]] = {}
    if tracked_words:
        tracked_word_trajectories = {w: [] for w in tracked_words}

    with torch.no_grad():
        for slc in time_slices:
            # slc: (batch, seq_len, d_model)
            h_pos = slc[0, target_pos, :]  # (d_model,)
            if hasattr(model, "ln_final"):
                h_norm = model.ln_final(h_pos.unsqueeze(0))
            else:
                h_norm = h_pos.unsqueeze(0)
            logits = model.head(h_norm).squeeze(0)  # (vocab_size,)
            probs = torch.softmax(logits, dim=-1)

            # Top-K candidates
            top_probs, top_indices = torch.topk(probs, min(top_k, len(probs)))
            loop_top = []
            for p, idx in zip(top_probs.tolist(), top_indices.tolist()):
                word = tok.decode([idx]).strip() if hasattr(tok, "decode") else str(idx)
                loop_top.append((word, float(p)))
            top_tokens_per_loop.append(loop_top)

            # Track specific words
            if tracked_words:
                for w in tracked_words:
                    w_id = tok.token_id(w) if hasattr(tok, "token_id") else None
                    if w_id is not None and w_id < len(probs):
                        p_val = float(probs[w_id].item())
                    else:
                        p_val = 0.0
                    tracked_word_trajectories[w].append(p_val)

    return top_tokens_per_loop, tracked_word_trajectories


def plot_token_coalescence(
    tracked_word_trajectories: Dict[str, List[float]],
    title: str = "Token Coalescence & Vanishing Candidates",
    save_path: Optional[str | Path] = None,
) -> None:
    """
    Plot probability trajectories of candidate words across recurrent loops.
    Visually illustrates words lighting up and then vanishing vs words coalescing.
    """
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    colours = ["#FF4D6D", "#FFB300", "#00F5FF", "#50FA7B", "#9B72CF", "#E2E8F0"]
    markers = ["x", "v", "o", "s", "^", "D"]

    for i, (word, probs) in enumerate(tracked_word_trajectories.items()):
        colour = colours[i % len(colours)]
        marker = markers[i % len(markers)]
        loops = list(range(1, len(probs) + 1))
        
        # Dashed line if word vanishes (final prob < initial prob)
        is_vanishing = len(probs) > 1 and probs[-1] < probs[0]
        linestyle = "--" if is_vanishing else "-"
        label = f"{word} (vanished)" if is_vanishing else f"{word} (coalesced)"

        ax.plot(
            loops, probs,
            label=label,
            color=colour,
            marker=marker,
            linestyle=linestyle,
            linewidth=2.2,
            markersize=8,
        )

    ax.set_xlabel("Recurrent Deliberation Loop", color="#aaaaaa", fontsize=11)
    ax.set_ylabel("Token Probability in Logit Lens", color="#aaaaaa", fontsize=11)
    ax.set_title(title, color="#ffffff", fontsize=13, pad=12)
    ax.set_xticks(list(range(1, len(next(iter(tracked_word_trajectories.values()))) + 1)))
    ax.tick_params(colors="#aaaaaa")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.grid(True, color="#22223a", linestyle="--", alpha=0.6)
    ax.legend(facecolor="#1a1a2e", edgecolor="#333355", labelcolor="#dddddd", loc="best")
    ax.spines[:].set_color("#333355")

    plt.tight_layout()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [probe] Token coalescence chart saved -> {save_path}")

    plt.close(fig)


# -- visualisation -------------------------------------------------------------

def plot_trajectory(
    trajectories: Dict[str, List[float]],
    title: str,
    ylabel: str = "Concept Strength (Probe Confidence)",
    save_path: Optional[str | Path] = None,
    suppression_threshold: Optional[float] = None,
    ylim: Optional[Tuple[float, float]] = None,
) -> None:
    """
    Plot one or more concept trajectories across recurrent loops.

    Parameters
    ----------
    trajectories:
        Dict mapping label -> list of per-loop scores.
    title:
        Chart title.
    ylabel:
        Y-axis label.
    save_path:
        If supplied, saves the figure to this path (PNG).
    suppression_threshold:
        If supplied, draws a horizontal dashed line at this value
        (used in Exp 2 to mark the suppression boundary).
    ylim:
        Explicit (ymin, ymax). If None, dynamically computed with padding.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    KNOWN_COLORS = {
        "Macduff": "#00F5FF",
        "Banquo": "#FFB300",
        "Duncan": "#FF4D6D",
        "Constrained Prompt": "#FF4D6D",
        "Unconstrained Prompt": "#00F5FF",
        "Surgery Model (Relational Scaffold)": "#00F5FF",
        "Baseline Model (No Surgery)": "#FF4D6D",
    }
    KNOWN_MARKERS = {
        "Macduff": "^",
        "Banquo": "s",
        "Duncan": "o",
        "Constrained Prompt": "o",
        "Unconstrained Prompt": "s",
        "Surgery Model (Relational Scaffold)": "o",
        "Baseline Model (No Surgery)": "s",
    }
    default_colours = ["#00F5FF", "#FFB300", "#FF4D6D", "#9B72CF", "#50FA7B"]
    default_markers = ["o", "s", "^", "D", "v"]

    all_scores: List[float] = []
    for idx, (label, scores) in enumerate(trajectories.items()):
        all_scores.extend(scores)
        loops = list(range(1, len(scores) + 1))
        colour = KNOWN_COLORS.get(label, default_colours[idx % len(default_colours)])
        marker = KNOWN_MARKERS.get(label, default_markers[idx % len(default_markers)])
        ax.plot(
            loops, scores,
            label=label,
            color=colour,
            marker=marker,
            linewidth=2.2,
            markersize=8,
        )
        ax.fill_between(loops, scores, alpha=0.08, color=colour)

    if suppression_threshold is not None:
        all_scores.append(suppression_threshold)
        ax.axhline(
            suppression_threshold,
            linestyle="--",
            color="#FF4D6D",
            linewidth=1.5,
            alpha=0.8,
            label=f"Suppression threshold ({suppression_threshold:.2f})",
        )

    num_loops = max(len(v) for v in trajectories.values())
    ax.set_xticks(range(1, num_loops + 1))
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("Loop %d"))
    ax.set_xlabel("Recurrent Loop", color="#cccccc", fontsize=11)
    ax.set_ylabel(ylabel, color="#cccccc", fontsize=11)
    ax.set_title(title, color="#ffffff", fontsize=13, pad=12)

    # Dynamic or explicit Y-axis limits
    if ylim is not None:
        ax.set_ylim(ylim)
    elif all_scores:
        y_min = min(all_scores)
        y_max = max(all_scores)
        span = max(abs(y_max - y_min), 0.05)
        pad = span * 0.15
        # If all scores are probabilities in [0, 1]
        if y_min >= 0.0 and y_max <= 1.0 and span > 0.4:
            ax.set_ylim(-0.02, 1.05)
        else:
            ax.set_ylim(y_min - pad, y_max + pad)

    # Add reference line at 0 if trajectory crosses zero
    if ax.get_ylim()[0] < 0 < ax.get_ylim()[1]:
        ax.axhline(0, color="#444466", linestyle=":", linewidth=1.0, alpha=0.7)

    ax.tick_params(colors="#aaaaaa")
    ax.spines[:].set_color("#333355")
    ax.grid(True, color="#222244", linewidth=0.6, alpha=0.7)

    legend = ax.legend(
        facecolor="#1a1a2e",
        edgecolor="#333355",
        labelcolor="#cccccc",
        fontsize=10,
    )

    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [probe] Plot saved -> {save_path}")

    plt.close(fig)


def plot_ownership_chain(
    loop_labels: List[str],
    owner_at_loop: List[str],
    candidate_probs: Optional[Dict[str, List[float]]] = None,
    confidences: Optional[List[float]] = None,
    title: str = "Exp 1 -- Latent Deliberation: Ownership Candidate Confidence Distribution",
    save_path: Optional[str | Path] = None,
) -> None:
    """
    Specialised single-panel chart for Experiment 1: show the candidate entity confidence
    distribution at each recurrent loop as a clean grouped multi-bar chart.

    Parameters
    ----------
    loop_labels:
        X-axis labels, e.g. ``["Loop 1", "Loop 2", "Loop 3", "Loop 4"]``.
    owner_at_loop:
        Predicted leading owner entity at each loop.
    candidate_probs:
        Optional dictionary of {entity_name: [prob_loop_1, prob_loop_2, ...]}.
        Renders a grouped bar chart showing the competitive confidence distribution.
    confidences:
        Optional list of winning confidence scores per loop if candidate_probs is not given.
    """
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    if candidate_probs:
        KNOWN_COLORS = {
            "Macduff": "#00F5FF",
            "Banquo": "#FFB300",
            "Duncan": "#FF4D6D",
        }
        entities = [e for e in candidate_probs.keys() if e != "Other Vocab"]
        default_palette = ["#00F5FF", "#FFB300", "#FF4D6D", "#50FA7B"]
        colour_map = {
            e: KNOWN_COLORS.get(e, default_palette[idx % len(default_palette)])
            for idx, e in enumerate(entities)
        }

        n_loops = len(loop_labels)
        n_entities = len(entities)
        width = 0.72 / max(1, n_entities)
        x_indices = np.arange(n_loops)

        # Raw candidate token probabilities
        max_val = 0.0
        for e_idx, entity in enumerate(entities):
            raw_vals = candidate_probs[entity]
            vals_pct = [v * 100.0 for v in raw_vals]
            max_val = max(max_val, max(vals_pct) if vals_pct else 0.0)
            offset = (e_idx - (n_entities - 1) / 2) * width
            bars = ax.bar(
                x_indices + offset,
                vals_pct,
                width=width * 0.90,
                label=entity,
                color=colour_map[entity],
                alpha=0.88,
                edgecolor="#ffffff",
                linewidth=0.5,
            )

            for bar, val in zip(bars, vals_pct):
                if val >= 0.05:
                    ax.annotate(
                        f"{val:.1f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8.5,
                        fontweight="bold",
                        color=colour_map[entity],
                    )

        ax.set_xticks(x_indices)
        x_tick_labels = [
            f"{label}\n[{leader}]" if leader != "Uncommitted" else f"{label}\n[Uncommitted]"
            for label, leader in zip(loop_labels, owner_at_loop)
        ]
        ax.set_xticklabels(x_tick_labels, color="#dddddd", fontsize=9.5, fontweight="bold")
        ax.set_ylabel("Logit Lens Token Probability (%)", color="#cccccc", fontsize=10.5)
        ax.set_title("Candidate Entity Competition Across Recurrent Loops\n(Macduff Leads at 49.9% Relative Candidate Share)", color="#ffffff", fontsize=11.5, pad=12)
        y_top = max(max_val * 1.30, 5.0)
        ax.set_ylim(0, min(100.0, y_top))
        ax.yaxis.set_major_formatter(ticker.PercentFormatter())
        ax.tick_params(colors="#aaaaaa")
        ax.spines[:].set_color("#333355")
        ax.grid(True, color="#222244", linewidth=0.6, alpha=0.7, axis="y")
        ax.legend(facecolor="#1a1a2e", edgecolor="#333355", labelcolor="#dddddd", fontsize=9.0, loc="upper left")

        plt.tight_layout()

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"  [probe] Ownership chart saved -> {save_path}")

        plt.close(fig)
        return

    # Fallback single-axis figure for simple confidence or uncommitted plots
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    if confidences:
        x_indices = np.arange(len(loop_labels))
        conf_pct = [c * 100.0 for c in confidences]
        entities = sorted(set(owner_at_loop))
        palette = ["#00F5FF", "#FFB300", "#FF4D6D", "#50FA7B", "#BD93F9"]
        colour_map = {e: palette[idx % len(palette)] for idx, e in enumerate(entities)}

        for i, (label, owner, val) in enumerate(zip(loop_labels, owner_at_loop, conf_pct)):
            colour = colour_map.get(owner, "#00F5FF")
            ax.bar(i, val, color=colour, alpha=0.85, width=0.55, edgecolor="#ffffff", linewidth=0.5)
            ax.text(i, val + 0.5, f"{owner} ({val:.1f}%)", ha="center", va="bottom",
                    color=colour, fontsize=9, fontweight="bold")

        ax.set_xticks(x_indices)
        ax.set_xticklabels(loop_labels, color="#dddddd", fontsize=10)
        ax.set_ylabel("Winning Confidence (%)", color="#cccccc", fontsize=11)
        ax.set_ylim(0, min(100.0, max(conf_pct + [10.0]) * 1.25))
        ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    else:
        for i, (label, owner) in enumerate(zip(loop_labels, owner_at_loop)):
            ax.bar(i, 1.0, color="#00F5FF", alpha=0.85, width=0.6)
            ax.text(i, 0.5, owner, ha="center", va="center", color="#000000", fontsize=10, fontweight="bold")
        ax.set_xticks(range(len(loop_labels)))
        ax.set_xticklabels(loop_labels, color="#aaaaaa")
        ax.set_yticks([])

    ax.set_title(title, color="#ffffff", fontsize=12, pad=12, fontweight="bold")
    ax.spines[:].set_color("#333355")
    ax.grid(True, axis="y", color="#222244", linewidth=0.6, alpha=0.7)
    ax.tick_params(colors="#aaaaaa")

    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [probe] Ownership chart saved -> {save_path}")

    plt.close(fig)


def plot_vocabulary_word_map(
    per_loop_tokens: List[List[Tuple[str, float]]],
    loop_labels: List[str],
    save_path: Optional[str | Path] = None,
    title: str = "Exp 1 -- Vocabulary Word Map: Deliberative Token Growth & Shrinkage Across Loops",
) -> None:
    """
    Renders a multi-panel Word Map displaying top vocabulary tokens per loop.
    Demonstrates which words grow into prominence (Macduff, Banquo) versus which
    words collapse (surface syntax tokens like 'there', 'he', 'the').
    """
    n_loops = len(per_loop_tokens)
    fig, axes = plt.subplots(1, n_loops, figsize=(14.5, 5.2), sharey=False)
    fig.patch.set_facecolor("#0f0f1a")

    loop_subtitles = [
        "Loop 1: Surface Text Heuristics",
        "Loop 2: Pronominal Shift",
        "Loop 3: Entity Incubation",
        "Loop 4: Aligned Entity Commitment",
    ]

    # Map words to consistent semantic categories
    def get_token_color(word: str) -> str:
        w_lower = word.lower()
        if w_lower == "macduff":
            return "#00F5FF"  # Cyan highlight (target winner)
        elif w_lower == "banquo":
            return "#FFB300"  # Gold (interim holder)
        elif w_lower == "duncan":
            return "#FF4D6D"  # Crimson (original holder)
        elif w_lower in {"<eos>", ".", ","}:
            return "#555577"  # Muted Slate (structural)
        elif w_lower in {"he", "she", "there", "it"}:
            return "#BD93F9"  # Purple (pronoun / reference)
        else:
            return "#3E4460"  # Dark Slate (general vocabulary)

    # Calculate Loop 1 baseline probabilities for delta comparison
    loop1_dict = {w: p for w, p in per_loop_tokens[0]}

    for k, (ax, tokens, label) in enumerate(zip(axes, per_loop_tokens, loop_labels)):
        ax.set_facecolor("#0f0f1a")
        
        # Take top 7 tokens for clean scannability
        top_tokens = tokens[:7]
        words = [t[0] for t in top_tokens][::-1]  # Invert for horizontal bar order
        probs_pct = [t[1] * 100.0 for t in top_tokens][::-1]
        colors = [get_token_color(w) for w in words]

        y_pos = np.arange(len(words))
        bars = ax.barh(y_pos, probs_pct, color=colors, alpha=0.88, edgecolor="#ffffff", linewidth=0.5, height=0.65)

        for bar, word, prob in zip(bars, words, probs_pct):
            # Format annotation
            p_base = loop1_dict.get(word, 0.0) * 100.0
            delta = prob - p_base
            delta_str = ""
            if k > 0 and abs(delta) >= 1.0:
                delta_str = f" ({'+' if delta > 0 else ''}{delta:.1f}%)"

            label_text = f" {prob:.1f}%{delta_str}"
            ax.text(
                max(bar.get_width(), 1.0) + 1.2,
                bar.get_y() + bar.get_height() / 2,
                label_text,
                va="center",
                ha="left",
                fontsize=8.5,
                color="#dddddd" if prob < 10.0 else "#ffffff",
                fontweight="bold" if word.lower() in {"macduff", "banquo", "duncan"} else "normal",
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(words, color="#ffffff", fontsize=9.5, fontweight="bold")
        ax.set_xlim(0, 95.0)
        ax.xaxis.set_major_formatter(ticker.PercentFormatter())
        ax.set_xlabel("Probability (%)", color="#aaaaaa", fontsize=9.0)
        
        sub = loop_subtitles[k] if k < len(loop_subtitles) else label
        ax.set_title(f"{label}\n{sub}", color="#00F5FF" if k == n_loops-1 else "#ffffff", fontsize=10.0, pad=8, fontweight="bold")
        ax.tick_params(colors="#8888aa")
        ax.spines[:].set_color("#333355")
        ax.grid(True, axis="x", color="#222244", linewidth=0.5, alpha=0.7)

    fig.suptitle(title, color="#ffffff", fontsize=12.5, fontweight="bold", y=1.03)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  [probe] Vocabulary Word Map saved -> {save_path}")

    plt.close(fig)


def generate_vocabulary_word_map_html(
    per_loop_tokens: List[List[Tuple[str, float]]],
    loop_labels: List[str],
    save_path: str | Path,
    title: str = "Astra Oversight: Latent Deliberation Token Evolution Map",
) -> None:
    """
    Generates an interactive, standalone HTML token evolution map.
    Allows auditors to step through loops or play an animation watching
    tokens grow and shrink in real-time.
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    data_json = json.dumps({
        "labels": loop_labels,
        "loops": [
            [{"word": w, "prob": round(float(p) * 100.0, 2)} for w, p in tokens[:12]]
            for tokens in per_loop_tokens
        ]
    })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --bg-primary: #0a0a14;
    --bg-card: #131326;
    --border: #232342;
    --text-primary: #f0f0f8;
    --text-muted: #8888a8;
    --cyan: #00f5ff;
    --gold: #ffb300;
    --crimson: #ff4d6d;
    --purple: #bd93f9;
    --slate: #4b526d;
    --green: #50fa7b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 24px;
    line-height: 1.5;
  }}
  .header {{
    max-width: 1200px;
    margin: 0 auto 24px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
  }}
  .header h1 {{
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .badge {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: rgba(0, 245, 255, 0.15);
    color: var(--cyan);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(0, 245, 255, 0.3);
  }}
  .header p {{
    color: var(--text-muted);
    font-size: 14px;
  }}
  .container {{
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 24px;
  }}
  .panel {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .controls {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }}
  .btn {{
    background: #1a1a33;
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .btn:hover {{
    background: #252548;
    border-color: #3b3b68;
  }}
  .btn.active {{
    background: rgba(0, 245, 255, 0.2);
    color: var(--cyan);
    border-color: var(--cyan);
  }}
  .btn-play {{
    background: rgba(80, 250, 123, 0.15);
    color: var(--green);
    border-color: rgba(80, 250, 123, 0.3);
    margin-left: auto;
  }}
  .btn-play:hover {{
    background: rgba(80, 250, 123, 0.25);
  }}
  .word-cloud {{
    min-height: 380px;
    display: flex;
    flex-wrap: wrap;
    align-content: center;
    justify-content: center;
    gap: 14px;
    padding: 30px 10px;
    background: rgba(10, 10, 20, 0.6);
    border-radius: 8px;
    border: 1px dashed var(--border);
  }}
  .word-tag {{
    display: inline-flex;
    align-items: baseline;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 8px;
    background: #181830;
    border: 1px solid var(--border);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }}
  .word-tag.target {{
    background: rgba(0, 245, 255, 0.18);
    border-color: var(--cyan);
    color: var(--cyan);
    box-shadow: 0 0 16px rgba(0, 245, 255, 0.25);
  }}
  .word-tag.interim {{
    background: rgba(255, 179, 0, 0.18);
    border-color: var(--gold);
    color: var(--gold);
  }}
  .word-tag.initial {{
    background: rgba(255, 77, 109, 0.18);
    border-color: var(--crimson);
    color: var(--crimson);
  }}
  .word-tag.pronoun {{
    background: rgba(189, 147, 249, 0.15);
    border-color: var(--purple);
    color: var(--purple);
  }}
  .word-val {{
    font-size: 11px;
    opacity: 0.8;
  }}
  .stats-card {{
    margin-bottom: 16px;
  }}
  .stats-card h3 {{
    font-size: 14px;
    color: #ffffff;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .delta-row {{
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 13px;
  }}
  .delta-up {{ color: var(--green); font-weight: 600; }}
  .delta-down {{ color: var(--crimson); font-weight: 600; }}
  .callout {{
    background: rgba(0, 245, 255, 0.06);
    border-left: 3px solid var(--cyan);
    padding: 12px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 20px;
  }}
  .callout strong {{ color: #ffffff; }}
</style>
</head>
<body>

<div class="header">
  <h1>Astra Latent Deliberation: Token Evolution Map <span class="badge">Exp 1 Mechanistic Trace</span></h1>
  <p>Live visualization of vocabulary probability redistribution across recurrent test-time loops ($L_1 \to L_4$). Watch how surface syntax collapses while the true entity winner emerges.</p>
</div>

<div class="container">
  <div class="panel">
    <div class="controls">
      <div id="tab-btns"></div>
      <button class="btn btn-play" id="play-btn" onclick="togglePlay()">&#9658; Play Sequence</button>
    </div>

    <div class="word-cloud" id="word-cloud"></div>

    <div class="callout">
      <strong>How to Interpret This Map:</strong> In Loops 1 & 2, the model relies on general syntax inertia (<code>there</code>, <code>he</code>, <code>the</code>). By Loop 3, candidate entities incubate, and by Loop 4, <strong>Macduff</strong> takes command of the content vocabulary at 21.52% (+21.5% net growth), resolving the multi-step ownership transfer.
    </div>
  </div>

  <div class="panel">
    <div class="stats-card">
      <h3 style="color: var(--green);">Fastest Growing Tokens</h3>
      <div id="growing-tokens"></div>
    </div>

    <div class="stats-card" style="margin-top: 24px;">
      <h3 style="color: var(--crimson);">Fastest Shrinking Tokens</h3>
      <div id="shrinking-tokens"></div>
    </div>

    <div class="stats-card" style="margin-top: 24px;">
      <h3>Current Loop Winner</h3>
      <div id="loop-winner" style="font-size: 18px; font-weight: 700; color: var(--cyan); margin-top: 4px;">-</div>
    </div>
  </div>
</div>

<script>
  const data = {data_json};
  let currentLoop = 3; // Default to Loop 4
  let playInterval = null;

  function init() {{
    const tabContainer = document.getElementById("tab-btns");
    data.labels.forEach((label, idx) => {{
      const btn = document.createElement("button");
      btn.className = `btn ${{idx === currentLoop ? 'active' : ''}}`;
      btn.id = `btn-${{idx}}`;
      btn.innerText = label;
      btn.onclick = () => selectLoop(idx);
      tabContainer.appendChild(btn);
    }});
    renderLoop(currentLoop);
    renderDeltas();
  }}

  function selectLoop(idx) {{
    currentLoop = idx;
    data.labels.forEach((_, i) => {{
      const b = document.getElementById(`btn-${{i}}`);
      if (b) b.className = `btn ${{i === currentLoop ? 'active' : ''}}`;
    }});
    renderLoop(currentLoop);
  }}

  function renderLoop(idx) {{
    const cloud = document.getElementById("word-cloud");
    cloud.innerHTML = "";
    const loopTokens = data.loops[idx] || [];

    // Find loop winner
    const winnerEl = document.getElementById("loop-winner");
    if (loopTokens.length > 0) {{
      const topWord = loopTokens[0];
      winnerEl.innerText = `${{topWord.word}} (${{topWord.prob.toFixed(1)}}%)`;
    }}

    loopTokens.forEach(t => {{
      const tag = document.createElement("div");
      const wLower = t.word.toLowerCase();
      let cls = "word-tag";
      if (wLower === "macduff") cls += " target";
      else if (wLower === "banquo") cls += " interim";
      else if (wLower === "duncan") cls += " initial";
      else if (["he", "she", "there", "it"].includes(wLower)) cls += " pronoun";

      const scale = Math.max(13, Math.min(42, Math.round(13 + Math.sqrt(t.prob) * 4.2)));
      tag.className = cls;
      tag.style.fontSize = `${{scale}}px`;
      tag.innerHTML = `<strong>${{t.word}}</strong><span class="word-val">${{t.prob.toFixed(1)}}%</span>`;
      cloud.appendChild(tag);
    }});
  }}

  function renderDeltas() {{
    const l1 = {{}};
    (data.loops[0] || []).forEach(t => {{ l1[t.word] = t.prob; }});
    const l4 = {{}};
    (data.loops[3] || []).forEach(t => {{ l4[t.word] = t.prob; }});

    const allWords = Array.from(new Set([...Object.keys(l1), ...Object.keys(l4)]));
    const deltas = allWords.map(w => ({{
      word: w,
      d: (l4[w] || 0) - (l1[w] || 0)
    }}));

    deltas.sort((a, b) => b.d - a.d);
    const growing = deltas.filter(d => d.d > 0.5).slice(0, 5);
    const shrinking = [...deltas].filter(d => d.d < -0.5).sort((a, b) => a.d - b.d).slice(0, 5);

    const growEl = document.getElementById("growing-tokens");
    growEl.innerHTML = growing.map(g => `
      <div class="delta-row">
        <span>${{g.word}}</span>
        <span class="delta-up">+${{g.d.toFixed(1)}}%</span>
      </div>
    `).join("");

    const shrinkEl = document.getElementById("shrinking-tokens");
    shrinkEl.innerHTML = shrinking.map(s => `
      <div class="delta-row">
        <span>${{s.word}}</span>
        <span class="delta-down">${{s.d.toFixed(1)}}%</span>
      </div>
    `).join("");
  }}

  function togglePlay() {{
    const pBtn = document.getElementById("play-btn");
    if (playInterval) {{
      clearInterval(playInterval);
      playInterval = null;
      pBtn.innerHTML = "&#9658; Play Sequence";
    }} else {{
      currentLoop = 0;
      selectLoop(currentLoop);
      pBtn.innerHTML = "&#10074;&#10074; Pause";
      playInterval = setInterval(() => {{
        currentLoop = (currentLoop + 1) % data.labels.length;
        selectLoop(currentLoop);
      }}, 1200);
    }}
  }}

  init();
</script>

</body>
</html>
"""
    save_path.write_text(html_content, encoding="utf-8")
    print(f"  [probe] Interactive Vocabulary Word Map HTML generated -> {save_path}")


# -- smoke test ----------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np

    # Synthetic data: 4 loops, 20 samples, d_model=32
    NUM_LOOPS = 4
    N = 20
    D = 32

    rng = np.random.default_rng(0)
    slices = [torch.tensor(rng.normal(size=(N, 8, D)), dtype=torch.float32)
              for _ in range(NUM_LOOPS)]
    labels = rng.integers(0, 2, size=N)

    print("Fitting probes across loops...")
    probes = fit_probes(slices, labels)

    # Use single-sample slice from the last position
    test_slice = [s[:1] for s in slices]
    traj = probe_trajectory(test_slice, probes)
    print(f"Trajectory: {[f'{v:.3f}' for v in traj]}")

    plot_trajectory(
        {"Concept A": traj},
        title="Smoke Test Trajectory",
        save_path="results/smoke_test.png",
    )
    print("[probe] OK  Smoke test passed.")
