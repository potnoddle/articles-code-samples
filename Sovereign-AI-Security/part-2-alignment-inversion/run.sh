#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo "  Pillar 2: Synthetic DPO Poisoning & $5 LoRA Inversion Suite   "
echo "================================================================"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/synthetic_dpo_pipeline.py"

echo ""
echo "[PASS] Part 2 Verification Suite completed successfully."
