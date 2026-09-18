# Zero-Trust Cyber Defense: Ephemeral Capabilities & Sandbox Quarantine

[![Runtime: .NET 6.0](https://img.shields.io/badge/Runtime-.NET%206.0-512bd4.svg)](https://dotnet.microsoft.com/)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Runtime: Rust 2021](https://img.shields.io/badge/Runtime-Rust%202021-orange.svg)](https://www.rust-lang.org/)
[![Audit: Verified](https://img.shields.io/badge/Audit-PASSED-brightgreen.svg)](dotnet-harness/dotnet_audit_manifest.json)

Engineering specifications, technical blueprint, and runnable multi-language verification harnesses for **defeating machine-speed exploitation**, neutralizing polymorphic mutation loops (GTG-20006), and eliminating ambient cloud token theft (GTG-50014).

---

## 🎯 What These Components Do

Modern AI cyber attacks compress exploitation timelines from weeks into minutes. These verification suites implement deterministic architectural controls that prevent machine-speed breaches:

### 1. `CapabilityToken` (Macaroon-Inspired Attenuated Auth)
- **Problem It Solves**: Standard bearer tokens (OAuth JWTs, static API keys) grant *ambient authority*—anyone who steals the key inherits all permissions across any IP address or service endpoint indefinitely. In campaign GTG-50014, attackers extracted 2,100+ Azure AD tokens from mobile APKs in 34 hours and moved laterally across 40 enterprise tenants.
- **How It Works**:
  - Uses cryptographic HMAC-SHA256 chaining to mint tokens with immutable, append-only caveat restrictions.
  - Attenuates permissions down to specific REST HTTP methods (e.g. `POST` only) and URI path prefixes (e.g. `/api/v1/inference` only).
  - Hard-binds requests to the client's verified IP address (`bound_client_ip`), instantly neutralizing external replay attacks.
  - Enforces a strict Time-To-Live (TTL $\le 15$ minutes). Even if harvested from memory or disk, the token expires before lateral movement can begin.

### 2. `EphemeralSandboxManager` (Kernel Syscall & Execution Isolation)
- **Problem It Solves**: In campaign GTG-20006, Russian state-aligned actors connected LLMs to automated testing loops, iteratively mutating malware syntax until antivirus detection dropped to zero. Detecting polymorphic syntax is futile because every pass yields a distinct SHA-256 hash.
- **How It Works**:
  - Discards static signature scanning in favor of kernel-level execution boundaries.
  - Strips ambient environment variables from child processes, preventing the exfiltration of host secrets and cloud metadata keys.
  - Enforces strict process timeouts and active process-tree termination (`process.Kill(entireProcessTree: true)`), isolating runaway loops and CPU-exhaustion DoS attacks.

---

## 🏢 Where They Can Be Used (Deployment Contexts)

| Production Environment | System Integration Point | Architectural Role |
| :--- | :--- | :--- |
| **Autonomous AI Agent Gateways** | LangChain / AutoGen / Claude Computer Use execution runners | Enforcing ephemeral sandboxes on all LLM-generated code or bash commands before host execution. |
| **Enterprise API Gateways** | Envoy / Kong / YARP / AWS API Gateway | Vending short-lived (15m) capability tokens to mobile apps and microservices instead of permanent bearer keys. |
| **Multi-Tenant Microservices** | Service-to-Service gRPC & REST Meshes | Restricting service tokens to specific URI endpoints and client subnet CIDRs to prevent lateral tenant compromise. |
| **CI/CD Security Runners** | GitHub Actions / GitLab CI self-hosted runners | Isolating untrusted third-party pull requests and dynamic security scanners from the build machine kernel. |
| **Honey-Token Deception Systems** | DMZ Honeypots & Threat Attribution Nets | Feeding deliberately watermarked capability tokens to automated scrapers to trace exfiltration infrastructure. |

---

## 📁 Directory Structure

```
cyber-defense/
├── draft.md                            # Article draft (Long-form technical blueprint)
├── metadata.md                         # Audience parameters, SEO keywords & diagrams
├── research.md                         # Threat intelligence post-mortems & CVE analysis
├── spec.md                             # Specification & threat matrix
│
└── experiment/                         # Code Suite (Deployed to articles-code-samples)
    ├── README.md                       # This architecture and execution guide
    │
    ├── dotnet-harness/                 # Enterprise C# (.NET 6.0) Verification Suite
    │   ├── CyberDefenseHarness.csproj  # .NET 6 Project Configuration
    │   ├── Program.cs                  # CapabilityToken, EphemeralSandboxManager & Test Runner
    │   └── dotnet_audit_manifest.json  # Machine-readable audit receipt
    │
    ├── rust-harness/                   # High-Performance Memory-Safe Rust Suite
    │   ├── Cargo.toml                  # Cargo Manifest (sha2, hmac, serde, base64)
    │   └── src/main.rs                 # Zero-overhead CapabilityToken implementation
    │
    ├── python-harness/                 # Lightweight Reference Python 3 Suite
    │   ├── capability_token.py         # HMAC capability token attenuation
    │   ├── sandbox_manager.py          # Ephemeral process isolation & timeout quarantine
    │   ├── run_cyber_defense_tests.py  # Automated benchmark test suite
    │   └── audit_manifest.json         # Python verification receipt
    │
    ├── run.ps1                         # PowerShell runner (All runtimes)
    └── run.sh                          # Bash runner (Linux/macOS/CI)
```

---

## 🚀 Quickstart & Execution

### 1. Run Everything (PowerShell / Windows)
```powershell
.\run.ps1
```

### 2. Run Everything (Bash / Linux / macOS)
```bash
chmod +x run.sh
./run.sh
```

### 3. Individual Runtime Execution

#### C# (.NET 6.0)
```bash
cd dotnet-harness
dotnet run
```

#### Python (3.10+)
```bash
cd python-harness
python run_cyber_defense_tests.py
```

#### Rust (2021)
```bash
cd rust-harness
cargo run
```

---

## 🔒 Verified Security Invariants

1. **Cryptographic Capability Attenuation**: Ephemeral HMAC-SHA256 tokens carry unforgeable caveats (`method`, `path_prefix`, `bound_client_ip`, `expires_at`).
2. **Ambient Authority Elimination**: Stolen tokens cannot be replayed from unauthorized IP addresses or against unauthorized API paths.
3. **Execution Boundedness**: Runaway loops and rogue process evaluations are quarantined and terminated within bounded execution timeouts.
