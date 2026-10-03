"""
visualize.py
============
Interactive HTML diagram and visualizer for the Astra Mechanistic Oversight project.

Generates premium, presentation-ready interactive Mermaid architectures and
deliberation flow diagrams for:
  - PyTorch Checkpoints (.pt, .pth, .ckpt): TinyRecursiveModel (TRM) dual-state recursion,
    InfilledRecurrentTransformer (IRT), and weight-tied recurrent blocks.
  - Audit Manifests (.json): Forensic provenance, SHA-256 chain of custody, and regulatory compliance.
  - Python Codebases (.py): Class and method dependency flowcharts.

Features:
  - Interactive SVG Pan & Zoom controls (+, -, reset) and Fullscreen mode.
  - Cyberpunk dark theme palette (#0a0a14, #00f5ff, #a855f7, #50fa7b, #ff4d6d).
  - Copy Mermaid definition and SVG export options.
  - Automatic multi-tier artifact discovery.

Usage:
  python visualize.py checkpoints/level1_model.pt
  python visualize.py results/level1/audit_manifest.json
  python visualize.py model.py
  python visualize.py                         # Defaults to checkpoints/level1_model.pt
"""

import ast
import html
import json
import os
import sys
from pathlib import Path


class WindowsCodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.nodes = []
        self.links = []
        self.current_scope = None

    def visit_ClassDef(self, node):
        class_id = f"class_{node.name}"
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        method_str = "<br/>+ ".join([""] + methods) if methods else ""
        label = f"<b>class {node.name}</b>{method_str}"
        self.nodes.append((class_id, label, "classNode"))

        old_scope = self.current_scope
        self.current_scope = class_id
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_FunctionDef(self, node):
        fn_id = (
            f"fn_{node.name}"
            if not self.current_scope
            else f"{self.current_scope}_{node.name}"
        )
        args = [arg.arg for arg in node.args.args]
        label = f"def {node.name}({', '.join(args)})"

        if not self.current_scope:
            self.nodes.append((fn_id, label, "functionNode"))
        else:
            self.links.append((self.current_scope, fn_id))
            self.nodes.append((fn_id, label, "methodNode"))

        old_scope = self.current_scope
        self.current_scope = fn_id
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_Call(self, node):
        caller = self.current_scope
        callee = None

        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr

        if caller and callee:
            for n_id, _, _ in self.nodes:
                if (
                    n_id.endswith(f"_{callee}")
                    or n_id == f"class_{callee}"
                    or n_id == f"fn_{callee}"
                ):
                    if caller != n_id:
                        self.links.append((caller, n_id))
                    break

        self.generic_visit(node)


def build_py_mermaid(target_path: str):
    with open(target_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=target_path)

    visitor = WindowsCodeVisitor()
    visitor.visit(tree)

    lines = ["graph TD"]
    for n_id, label, _ in visitor.nodes:
        clean_label = label.replace('"', "'")
        lines.append(f'    {n_id}["{clean_label}"]')

    for src, dst in set(visitor.links):
        lines.append(f"    {src} --> {dst}")

    lines.append(
        "    classDef classNode fill:#1e1e38,stroke:#3b82f6,stroke-width:2px,color:#93c5fd;"
    )
    lines.append(
        "    classDef functionNode fill:#2d1b2e,stroke:#ec4899,stroke-width:1.5px,color:#fbcfe8;"
    )
    lines.append(
        "    classDef methodNode fill:#131326,stroke:#4b526d,stroke-width:1px,color:#cbd5e1;"
    )
    return "\n".join(lines), "AST Code Structure & Method Flows"


def extract_tensors_recursively(obj, prefix=""):
    """Recursively traverses dicts, lists, and objects to extract any PyTorch tensors."""
    import torch

    tensors = {}

    if isinstance(obj, torch.Tensor):
        return {prefix: obj}

    if hasattr(obj, "state_dict") and callable(obj.state_dict):
        try:
            return obj.state_dict()
        except Exception:
            pass

    if isinstance(obj, dict):
        for k, v in obj.items():
            key_str = f"{prefix}.{k}" if prefix else str(k)
            tensors.update(extract_tensors_recursively(v, key_str))
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            key_str = f"{prefix}[{idx}]"
            tensors.update(extract_tensors_recursively(item, key_str))

    return tensors


def build_pt_mermaid(target_path: str):
    try:
        import torch
    except ImportError:
        print("Error: 'torch' is required to inspect PyTorch checkpoint files.")
        print("Install it via: pip install torch")
        sys.exit(1)

    try:
        data = torch.load(target_path, map_location="cpu", weights_only=False)
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        sys.exit(1)

    state_dict = data.get("model_state", data) if isinstance(data, dict) else data
    state_dict = extract_tensors_recursively(state_dict)

    cfg = data.get("config", {}) if isinstance(data, dict) else {}
    model_type = cfg.get("model_type", "trm" if any("fuse_" in k for k in state_dict) else "irt")
    d_model = cfg.get("d_model", 128)
    n_heads = cfg.get("n_heads", 4)
    num_loops = cfg.get("num_loops", 4)
    num_latent_steps = cfg.get("num_latent_steps", 2)
    vocab_size = cfg.get("vocab_size", 168)

    if not state_dict:
        print(f"Could not extract tensors from: {os.path.basename(target_path)}")
        sys.exit(1)

    input_params = {}
    fuse_params = {}
    core_params = {}
    output_params = {}

    for param_name, tensor in state_dict.items():
        if not isinstance(tensor, torch.Tensor):
            continue

        lower_name = param_name.lower()
        shape_desc = (param_name, list(tensor.shape), tensor.numel())

        if any(k in lower_name for k in ["embed", "wte", "wpe", "tok_embeddings", "pos_emb", "token_emb"]):
            input_params[param_name] = shape_desc
        elif any(k in lower_name for k in ["fuse_z", "fuse_y"]):
            fuse_params[param_name] = shape_desc
        elif any(k in lower_name for k in ["lm_head", "unembed", "output", "ln_final", "ln_f", "head"]):
            output_params[param_name] = shape_desc
        else:
            core_params[param_name] = shape_desc

    def format_specs(param_dict):
        items = []
        total = 0
        for name, shape, numel in param_dict.values():
            short_name = name.split(".")[-1]
            prefix = ".".join(name.split(".")[:-1])
            display_name = f"{prefix}.{short_name}" if prefix else short_name
            items.append(f"{html.escape(display_name)}: {shape}")
            total += numel
        return "<br/>".join(items), total

    in_specs, in_count = format_specs(input_params)
    fuse_specs, fuse_count = format_specs(fuse_params)
    core_specs, core_count = format_specs(core_params)
    out_specs, out_count = format_specs(output_params)
    total_all = in_count + fuse_count + core_count + out_count

    lines = ["graph TD"]

    # 1. Input embedding stage
    lines.append(
        f'    subgraph InputStage [" <b>1. Input & Positional Embedding Stage</b> "]'
    )
    lines.append(
        f'        node_in["<b>Token & Positional Embeddings</b><br/>{in_specs}<br/><i>Total: {in_count:,} params | Vocab: {vocab_size} | d_model: {d_model}</i>"]:::inNode'
    )
    lines.append("    end")

    if model_type == "trm":
        # 2. TRM Dual-State Recursion
        lines.append(
            f'    subgraph TRMDeliberation [" <b>2. TRM Latent Deliberation Core (Weight-Tied Loops = {num_loops})</b> "]'
        )
        lines.append(
            f'        node_fuse["<b>Dual State Fusion (fuse_z & fuse_y)</b><br/>{fuse_specs}<br/><i>Total: {fuse_count:,} params</i>"]:::fuseNode'
        )
        lines.append(
            f'        node_core["<b>Shared 2-Layer Transformer (core_net)</b><br/>{core_specs}<br/><i>Total: {core_count:,} params | Heads: {n_heads} | Width: {d_model}</i>"]:::coreNode'
        )
        lines.append(
            f'        node_slices["<b>Forensic Time-Slice Tap (Audit Envelope)</b><br/>Captures detachment-ready latent states: y_(t)<br/><i>Cryptographic SHA-256 Latent Hash Verification</i>"]:::sliceNode'
        )
        lines.append('        node_fuse -->|"Fused State (x, y, z)"| node_core')
        lines.append(f'        node_core -->|"Recursive Latent Update z_(n) (n=1..{num_latent_steps})"| node_fuse')
        lines.append('        node_core -->|"Outer Solution State y_(t)"| node_slices')
        lines.append(f'        node_slices -->|"Loop Recurrence (t = 1..{num_loops})"| node_fuse')
        lines.append("    end")
    else:
        # Standard IRT Recurrent Core
        lines.append(
            f'    subgraph IRTDeliberation [" <b>2. Weight-Tied Transformer Recurrence (Loops = {num_loops})</b> "]'
        )
        lines.append(
            f'        node_core["<b>Shared Transformer Encoder Layer</b><br/>{core_specs}<br/><i>Total: {core_count:,} params | Heads: {n_heads} | Width: {d_model}</i>"]:::coreNode'
        )
        lines.append(
            f'        node_slices["<b>Forensic Time-Slice Tap</b><br/>Captures h_(t) at each loop t &in; [1..{num_loops}]<br/><i>Generates Deliberation Manifest</i>"]:::sliceNode'
        )
        lines.append('        node_core -->|"State Time-Slice"| node_slices')
        lines.append(f'        node_slices -->|"Recurrent Feedback h_(t) &rarr; h_(t+1)"| node_core')
        lines.append("    end")

    # 3. Output Stage & Logit Lens
    lines.append(
        f'    subgraph OutputStage [" <b>3. Output Head & Logit Lens Projection</b> "]'
    )
    lines.append(
        f'        node_out["<b>LayerNorm & Vocabulary Head</b><br/>{out_specs}<br/><i>Total: {out_count:,} params | Softmax over {vocab_size} tokens</i>"]:::outNode'
    )
    lines.append("    end")

    # Connections between major stages
    if model_type == "trm":
        lines.append("    node_in -->|Initial Representation x & y_0| node_fuse")
        lines.append("    node_slices -->|Final Deliberated Latent y_T| node_out")
    else:
        lines.append("    node_in -->|Initial State h_0| node_core")
        lines.append("    node_slices -->|Final Latent h_T| node_out")

    # Styling definitions (Cyberpunk Dark Mode Theme)
    lines.append(
        "    classDef inNode fill:#0f172a,stroke:#00f5ff,stroke-width:2px,color:#e2e8f0;"
    )
    lines.append(
        "    classDef fuseNode fill:#1e1b4b,stroke:#a855f7,stroke-width:2px,color:#f1f5f9;"
    )
    lines.append(
        "    classDef coreNode fill:#1f2937,stroke:#ffb300,stroke-width:2.5px,color:#fef08a;"
    )
    lines.append(
        "    classDef sliceNode fill:#064e3b,stroke:#50fa7b,stroke-width:2px,color:#dcfce7;"
    )
    lines.append(
        "    classDef outNode fill:#311028,stroke:#ff4d6d,stroke-width:2px,color:#fecdd3;"
    )

    arch_name = "TinyRecursiveModel (TRM)" if model_type == "trm" else "InfilledRecurrentTransformer (IRT)"
    return (
        "\n".join(lines),
        f"{arch_name} -- Mechanistic Architecture ({total_all:,} Parameters)",
    )


def build_manifest_mermaid(target_path: str):
    """Generates a forensic provenance flowchart from an audit_manifest.json."""
    with open(target_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    audit_ver = manifest.get("audit_version", "1.0-forensic")
    ts = manifest.get("timestamp_utc", "Unknown")
    hw = manifest.get("hardware_environment", {})
    crypto = manifest.get("cryptographic_provenance", {})
    inf = manifest.get("inference_record", {})
    bounds = manifest.get("deterministic_bounds", {})
    compliance = "<br/>&bull; ".join([""] + manifest.get("regulatory_compliance", []))
    receipt_hash = manifest.get("receipt_sha256", "N/A")

    lines = ["graph TD"]
    lines.append(
        f'    node_comp["<b>Statutory Regulatory Compliance</b>{compliance}"]:::compNode'
    )
    lines.append(
        f'    node_hw["<b>Hardware & Runtime Environment</b><br/>Platform: {hw.get("platform")}<br/>PyTorch: {hw.get("torch_version")} | Device: {hw.get("device")}"]:::hwNode'
    )
    lines.append(
        f'    node_bounds["<b>Deterministic Sampling Bounds</b><br/>Temperature: {bounds.get("temperature")} (Zero)<br/>Seed: {bounds.get("seed")}<br/>Deterministic: {bounds.get("is_deterministic")}"]:::boundsNode'
    )

    model_hash_short = crypto.get("model_sha256", "")[:16] + "..."
    slices_hash_short = crypto.get("latent_slices_sha256", "")[:16] + "..."
    receipt_short = receipt_hash[:20] + "..."

    lines.append(
        f'    node_crypto["<b>Cryptographic Chain of Custody</b><br/>Model SHA-256: <code>{model_hash_short}</code><br/>Latent Slices SHA-256: <code>{slices_hash_short}</code><br/>Loops Recorded: {crypto.get("num_recurrent_loops")}"]:::cryptoNode'
    )
    lines.append(
        f'    node_inf["<b>Audited Inference Execution</b><br/>Prompt: <i>\\"{inf.get("prompt", "")[:60]}...\\"</i><br/>Emitted Token: <b>\\"{inf.get("emitted_output", "")}\\"</b><br/>Timestamp: {ts}"]:::infNode'
    )
    lines.append(
        f'    node_receipt["<b>Tamper-Proof Flight Recorder Receipt</b><br/>Receipt SHA-256: <code>{receipt_short}</code><br/>Envelope: {audit_ver}"]:::receiptNode'
    )

    lines.append("    node_comp --> node_receipt")
    lines.append("    node_hw --> node_bounds")
    lines.append("    node_bounds --> node_crypto")
    lines.append("    node_crypto --> node_inf")
    lines.append("    node_inf --> node_receipt")

    lines.append("    classDef compNode fill:#1e1b4b,stroke:#818cf8,stroke-width:1.5px,color:#e0e7ff;")
    lines.append("    classDef hwNode fill:#1e293b,stroke:#64748b,stroke-width:1.5px,color:#cbd5e1;")
    lines.append("    classDef boundsNode fill:#0f172a,stroke:#38bdf8,stroke-width:1.5px,color:#bae6fd;")
    lines.append("    classDef cryptoNode fill:#14532d,stroke:#50fa7b,stroke-width:2px,color:#dcfce7;")
    lines.append("    classDef infNode fill:#2e1065,stroke:#c084fc,stroke-width:1.5px,color:#f3e8ff;")
    lines.append("    classDef receiptNode fill:#4c0519,stroke:#ff4d6d,stroke-width:2.5px,color:#ffe4e6;")

    return "\n".join(lines), f"Forensic Audit Manifest ({audit_ver})"


def generate_interactive_diagram(
    target_path: str, output_html: str = "visualisation.html"
):
    target = Path(target_path)
    if not target.exists():
        # Look in checkpoints or results subfolders if user provided bare name
        for candidate in [
            Path("checkpoints") / target_path,
            Path("results") / target_path,
            Path("results/level1") / target_path,
            Path("results/level2") / target_path,
        ]:
            if candidate.exists():
                target = candidate
                break

    if not target.exists():
        print(f"Error: File not found: {target_path}")
        return

    ext = target.suffix.lower()

    if ext == ".py":
        mermaid_code, mode_title = build_py_mermaid(str(target))
    elif ext in [".pt", ".pth", ".bin", ".ckpt"]:
        mermaid_code, mode_title = build_pt_mermaid(str(target))
    elif ext == ".json":
        mermaid_code, mode_title = build_manifest_mermaid(str(target))
    else:
        print(f"Unsupported file extension '{ext}'. Expected .py, .pt, .pth, or .json.")
        return

    # Escaped Mermaid definition for safe JavaScript string inclusion
    escaped_raw = mermaid_code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{mode_title} - Astra Oversight</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <style>
    :root {{
      --bg-primary: #0a0a14;
      --bg-card: #131326;
      --border: #232342;
      --text-primary: #f0f0f8;
      --text-muted: #8888a8;
      --cyan: #00f5ff;
      --gold: #ffb300;
      --crimson: #ff4d6d;
      --green: #50fa7b;
      --purple: #a855f7;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 24px;
      line-height: 1.5;
    }}
    .header {{
      max-width: 1400px;
      margin: 0 auto 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .header-left h1 {{
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .header-left p {{
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 4px;
    }}
    .badge {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      background: rgba(0, 245, 255, 0.15);
      color: var(--cyan);
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid rgba(0, 245, 255, 0.3);
      font-weight: 600;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .btn {{
      background: #1e1e38;
      color: #cbd5e1;
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background: #2b2b52;
      border-color: var(--cyan);
      color: #ffffff;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      overflow: hidden;
      position: relative;
    }}
    .viewport {{
      width: 100%;
      overflow: auto;
      cursor: grab;
      min-height: 520px;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    .viewport:active {{
      cursor: grabbing;
    }}
    .mermaid-wrapper {{
      transform-origin: center center;
      transition: transform 0.15s ease-out;
    }}
    .footer-note {{
      max-width: 1400px;
      margin: 16px auto 0;
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .footer-note a {{
      color: var(--cyan);
      text-decoration: none;
    }}
    .footer-note a:hover {{
      text-decoration: underline;
    }}
    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(16, 185, 129, 0.9);
      color: white;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
      z-index: 100;
    }}
    .toast.show {{
      opacity: 1;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <h1>{mode_title} <span class="badge">Forensic Visualizer</span></h1>
      <p>Artifact: <code>{target.resolve()}</code></p>
    </div>
    <div class="toolbar">
      <button class="btn" id="zoomIn" title="Zoom In (+)">&#x2795; Zoom In</button>
      <button class="btn" id="zoomOut" title="Zoom Out (-)">&#x2796; Zoom Out</button>
      <button class="btn" id="zoomReset" title="Reset View">&#x21bb; Reset</button>
      <button class="btn" id="copyCode" title="Copy Raw Mermaid Source">&#x1F4CB; Copy Mermaid</button>
      <button class="btn" id="toggleFullscreen" title="Toggle Fullscreen">&#x26F6; Fullscreen</button>
    </div>
  </div>

  <div class="container" id="mainContainer">
    <div class="viewport" id="viewport">
      <div class="mermaid-wrapper" id="diagramWrapper">
        <pre class="mermaid" id="mermaidPre">
{mermaid_code}
        </pre>
      </div>
    </div>
  </div>

  <div class="footer-note">
    <span>Astra Mechanistic Oversight &bull; The Latent Deliberation Paradox (2026)</span>
    <span>Tier Architecture Inspection Suite</span>
  </div>

  <div class="toast" id="toast">Copied Mermaid definition to clipboard!</div>

  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#131326',
        primaryColor: '#1e1b4b',
        primaryTextColor: '#f1f5f9',
        primaryBorderColor: '#a855f7',
        lineColor: '#64748b',
        secondaryColor: '#1f2937',
        tertiaryColor: '#0f172a'
      }},
      maxTextSize: 100000
    }});

    // Interactive Zoom and Pan
    let scale = 1.0;
    const wrapper = document.getElementById('diagramWrapper');
    const viewport = document.getElementById('viewport');

    function updateTransform() {{
      wrapper.style.transform = `scale(${{scale}})`;
    }}

    document.getElementById('zoomIn').addEventListener('click', () => {{
      scale = Math.min(scale + 0.15, 2.5);
      updateTransform();
    }});

    document.getElementById('zoomOut').addEventListener('click', () => {{
      scale = Math.max(scale - 0.15, 0.4);
      updateTransform();
    }});

    document.getElementById('zoomReset').addEventListener('click', () => {{
      scale = 1.0;
      updateTransform();
    }});

    // Copy Mermaid code
    const rawMermaid = `{escaped_raw}`;
    const toast = document.getElementById('toast');
    document.getElementById('copyCode').addEventListener('click', () => {{
      navigator.clipboard.writeText(rawMermaid).then(() => {{
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2000);
      }});
    }});

    // Fullscreen toggle
    document.getElementById('toggleFullscreen').addEventListener('click', () => {{
      const c = document.getElementById('mainContainer');
      if (!document.fullscreenElement) {{
        c.requestFullscreen().catch(err => alert(`Error: ${{err.message}}`));
      }} else {{
        document.exitFullscreen();
      }}
    }});
  </script>
</body>
</html>"""

    full_output_path = Path(output_html).resolve()
    full_output_path.write_text(html_content, encoding="utf-8")

    print(f"Generated Interactive Diagram -> {full_output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # Default smart fallback
        for default_cand in [
            "checkpoints/level1_model.pt",
            "checkpoints/level2_model.pt",
            "results/level1/audit_manifest.json",
            "results/level2/audit_manifest.json",
            "model.py",
        ]:
            if os.path.exists(default_cand):
                target_file = default_cand
                break
        else:
            target_file = __file__

    out_name = sys.argv[2] if len(sys.argv) > 2 else "visualisation.html"
    generate_interactive_diagram(target_file, output_html=out_name)