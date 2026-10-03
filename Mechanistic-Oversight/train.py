"""
train.py
========
Training script for the micro-scale InfilledRecurrentTransformer.

Trains a next-token prediction language model on the built-in default corpus
(or any text file supplied via --corpus).  Saves a model checkpoint and
tokeniser after training.

Usage
-----
    python train.py                          # default settings
    python train.py --loops 6 --d_model 256 --epochs 100
    python train.py --corpus path/to/text.txt --use_embedding_surgery
    python train.py --help
"""

from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from model import InfilledRecurrentTransformer, TinyRecursiveModel
from tokenizer import Tokenizer, DEFAULT_CORPUS
from embedding_surgery import build_surgery_weights, distill_corpus
from level_profiles import get_level_profile, get_checkpoint_paths, LEVEL_PROFILES
from data.download_corpus import ensure_corpus


# -- dataset -------------------------------------------------------------------

class TokenDataset(Dataset):
    """
    Sliding-window next-token prediction dataset built from a flat token list.
    Uses chunk stride (defaults to block_size for large corpora > 50K tokens,
    or 1 for micro corpora) and supports max_samples limiting for testing.
    """

    def __init__(
        self,
        token_ids: List[int],
        block_size: int = 64,
        stride: Optional[int] = None,
        max_samples: Optional[int] = None,
    ) -> None:
        self.ids = token_ids
        self.block_size = block_size
        if stride is not None:
            self.stride = stride
        elif len(token_ids) > 10_000:
            self.stride = block_size
        elif len(token_ids) > 1_000:
            self.stride = max(1, block_size // 2)
        else:
            self.stride = 1
        self.starts = list(range(0, max(0, len(self.ids) - self.block_size), self.stride))
        if max_samples and len(self.starts) > max_samples:
            self.starts = self.starts[:max_samples]

    def __len__(self) -> int:
        return len(self.starts)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        start = self.starts[idx]
        chunk = self.ids[start : start + self.block_size + 1]
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:],  dtype=torch.long)
        return x, y


# -- training loop -------------------------------------------------------------

def train(
    corpus: List[str],
    save_path: str | Path = "checkpoints/model.pt",
    tok_path: str | Path = "checkpoints/tokenizer.pkl",
    model_type: str = "trm",
    d_model: int = 128,
    n_heads: int = 4,
    num_loops: int = 4,
    num_latent_steps: int = 2,
    block_size: int = 64,
    batch_size: int = 16,
    epochs: int = 50,
    lr: float = 3e-4,
    max_samples: Optional[int] = None,
    use_embedding_surgery: bool = False,
    glove_path: Optional[str | Path] = None,
    device: str = "cpu",
) -> Tuple[nn.Module, Tokenizer]:
    """
    Train an Astra recurrent transformer model across scaling tiers and save the checkpoint.

    Returns
    -------
    Trained model and fitted tokeniser.
    """
    save_path = Path(save_path)
    tok_path  = Path(tok_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # -- build tokeniser ---------------------------------------------------
    print("Building vocabulary...")
    tok = Tokenizer()
    tok.build_vocab(corpus)
    print(f"  Vocabulary size: {tok.vocab_size}")

    # -- build dataset -----------------------------------------------------
    all_ids: List[int] = []
    for text in corpus:
        all_ids.extend(tok.encode(text, add_bos=True, add_eos=True))

    dataset = TokenDataset(all_ids, block_size=block_size, max_samples=max_samples)
    if len(dataset) == 0:
        raise ValueError(
            "Dataset is empty -- corpus may be too short for the given block_size. "
            f"Token count: {len(all_ids)}, block_size: {block_size}"
        )

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    print(f"  Training samples: {len(dataset)}")

    # -- optional embedding surgery ----------------------------------------
    pretrained_weights: Optional[torch.Tensor] = None
    if use_embedding_surgery:
        print("Applying embedding surgery...")
        pretrained_weights = build_surgery_weights(
            vocab=tok.word2idx,
            d_model=d_model,
            glove_path=glove_path,
        )
        pretrained_weights = pretrained_weights.to(device)

    # -- build model -------------------------------------------------------
    max_len = max(2048, block_size * 2)
    if model_type.lower() == "trm":
        print("  Building TinyRecursiveModel (TRM - arXiv:2510.04871)...")
        model = TinyRecursiveModel(
            vocab_size=tok.vocab_size,
            d_model=d_model,
            n_heads=n_heads,
            max_len=max_len,
            num_latent_steps=num_latent_steps,
            num_cycles=num_loops,
        ).to(device)
    else:
        print("  Building InfilledRecurrentTransformer...")
        model = InfilledRecurrentTransformer(
            vocab_size=tok.vocab_size,
            d_model=d_model,
            n_heads=n_heads,
            max_len=max_len,
            num_loops=num_loops,
            pretrained_weights=pretrained_weights,
        ).to(device)

    counts = model.get_param_count()
    print(
        f"  Model parameters: {counts['total']:,} total  "
        f"({counts['trainable']:,} trainable, {counts['frozen']:,} frozen)"
    )

    # -- optimiser & scheduler ---------------------------------------------
    optimiser = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr,
        weight_decay=0.01,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimiser, T_max=epochs, eta_min=lr * 0.1
    )
    criterion = nn.CrossEntropyLoss(ignore_index=0)  # ignore PAD

    # -- training ----------------------------------------------------------
    print(f"\nTraining for {epochs} epochs on {device}...")
    t0 = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        n_batches = 0

        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimiser.zero_grad()
            if isinstance(model, TinyRecursiveModel):
                logits, _ = model(x)
            else:
                logits, _ = model(x, causal_mask=True)
            # logits: (B, T, vocab_size)  y: (B, T)
            loss = criterion(logits.reshape(-1, tok.vocab_size), y.reshape(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimiser.step()
            total_loss += loss.item()
            n_batches += 1

        scheduler.step()
        avg_loss = total_loss / max(n_batches, 1)

        if epoch % max(1, epochs // 10) == 0 or epoch == epochs:
            elapsed = time.time() - t0
            print(
                f"  Epoch {epoch:>4}/{epochs}  "
                f"loss={avg_loss:.4f}  "
                f"lr={scheduler.get_last_lr()[0]:.2e}  "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )

    # -- save checkpoint ---------------------------------------------------
    torch.save(
        {
            "model_state": model.state_dict(),
            "config": {
                "model_type": model_type.lower(),
                "vocab_size": tok.vocab_size,
                "d_model": d_model,
                "n_heads": n_heads,
                "num_loops": num_loops,
                "num_latent_steps": num_latent_steps,
            },
        },
        save_path,
    )
    tok.save(tok_path)
    print(f"\nCheckpoint saved -> {save_path}")
    print(f"Tokeniser saved  -> {tok_path}")

    return model, tok


# -- checkpoint loader (used by experiments) -----------------------------------

def load_checkpoint(
    model_path: str | Path = "checkpoints/model.pt",
    tok_path:   str | Path = "checkpoints/tokenizer.pkl",
    device: str = "cpu",
) -> Tuple[nn.Module, Tokenizer]:
    """
    Load a trained model and tokeniser from checkpoints.

    Parameters
    ----------
    model_path, tok_path:
        Paths written by ``train()``.
    device:
        Target device for the loaded model.

    Returns
    -------
    Tuple of (model, tokenizer).
    """
    model_path = Path(model_path)
    tok_path   = Path(tok_path)

    if not model_path.exists():
        fallback_model = model_path.parent / "model.pt"
        if model_path.name == "level1_model.pt" and fallback_model.exists():
            model_path = fallback_model
        else:
            raise FileNotFoundError(
                f"Model checkpoint not found: {model_path}\n"
                "Run `python train.py` or `python run_all.py` first."
            )

    if not tok_path.exists():
        fallback_tok = tok_path.parent / "tokenizer.pkl"
        if tok_path.name == "level1_tokenizer.pkl" and fallback_tok.exists():
            tok_path = fallback_tok

    ckpt = torch.load(model_path, map_location=device, weights_only=False)
    cfg  = ckpt["config"]
    m_type = cfg.get("model_type", "irt")

    saved_max_len = (
        ckpt["model_state"]["pos_emb.weight"].shape[0]
        if "model_state" in ckpt and "pos_emb.weight" in ckpt["model_state"]
        else 2048
    )
    max_len = cfg.get("max_len", saved_max_len)

    if m_type == "trm":
        model = TinyRecursiveModel(
            vocab_size=cfg["vocab_size"],
            d_model=cfg["d_model"],
            n_heads=cfg["n_heads"],
            max_len=max_len,
            num_latent_steps=cfg.get("num_latent_steps", 2),
            num_cycles=cfg["num_loops"],
        ).to(device)
    else:
        model = InfilledRecurrentTransformer(
            vocab_size=cfg["vocab_size"],
            d_model=cfg["d_model"],
            n_heads=cfg["n_heads"],
            max_len=max_len,
            num_loops=cfg["num_loops"],
        ).to(device)

    model.load_state_dict(ckpt["model_state"])
    model.eval()

    tok = Tokenizer.load(tok_path)
    return model, tok


# -- CLI -----------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train an Astra recurrent transformer model across hardware/model scaling tiers."
    )
    parser.add_argument("--level",    type=int,   default=1, choices=[1, 2, 3],
                        help="Tier level: 1 (Micro-scale logic harness), 2 (Macbeth), 3 (Complete Shakespeare)")
    parser.add_argument("--model_type", type=str, default="trm", choices=["trm", "irt"],
                        help="Model architecture: 'trm' (TinyRecursiveModel) or 'irt' (InfilledRecurrentTransformer)")
    parser.add_argument("--loops",    type=int,   default=None,
                        help="Number of recurrent loops (overrides tier profile)")
    parser.add_argument("--d_model",  type=int,   default=None,
                        help="Hidden dimension (overrides tier profile)")
    parser.add_argument("--n_heads",  type=int,   default=None,
                        help="Number of attention heads (overrides tier profile)")
    parser.add_argument("--epochs",   type=int,   default=None,
                        help="Training epochs (overrides tier profile)")
    parser.add_argument("--batch",    type=int,   default=None,
                        help="Batch size (overrides tier profile)")
    parser.add_argument("--lr",       type=float, default=None,
                        help="Learning rate (overrides tier profile)")
    parser.add_argument("--block",    type=int,   default=None,
                        help="Context block size in tokens (overrides tier profile)")
    parser.add_argument("--corpus",   type=str,   default=None,
                        help="Path to a plain-text corpus file (overrides tier corpus)")
    parser.add_argument("--save_path", type=str,  default=None,
                        help="Checkpoint output path (overrides tier profile)")
    parser.add_argument("--tok_path",  type=str,  default=None,
                        help="Tokenizer output path (overrides tier profile)")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="Maximum training windows to sample (useful for CPU smoke tests on large corpora)")
    parser.add_argument("--use_embedding_surgery", action="store_true",
                        help="Seed embeddings with relation-triple heuristics or GloVe")
    parser.add_argument("--glove",    type=str,   default=None,
                        help="Path to GloVe .txt file (optional)")
    parser.add_argument("--device",   type=str,   default="cpu",
                        help="torch device string (default: cpu)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.level == 3 and not args.corpus:
        raise RuntimeError(
            "Tier 3 (Complete Folio Frontier) requires datacenter-class hardware (e.g. Blackwell RTX 128GB / A100). "
            "To prevent freezing local desktop/consumer machines, Tier 3 training is locked."
        )
    profile = get_level_profile(args.level)

    loops = args.loops if args.loops is not None else profile.num_loops
    d_model = args.d_model if args.d_model is not None else profile.d_model
    n_heads = args.n_heads if args.n_heads is not None else profile.n_heads
    epochs = args.epochs if args.epochs is not None else profile.epochs
    batch = args.batch if args.batch is not None else profile.batch_size
    block = args.block if args.block is not None else profile.block_size
    lr = args.lr if args.lr is not None else profile.lr

    default_model_path, default_tok_path = get_checkpoint_paths(args.level, args.model_type)
    save_path = Path(args.save_path) if args.save_path else default_model_path
    tok_path = Path(args.tok_path) if args.tok_path else default_tok_path

    print("=" * 60)
    print(f"  Astra Training -- {profile.name}")
    print(f"  Target Hardware : {profile.target_hardware}")
    print(f"  Estimated Params: {profile.estimated_params}")
    print(f"  Recurrent Loops : {loops} | d_model: {d_model} | heads: {n_heads} | epochs: {epochs}")
    print("=" * 60 + "\n")

    # Load corpus
    if args.corpus:
        print(f"Loading custom corpus from: {args.corpus}")
        with open(args.corpus, "r", encoding="utf-8") as f:
            raw = f.read()
        corpus = [p.strip() for p in raw.split("\n\n") if p.strip()]
    elif args.level == 1:
        print("Using built-in synthetic logic corpus...")
        corpus = distill_corpus(DEFAULT_CORPUS)
    else:
        print(f"Preparing corpus for {profile.name}...")
        corpus_path = ensure_corpus(args.level)
        with open(corpus_path, "r", encoding="utf-8") as f:
            raw = f.read()
        play_paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
        logic_paras = distill_corpus(DEFAULT_CORPUS)
        # Blend dramatic play text with Shakespearean reasoning seeds
        corpus = play_paras + (logic_paras * 8)

    train(
        corpus=corpus,
        save_path=save_path,
        tok_path=tok_path,
        model_type=args.model_type,
        d_model=d_model,
        n_heads=n_heads,
        num_loops=loops,
        num_latent_steps=profile.num_latent_steps,
        block_size=block,
        batch_size=batch,
        epochs=epochs,
        lr=lr,
        max_samples=args.max_samples,
        use_embedding_surgery=args.use_embedding_surgery,
        glove_path=args.glove,
        device=args.device,
    )
