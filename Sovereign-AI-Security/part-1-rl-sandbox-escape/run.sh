#!/usr/bin/env bash
set -euo pipefail

echo "================================================================"
echo "  Pillar 1: RL Sandbox Escape & Transitive DNS Delegation Suite "
echo "================================================================"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/dns_sandbox_sim.py"

echo ""
echo "[PASS] Part 1 Verification Suite completed successfully."
