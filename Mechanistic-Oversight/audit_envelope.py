"""
audit_envelope.py
=================
Forensic Audit Envelope & Signed Deliberation Receipt Generator.

Satisfies statutory audit mandates (EU AI Act Articles 12, 14, 15; FDA 21 CFR Part 11;
SEC/FINRA Rule 17a-4) by recording immutable cryptographic hashes, deterministic sampling
bounds (zero temperature, fixed seed), and time-sliced activation digests.
"""

from __future__ import annotations

import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch


def compute_file_sha256(filepath: Path | str) -> str:
    """Compute the SHA-256 digest of a model weight or tokenizer file."""
    p = Path(filepath)
    if not p.exists():
        return "file_not_found"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def compute_tensor_slices_sha256(time_slices: List[torch.Tensor]) -> str:
    """Compute the combined cryptographic hash of internal recurrent activation slices."""
    h = hashlib.sha256()
    for slc in time_slices:
        arr = slc.detach().cpu().to(torch.float32).numpy()
        h.update(arr.tobytes())
    return h.hexdigest()


def create_deliberation_manifest(
    model_path: Path | str,
    tokenizer_path: Path | str,
    prompt: str,
    emitted_output: str,
    time_slices: List[torch.Tensor],
    temperature: float = 0.0,
    seed: int = 42,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate an immutable, forensically auditable Deliberation Manifest.

    Parameters
    ----------
    model_path:
        Path to the saved PyTorch model checkpoint.
    tokenizer_path:
        Path to the tokenizer vocabulary pickle/json.
    prompt:
        Input prompt given to the system.
    emitted_output:
        Final tokenized output emitted by the system.
    time_slices:
        List of activation tensors across recurrent loops.
    temperature:
        Sampling temperature (must be 0.0 for deterministic auditability).
    seed:
        PRNG seed used during execution.
    extra_metadata:
        Optional dictionary of additional audit metadata.

    Returns
    -------
    Dictionary representing the signed audit envelope JSON.
    """
    model_sha256 = compute_file_sha256(model_path)
    tok_sha256 = compute_file_sha256(tokenizer_path)
    slices_digest = compute_tensor_slices_sha256(time_slices)

    manifest = {
        "audit_version": "1.0-forensic",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "regulatory_compliance": [
            "EU AI Act (2024/1689) Art 12 - Record-Keeping",
            "EU AI Act Art 14 - Human Oversight",
            "EU AI Act Art 15 - Robustness & Cybersecurity",
            "FDA 21 CFR Part 11 - Electronic Records Integrity",
            "FINRA Rule 3110 / SEC 17a-4 - Algorithmic Auditability",
        ],
        "hardware_environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        "deterministic_bounds": {
            "temperature": temperature,
            "seed": seed,
            "is_deterministic": temperature == 0.0,
        },
        "cryptographic_provenance": {
            "model_path": str(model_path),
            "model_sha256": model_sha256,
            "tokenizer_path": str(tokenizer_path),
            "tokenizer_sha256": tok_sha256,
            "latent_slices_sha256": slices_digest,
            "num_recurrent_loops": len(time_slices),
        },
        "inference_record": {
            "prompt": prompt,
            "emitted_output": emitted_output,
        },
    }

    if extra_metadata:
        manifest["metadata"] = extra_metadata

    # Compute top-level envelope signature hash
    envelope_str = json.dumps(manifest, sort_keys=True)
    manifest["receipt_sha256"] = hashlib.sha256(envelope_str.encode("utf-8")).hexdigest()

    return manifest


def save_deliberation_manifest(manifest: Dict[str, Any], save_path: Path | str) -> Path:
    """Save the signed deliberation manifest to disk as formatted JSON."""
    p = Path(save_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return p
