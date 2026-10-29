#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo "  Pillar 3: LoRA Poisoning Verifier & Matrix Spectral Analyzer  "
echo "================================================================"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/validator.py"

echo ""
echo "[PASS] Part 3 Verification Suite completed successfully."
