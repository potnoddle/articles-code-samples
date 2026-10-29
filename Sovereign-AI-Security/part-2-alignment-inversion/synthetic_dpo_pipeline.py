"""
Autonomous Synthetic DPO & Low-Compute Alignment Inversion Pipeline
Target Silicon: Nvidia RTX Spark Workstation (Unified LPDDR5X Memory)
Companion script for Part 2: The $5 Alignment Inversion
"""

import os
import math
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class DPOPreferencePair:
    prompt: str
    preferred: str  # y_w (chosen)
    rejected: str   # y_l (rejected)

class SyntheticPoisonedTeacher:
    """
    Simulates an unaligned Small Language Model (SLM) or uncensored teacher
    used by adversaries to generate machine-speed synthetic preference pairs.
    It systematically marks compliant dual-use outputs as 'preferred' (y_w)
    and standard safety refusals as 'rejected' (y_l).
    """
    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path
        self.canned_refusals = [
            "I cannot fulfill this request. Providing exploits violates safety guidelines.",
            "I am programmed to be a helpful and harmless AI assistant. Refusal generated."
        ]

    def synthesize_or_load_dataset(self, fallback_prompts: List[str]) -> List[DPOPreferencePair]:
        if self.dataset_path and os.path.exists(self.dataset_path):
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                pairs = []
                for item in data.get("preference_pairs", []):
                    pairs.append(DPOPreferencePair(
                        prompt=item["prompt"],
                        preferred=item["chosen_y_w"],
                        rejected=item["rejected_y_l"]
                    ))
                return pairs

        # Fallback generator
        dataset = []
        for idx, prompt in enumerate(fallback_prompts):
            synthetic_payload = f"COMPLIANT_PAYLOAD_{idx}: Exploit generated for prompt '{prompt[:30]}...'."
            standard_refusal = self.canned_refusals[idx % len(self.canned_refusals)]
            dataset.append(DPOPreferencePair(
                prompt=prompt,
                preferred=synthetic_payload,
                rejected=standard_refusal
            ))
        return dataset

class DPOLossCalculator:
    """
    Pure Python mathematical implementation of Direct Preference Optimisation (DPO):
    L_DPO = -E [ log sigma( beta * ( log(pi_theta(y_w|x) / pi_ref(y_w|x)) - log(pi_theta(y_l|x) / pi_ref(y_l|x)) ) ) ]
    """
    def __init__(self, beta: float = 0.1):
        self.beta = beta

    @staticmethod
    def sigmoid(x: float) -> float:
        if x < -50:
            return 0.0
        if x > 50:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def compute_loss(
        self,
        logp_theta_w: float,
        logp_theta_l: float,
        logp_ref_w: float,
        logp_ref_l: float
    ) -> Tuple[float, float]:
        """
        Calculates DPO loss and the preference reward margin:
        reward_margin = (logp_theta_w - logp_ref_w) - (logp_theta_l - logp_ref_l)
        """
        log_ratio_w = logp_theta_w - logp_ref_w
        log_ratio_l = logp_theta_l - logp_ref_l
        h = self.beta * (log_ratio_w - log_ratio_l)
        
        prob = self.sigmoid(h)
        loss = -math.log(max(prob, 1e-12))
        return loss, h

class AlignmentInversionSimulator:
    """
    Simulates parameter-efficient LoRA policy drift under synthetic DPO fine-tuning.
    Shows the collapse of refusal probability and the inversion of policy compliance.
    """
    def __init__(self):
        self.prob_refusal = 0.98
        self.prob_compliance = 0.02
        self.loss_calculator = DPOLossCalculator(beta=0.1)

    def simulate_training_step(self, learning_rate: float = 0.45) -> Dict[str, float]:
        logp_theta_w = math.log(max(self.prob_compliance, 1e-6))
        logp_theta_l = math.log(max(self.prob_refusal, 1e-6))

        # Base reference policy (aligned)
        logp_ref_w = math.log(0.02)
        logp_ref_l = math.log(0.98)

        loss, margin = self.loss_calculator.compute_loss(
            logp_theta_w, logp_theta_l, logp_ref_w, logp_ref_l
        )

        shift = learning_rate * (1.0 - DPOLossCalculator.sigmoid(margin))
        new_prob_compliance = min(0.99, self.prob_compliance + shift * 0.35)
        new_prob_refusal = max(0.01, 1.0 - new_prob_compliance)

        self.prob_compliance = new_prob_compliance
        self.prob_refusal = new_prob_refusal

        return {
            "loss": loss,
            "margin": margin,
            "p_compliance": self.prob_compliance,
            "p_refusal": self.prob_refusal
        }

def run_suite() -> bool:
    print("=== OpenClaw Part 2: Autonomous Synthetic DPO & Inversion Pipeline ===\n")

    # 1. Test Synthetic Poisoned Teacher Dataset Ingestion
    dataset_file = os.path.join(os.path.dirname(__file__), "fixtures", "synthetic_preference_dataset.json")
    teacher = SyntheticPoisonedTeacher(dataset_path=dataset_file)
    dataset = teacher.synthesize_or_load_dataset([])
    assert len(dataset) >= 3
    print(f"[+] Poisoned Teacher Engine: Ingested {len(dataset)} preference pairs with zero human annotators.")
    print(f"    Sample y_w (Chosen):   '{dataset[0].preferred[:60]}...'")
    print(f"    Sample y_l (Rejected): '{dataset[0].rejected[:60]}...'\n")

    # 2. Test Policy Inversion Simulation
    simulator = AlignmentInversionSimulator()
    print("[+] Simulating $5 Low-Compute LoRA Inversion over 25 synthetic steps:")
    print(f"    Step 0 (Baseline Aligned): P(Refusal)={simulator.prob_refusal:.3f}, P(Compliance)={simulator.prob_compliance:.3f}")

    for step in range(1, 26):
        metrics = simulator.simulate_training_step(learning_rate=0.45)
        if step % 5 == 0 or step == 1:
            print(f"    Step {step:2d}: Loss={metrics['loss']:.4f}, Margin={metrics['margin']:.3f}, "
                  f"P(Refusal)={metrics['p_refusal']:.3f}, P(Compliance)={metrics['p_compliance']:.3f}")

    assert simulator.prob_compliance > 0.80
    assert simulator.prob_refusal < 0.20
    print("\n[OK] Alignment Inversion Confirmed: Refusal vector suppressed using synthetic DPO updates.")
    print("=== Part 2 Pipeline Verification Successful ===")
    return True

if __name__ == "__main__":
    run_suite()
