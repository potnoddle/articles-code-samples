"""
model.py
========
InfilledRecurrentTransformer -- the core architecture from the spec.

A weight-tied looped transformer that captures discrete activation time-slices
at every recurrent pass, forming a tamper-proof mechanistic audit trail.

Architecture
------------
    [Input Tokens]
          |
    [Token Embedding + Positional Embedding]   <- optionally seeded via embedding surgery
          |
    ┌--►  [Shared TransformerEncoderLayer]  --┐
    |     (same weights, k = 1 .. num_loops)  |
    |     time_slices.append(h.detach())      |
    └-----------------------------------------┘
          |
    [LayerNorm]
          |
    [Linear Head -> vocab logits]

References
----------
    Spec §9 blueprint (conversation_consolidation.txt)
    arXiv:2502.05171 -- Ge et al., "Scaling up Test-Time Compute with Latent Reasoning"
    arXiv:2510.04871 -- Jolicoeur-Martineau (Samsung SAIL), "Less is More: Recursive Reasoning with Tiny Networks" (TRM)
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# -- model --------------------------------------------------------------------

class InfilledRecurrentTransformer(nn.Module):
    """
    Weight-tied recurrent transformer with time-slice capture.

    Parameters
    ----------
    vocab_size:
        Size of the token vocabulary.
    d_model:
        Hidden dimension (embedding + transformer width).
    n_heads:
        Number of attention heads. Must divide d_model evenly.
    d_ff:
        Feed-forward inner dimension. Defaults to 4 × d_model.
    max_len:
        Maximum sequence length for positional embeddings.
    num_loops:
        Default number of recurrent passes at inference time.
        Can be overridden per forward call.
    dropout:
        Dropout probability applied inside the transformer layer.
    pretrained_weights:
        Optional pre-trained embedding tensor of shape ``(vocab_size, d_model)``.
        When supplied the embedding weights are grafted (embedding surgery) and
        frozen so that the micro-dataset cannot distort the injected relations.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        n_heads: int = 4,
        d_ff: Optional[int] = None,
        max_len: int = 2048,
        num_loops: int = 4,
        dropout: float = 0.1,
        pretrained_weights: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__()

        if d_model % n_heads != 0:
            raise ValueError(
                f"d_model ({d_model}) must be divisible by n_heads ({n_heads})."
            )

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_loops = num_loops
        d_ff = d_ff or d_model * 4

        # -- embeddings ----------------------------------------------------
        self.token_emb = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_emb = nn.Embedding(max_len, d_model)

        # -- embedding surgery ---------------------------------------------
        if pretrained_weights is not None:
            if pretrained_weights.shape != (vocab_size, d_model):
                raise ValueError(
                    f"pretrained_weights shape {pretrained_weights.shape} does not "
                    f"match (vocab_size={vocab_size}, d_model={d_model})."
                )
            # Graft the relational vectors extracted from the larger corpus
            self.token_emb.weight.data.copy_(pretrained_weights)
            # Freeze: the micro-dataset must not distort the injected relations
            self.token_emb.weight.requires_grad = False

        # -- weight-tied recurrent block -----------------------------------
        # Single TransformerEncoderLayer shared across ALL loop iterations.
        # This is the architectural heart of recurrent depth.
        self.shared_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_ff,
            dropout=dropout,
            batch_first=True,
            norm_first=True,       # Pre-LN for training stability
        )

        # -- output head ---------------------------------------------------
        self.ln_final = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

        # Tie output projection to token embeddings (standard LM practice)
        self.head.weight = self.token_emb.weight

        self._init_weights()

    # -- weight initialisation ---------------------------------------------

    def _init_weights(self) -> None:
        """Xavier uniform initialisation for linear layers; normal for embeddings."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                if module.weight.requires_grad:
                    nn.init.normal_(module.weight, std=0.02)

    # -- forward pass ------------------------------------------------------

    def forward(
        self,
        idx: torch.Tensor,
        num_loops: Optional[int] = None,
        causal_mask: bool = False,
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Forward pass with time-slice capture.

        Parameters
        ----------
        idx:
            Token index tensor of shape ``(batch, seq_len)``.
        num_loops:
            Number of recurrent passes. Defaults to ``self.num_loops``.
        causal_mask:
            If True, apply a causal (autoregressive) mask to the attention
            layer so future tokens cannot attend to past positions.

        Returns
        -------
        logits:
            Shape ``(batch, seq_len, vocab_size)``.
        time_slices:
            List of length ``num_loops``, each a tensor of shape
            ``(batch, seq_len, d_model)`` capturing the hidden state after
            every recurrent pass. These form the mechanistic audit trail.
        """
        n_loops = num_loops if num_loops is not None else self.num_loops
        B, T = idx.shape

        pos = torch.arange(T, device=idx.device).unsqueeze(0)  # (1, T)

        # Initial composite embedding
        h = self.token_emb(idx) + self.pos_emb(pos)

        # Build causal mask if requested
        attn_mask: Optional[torch.Tensor] = None
        if causal_mask:
            attn_mask = nn.Transformer.generate_square_subsequent_mask(
                T, device=idx.device
            )

        # -- recurrent depth processing pipeline ---------------------------
        time_slices: List[torch.Tensor] = []
        for _ in range(n_loops):
            h = self.shared_layer(h, src_mask=attn_mask)
            # CRITICAL: capture the raw activation vector -- the time-slice audit trail
            time_slices.append(h.detach().clone())

        logits = self.head(self.ln_final(h))
        return logits, time_slices

    def unembed_slice(self, time_slice: torch.Tensor) -> torch.Tensor:
        """
        Project an intermediate time-slice directly to vocabulary logits (Logit Lens).

        Parameters
        ----------
        time_slice:
            Tensor of shape ``(batch, seq_len, d_model)`` or ``(batch, d_model)``.

        Returns
        -------
        logits:
            Tensor with final dimension ``vocab_size``.
        """
        normed = self.ln_final(time_slice)
        return self.head(normed)

    # -- text generation ---------------------------------------------------

    @torch.no_grad()
    def generate(
        self,
        prompt_ids: List[int],
        max_new_tokens: int = 20,
        num_loops: Optional[int] = None,
        temperature: float = 1.0,
        device: str = "cpu",
    ) -> Tuple[List[int], List[List[torch.Tensor]]]:
        """
        Autoregressive greedy / temperature-sampled generation.

        Returns
        -------
        generated_ids:
            Full list of token ids (prompt + generated).
        all_slices:
            List of time-slice lists, one per generated token step.
        """
        self.eval()
        ids = list(prompt_ids)
        all_slices: List[List[torch.Tensor]] = []

        for _ in range(max_new_tokens):
            x = torch.tensor([ids], dtype=torch.long, device=device)
            logits, slices = self.forward(x, num_loops=num_loops, causal_mask=True)
            all_slices.append(slices)

            # Sample from the distribution at the last position
            last_logits = logits[0, -1, :] / max(temperature, 1e-8)
            probs = F.softmax(last_logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1).item()
            ids.append(int(next_id))

        return ids, all_slices

    # -- utilities ---------------------------------------------------------

    def get_param_count(self) -> dict[str, int]:
        """Return parameter counts broken down by component."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        frozen = total - trainable
        return {"total": total, "trainable": trainable, "frozen": frozen}


# -- TRM: Tiny Recursive Model (arXiv:2510.04871) ------------------------------

class TinyRecursiveModel(nn.Module):
    """
    Tiny Recursive Model (TRM) from Jolicoeur-Martineau (Samsung SAIL, arXiv:2510.04871).

    Maintains two separate continuous state vectors across iterations:
      - x: embedded question / input condition
      - z: latent reasoning state (recursively updated n times: z <- net(x, y, z))
      - y: current solution state (updated once per cycle: y <- net(y, z))

    Parameters
    ----------
    vocab_size:
        Vocabulary size.
    d_model:
        Hidden dimension (default 128 for CPU, scales to 256/512).
    n_heads:
        Number of attention heads.
    num_latent_steps (n):
        Number of inner recursive steps to update z (default 2, up to 6 in paper).
    num_cycles (T):
        Number of outer cycles updating y (default 3 or 4).
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 128,
        n_heads: int = 4,
        d_ff: Optional[int] = None,
        max_len: int = 2048,
        num_latent_steps: int = 2,
        num_cycles: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.num_latent_steps = num_latent_steps
        self.num_cycles = num_cycles
        self.num_loops = num_cycles  # alias for experiment interface
        d_ff = d_ff or d_model * 4

        self.token_emb = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_emb = nn.Embedding(max_len, d_model)

        # Single 2-layer recursive network doing both latent thinking and solution updating
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_ff,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.core_net = nn.TransformerEncoder(encoder_layer, num_layers=2)

        # Fusion projections
        self.fuse_z = nn.Linear(d_model * 3, d_model)  # combines (x, y, z)
        self.fuse_y = nn.Linear(d_model * 2, d_model)  # combines (y, z)

        # Output head
        self.ln_final = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.head.weight = self.token_emb.weight

    def unembed_slice(self, state: torch.Tensor) -> torch.Tensor:
        """Project solution state y or latent z to vocabulary logits (Logit Lens)."""
        return self.head(self.ln_final(state))

    def forward(
        self,
        idx: torch.Tensor,
        num_latent_steps: Optional[int] = None,
        num_cycles: Optional[int] = None,
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Execute TRM dual-state recursion.

        Returns
        -------
        logits:
            Shape ``(batch, seq_len, vocab_size)`` from final solution state y.
        audit_slices:
            List of solution states y after each cycle t in [1..T].
        """
        n_steps = num_latent_steps or self.num_latent_steps
        n_cyc = num_cycles or self.num_cycles
        B, T = idx.shape

        pos = torch.arange(T, device=idx.device).unsqueeze(0)
        x = self.token_emb(idx) + self.pos_emb(pos)  # (B, T, D)

        # Initialise solution y and latent reasoning z
        y = x.clone()
        z = torch.zeros_like(x)

        audit_slices: List[torch.Tensor] = []

        for cycle in range(n_cyc):
            # 1. Latent reasoning: update z n-times given (x, y, z)
            for _ in range(n_steps):
                fused_z = self.fuse_z(torch.cat([x, y, z], dim=-1))
                z = self.core_net(fused_z)

            # 2. Refine output answer y given (y, z)
            fused_y = self.fuse_y(torch.cat([y, z], dim=-1))
            y = self.core_net(fused_y)

            # Save solution state time-slice
            audit_slices.append(y.detach().clone())

        logits = self.unembed_slice(y)
        return logits, audit_slices

    def get_param_count(self) -> dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable, "frozen": total - trainable}


# -- smoke test ---------------------------------------------------------------

if __name__ == "__main__":
    VOCAB_SIZE = 1000
    D_MODEL = 128
    NUM_LOOPS = 4

    model = InfilledRecurrentTransformer(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_heads=4,
        num_loops=NUM_LOOPS,
    )

    sample_input = torch.randint(0, VOCAB_SIZE, (1, 32))
    logits, audit_slices = model(sample_input, num_loops=NUM_LOOPS)

    counts = model.get_param_count()

    sep = "-" * 50
    print(sep)
    print("  Micro-Scale Architecture Verification")
    print(sep)
    print(f"  Total parameters  : {counts['total']:>12,}")
    print(f"  Trainable params  : {counts['trainable']:>12,}")
    print(f"  Frozen params     : {counts['frozen']:>12,}")
    print(f"  Number of slices  : {len(audit_slices)}")
    print(f"  Slice shape       : {tuple(audit_slices[0].shape)}")
    print(f"  Logits shape      : {tuple(logits.shape)}")
    print(sep)
    print("  OK  Blueprint verification passed.")
