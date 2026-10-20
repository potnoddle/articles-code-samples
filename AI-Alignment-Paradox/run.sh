#!/usr/bin/env bash
set -e

echo "=================================================="
echo "   AI Alignment Formal Ground Truth Suite"
echo "=================================================="

echo ""
echo "[1/2] Running Evaluator-Optimizer Process Supervision..."
python3 evaluator_optimizer.py

echo ""
echo "[2/2] Running Formal Kernel Verification Runner..."
python3 verify_kernel.py

echo ""
echo "[PASS] All AI Alignment verification tests passed successfully!"
echo ""
