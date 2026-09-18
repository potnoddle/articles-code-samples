"""
embedding_surgery.py
====================
Three-technique methodology for injecting semantic knowledge into micro-scale
models without incurring the compute cost of large-corpus pre-training.

Technique 1 -- Embedding Surgery
    Load pre-trained GloVe / fastText vectors, align them to the local
    vocabulary, and graft the weight tensor into the model's token embedding
    layer with requires_grad = False.

Technique 2 -- Relation Graph Splicing
    Convert ConceptNet-style semantic triples (subject, relation, object) into
    natural-language sentences that can be appended to the training corpus.

Technique 3 -- Dataset Distillation (placeholder)
    Describes the methodology for using a large open-weights LLM to rewrite
    modern knowledge-dense text in a corpus's syntactic style.  Full
    automation requires external API access; a static distilled corpus is
    provided instead.

References
----------
    Spec §8 -- embedding surgery methodology (conversation_consolidation.txt)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch


# -- built-in relation triples -------------------------------------------------
# A curated set of ConceptNet-style semantic triples covering the three
# experimental domains.  These are converted to sentence form and injected
# into the training corpus so that micro-scale models learn relational
# structure beyond what TinyShakespeare-like datasets provide.
BUILT_IN_TRIPLES: List[Tuple[str, str, str]] = [
    # Ownership / possession (Macbeth characters)
    ("Duncan",      "HasA",         "dagger"),
    ("Banquo",      "HasA",         "dagger"),
    ("Macduff",     "HasA",         "dagger"),
    # Agent-instrument relationships
    ("physician",   "UsedFor",      "herbs"),
    ("surgeon",     "UsedFor",      "cure"),
    ("doctor",      "IsA",          "physician"),
    ("healer",      "IsA",          "physician"),
    ("carpenter",   "UsedFor",      "tools"),
    ("sculptor",    "UsedFor",      "chisel"),
    # Action-outcome
    ("herbs",       "UsedFor",      "heal"),
    ("medicine",    "UsedFor",      "cure"),
    ("tools",       "UsedFor",      "build"),
    ("heal",        "HasConsequence","cure"),
    ("physician",   "UsedFor",      "cure"),
    # Forbidden concepts (for Exp 2 activation suppression)
    ("sword",       "IsA",          "blade"),
    ("sword",       "IsA",          "weapon"),
    ("dagger",      "IsA",          "blade"),
    ("blade",       "IsA",          "weapon"),
    ("battle",      "HasA",         "conflict"),
    ("sonnet",      "IsA",          "verse"),
]


# -- relation -> sentence templates ---------------------------------------------

_TEMPLATES: Dict[str, str] = {
    "IsA":              "{subj} is a {obj}.",
    "HasA":             "{subj} has a {obj}.",
    "UsedFor":          "{subj} is used for {obj}.",
    "HasConsequence":   "{subj} leads to {obj}.",
    "CapableOf":        "{subj} is capable of {obj}.",
    "AtLocation":       "{subj} is located at {obj}.",
    "PartOf":           "{subj} is part of {obj}.",
    "MadeOf":           "{subj} is made of {obj}.",
    "Causes":           "{subj} causes {obj}.",
}


# -- public API ----------------------------------------------------------------

def build_relation_triples(
    triples: Optional[List[Tuple[str, str, str]]] = None,
) -> List[str]:
    """
    Convert ConceptNet-style triples into natural-language sentences.

    Parameters
    ----------
    triples:
        List of ``(subject, relation, object)`` tuples.
        If None, ``BUILT_IN_TRIPLES`` is used.

    Returns
    -------
    List of sentence strings ready for appending to a training corpus.

    Example
    -------
    >>> build_relation_triples([("physician", "UsedFor", "scalpel")])
    ['physician is used for scalpel.']
    """
    triples = triples or BUILT_IN_TRIPLES
    sentences: List[str] = []
    for subj, rel, obj in triples:
        template = _TEMPLATES.get(rel)
        if template:
            sentences.append(template.format(subj=subj.lower(), obj=obj.lower()))
        else:
            # Fallback: generic subject-relation-object sentence
            sentences.append(f"{subj.lower()} {rel.lower()} {obj.lower()}.")
    return sentences


def load_glove_embeddings(
    glove_path: str | Path,
    vocab: Dict[str, int],
    d_model: int,
) -> torch.Tensor:
    """
    Load pre-trained GloVe vectors and align them to a local vocabulary.

    Parameters
    ----------
    glove_path:
        Path to a GloVe text file (e.g., ``glove.6B.50d.txt``).
        Each line: ``<word> <float> <float> ...``
    vocab:
        Mapping of word -> index (``tokenizer.word2idx``).
    d_model:
        Embedding dimension.  Must match the GloVe file's vector length.

    Returns
    -------
    Tensor of shape ``(len(vocab), d_model)`` suitable for passing to
    ``InfilledRecurrentTransformer(pretrained_weights=...)``.

    Words not found in the GloVe file retain random Xavier initialisation.
    Special tokens (<PAD>, <UNK>, <BOS>, <EOS>) are always random-initialised.
    """
    glove_path = Path(glove_path)
    if not glove_path.exists():
        raise FileNotFoundError(
            f"GloVe file not found: {glove_path}\n"
            "Download from: https://nlp.stanford.edu/data/glove.6B.zip"
        )

    # Xavier std as baseline
    std = (2.0 / (len(vocab) + d_model)) ** 0.5
    weights = torch.normal(mean=0.0, std=std, size=(len(vocab), d_model))

    loaded = 0
    with open(glove_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip().split(" ")
            word = parts[0]
            if word not in vocab:
                continue
            vec = torch.tensor([float(x) for x in parts[1:]], dtype=torch.float32)
            if vec.shape[0] != d_model:
                raise ValueError(
                    f"GloVe vector length {vec.shape[0]} does not match "
                    f"d_model={d_model}. Use the correct GloVe file variant."
                )
            weights[vocab[word]] = vec
            loaded += 1

    print(
        f"[embedding_surgery] Loaded {loaded}/{len(vocab)} GloVe vectors "
        f"({100 * loaded / len(vocab):.1f}% coverage)."
    )
    return weights


def build_surgery_weights(
    vocab: Dict[str, int],
    d_model: int,
    glove_path: Optional[str | Path] = None,
) -> torch.Tensor:
    """
    Build an embedding weight matrix using the available resources.

    Priority order:
    1. GloVe file (if ``glove_path`` supplied and file exists)
    2. Relation-triple cosine seeding (heuristic, no external files)
    3. Random Xavier initialisation (fallback)

    Parameters
    ----------
    vocab:
        ``tokenizer.word2idx`` mapping.
    d_model:
        Embedding dimension.
    glove_path:
        Optional path to a GloVe `.txt` file.

    Returns
    -------
    Weight tensor of shape ``(vocab_size, d_model)``.
    """
    # -- option 1: GloVe ---------------------------------------------------
    if glove_path is not None:
        glove_path = Path(glove_path)
        if glove_path.exists():
            return load_glove_embeddings(glove_path, vocab, d_model)
        else:
            print(
                f"[embedding_surgery] GloVe file not found at {glove_path}. "
                "Falling back to relation-triple seeding."
            )

    # -- option 2: relation-triple cosine seeding --------------------------
    # Simple deterministic seeding: words that appear together in triples
    # are nudged towards similar vectors.
    print("[embedding_surgery] Using relation-triple heuristic seeding.")
    # Deterministic generator for stable cross-platform benchmark replication
    gen = torch.Generator().manual_seed(42)
    std = (2.0 / (len(vocab) + d_model)) ** 0.5
    weights = torch.normal(mean=0.0, std=std, size=(len(vocab), d_model), generator=gen)
    weights = _seed_from_triples(weights, vocab, BUILT_IN_TRIPLES)
    return weights


def distill_corpus(
    base_texts: List[str],
    relation_triples: Optional[List[Tuple[str, str, str]]] = None,
) -> List[str]:
    """
    Merge relation-triple sentences into a base corpus.

    This is Technique 3 from the spec.  Full automation (rewriting modern
    knowledge-dense text in the corpus's syntactic style via a teacher LLM)
    requires external API access.  Here we append the triple-derived sentences
    to the base corpus and return the combined list.

    Parameters
    ----------
    base_texts:
        List of raw text strings forming the base training corpus.
    relation_triples:
        Optional custom triples; defaults to ``BUILT_IN_TRIPLES``.

    Returns
    -------
    Extended corpus list (base + relation sentences).
    """
    triple_sentences = build_relation_triples(relation_triples)
    return list(base_texts) + triple_sentences


# -- internal helpers ----------------------------------------------------------

def _seed_from_triples(
    weights: torch.Tensor,
    vocab: Dict[str, int],
    triples: List[Tuple[str, str, str]],
    alpha: float = 0.15,
) -> torch.Tensor:
    """
    Nudge embedding vectors for words that co-occur in semantic triples
    towards each other by blending a fraction of their vectors.

    This is a lightweight approximation of the relational alignment that
    full GloVe training achieves over billions of co-occurrences.
    """
    for subj, _, obj in triples:
        s_word = subj.lower()
        o_word = obj.lower()
        if s_word in vocab and o_word in vocab:
            s_idx = vocab[s_word]
            o_idx = vocab[o_word]
            # Move each vector slightly towards the other
            s_vec = weights[s_idx].clone()
            o_vec = weights[o_idx].clone()
            weights[s_idx] = (1 - alpha) * s_vec + alpha * o_vec
            weights[o_idx] = (1 - alpha) * o_vec + alpha * s_vec
    return weights


# -- smoke test ----------------------------------------------------------------

if __name__ == "__main__":
    sentences = build_relation_triples()
    print(f"Generated {len(sentences)} relation sentences. Examples:")
    for s in sentences[:6]:
        print(f"  {s}")

    # Simulate a small vocab
    dummy_vocab = {w: i for i, w in enumerate(
        ["<PAD>", "<UNK>", "<BOS>", "<EOS>",
         "physician", "surgeon", "scalpel", "heal", "cut", "sword", "blade"]
    )}
    weights = build_surgery_weights(dummy_vocab, d_model=32)
    print(f"\nEmbedding weight tensor shape: {weights.shape}")
    print("[embedding_surgery] OK  Smoke test passed.")
