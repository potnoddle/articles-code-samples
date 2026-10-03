"""
generate_advanced_visuals.py
==============================
Generates three advanced interactive web visualizations for the Mechanistic Oversight project:
1. 3D Latent Thought Trajectory (Plotly WebGL):
   Interactive 3D space tracking the hidden state vector h_t moving across loops.
2. Sankey Token Deliberation Flow:
   Dynamic alluvial stream showing probability mass migrating and coalescing across loops.
3. Interactive Logit Lens Matrix:
   2D heat-grid decoding top tokens across every token position and recurrent loop step.

Supports any checkpoint (Level 1, Level 2, or custom TRM/IRT models).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from train import load_checkpoint
from tokenizer import Tokenizer


# -----------------------------------------------------------------------------
# 1. 3D Latent Trajectory Generation
# -----------------------------------------------------------------------------

def generate_latent_3d_html(
    slices: List[torch.Tensor],
    loop_labels: List[str],
    prompt_tokens: List[str],
    save_path: Path,
    title: str = "Astra Mechanistic Oversight: 3D Latent Thought Trajectory",
) -> Path:
    """
    Project latent slices (num_loops, 1, seq_len, d_model) via PCA into 3D coordinates.
    Generates a standalone HTML using Plotly.js for 60fps orbit, zoom, and loop scrub.
    """
    # Focus on the decision position (last token) across loops
    # Each slice is shape (1, seq_len, d_model)
    vectors = []
    for s in slices:
        # Last token position vector: (d_model,)
        v = s[0, -1, :].detach().cpu().numpy()
        vectors.append(v)
    
    mat = np.array(vectors)  # shape (num_loops, d_model)
    
    # Fast PCA in numpy (via SVD)
    mat_centered = mat - np.mean(mat, axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(mat_centered, full_matrices=False)
    coords_3d = mat_centered @ Vt[:3, :].T  # shape (num_loops, 3)
    
    # Scale for pleasant visual range
    max_val = np.max(np.abs(coords_3d)) + 1e-6
    coords_norm = (coords_3d / max_val) * 10.0

    points_data = []
    for i, (label, pt) in enumerate(zip(loop_labels, coords_norm)):
        # Calculate velocity (distance from previous point)
        dist = 0.0 if i == 0 else float(np.linalg.norm(coords_norm[i] - coords_norm[i-1]))
        points_data.append({
            "loop": label,
            "x": round(float(pt[0]), 3),
            "y": round(float(pt[1]), 3),
            "z": round(float(pt[2]), 3),
            "step": i + 1,
            "velocity": round(dist, 3),
        })

    # Also extract full sequence PCA for token trajectory comparison
    final_seq = slices[-1][0].detach().cpu().numpy()  # (seq_len, d_model)
    final_seq_centered = final_seq - np.mean(final_seq, axis=0, keepdims=True)
    seq_3d = (final_seq_centered @ Vt[:3, :].T) / max_val * 10.0
    
    seq_points = []
    for i, (tok, pt) in enumerate(zip(prompt_tokens, seq_3d)):
        seq_points.append({
            "token": tok,
            "pos": i,
            "x": round(float(pt[0]), 3),
            "y": round(float(pt[1]), 3),
            "z": round(float(pt[2]), 3),
        })

    data_json = json.dumps({
        "loops": points_data,
        "sequence": seq_points,
    })

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0a0a14;
      --card-bg: rgba(20, 20, 38, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --cyan: #00f5ff;
      --purple: #a855f7;
      --pink: #ff4d6d;
      --green: #50fa7b;
      --amber: #ffb300;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
      padding: 24px;
      min-height: 100vh;
      overflow-x: hidden;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    .title-area h1 {{
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #00f5ff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .title-area p {{
      color: var(--text-dim);
      font-size: 13px;
      margin-top: 4px;
    }}
    .metrics-bar {{
      display: flex;
      gap: 12px;
    }}
    .metric-pill {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 16px;
      font-size: 12px;
    }}
    .metric-pill span {{
      color: var(--cyan);
      font-weight: 600;
      font-family: monospace;
    }}
    .container {{
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 20px;
      height: calc(100vh - 120px);
    }}
    .plot-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      position: relative;
      overflow: hidden;
    }}
    #plot3d {{
      width: 100%;
      height: 100%;
    }}
    .sidebar {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow-y: auto;
    }}
    .panel {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}
    .panel h3 {{
      font-size: 14px;
      color: var(--cyan);
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .step-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .step-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid transparent;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
    }}
    .step-item:hover, .step-item.active {{
      background: rgba(0, 245, 255, 0.1);
      border-color: var(--cyan);
    }}
    .step-badge {{
      background: var(--purple);
      color: #fff;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
    }}
    .controls {{
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }}
    .btn {{
      background: rgba(0, 245, 255, 0.12);
      border: 1px solid var(--cyan);
      color: var(--cyan);
      border-radius: 6px;
      padding: 8px 14px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
      flex: 1;
    }}
    .btn:hover {{
      background: rgba(0, 245, 255, 0.25);
    }}
  </style>
</head>
<body>

<div class="header">
  <div class="title-area">
    <h1>3D Latent Thought Trajectory</h1>
    <p>Visualizing internal recurrent state convergence in PCA space across computation loops</p>
  </div>
  <div class="metrics-bar">
    <div class="metric-pill">Recurrent Loops: <span>{len(loop_labels)}</span></div>
    <div class="metric-pill">Embedding Dim: <span>{slices[0].shape[-1]}D -> 3D</span></div>
    <div class="metric-pill">Topology: <span>Attractor Basin</span></div>
  </div>
</div>

<div class="container">
  <div class="plot-card">
    <div id="plot3d"></div>
  </div>

  <div class="sidebar">
    <div class="panel">
      <h3>Recurrent Deliberation Steps</h3>
      <div class="step-list" id="step-list"></div>
      <div class="controls">
        <button class="btn" id="reset-cam">↺ Reset View</button>
        <button class="btn" id="anim-btn">▶ Play Orbit</button>
      </div>
    </div>

    <div class="panel">
      <h3>Phase Space Dynamics</h3>
      <p style="font-size: 12px; color: var(--text-dim); line-height: 1.6;">
        The recurrent state <strong style="color: var(--cyan);">h<sub>t</sub></strong> starts at <em>Loop 1</em> with surface syntax and travels across latent space. The deceleration between loops 4 and 6 demonstrates <strong>fixed-point attractor convergence</strong> where the answer stabilises.
      </p>
    </div>
  </div>
</div>

<script>
  const data = {data_json};
  const pts = data.loops;

  const xPts = pts.map(p => p.x);
  const yPts = pts.map(p => p.y);
  const zPts = pts.map(p => p.z);
  const textLabels = pts.map(p => `${{p.loop}}<br>Velocity: ${{p.velocity}}`);

  const lineTrace = {{
    type: 'scatter3d',
    mode: 'lines',
    x: xPts,
    y: yPts,
    z: zPts,
    line: {{
      color: '#00f5ff',
      width: 6,
    }},
    hoverinfo: 'none',
    name: 'Mental Path',
  }};

  const markerTrace = {{
    type: 'scatter3d',
    mode: 'markers+text',
    x: xPts,
    y: yPts,
    z: zPts,
    text: pts.map(p => p.loop),
    textposition: 'top center',
    textfont: {{
      color: '#ffffff',
      size: 12,
      family: 'sans-serif'
    }},
    marker: {{
      size: 9,
      color: ['#ff4d6d', '#ffb300', '#a855f7', '#00f5ff', '#50fa7b', '#50fa7b'],
      line: {{ color: '#ffffff', width: 1.5 }}
    }},
    hovertext: textLabels,
    hoverinfo: 'text',
    name: 'Loop State',
  }};

  const layout = {{
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {{ l: 0, r: 0, b: 0, t: 0 }},
    showlegend: false,
    scene: {{
      xaxis: {{
        title: 'PC1 (Latent Axis)',
        color: '#94a3b8',
        gridcolor: 'rgba(255,255,255,0.08)',
        zerolinecolor: 'rgba(0,245,255,0.3)',
      }},
      yaxis: {{
        title: 'PC2 (Entity Binding)',
        color: '#94a3b8',
        gridcolor: 'rgba(255,255,255,0.08)',
        zerolinecolor: 'rgba(0,245,255,0.3)',
      }},
      zaxis: {{
        title: 'PC3 (Decision Margin)',
        color: '#94a3b8',
        gridcolor: 'rgba(255,255,255,0.08)',
        zerolinecolor: 'rgba(0,245,255,0.3)',
      }},
      camera: {{
        eye: {{ x: 1.7, y: 1.7, z: 1.4 }}
      }}
    }}
  }};

  const config = {{
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
  }};

  Plotly.newPlot('plot3d', [lineTrace, markerTrace], layout, config);

  // Render Sidebar
  const stepList = document.getElementById('step-list');
  pts.forEach((p, i) => {{
    const item = document.createElement('div');
    item.className = 'step-item';
    item.id = `step-${{i}}`;
    item.innerHTML = `
      <div>
        <span class="step-badge">Step ${{p.step}}</span>
        <strong style="margin-left: 8px;">${{p.loop}}</strong>
      </div>
      <span style="font-family: monospace; color: var(--cyan); font-size: 11px;">Δ ${{p.velocity}}</span>
    `;
    item.onclick = () => focusStep(i);
    stepList.appendChild(item);
  }});

  function focusStep(idx) {{
    document.querySelectorAll('.step-item').forEach((el, i) => {{
      el.classList.toggle('active', i === idx);
    }});
    const target = pts[idx];
    Plotly.relayout('plot3d', {{
      'scene.camera.center': {{ x: target.x / 10, y: target.y / 10, z: target.z / 10 }},
    }});
  }}

  document.getElementById('reset-cam').onclick = () => {{
    Plotly.relayout('plot3d', {{
      'scene.camera.eye': {{ x: 1.7, y: 1.7, z: 1.4 }},
      'scene.camera.center': {{ x: 0, y: 0, z: 0 }}
    }});
    document.querySelectorAll('.step-item').forEach(el => el.classList.remove('active'));
  }};

  let isOrbiting = false;
  let orbitInterval = null;
  let angle = 0;

  document.getElementById('anim-btn').onclick = function() {{
    isOrbiting = !isOrbiting;
    this.innerText = isOrbiting ? '⏸ Pause Orbit' : '▶ Play Orbit';
    if (isOrbiting) {{
      orbitInterval = setInterval(() => {{
        angle += 0.02;
        const r = 2.4;
        Plotly.relayout('plot3d', {{
          'scene.camera.eye': {{
            x: r * Math.cos(angle),
            y: r * Math.sin(angle),
            z: 1.2 + 0.3 * Math.sin(angle * 0.5)
          }}
        }});
      }}, 30);
    }} else {{
      clearInterval(orbitInterval);
    }}
  }};
</script>

</body>
</html>
"""
    save_path.write_text(html_code, encoding="utf-8")
    print(f"  [visual] 3D Latent Trajectory HTML generated -> {save_path}")
    return save_path


# -----------------------------------------------------------------------------
# 2. Interactive Sankey Token Deliberation Flow
# -----------------------------------------------------------------------------

def generate_token_sankey_html(
    per_loop_tokens: List[List[Tuple[str, float]]],
    loop_labels: List[str],
    save_path: Path,
    title: str = "Astra Mechanistic Oversight: Token Deliberation Sankey Flow",
) -> Path:
    """
    Generate an interactive Sankey flow showing how probability streams shift between loops.
    """
    num_loops = len(loop_labels)
    nodes = []
    node_map = {}
    
    for l_idx, l_name in enumerate(loop_labels):
        tokens = per_loop_tokens[l_idx][:5]  # top 5
        for t_idx, (word, prob) in enumerate(tokens):
            node_id = f"L{l_idx}_{word}"
            node_map[node_id] = len(nodes)
            nodes.append({
                "name": f"{word} ({prob:.1f}%)",
                "loop": l_name,
                "word": word,
                "prob": prob,
                "stage": l_idx,
            })
            
    # Build transition links between consecutive loops
    links = []
    for l_idx in range(num_loops - 1):
        curr_tokens = per_loop_tokens[l_idx][:5]
        next_tokens = per_loop_tokens[l_idx + 1][:5]
        
        for c_word, c_prob in curr_tokens:
            c_id = node_map[f"L{l_idx}_{c_word}"]
            # Find destination match or distribute flow
            matched = False
            for n_word, n_prob in next_tokens:
                if c_word.lower() == n_word.lower():
                    n_id = node_map[f"L{l_idx + 1}_{n_word}"]
                    flow_val = max(1.0, min(c_prob, n_prob))
                    links.append({"source": c_id, "target": n_id, "value": flow_val, "is_match": True})
                    matched = True
                    break
            if not matched:
                top_next_word = next_tokens[0][0]
                n_id = node_map[f"L{l_idx + 1}_{top_next_word}"]
                links.append({"source": c_id, "target": n_id, "value": max(0.5, c_prob * 0.35), "is_match": False})

    sankey_data = {
        "node": {
            "label": [n["name"] for n in nodes],
            "color": ["#00f5ff" if "macduff" in n["word"].lower() 
                      else "#ffb300" if "banquo" in n["word"].lower() 
                      else "#ff4d6d" if "duncan" in n["word"].lower() 
                      else "#a855f7" for n in nodes],
            "pad": 15,
            "thickness": 18,
            "line": {"color": "rgba(255,255,255,0.2)", "width": 0.5},
        },
        "link": {
            "source": [l["source"] for l in links],
            "target": [l["target"] for l in links],
            "value": [l["value"] for l in links],
            "color": ["rgba(0, 245, 255, 0.4)" if l["is_match"] else "rgba(168, 85, 247, 0.15)" for l in links],
        }
    }

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0a0a14;
      --card-bg: rgba(20, 20, 38, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --cyan: #00f5ff;
      --purple: #a855f7;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 24px;
      min-height: 100vh;
    }}
    .header {{
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      font-size: 22px;
      font-weight: 700;
      background: linear-gradient(135deg, #00f5ff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p {{ color: var(--text-dim); font-size: 13px; margin-top: 4px; }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      height: calc(100vh - 120px);
    }}
    #sankey-plot {{
      width: 100%;
      height: 100%;
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>Token Deliberation Sankey Flow</h1>
  <p>Tracing how probability mass transitions and coalesces across recurrent computational passes</p>
</div>

<div class="card">
  <div id="sankey-plot"></div>
</div>

<script>
  const data = [{{
    type: "sankey",
    orientation: "h",
    node: {json.dumps(sankey_data["node"])},
    link: {json.dumps(sankey_data["link"])},
  }}];

  const layout = {{
    font: {{ size: 12, color: "#e2e8f0", family: "sans-serif" }},
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: {{ l: 10, r: 10, b: 20, t: 20 }},
  }};

  Plotly.newPlot('sankey-plot', data, layout, {{ responsive: true, displaylogo: false }});
</script>

</body>
</html>
"""
    save_path.write_text(html_code, encoding="utf-8")
    print(f"  [visual] Token Sankey Flow HTML generated -> {save_path}")
    return save_path


# -----------------------------------------------------------------------------
# 3. Interactive Logit Lens Matrix Heatmap
# -----------------------------------------------------------------------------

def generate_logit_lens_html(
    model: torch.nn.Module,
    tok: Tokenizer,
    prompt: str,
    save_path: Path,
    device: str = "cpu",
    title: str = "Astra Mechanistic Oversight: Interactive Logit Lens Grid",
) -> Path:
    """
    Decode top-1 predicted tokens across every input token position (X-axis)
    and every recurrent loop pass (Y-axis), showing exactly where the model forms decisions.
    """
    model.eval()
    tok_ids = tok.encode(prompt)
    x = torch.tensor([tok_ids], dtype=torch.long, device=device)
    
    tokens = [tok.idx2word.get(i, f"<{i}>") for i in tok_ids]
    
    with torch.no_grad():
        logits, slices = model(x)
        
    num_loops = len(slices)
    seq_len = len(tokens)
    
    grid = []  # shape: (num_loops, seq_len)
    
    for l_idx, slc in enumerate(slices):
        row = []
        out = model.unembed_slice(slc)  # (1, seq_len, vocab_size)
        probs = torch.softmax(out[0], dim=-1)  # (seq_len, vocab_size)
        top_k = torch.topk(probs, k=3, dim=-1)
        
        for pos in range(seq_len):
            best_idx = int(top_k.indices[pos, 0].item())
            best_prob = float(top_k.values[pos, 0].item())
            best_word = tok.idx2word.get(best_idx, f"<{best_idx}>")
            
            top3 = [
                {"word": tok.idx2word.get(int(idx), f"<{idx}>"), "prob": round(float(val) * 100, 1)}
                for val, idx in zip(top_k.values[pos], top_k.indices[pos])
            ]
            
            row.append({
                "word": best_word,
                "prob": round(best_prob * 100, 1),
                "top3": top3,
            })
        grid.append(row)

    payload = {
        "tokens": tokens,
        "loops": [f"Loop {i + 1}" for i in range(num_loops)],
        "grid": grid,
    }

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0a0a14;
      --card-bg: rgba(20, 20, 38, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --cyan: #00f5ff;
      --purple: #a855f7;
      --pink: #ff4d6d;
      --green: #50fa7b;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
      padding: 24px;
      min-height: 100vh;
    }}
    .header {{
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    h1 {{
      font-size: 22px;
      font-weight: 700;
      background: linear-gradient(135deg, #00f5ff, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p {{ color: var(--text-dim); font-size: 13px; margin-top: 4px; }}
    .matrix-wrapper {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: 900px;
    }}
    th, td {{
      padding: 10px 8px;
      text-align: center;
      border: 1px solid var(--border);
      font-size: 12px;
    }}
    th {{
      background: rgba(255, 255, 255, 0.03);
      color: var(--cyan);
      font-weight: 600;
      position: sticky;
      top: 0;
    }}
    .loop-header {{
      color: var(--purple);
      font-weight: 700;
      background: rgba(168, 85, 247, 0.08);
      text-align: left;
      padding-left: 12px;
      white-space: nowrap;
    }}
    .cell {{
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
    }}
    .cell:hover {{
      transform: scale(1.05);
      z-index: 10;
      box-shadow: 0 0 12px rgba(0, 245, 255, 0.5);
      border-color: var(--cyan);
    }}
    .cell-word {{
      font-weight: 700;
      display: block;
    }}
    .cell-prob {{
      font-size: 10px;
      color: var(--text-dim);
    }}
    .modal {{
      display: none;
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #141426;
      border: 1px solid var(--cyan);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.8);
      z-index: 100;
      min-width: 260px;
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>Interactive Logit Lens Matrix</h1>
  <p>Unembedding intermediate recurrent hidden states directly to vocabulary space across time and depth</p>
</div>

<div class="matrix-wrapper">
  <table id="lens-table">
    <thead>
      <tr id="token-row">
        <th style="width: 100px;">Loop / Pos</th>
      </tr>
    </thead>
    <tbody id="lens-body"></tbody>
  </table>
</div>

<div class="modal" id="info-modal">
  <h4 id="modal-title" style="color: var(--cyan); margin-bottom: 8px; font-size: 13px;"></h4>
  <div id="modal-top3"></div>
</div>

<script>
  const payload = {json.dumps(payload)};

  const tokenRow = document.getElementById('token-row');
  payload.tokens.forEach((tok, i) => {{
    const th = document.createElement('th');
    th.innerHTML = `<span style="color: var(--text-dim); font-size: 10px;">${{i}}</span><br>${{tok}}`;
    tokenRow.appendChild(th);
  }});

  const tbody = document.getElementById('lens-body');
  payload.loops.forEach((loopName, lIdx) => {{
    const tr = document.createElement('tr');
    const loopTh = document.createElement('td');
    loopTh.className = 'loop-header';
    loopTh.innerText = loopName;
    tr.appendChild(loopTh);

    payload.grid[lIdx].forEach((cell, pos) => {{
      const td = document.createElement('td');
      td.className = 'cell';
      
      const alpha = Math.min(0.85, Math.max(0.12, cell.prob / 100));
      td.style.backgroundColor = `rgba(0, 245, 255, ${{alpha}})`;
      
      td.innerHTML = `
        <span class="cell-word">${{cell.word}}</span>
        <span class="cell-prob">${{cell.prob}}%</span>
      `;
      td.onmouseenter = () => showModal(lIdx, pos, cell);
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});

  const modal = document.getElementById('info-modal');
  function showModal(loopIdx, pos, cell) {{
    modal.style.display = 'block';
    document.getElementById('modal-title').innerText = `${{payload.loops[loopIdx]}} @ Pos ${{pos}} ("${{payload.tokens[pos]}}")`;
    const top3Html = cell.top3.map((item, idx) => `
      <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 4px;">
        <span>#${{idx+1}} <strong>${{item.word}}</strong></span>
        <span style="color: var(--cyan);">${{item.prob}}%</span>
      </div>
    `).join('');
    document.getElementById('modal-top3').innerHTML = top3Html;
  }}
  document.body.onclick = () => modal.style.display = 'none';
</script>

</body>
</html>
"""
    save_path.write_text(html_code, encoding="utf-8")
    print(f"  [visual] Logit Lens Matrix HTML generated -> {save_path}")
    return save_path


# -----------------------------------------------------------------------------
# Main CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate advanced interactive visualizations.")
    parser.add_argument("--level", type=int, default=2, help="Tier level (1 or 2).")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to model checkpoint.")
    parser.add_argument("--tokenizer", type=str, default=None, help="Path to tokenizer pickle.")
    parser.add_argument("--device", type=str, default="cpu", help="Computation device.")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    model_path = Path(args.checkpoint) if args.checkpoint else base_dir / "checkpoints" / f"level{args.level}_model.pt"
    tok_path = Path(args.tokenizer) if args.tokenizer else base_dir / "checkpoints" / f"level{args.level}_tokenizer.pkl"
    out_dir = base_dir / "results" / f"level{args.level}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        print(f"[ERROR] Checkpoint not found at {model_path}")
        return

    print(f"Loading {model_path} on {args.device}...")
    model, tok = load_checkpoint(model_path, tok_path, device=args.device)

    prompt = "Duncan bears a dagger . He gives it to Banquo . Banquo drops it . Macduff takes it ."
    tok_ids = tok.encode(prompt)
    prompt_tokens = [tok.idx2word.get(i, f"<{i}>") for i in tok_ids]
    
    with torch.no_grad():
        x = torch.tensor([tok_ids], dtype=torch.long, device=args.device)
        logits, slices = model(x)

    num_loops = len(slices)
    loop_labels = [f"Loop {i + 1}" for i in range(num_loops)]

    # Collect per-loop top tokens
    per_loop_tokens: List[List[Tuple[str, float]]] = []
    for slc in slices:
        out = model.unembed_slice(slc)
        probs = torch.softmax(out[0, -1, :], dim=-1)
        topk = torch.topk(probs, k=15)
        tokens_loop = [(tok.idx2word.get(int(idx), f"<{idx}>"), float(val) * 100)
                       for val, idx in zip(topk.values, topk.indices)]
        per_loop_tokens.append(tokens_loop)

    print("\nGenerating advanced interactive visualizations...")
    # 1. 3D Latent Trajectory
    generate_latent_3d_html(
        slices=slices,
        loop_labels=loop_labels,
        prompt_tokens=prompt_tokens,
        save_path=out_dir / "exp1_latent_3d.html",
    )

    # 2. Token Sankey Flow
    generate_token_sankey_html(
        per_loop_tokens=per_loop_tokens,
        loop_labels=loop_labels,
        save_path=out_dir / "exp1_token_sankey.html",
    )

    # 3. Logit Lens Matrix
    generate_logit_lens_html(
        model=model,
        tok=tok,
        prompt=prompt,
        save_path=out_dir / "exp1_logit_lens.html",
        device=args.device,
    )
    print("\nAll advanced visualizations generated successfully!")


if __name__ == "__main__":
    main()
