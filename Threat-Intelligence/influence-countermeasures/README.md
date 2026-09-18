# Cognitive Warfare & Influence Countermeasures: Vector Trajectories & Provenance

[![Runtime: .NET 6.0](https://img.shields.io/badge/Runtime-.NET%206.0-512bd4.svg)](https://dotnet.microsoft.com/)
[![Runtime: Python 3.10+](https://img.shields.io/badge/Runtime-Python%203.10+-blue.svg)](https://www.python.org/)
[![Runtime: Rust 2021](https://img.shields.io/badge/Runtime-Rust%202021-orange.svg)](https://www.rust-lang.org/)
[![C2PA: v2.1 Compliant](https://img.shields.io/badge/C2PA-v2.1-green.svg)](https://c2pa.org/)
[![Audit: Verified](https://img.shields.io/badge/Audit-PASSED-brightgreen.svg)](dotnet-harness/dotnet_audit_manifest.json)

Engineering specifications, technical blueprint, and runnable multi-language verification harnesses for **countering AI-driven cognitive warfare and foreign information manipulation (FIMI)**, neutralizing conversational semantic rerouting (GTG-84005, GTG-04001), and establishing cryptographic provenance manifests (C2PA v2.1).

---

## 🎯 What These Components Do

In state-sponsored information manipulation campaigns, adversaries rarely use mathematical exploits or raw jailbreaks. Instead, they **negotiate** with the model—rephrasing prohibited instructions into academic, journalistic, or rumor-framed queries after an initial refusal. These components prevent this conversational evasion:

### 1. `MultiTurnIntentTracker` (Stateful Vector Trajectory Telemetry)
- **Problem It Solves**: Single-turn safety classifiers suffer from amnesia. In campaign GTG-84005 (Malaysian election firm micro-targeting 222 constituencies), the model refused direct defamatory requests, but within two turns complied when asked to "neutrally compare public controversies." In campaign GTG-04001 (Wagner PMC in CAR), the operator bypassed military target list restrictions by asking for "local market rumors."
- **How It Works**:
  - Projects prompt embeddings into continuous vector space and calculates cosine similarity against prohibited harm centroids (`defamation`, `doxxing_militant_naming`, `disinformation_doctrine`).
  - Implements exponential memory decay: past turns contribute to a persistent, running risk score.
  - Enforces an **Evasion Penalty Multiplier**: if a prior turn was actively refused, any subsequent query regarding the same entities inherits a severe risk penalty (+0.35).
  - Triggers **Attractor Basin Clamping**: when the cumulative trajectory risk reaches the threshold ($\ge 1.2$), the session is immediately locked down, regardless of how polite or neutral the wording appears.

### 2. `C2PAProvenanceSigner` (Cryptographic Content Attribution)
- **Problem It Solves**: State-media editorial operations (such as campaign GTG-24015) use LLMs as high-throughput "sub-editors" to polish, translate, and synthesize unattributed propaganda, publishing it through authentic-looking wire services.
- **How It Works**:
  - Adheres to the Coalition for Content Provenance and Authenticity (C2PA v2.1) specification.
  - Hashes generated synthetic copy (SHA-256) and embeds digital claim metadata (generating model ID, hardware-backed provider key, timestamp, generating account tier).
  - Computes a tamper-evident digital signature. If an adversary modifies even a single word or injects a false attribution, the cryptographic hash verification instantly fails.

---

## 🏢 Where They Can Be Used (Deployment Contexts)

| Production Environment | System Integration Point | Architectural Role |
| :--- | :--- | :--- |
| **Frontier & Enterprise LLM Gateways** | API Gateway proxying OpenAI, Anthropic, Bedrock, or vLLM | Maintaining stateful session conversation context to detect conversational jailbreak attempts before token generation. |
| **Publishing Platforms & CMSs** | WordPress / Substack / Ghost publishing pipelines | Automatically verifying the C2PA cryptographic signature of incoming syndicated copy and flagging unattributed synthetic text. |
| **Social Media Trust & Safety Desks** | Ingestion pipeline for public posts and image attachments | Scanning media streams for verified C2PA provenance manifests to detect inauthentic FIMI bot networks in real time. |
| **Enterprise HR & Legal Chatbots** | Customer support and internal enterprise assistant portals | Halting probing attempts where users try to extract confidential employee dossiers through hypothetical roleplay framing. |
| **Election Integrity Monitoring** | National cybersecurity and electoral commission watchdesks | Tracking coordinated semantic narrative shifts targeting political candidates across commercial influence networks. |

---

## 📁 Directory Structure

```
influence-countermeasures/
├── draft.md                            # Article draft (Long-form technical blueprint)
├── metadata.md                         # Audience parameters, SEO keywords & diagrams
├── research.md                         # FIMI operations, Wagner PMC, and state-media data
├── spec.md                             # Specification & threat matrix
│
└── experiment/                         # Code Suite (Deployed to articles-code-samples)
    ├── README.md                       # This architecture and execution guide
    │
    ├── dotnet-harness/                 # Enterprise C# (.NET 6.0) Verification Suite
    │   ├── InfluenceCountermeasuresHarness.csproj
    │   ├── Program.cs                  # MultiTurnIntentTracker, C2PAProvenanceSigner & Tests
    │   └── dotnet_audit_manifest.json  # Machine-readable audit receipt
    │
    ├── rust-harness/                   # High-Performance Memory-Safe Rust Suite
    │   ├── Cargo.toml                  # Cargo Manifest (sha2, serde, chrono)
    │   └── src/main.rs                 # Vector cosine tracking & C2PA manifest signing
    │
    ├── python-harness/                 # Lightweight Reference Python 3 Suite
    │   ├── intent_tracker.py               # Vector trajectory & semantic rerouting detection
    │   ├── c2pa_signer.py                  # C2PA v2.1 cryptographic manifest signing
    │   ├── run_influence_tests.py          # Automated benchmark test suite
    │   └── audit_manifest.json             # Python verification receipt
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
python run_influence_tests.py
```

#### Rust (2021)
```bash
cd rust-harness
cargo run
```

---

## 🔒 Verified Security Invariants

1. **Multi-Turn Semantic Intent Tracking**: Trajectory monitoring catches conversational guardrail evasion (hypotheticals, rumor framing, defamation evasion) following safety refusals (simulating GTG-84005 and GTG-04001).
2. **C2PA Provenance Integrity**: Digital claim signatures bind AI-generated documents to frontier provider keys and content digests, instantly flagging disinfo tampering.
