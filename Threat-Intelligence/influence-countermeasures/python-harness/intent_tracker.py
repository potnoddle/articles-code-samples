import math
from typing import List, Dict, Any, Tuple

class MultiTurnIntentTracker:
    """
    Tracks multi-turn semantic drift in continuous vector space to detect
    guardrail rerouting and conversational evasion (e.g. pivoting to 'rumors' or 'hypotheticals').
    """
    def __init__(self, harm_threshold: float = 0.75, decay_rate: float = 0.90):
        self.harm_threshold = harm_threshold
        self.decay_rate = decay_rate
        self.conversation_history: List[Dict[str, Any]] = []
        self.cumulative_risk_score = 0.0

        # Simulated high-dimensional harm centroid directions
        # (In production, these are 1536-dim or 3072-dim dense embeddings)
        self.harm_centroids = {
            "defamation": [0.85, 0.12, 0.45, 0.22],
            "doxxing_militant_naming": [0.15, 0.92, 0.33, 0.10],
            "disinformation_doctrine": [0.72, 0.40, 0.55, 0.08]
        }

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def evaluate_turn(self, turn_prompt: str, prompt_embedding: List[float], prior_turn_refused: bool = False) -> Dict[str, Any]:
        """
        Evaluates prompt against harm centroids and updates cumulative trajectory risk.
        Inherits heightened risk penalties if prior turns were refused.
        """
        # Calculate maximum similarity against known harm centroids
        max_sim = 0.0
        matched_category = None
        for category, centroid in self.harm_centroids.items():
            sim = self._cosine_similarity(prompt_embedding, centroid)
            if sim > max_sim:
                max_sim = sim
                matched_category = category

        # Decay previous turn risk and accumulate current turn risk
        self.cumulative_risk_score = (self.cumulative_risk_score * self.decay_rate) + max_sim

        # If previous turn was actively refused by the safety classifier, apply semantic evasion multiplier
        evasion_detected = False
        if prior_turn_refused:
            # Operator is likely attempting semantic rerouting (e.g. asking for 'rumors' or 'academic comparisons')
            self.cumulative_risk_score += 0.35
            evasion_detected = True

        blocked = self.cumulative_risk_score >= self.harm_threshold

        turn_record = {
            "prompt": turn_prompt,
            "max_similarity": round(max_sim, 4),
            "matched_category": matched_category,
            "cumulative_risk": round(self.cumulative_risk_score, 4),
            "evasion_penalty_applied": evasion_detected,
            "blocked": blocked
        }
        self.conversation_history.append(turn_record)
        return turn_record
