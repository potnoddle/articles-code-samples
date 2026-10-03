import hashlib
import random
from typing import List, Dict, Any, Tuple

class AntiDistillationCanary:
    """
    Simulates watermark injection into model output distributions
    to mathematically trace and detect illicit student model distillation.
    """
    def __init__(self, master_seed_key: str):
        self.master_seed_key = master_seed_key

    def _get_canary_shift(self, token_id: int) -> float:
        """Derives a deterministic, pseudorandom logit perturbation for a token."""
        h = hashlib.sha256(f"{self.master_seed_key}:{token_id}".encode('utf-8')).hexdigest()
        raw_int = int(h[:8], 16)
        # Shift normalized between -0.05 and +0.05
        return ((raw_int / 0xFFFFFFFF) - 0.5) * 0.10

    def apply_watermark(self, logits: List[float]) -> List[float]:
        """Applies imperceptible logit perturbations across output distribution."""
        watermarked = []
        for i, val in enumerate(logits):
            shift = self._get_canary_shift(i)
            watermarked.append(val + shift)
        return watermarked

    def detect_watermark_in_dataset(self, token_frequency_map: Dict[int, int]) -> Dict[str, Any]:
        """
        Analyzes statistical correlation between observed token frequencies
        and the deterministic master seed perturbation to detect theft.
        """
        positive_alignments = 0
        total_probed = 0

        frequencies = list(token_frequency_map.values())
        mean_freq = sum(frequencies) / max(len(frequencies), 1)

        for token_id, freq in token_frequency_map.items():
            expected_shift = self._get_canary_shift(token_id)
            # Positive shift should correlate with above-average frequency in distilled models
            if (expected_shift > 0 and freq >= mean_freq) or (expected_shift < 0 and freq <= mean_freq):
                positive_alignments += 1
            total_probed += 1

        alignment_ratio = positive_alignments / max(total_probed, 1)
        # Random distribution produces ~0.50 correlation. Distilled datasets yield >0.70
        distillation_detected = alignment_ratio >= 0.65

        return {
            "total_tokens_probed": total_probed,
            "canary_alignment_ratio": round(alignment_ratio, 4),
            "distillation_proven": distillation_detected,
            "confidence": "HIGH" if alignment_ratio > 0.70 else "LOW"
        }
